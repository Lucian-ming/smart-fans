# ASR-PRO 新资料只读接口审计

审计日期：2026-11-04。未修改主设计、PCB、原理图或生成器。整机单5V输入是父任务确认的设计方向，不等于本开发板所有标为电源的脚均可随意反向供电。

## 结论

**旧30×28mm、2×7排母假设不适用于本次提供的板载CH340开发板。** 新PDF明确P1/P2均为Header 8（两个1×8），不能把旧14针直插接口继续用于新16针开发板。原理图不提供实际PCB轮廓、两排间距、Pin1朝向的机械定位或USB净空；本轮不能签署直插封装尺寸合格。若先做主板，应使用按功能标注的线束连接器，不把未知开发板排距固化成直插座。

## 来源和可复核证据

- [用户PDF](<E:/桌面/原理图/ASR-PRO语音模块资料/ASR-PRO语音模块资料/ASR-PRO开发板原理图（板载CH340）.pdf>)：图纸2022-10-10，Lu-ASR-PRO-V1.0.SchDoc。正常文字层+Altium嵌入网络连接标记，可以独立核对每个排针网络，不依赖OCR猜针序。
- [PDF文字和坐标提取](<D:/smart_fans/artifacts/user_module_sources/asr_pdf.json>)。
- [用户PNG](<E:/桌面/原理图/ASR-PRO语音模块资料/ASR-PRO语音模块资料/asr-pro开发板原理图.png>)：OCR可读CH340K/UART0等但质量低，不用其模糊字符覆盖PDF证据。[OCR记录](<D:/smart_fans/artifacts/user_module_sources/asr_ocr.json>)。
- [用户说明书](<E:/桌面/原理图/ASR-PRO语音模块资料/ASR-PRO语音模块资料/ASR-PRO开发板使用说明书.docx>)已按office技能复制并导入[审阅容器](<D:/smart_fans/artifacts/asr_manual_review.univer>)，worktree `wt-mw1ueb26-904co1`、unit `u-mw1uhcfq-2sn3bp`。但本端工具schema强制同时传code/codeFile，读取返回`INVALID_EXECUTION_SOURCE`；inspect同时range/elementIds返回`INSPECTION_INPUT_INVALID`。**正文尚未成功读取，不能声称手册确认尺寸/供电。** 未用ZIP/XML/python-docx绕过Office技能。

## 已确认电气排针表

| 接口针号 | PDF网络/功能 | 关键原始网络证据 |
|---|---|---|
| P1.1 | PA6 / RX2复用 | PIP101 PIU1013 NLPA6 |
| P1.2 | PA5 / TX2复用 | PIP102 PIU1011 NLPA5 |
| P1.3 | PA3 / RX1复用 | PIP103 PIU1010 NLPA3 |
| P1.4 | PA2 / TX1复用 | PIP104 PIU109 NLPA2 |
| P1.5 | PB6 / UART0_RX | PIP105 PIU1015 NLPB6 NLUART00RX |
| P1.6 | PB5 / UART0_TX | PIP106 PIU1014 NLPB5 NLUART00TX |
| P1.7 | VOUT | PIP107 PIQ103 PIU306等同网 |
| P1.8 | GND | PIP108 PIU105 PIU108 PIU307等同网 |
| P2.1 | SPKL+，桥接功放输出 | PIP201 PIJ201 PIU308；图文字SPKL+ |
| P2.2 | SPKL−，桥接功放输出 | PIP202 PIJ202 PIU305；图文字SPKL− |
| P2.3 | PC4 / AIN2 | PIP203 PIU1016 NLPC4 |
| P2.4 | PA1 / XOUT复用 | PIP204 PIU107 NLPA1 |
| P2.5 | PA0 / XIN复用 | PIP205 PIU106 NLPA0 |
| P2.6 | 3V3，芯片VDD33同网 | PIP206 PIU103 NL3V3 |
| P2.7 | GND | PIP207同GND网络 |
| P2.8 | PA4 / PG_EN复用 | PIP208 PIU1012 NLPA4 |

以上是**原理图引脚编号**，不是从实物某一视角的左右/上下位置。PDF中P1/P2示意符号针1在底部、针8在顶部，禁止将图纸摆放方向误当PCB实物插接朝向。

## 扬声器/麦克风

U3为8002A（符号库含LM4890名），VO1=5、VO2=8，二者均为主动输出。SPKL+接VO2(8)，SPKL−接VO1(5)，这是本图的网名，不能自行按芯片输出名重排极性。两线喇叭跨接SPKL+/SPKL−，任一端不得接GND。J2.1=SPKL+，J2.2=SPKL−；PDF BOM明确J2为`PH-2P卧式贴片2.0间距`，不是XH2.54。主板若设置XH座，应定义为不同端的转接线束，不能宣称与开发板插头直接互配。

P3为板载咪头，MICL+/MIC−相关网络；P1/P2没有麦克风正负引脚。不能沿用旧接口中所谓外部麦克风脚而不另查板焊点。

## 供电、USB及UART0冲突

PDF可确证：USB J1 VBUS经D2 SS14相关通路至`5V`网络；5V包含CH340K VCC(7)和Q1端2，VOUT包含Q1端3、P1.7、8002A VDD(6)。Q1为LP2301 P沟道，Q2/RTS/DTR构成下载控制电路，**P1.7 VOUT不等同于USB上游5V直接节点**。外加5V到VOUT的实际允许方式、Q1体二极管方向及USB同时连接时所有反供路径尚需手册/器件引脚方向/板测确认，不能把有D2误当整板双电源完全隔离已通过。

UART0_RX(PB6)同时接D1.1、R6.2；D1.2接CH340 TXD(8)。UART0_TX(PB5)经R2=330Ω接CH340 RXD(9)。因此PB5/PB6不是独立空闲UART，在主MCU接UART0时必须考虑下载桥驱动和复位/启动过程；不宣称UART0可在USB连接时无条件被两主机同时驱动。

3V3为芯片VDD33同网，不是给单5V系统输入的位置。禁止将整机5V送P2.6。也不能未经电流额定核实将其作主板3.3V供电源。

## 明确可实现的接口方案（需在主设计和固件落实）

建议单独4线UART线束+2线扬声器，避免未知直插尺寸：

| 主板功能 | ASR开发板端 | 状态 |
|---|---|---|
| MCU UART TX（3.3V逻辑） | P1.3 PA3/RX1 | 针脚复用由PDF证实；必须把ASR固件设置UART1/RX1 |
| MCU UART RX | P1.4 PA2/TX1 | 针脚复用由PDF证实；必须把ASR固件设置UART1/TX1 |
| GND | P1.8 或P2.7 | 已确认 |
| ASR供电5V | 板厂认可的5V输入；P1.7 VOUT仅作候选 | 手册/板测未核，不可当已签核 |
| 扬声器两端 | J2.1/J2.2 或P2.1/P2.2 | 已确认，BTL浮置两线 |

选UART1是为了避开CH340占用UART0，不表示当前语音固件已配置成功。UART2也可按P1.2 TX2/P1.1 RX2规划，但同样须固件支持。不能将UART0命令协议直接假定自动迁移到UART1。

暂不允许USB和主板电源同时接通，是验证前使用约束而不是已实现保护。正式方案应在供电路径落实跳帽/开关或合格电源隔离，测试断电反灌、下载和运行三种状态；禁止直接并接两个5V源。

## 未完成/需补证

1. 手册正文读取及其中开发板尺寸图；实际两排间距/排针节距/Pin1标识/板边与USB位置。
2. P1.7外供5V是否为厂家允许输入、USB同时插入允许条件、下载自动断电行为。
3. ASR实际固件UART1配置、3.3V逻辑规格与通信测试。
4. 峰值语音播放电流、单5V适配器总预算、电机/舵机电源噪声与退耦。

因此结论为：**电气针序核实完成，直插物理封装和供电签核未完成；应撤回旧2×7直插假设，不能以本报告标记整机可下单。**
