# RevB 单5V电气独立复核

日期：2026-11-04。范围：读取最终PCB实际网络、生成器物料定义、本地器件PDF及原厂公开资料；不改生成器、固件或交付物。不把静态一致性等同于SPICE或实物验证。

**结论：不能电气放行。** 电源基本极性与模块标称电压未发现新反接错误，但AMS1117输出电容/稳定性、最低负载、保护协调及分电源域反供仍未闭环。此结论独立于其他代理正在调查的原生DRC错误。

## 1. 实际产物，而非仅比较生成器常量

[独立提取脚本](<D:/smart_fans/artifacts/simulation_review/extract_electrical_pcb_nets.py>)使用sexpdata直接解析[最终PCB](<D:/smart_fans/hardware/kicad/fan_ctrl_revB.kicad_pcb>)，未导入构建脚本。脚本已执行成功，提取48元件，完整结果在[PCB网络提取](<D:/smart_fans/artifacts/simulation_review/electrical_pcb_nets.json>)。

PCB SHA256：`c9cb106cdc48e9b3e44ff9b6d379062e31b24f2d6fec1b29f22d64fc3b3264a1`。

| 实际网络 | 复核 |
|---|---|
| DC1.1→+5V_RAW→F1.1，F1.2→+5V_FUSED→Q_PWR.5/6/7/8 | 保险串联，未见网名级旁路；仍须实际铜连通/DRC覆盖 |
| Q_PWR.1/2/3→+5V，Q_PWR.4→GND | 与AO4409 S1/2/3、G4、D5/6/7/8的反接保护用法一致 |
| U3.1→GND，U3.2及tab2→+3.3V，U3.3→+5V | AMS1117固定输出接法正确 |
| +3.3V仅C6=10uF、C7=100nF直接对地 | 没有输出电解/钽电容；不能把+5V上的C1/C3/C_VM算到LDO输出侧 |
| JP_USB把+5V和+5V_MCU分开，后者只给MCU左3；MCU左1/右18均NC | 避免两个3.3V稳压器直接并联；拔电源跳帽不隔离信号 |
| JP_ASR电源以及JP_ASR_TX/RX分别串联三条域间线路 | 三跳帽都拔出才切断所列供电/UART路径；不是自动互锁 |
| TB右1=+5V、右2=+3.3V；左4=TB_STBY并10k下拉；左5/6/7=GND，右6/7=NC | VM/VCC标称电压适配；未用B桥输入固定，输出悬空正确 |

原理图网与PCB全量逐针一致性由主审核的独立追踪检查负责；本脚本仅为实际PCB物理pin/net取证，不自行宣称新一轮完整网表或连通检查PASS。

## 2. 优先阻断：AMS1117-3.3 稳定性证据不足

[生成器:152–176](<D:/smart_fans/tools/build_perfect_revB_v3.py#L152-L176>)指定U3为Advanced Monolithic Systems AMS1117-3.3/C6186；C6为FH 0805B106K160NT/C15849，10uF陶瓷。实际PCB确有这个10uF输出电容而无带受控ESR的储能电容。

[LCSC准确SKU页面](https://www.lcsc.com/product-detail/C6186.html)标题确认Advanced Monolithic Systems，不可拿Slkor、ARTSCHIP、TI LM1117等同名近似器件手册代替。此次读到的[Unikey镜像](https://www.unikeyic.com/media/datasheet/65/38/935a/65/194a3cf5bec03c1a9105ac3cdce1c334.pdf)实为Slkor，**明确排除，不采其10uF/10mA/热阻作本器件验收**。

[AMS原厂地址](http://www.advanced-monolithic.com/pdf/ds1117.pdf)未成功提取：HTTP请求403，HTTPS握手失败；检索及[二手实验记录](https://raw.githubusercontent.com/tardate/LittleArduinoProjects/refs/heads/main/Electronics101/Power/LinearRegulators/AMS1117/README.md)提到22uF钽建议，但二手资料不能作为精确全温ESR要求的唯一依据。

因此当前状态为**未证明稳定，不是已经证明必振荡**。必须取得该准确厂牌手册，确认固定3.3V版本允许的输出电容、ESR、偏压有效容量、全负载温度条件；然后选择满足要求的电容或换经验证可用陶瓷的LDO（更换需重新核封装/脚号/电压及布局）。不能用理想3.3V电压源仿真盖过此项。

最低负载同样待核：D5是蓝LED串1k，实际低负载电流取决于Vf，在临界导通附近可能很小；OLED熄屏/TB待机/模块未插时不能认定总有数mA。拉高状态的I2C/DHT上拉也不构成持续负载。**未拿原厂适用条款前不宣称固定输出必需某个5mA/10mA值。**

功耗基本式P≈(Vin−3.3)Iout+Vin·Iq：5V、100mA时仅通路损耗0.17W；300mA为0.51W，1A为1.7W。原描述“1A”不等于本板可连续输出1A。热阻、地铜不连接输出tab的实际散热条件、Iq、环境温度均未实测，尚无温升PASS。

## 3. AO4409、保险与系统过流

此次直接读取[AO4409原厂Rev8.0](https://www.aosmd.com/sites/default/files/res/datasheets/AO4409.pdf)前两页：30V P-MOS，VGS绝对值20V；RDS(on)在−4.5V/25°C给12mΩ上限。当前S为负载、D为输入，正接从D→S体二极管启动，门极接地后负VGS导通；反接在无其他电源注入条件下阻断。

2A、12mΩ的沟道损耗0.048W只是室温条件计算，不包括热增阻、保险和接头、铜路；原厂热数据基于1in²/2oz板，不得直接移植。**MOS导通沟道双向，不能阻止USB/舵机/电机再生回灌输入，也不保护12V误接。** 3A保险不能把母板限在2A，更不能自动保护额定较小的H桥或GPIO。

[保险补证](<D:/smart_fans/docs/hardware/power_parts_followup.md#L9-L10>)尚缺准确原厂时间-电流/I²t/温度降额闭环；短路源若为折返电源，可能长时间在不熔断电流区工作。此处保持保护协调未通过，而不是把“fast fuse”当即时保护。

## 4. TB6612边界（原厂本地PDF）

读取[Toshiba手册](<D:/smart_fans/artifacts/electrical_evidence/tb6612.pdf>)及[文本](<D:/smart_fans/artifacts/electrical_evidence/tb6612.txt#L150-L159>)：VCC工作2.7–5.5V、VM2.5–13.5V；VM≥4.5V的H-SW推荐输出上限1.0A，VM<4.5V时0.4A。3.2A是10ms单脉冲**绝对最大**，2A是20ms且占空≤20%条件，不是连续能力。

当前VM5V/VCC3.3V标称处于工作区；VIH≥0.7VCC=2.31V，VIL≤0.3VCC=0.99V，名义3.3V MCU输出匹配。真实MCU与母板两颗LDO的容差、低压启动和压降仍要测，不把名义电压相同当全角落验证。

[手册:709–718](<D:/smart_fans/artifacts/electrical_evidence/tb6612.txt#L709-L718>)明确热关断不能保证所有条件下保护。当前没有电流检测回路，未知130电机堵转电流；3A总熔丝无法保证先于H桥损坏动作。首通电不得直接加载未知电机；测堵转电流须限时限流并符合电机/驱动额定，必要时改支路保护/驱动。母板2A总目标不可改写为电机通道2A额定。

## 5. 电源域/上电状态仍需禁止或设计隔离

- MCU电源跳帽拔掉而母板仍上电时，母板+3.3V经R_SCL/R_SDA/R_DHT及模块信号接到未供电MCU；不能因为两处3V3为NC就断言无反供。
- MCU USB单侧上电、母板掉电时，MCU推挽输出可能越过TB6612的VCC+0.2V工作输入上界；实际注入电流取决于未核保护结构。禁止以这种状态驱动GPIO。
- ASR三跳帽都断开可切所列5V/TX/RX路径；只拔电源跳帽不足。真实ASR板与USB控制结构仍遵[已有独立电源路径证据](<D:/smart_fans/artifacts/asr_power_path_followup.md>)，不同版本不能混用。
- “两边均供电”操作条件不能保证上电先后过程安全。没有Ioff缓冲/硬互锁时，需明确禁用单侧供电、断电接插并实测序列；不能宣称USB任意热插拔安全。

## 6. 历史仿真不可继续标当前通过

[旧脚本](<D:/smart_fans/tools/simulate_circuits.py>)仿真12V/XL1509、S8050、AO3400四线风扇、DS18B20，不是现单5V/TB6612/2N3904/DHT11。515–635us传感器应答是硬编码，最后无条件打印成功；I2C以2.2RC的10–90%指标比较30–70%规范也不一致。正确一阶RC的30–70%系数为ln(7/3)=0.8473。

[旧LTspice日志](<D:/smart_fans/hardware/ltspice/buzzer_flyback.log>)证明11月3日确实运行过LTspice26.1.1，不能说历史从未仿真；但[旧输入](<D:/smart_fans/hardware/ltspice/buzzer_flyback.cir>)仍是S8050/PB14及假定100Ω+5mH负载，模型无器件来源、无晶体管击穿参数，不能验证当前器件安全。[旧报告100%通过结论](<D:/smart_fans/hardware/SIMULATION_REPORT.md#L97-L107>)不适用于当前版本，应明确撤销当前适用性而非重复运行旧脚本重获PASS。

## 7. 最小整改候选（仅建议，未改源）

**TI TLV1117LV33DCYR**，证据为[TI原厂PDF](https://www.ti.com/lit/ds/symlink/tlv1117lv.pdf)，SBVS160C（Jan2023），包装附录2026年更新。此次直接requests下载并pypdf读取原文；不是套用其他1117厂牌。

- P3：GND=1，OUT=2及Tab，IN=3，与当前逻辑脚序相符。P18准确订购号33DCYR为Active、SOT223/DCY4pin、3.3V版本。
- P1/P13：零负载稳定、允许0Ω ESR陶瓷。要求输出名义1µF陶瓷，计入偏压/温度/老化后的有效容量**>0.5µF**；推荐X5R/X7R。当前10µF陶瓷不能仅凭标称直接签核有效容量，但相较0.5µF门槛有条件余量，须核精确C15849曲线及容差。
- P4：推荐VIN 2–5.5V，绝对6V。现5V系统只在适配器及再生/热插拔瞬态保持≤5.5V时适用；不能接12V。5V±5%有静态余量，不等于电机再生尖峰已被限制。
- P5：3.3V版本1A dropout最大700mV；没有最低负载要求。不能把器件1A能力变成当前板热承诺，仍按实际负载计算P=(Vin−3.3)I。
- P11：OUT高于IN时内置体二极管反向导通且不受限；持续反向工作建议外部限至额定电流5%（1A的5%=50mA）。它**不是反供隔离器**，USB和IO状态要求仍保留。
- P14：输入/输出电容尽量贴近引脚，输出电容地直接回到GND脚；选型替换不能忽略现布线回路。
- P22/23封装推荐版图：TI示例pad中心排距5.8mm，三个小pad0.95×2.15mm、大pad3.25×2.15mm，针间距2.3mm。当前KiCad通用SOT223旋转封装pad排距6.3mm、小pad1.5×2.0、大pad3.8×2.0。脚序/封装族相同但推荐焊盘不同，**未签核无改板完全兼容**；主代理可按实际引脚公差覆盖再决定是否保留通用pad，不能仅凭同为SOT223下单。
- 未核准确库存/价格/LCSC替代码；若采用需同步BOM、SCH库名/值及相关测试，不可只换BOM而保留AMS声明。

这是可减少稳定性证据缺口的候选，不是自动放行。也可继续取得AMS准确手册并据其要求修电容，但不能无条件把传统AMS与陶瓷稳定LV系列等同。

## 完成与保留

已完成实际PCB网提取、AO4409原厂额定复读、TB6612原厂工作范围复读及电源域风险复核。未完成AMS准确手册、稳定性模型、原生DRC修复、模块额定/全负载热测试及完整固件功能。建议继续保持暂停投板状态，尤其不可仅因几何14项通过解除上述问题。
