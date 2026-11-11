# RevB 单5V电源改版：拓扑、证据与放行条件

## 状态
这是电源局部改版，不是量产签核。仅运行隔离组件/原理图测试，没有运行整板布线、Gerber或BOM构建。所有新增物料库存和采购价格未核；未核LCSC编号用 `-`，不编造现货编号。

## 已实现拓扑
- 唯一输入 DC1：稳压5V（要求板端4.75–5.25V），Phoenix Contact **1729128 / MKDS 1,5/2-5,08** 两针螺丝端子。1=正，2=GND。**严禁12V**。外置5V5A仅是供电容量，不是板载额定电流。
- DC1.1 → `+5V_RAW` → F1 **Littelfuse 0451003.MRL（3A快断）** → `+5V_FUSED` → Q_PWR **AO4409** → `+5V`。
- AO4409：1/2/3 Source 接负载+5V；4 Gate 接GND；5/6/7/8 Drain 接熔断后输入。体二极管从D到S使正常极性启动，正电压使VGS为负导通；反接时体二极管截止。**这不是双向供电隔离器，也不是过压保护器**。禁止其它接口向5V轨送电。
- 删除U2/L1/D1/D2及全部旧12V/SW网络；保留C1 100uF/25V（接保护后5V）、C2高频去耦、C3/C4滤波。
- 母板AMS1117保持独立3.3V供传感器/驱动逻辑。BluePill两处3V3仍NC，不并联两颗稳压器。
- JP_USB（Harwin M20-9990245针排 + M7566-05跳帽，库存未核）连接母板+5V与专网+5V_MCU，后者仅接BluePill L3。未更改任何MCU针序/坐标，也未更改ASR/其它模块定义。

## USB操作规则（必须印在操作说明和板上）
1. 正常脱离电脑运行：无USB线；安装JP_USB；母板5V给BluePill。
2. **任何USB线插入前，先断电并拔下JP_USB**。不依赖BluePill是否有肖特基、克隆板供电结构或USB线是否被称为“数据线”。
3. 调试时USB只供BluePill，母板必须另由DC1供电；跳帽不得插回。USB不能用于给电机/舵机/语音或母板供电。
4. 跳帽只断开电源铜路，不隔离GPIO。只给一侧上电会通过I/O保护结构寄生供电。因此装在母板上的BluePill不允许长期USB单侧上电；需安排两边供电时序、保证GPIO安全态，或将BluePill从母板拔下进行独立USB调试。**未实现自动电源切换或自动I/O隔离，不声称USB任意插拔安全。**

## 电流及布线约束
- **总连续电流2.0A是待验证设计目标，不是已验额定。** F1为3A熔丝，不是2A硬限流，不能保证超过2A立即断开。不能用标称“快断”代替时间-电流曲线/短路测试。
- 从端子、保险、MOSFET到5V分配点及对应GND主回流，外层1oz铜建议至少2.0mm连续有效宽度；单个0.5mm长线和单个0.3mm过孔不合格。MOSFET并联S/D引脚均须有效并接，在封装逃线处短距离分流而非把总电流挤到一根0.6mm焊盘。
- 电机/舵机支路建议至少1.0mm，并以实测启动、堵转、线损、铜温升重新定宽；语音/MCU支路应分开回流至电源分配处。过孔必须按铜厚/孔壁电镀建立并联容量，不给出未经证实的单孔额定。
- 2A时AO4409按25°C、VGS=-4.5V下12mΩ上限估算功耗0.048W（仅沟道，未计升温电阻增大、焊盘/线路/保险/接插件压降）。这不是实物热验证。
- 原router的0.5mm电源线规则**没有在本子任务改动**；父任务必须落实主干与回流、压降、启动和堵转保护后再放行。保险3A必须核制造商I²t、分断能力以及5V5A适配器短路模式，不能假定可保护所有细支路/模块。
- 母板3.3V先以<=100mA设计预算审查（AMS1117压差耗散约0.17W，不是直接宣称1A可用）；现有输出电容/ESR与准确器件来源稳定性仍须核。
- 电机额定未知：仅确认现在输出源为5V，**不能声称该电机在5V的转速/转矩/寿命匹配**。ASR建议约500mA，MG90S启动/堵转和电机均未知，因此2A总目标不代表满足全部并发功能。电机再生/电源过冲尚无专用钳位验证。

## 已实读证据与未闭环项
1. [AO4409 原厂PDF Rev8.0 July2013](https://www.aosmd.com/sites/default/files/res/datasheets/AO4409.pdf)：30V P-MOS，VGS=-4.5V时RDS(on)<=12mΩ，SOIC8，S1/2/3 G4 D5/6/7/8；该页电流极值基于特定2oz/1in²板而不是本PCB。曾核AO4407A，其保证条件最低-6V，故未选。
2. [KiCad官方Phoenix端子封装](https://github.com/KiCad/kicad-footprints/blob/master/TerminalBlock_Phoenix.pretty/TerminalBlock_Phoenix_MKDS-1%2C5-2-5.08_1x02_P5.08mm_Horizontal.kicad_mod)：已通过GitHub Contents API实读；针距5.08mm，孔1.3mm，铜2.6mm，外形10.16x9.8mm，原点pin1。当前生成器两个THT焊盘均圆铜，避免铺铜形状不一致。
3. 官方库引用[Phoenix原厂图Farnell镜像](https://www.farnell.com/datasheets/100425.pdf)，本次请求超时；[Phoenix型号页](https://www.phoenixcontact.com/en-us/products/pcb-terminal-block-mkds-15-2-508-1729128)403。**因此孔位依据是官方EDA库，原厂机械公差/接线方向/额定电流尚未二次读图核对，不宣称已完成双证据采购签核。**
4. [KiCad官方Nano2封装](https://github.com/KiCad/kicad-footprints/blob/master/Fuse.pretty/Fuse_Littelfuse-NANO2-451_453.kicad_mod)：实读焊盘中心±2.455mm，1.96x3.15mm；body6.10x2.69mm。引用[原厂451/453资料](https://www.littelfuse.com/~/media/electronics/datasheets/fuses/littelfuse_fuse_451_453_datasheet.pdf)，本次403。**准确料号后缀/3A曲线/温度降额/分断能力/I²t仍须取得原厂页确认**。代码选型可供继续审查，尚不能将保护协调标为PASS。
5. JP_USB针排按2.54mm/1mm孔/1.7mm铜实现标准两针连接；Harwin组合型号已注明但原厂机械公差未在本次实读，采购前核实针长、跳帽兼容性及帽高（不能把跳帽值当自动隔离芯片）。

## 局部回归
`python -X utf8 tools/test_revb_electrical_semantics.py` 隔离AST提取组件与SCH导出，不导入主构建器。
- 验DC1两针、F1串联、PMOS引脚/库symbol、USB专网唯一性、原Buck完全撤销。
- 旧D1/D2测试是因为取消电路而明确撤除，不是掩盖其方向错误；保留D3/D4/D5方向与K条图形测试。
- 独立SCH几何/标签网验证：42symbols、162pins=135导线连接+27NC，errors=[]。
- 负例：D3反向、MCU_R20错5V、3V3并联、K脚号篡改；新增保险绕过、PMOS反接、JP_USB绕过均应拒绝。
- 未复用旧126pad/166pin计数；整板新计数应重新从最终生产文件测量。
