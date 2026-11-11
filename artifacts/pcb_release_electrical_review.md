# RevB PCB 下单前只读电气审计

2026-11-04；审计对象：[生成器](<D:/smart_fans/tools/build_perfect_revB_v3.py>)。以下主体为修改前审计快照；后续父代理授权仅修改D1–D5脚号及BluePill隔离，详见本节。**结论：仍不得直接下单装配。几何净距通过不能排除其余电路/器件身份错误。**

### 后续已完成的受限修复

- D1–D5仅交换左右pad编号，保留位置、尺寸、功能net不变；3种缓存二极管符号左A改2、右K改1，图形条杠未动。
- J_MCU_L.1、J_MCU_R.18、J_MCU_R.20改NC；只保留L3为蓝板5V供电；去掉“已对实物逐脚验证”声明，右排末脚改为常见GND/未知版型保守隔离描述。
- [新增独立测试](<D:/smart_fans/tools/test_revb_electrical_semantics.py>) AST隔离生成原理图到[测试副本](<D:/smart_fans/artifacts/electrical_semantics_check/fan_ctrl_revB.kicad_sch>)，验证实际缓存K/A编号、K条杠方向、功能网络、三NC与单5V入口，以及全部导线/标签实际连接。实跑exit0：43symbols、166pins、138connected、28NC、0错误；四负例（D1反网、R20接5V、3V3并联、缓存K编号2）均拒绝。
- 没运行完整生产生成器；旧PCB/Gerber仍需父代理重建，新增NC改变网络拓扑，必须重新布线/验证（不能只用旧铜）。USB反灌、L1/C1、ASR与实物版型仍未闭环；不宣称此局部测试为放行。


## 1. 阻断汇总

|优先级|发现|确定性|最小行动|
|---|---|---|---|
|P0|常见BluePill右排20为GND，设计却为+5V|公开参考板针表与设计其余19脚一致；用户具体变种待确认|R20先设NC，确认实物后接GND，绝不可先保留+5V|
|P0|D1–D5缓存符号1=A、2=K，违反标准KiCad二极管/LED的1=K、2=A约定|脚本直接证据；官方本地库待父代理安装后复核|同时修pad编号、缓存符号、K丝印/装配极性，不只换符号|
|P1|L1 C2826666实际DMBJ 0.72A，不是Sunlord 1.4A|商城+关联制造商PDF双证据|重新选择满足峰值/温升电流的真实功率电感并改封装|
|P1|C1输入纹波能力与5V/2A目标不匹配|340mA商城参数；2A理想buck估算约986mArms|重选高纹波输入电容/并联方案并保留容量、温度降额|
|P1|BluePill和U3的3V3输出硬并联，外部5V可能回送USB|母板连接确定；实际蓝板稳压器/USB结构待实物确认|分离蓝板3V3与母板3V3；USB VBUS断开或设计真正双向电源隔离|
|P1待证|ASR双排7P映射没有模块版型证据，可能TX/TX及MIC负端错误|缺证，不宣称已确定错线|拿到对应版型针表；未拿到前改独立可跳接接口而非假定直插|

## 2. 二极管最小修复矩阵：保留位置和功能网络，只重编号

当前每个二极管的左焊盘都为1(A)，右焊盘2(K)。若目标为最小铜变化，可以保持每个焊盘的xy、size、net完全不动，仅把**左pad编号1→2，右pad编号2→1**；缓存图中左A也改number2，右K改number1。这样功能电路和铜网保持不变，同时采用标准1K2A定义。K侧丝印必须在右；不可同时又交换左右net，否则等于二次反转。若改用官方左K右A符号，重新提取其pin坐标即可，不要求原理图方向和PCB左右相同。

|元件|左物理焊盘，修后2=A|右物理焊盘，修后1=K|代码位置|
|---|---|---|---|
|D1续流|GND|XL1509_SW|[132–135](<D:/smart_fans/tools/build_perfect_revB_v3.py#L132-L135>)|
|D2防反接|+12V_RAW|+12V_IN|[99–102](<D:/smart_fans/tools/build_perfect_revB_v3.py#L99-L102>)|
|D3钳位|BUZ_DRV|+5V|[237–240](<D:/smart_fans/tools/build_perfect_revB_v3.py#L237-L240>)|
|D4|+5V|LED_5V_K|[187–190](<D:/smart_fans/tools/build_perfect_revB_v3.py#L187-L190>)|
|D5|+3.3V|LED_3V3_K|[199–202](<D:/smart_fans/tools/build_perfect_revB_v3.py#L199-L202>)|

缓存定义证据：[887–888](<D:/smart_fans/tools/build_perfect_revB_v3.py#L887-L888>)、[893–916](<D:/smart_fans/tools/build_perfect_revB_v3.py#L893-L916>)。当前图形A/K与其网络功能一致，问题是冒用标准库ID但脚号反标准，并且没有可信装配极性闭环；不是声称裸铜无器件时已经物理短路。按标准封装极性贴D1将SW对地正向导通，D2将阻止正常输入，D3使蜂鸣器驱动导通时形成旁路电流。还应核实每个SKU实际封装和外壳极性标记，不能从库名推出真实料号。

官方远端Device库本轮raw请求失败，GitHub API未返回content导致KeyError；本地官方库由父代理安装后复核。不能把这一失败说成已经完成官方库逐字比较。

## 3. 电源额定、纹波和布局

### L1明确物料错误

[商城C2826666](https://item.szlcsc.com/2970870.html)：DMBJ(振宝佳)，CD54-470M 47UH，47uH±20%，额定720mA，DCR370mΩ，非屏蔽，5.8×5.2mm。[关联制造商PDF](https://atta.szlcsc.com/upload/public/pdf/source/20220324/2A0FB68E0EC6121FE8827F0972651A65.pdf)已用pypdf抽取，CD54-470M表格明确47±20%、DCR max .37Ω、IDC max .72A；末页定义为初始电感降低25%或温升40℃先达到者（参考环境20℃）。不是可以承受2A的零件，也不能把0.72A理解成独立的宽裕饱和电流。

[现代码138–141](<D:/smart_fans/tools/build_perfect_revB_v3.py#L138-L141>)写Sunlord、1.4A，均与该SKU不符。即使仅按错误的1.4A也不支持2A。

理想CCM初筛，12→5V、150kHz、47uH：D≈5/12；ΔIL=Vo(1−D)/(Lf)≈0.414App；2A输出Ipeak≈2.207A，ILrms≈2.004A。L容差−20%、fmin127kHz时Δ≈0.611App，Ipeak≈2.305A；尚未计输入范围、温漂、启动和限流。该电感2A时仅铜损约1.48W，远超其额定使用点。优先按XL1509推荐68uH并选择有独立Isat/Irms曲线的器件；正常2A初筛Isat至少高于计算峰值且留余量（例如≥3A），但故障限流处的饱和必须另核，不能把“3A”当任意条件保证。

### C1输入RMS不应只核容量

[现有电容证据](<D:/smart_fans/docs/hardware/component-evidence.md#L20>)记录C1 C134665为340mA@100kHz。理想buck ICin,rms≈Iout√[D(1−D)]：2A时≈0.986A，1A时≈0.493A；小100nF旁路不能凭空承担此低频电流。换用纹波额定至少覆盖负载、温度、频率的真实低阻抗输入电容，必要时扩大封装/并联并计算分流。该估算不是实测温升，也不意味任何低负载下必坏。

### 布局尚未通过电源专用评审

[XL1509原厂手册](https://www.xlsemi.com/datasheet/XL1509-EN.pdf)，[本地PDF](<D:/smart_fans/docs/hardware/sources/XL1509-EN.pdf>)第6页fosc127/150/173kHz、限流4A为typ；第7页要求功率粗线短、地平面、FB避开电感磁通，输入旁路紧贴pin1与5–8；第8页5V/2A、最大Vin20V参考68uH，第10页12→5V/2A亦68uH。47uH不是凭数值就必错，必须核完整电流和稳定性。

现坐标U2 SW=(33.4,6.365)、D1 K=(44.3,7)、L1 SW=(46.9,7)，SW端物理跨度已经13.5mm；U2 FB=(33.4,7.635)、C3正=(55.25,7)，跨度21.86mm。自动路由仅通连/避障，不自动满足最小开关回路、Kelvin反馈、散热。建议把D1紧贴U2 SW/GND、C1及适当MLCC紧贴VIN/GND、L1跟随SW，C3紧跟L1；FB从C3正端独立安静取样、避免与SW并行。0.5mm线宽不能等价为2A温升合格，过孔/热岛/铜厚亦需核算。

## 4. BluePill：一个具体短路风险和两个供电架构风险

[STM32-base参考针表](https://stm32-base.org/boards/STM32F103C8T6-Blue-Pill.html)Header1从VBAT、PC13…NRST到18=3V3、19=GND、**20=GND**；与现右排其它19脚匹配。设计[371行](<D:/smart_fans/tools/build_perfect_revB_v3.py#L371>)却标5V。因此插常见BluePill会将母板5V短地。该公开参考不是ST官方板标准，也不能替代用户实物；最快安全做法是R20先不接任何网，只依赖已确认的GND脚，再拿实物通断确认后接GND。

母板[U3](<D:/smart_fans/tools/build_perfect_revB_v3.py#L156-L176>)输出+3V3硬接蓝板[左1、右18](<D:/smart_fans/tools/build_perfect_revB_v3.py#L325-L371>)；又接5V到蓝板左3，故常见板内LDO与母板LDO输出并联，无均流/隔离。不要把两个都是3.3V当成可并联保证。最小方案：母板U3只供外设，蓝板两个3V3脚NC，蓝板只由隔离后的5V供电（共地）；为避免不同上电顺序时IO反灌，还需核限流/上电策略。另一方案是保留母板3V3并停用/移除蓝板LDO，但需用户改实物，不宜默认。

该页面还明确警告蓝板5V直连USB VBUS无保护。仅在母板→蓝板5V串一只二极管**不能阻止母板给USB主机VBUS送电**，因为蓝板侧仍直连。可选：只使用不带VBUS的USB数据连接；或在蓝板USB VBUS路径隔离/使用电源MUX；或改SWD调试并禁止USB外电同时接。仅丝印提醒属于使用限制，不是硬件防反灌设计。

## 5. ASR-PRO：必须保留为未知，不凭泛称造针表

[当前左排395–401](<D:/smart_fans/tools/build_perfect_revB_v3.py#L395-L401>)按+5V,GND,VOICE_TX,VOICE_RX,NC×3；[右排409–415](<D:/smart_fans/tools/build_perfect_revB_v3.py#L409-L415>)按SPK+,SPK−,MIC+,GND,NC×3；排距15.24mm。[用户清单](<D:/smart_fans/docs/hardware/user_modules.md#L25-L26>)只有30×28×2.9、双排7P、5V、UART，并没有这份逐脚顺序或排距证据。

MCU PA2(TX)连VOICE_TX、PA3(RX)连VOICE_RX。若模块L3真的叫TX，那么是TX对TX、RX对RX；若L3是RX，则当前网名只是MCU视角，没有错。必须用实物对应版型文档判定，不能直接盲换。MIC1负端接GND，而清单称差分偏置输入；若实际模块MIC−不是GND则错误，当前也未有证据。SPK−没有接地，保留差分/BTL结构是合理的，但仍待对应模块确认。

尝试[天问ASR核心板PDF](https://haohaodada.com/jpeguploadfile/twen/ASRPRO/asr_pro_core.pdf)：工具不解PDF，requests又超时，没有取得可用逐脚原文。世强的泛ASR介绍不是该板针表，未用于批准映射。

最小可落地办法：在版本无法确认时，不做不可变2×7直插假定；保留5V/GND/MCU_TX/MCU_RX独立有字连接器（UART可用交叉跳线），MIC/SPK直接接模块原有插座，不经未经确认的母板针脚。模块实测逻辑电平与5V启动电流仍须补齐。此举牺牲直插便利但能消除“未知针序硬接电源”的风险；需父代理/用户确认后再改板。

## 6. 放行最低证据

1. 独立断言每个二极管1K2A与目标功能网、装配K标记一致；参考真实SKU图纸，而不只比较缓存自洽。
2. BluePill R20与GND实测通断/清晰对应版型资料，3V3不硬并联，USB电源互锁方案闭环。
3. 选定真实L1与C1，额定电流/纹波/散热覆盖目标负载；130电机型号不明时，不默认可以5V或12V，不默认启动/堵转电流小于预算。
4. ASR对应针表证据或安全可跳接接口；确认TX交叉、MIC偏置/差分、5V峰值预算。
5. 电源区专用布局复核后再跑原生ERC/DRC、几何与Gerber一致性；限流台架先测空载、阶跃负载、纹波、温升和USB隔离。不把无ERC错误称为功能保证。
