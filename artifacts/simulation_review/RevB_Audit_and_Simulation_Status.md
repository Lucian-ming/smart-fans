# RevB 单5V版：独立审核与真实求解器条件仿真记录

日期：2026-11-04。状态：**禁止投板，原打样放行结论已撤回**。本记录是审核结果，不是整机仿真通过证明。

## 1. 审计对象和撤回原因

冻结PCB SHA256：`c9cb106cdc48e9b3e44ff9b6d379062e31b24f2d6fec1b29f22d64fc3b3264a1`。下载目录的原六文件不覆盖，保留故障证据。[最高优先级禁止投板通知](<D:/下载/RevB_5V_Prototype_20261104_1856/00_暂停投板_待审核仿真.md>)。

此前14项自检并不足够，且几何检查存在实质性漏检：用Shapely `buffer(0)`修复自交铺铜时丢掉负绕向铜区域，使检查对象不再等于文件实际铜形，产生假通过。不得继续引用旧的“0短路”结论放行该包。

KiCad 10.0.7对冻结PCB的[原生DRC](<D:/smart_fans/artifacts/revb_native_drc_board_only.json>)返回exit 5，91项：23间距错误、9孔间距类错误、10阻焊桥错误、1热焊盘连接错误、48库警告；0未连接。原始边界[绕数复核](<D:/smart_fans/artifacts/native_pcb_review/winding_evidence.json>)证明BUZ_BASE及部分MCU NC引脚位置实际落在地铜内，不是单纯规则配置差异。生产Gerber使用同一畸形边界，因此也不能投板。

生成器将多个外环仅保留第一个，却把所有岛的孔都接入该外环，导致独立负绕向区域。后续必须用原生铺铜/光绘或正确多轮廓实现，并使验收拒绝歧义输入，而非自动删铜后报PASS。

## 2. 原理图原生检查

原生解析发现缓存子符号前缀不合法，例如外层`Device:C_Polarized`与内部`C_Pol_0_1`不一致。生成器已修复命名；仅在隔离目录生成候选，冻结交付文件未替换。

[原生回归](<D:/smart_fans/artifacts/native_sch_review/native_regression_summary.json>)证明40个子符号前缀正确；只归一化名称后，与冻结SCH整体S表达式相同。原生网表导出exit 0，33命名网、137已连接引脚、31 NC，逐引脚网络集合一致，错误前缀负例被拒绝。

但[ERC](<D:/smart_fans/artifacts/native_sch_review/erc.json>)仍exit 5：U3 VIN/GND两项电源未驱动错误、181连接栅格警告、44封装库和44符号库警告。解析成功不等于ERC通过；将配置、供电声明与实际电路问题分开整改，不能用清空错误列表替代修复。

## 3. 真实LTspice条件仿真

使用本机LTspice 26.1.1，独立网表批处理，保存`.cir`、`.log`、`.raw`。先执行RC解析解一致性自检；它仅检查求解器是否工作，不是性能排名或整板证明。

[结果JSON](<D:/smart_fans/artifacts/simulation_review/conditional_simulation_results.json>)绑定实际PCB、网表、日志和波形SHA256；[测量审核脚本](<D:/smart_fans/tools/audit_revb_conditional_simulations.py>)验证工况完整、真实板上阻容值及解析关系，同时要求已知失败工况确实被识别。`numerical_consistency_pass=true`，但`board_release_approved=false`。

### 3.1 I2C：18个条件工况

[网表](<D:/smart_fans/artifacts/simulation_review/revb_i2c_rc_sweep.cir>) / [日志](<D:/smart_fans/artifacts/simulation_review/revb_i2c_rc_sweep.log>)。

实际R_SCL/R_SDA各4.7kΩ接3.3V。扫描总线电容50、100、200、250、400、800pF；并扫描假设存在模块并联上拉后的4.7k、2.35k、1.5667kΩ等效值。电容和模块上拉数量不是实测。

采用30%–70%上升时间，解析式`t_r=ln(7/3)RC≈0.8473RC`，不再误用10%–90%的2.2RC。所有仿真与解析误差<1%。对照标准模式1000ns、快速模式300ns上升时间限值，18组中分别4组和12组不满足，仅代表对应假设工况。

| 4.7kΩ总上拉 | 仿真30%–70%上升时间 | 仅上升时间判定 |
|---|---:|---|
| 100pF | 398.2ns | 100kHz标准模式通过；400kHz快速模式不通过 |
| 250pF | 995.6ns | 标准模式贴近限值，无足够容差余量 |
| 400pF | 1592.9ns | 标准模式不通过 |

4.7kΩ理想电阻对应标准模式电容上限约251pF，快速模式约75pF；还需考虑电阻公差、实际模块上拉与引脚驱动。理想开漏开关的低电平结果不能认证芯片灌电流能力。未模拟地址冲突、协议、PAJ/OLED固件或真实线束寄生。

### 3.2 单5V供电：18个条件工况

[网表](<D:/smart_fans/artifacts/simulation_review/revb_supply_loop_sweep.cir>) / [日志](<D:/smart_fans/artifacts/simulation_review/revb_supply_loop_sweep.log>)。

输入4.75/5.00/5.25V；**正负完整回路总电阻**假设0.05/0.15/0.30Ω；C1+C3+C_VM名义540µF，按80%和100%扫描；总电感1µH、合并ESR50mΩ均为假设；整板总负载由0.25A阶跃到2A。不是声称电机可连续承受2A，也不是从PCB提取的精确分布模型。

稳态测量符合`Vbus=Vin−2A×Rloop`，最差假设工况最低4.150V；18组中6组低于TB6612的4.5V工作电压条件。在4.75V输入、2A总负载的集总模型中，要保持≥4.5V，总回路电阻必须≤0.125Ω，且没有额外动态余量。不能只用更大的电容修复稳态压降。

首轮一致性测试真实失败：结果多出2mV压降，追查为LTspice电感默认1mΩ串阻。已保留[首次日志](<D:/smart_fans/artifacts/simulation_review/revb_supply_loop_before_explicit_L_Rser.log>)，在网表显式设置`Rser=0`避免与总回路电阻重复计入后重跑通过；未放宽数值验收门槛。

该模型未覆盖适配器限流、真实启动/堵转电流、PCB分支与地回流、保险熔断I²t、MOS开关/反向、线束电感、温升及AMS稳压环路。失败工况说明必须约束/测量这些参数，不证明未知实物恰好属于某一工况。

## 4. 电气复审未闭环项

详见[独立电气报告](<D:/smart_fans/artifacts/simulation_review/electrical_independent_review.md>)和[模型清单](<D:/smart_fans/artifacts/simulation_review/simulator_model_inventory.md>)。

- U3确为Advanced Monolithic Systems AMS1117-3.3/C6186。实际输出仅10µF陶瓷+0.1µF；尚未取得准确型号的稳定性/ESR/最低负载证据或可信模型。不能说一定振荡，也不能说已证明稳定。蓝LED及空闲上拉不构成有保证的最低负载。
- TI TLV1117LV33DCYR是有[原厂资料](<https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf>)的陶瓷稳定候选，零负载可用、有效Cout>0.5µF，正常输入≤5.5V。但反向电流不受限，TI推荐焊盘与现通用封装须做覆盖检查，尚未替换BOM。
- TB6612资料的VM≥4.5V推荐工作电流为1A；3.2A是短脉冲绝对额定，不能当连续能力。3A总保险不保证保护未知电机的堵转状态。
- AO4409反接保护不等于防反流、过压或精确限流。准确厂商SPICE模型未取得，不借近似模型宣称器件动态安全。
- MCU拔电源跳帽不能自动隔离所有GPIO；USB单侧供电仍有反供风险。ASR烧录须按三跳帽电源/TX/RX隔离要求操作。
- 固件业务初始化仍有TODO、旧ENC_SW定义与新板不符，疑似未定义BTN_Pin需真实编译核实；连续旋转舵机不能靠旧定位舵机角度算法保证扫风边界。[启动审查](<D:/smart_fans/artifacts/revb_boot_sequence_review.md>)。

## 5. 当前允许与禁止

允许继续在隔离副本修复并运行验证。**不允许上传被冻结Gerber投板，不允许据本报告认定实物功能、热安全或整机合格。** 恢复放行需有修复后PCB/原生DRC/ERC、Gerber独立检查及绑定新文件哈希的明确结论；实测项目仍须单列，不能用仿真代替。
