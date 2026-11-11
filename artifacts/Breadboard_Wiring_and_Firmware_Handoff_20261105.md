# RevB 单5V母板：面包板接线及固件 Agent 交接

日期：2026-11-05。用户已暂停外壳制作，先进行面包板分模块测试。

## 0. 适用版本与证据

本文件依据已交付的 TI 版 PCB，而不是尚未完成的固件或采购候选清单。附录直接解析 PCB 的全部173个焊盘（包括同号焊盘、安装孔），并与原生网表引脚网络逐项比较。

- [已交付PCB](<D:/下载/RevB_5V_TI_NATIVE_20261104_202141/fan_ctrl_revB.kicad_pcb>)
- [已交付原理图](<D:/下载/RevB_5V_TI_NATIVE_20261104_202141/fan_ctrl_revB.kicad_sch>)
- [原生引脚网表](<D:/smart_fans/artifacts/native_pcb_review/candidate_tlv1117/native_pin_nets.json>)
- 本文件说明连接关系，不代表已进行面包板实测、固件编译或整机负载验证。不要以旧采购表的器件编号采购替代件。

## 1. 最重要的上电约束

1. **只用稳压5V，不接12V。** 电机、舵机、ASR的5V不要经STM32核心板或ST-Link供电。
2. 电机/舵机的电源和回流用独立、足够粗的导线到供电分配点；**不要让其电流经过面包板电源轨或细杜邦线**。面包板只做逻辑信号/低电流部分，所有逻辑地与功率地在合理分配点共地。
3. GPIO是3.3V逻辑。不得把模块5V上拉直接接入MCU；先核对模块原理图，必要时用电平转换。使用额定5V的模块不代表其信号一定是3.3V。
4. MCU核心板3V3脚与母板U3输出是两路稳压输出，**不能直接并联**。母板用U3给外设3.3V，核心板自己稳压；面包板若临时采用核心板3V3供少量外设，必须确认其电流预算，并明确这是临时供电方案、不要再连接U3输出。
5. MCU用USB供电时，断开外部5V到核心板的连接（相当于拔JP_USB）；ASR接USB时断开其外部5V及TX/RX三条连接（相当于拔JP_ASR、JP_ASR_TX、JP_ASR_RX）。**仅断5V仍可能经GPIO反供电**。断电改线，不能用这些跳帽推断支持热插拔。
6. 用户此前表示没有限流电源/万用表/示波器。建议先取得至少万用表和有保护的电源；在无法检查极性、短路和电压时，不进行电机/舵机高电流测试。保险丝不是精确限流器。
7. 烧录建议使用SWD：PA13=SWDIO、PA14=SWCLK、GND，目标电压参考按具体下载器接法处理；下载器的3.3V输出不要与已供电目标并联。BOOT0保持正常Flash启动配置，先确认实际芯片型号。

## 2. STM32功能引脚总表（固件必须遵守）

核心板目标为STM32F103C8T6 Blue Pill；以实物丝印确认PA/PB脚，不能只按“第几个针”数。

|功能|STM32脚|母板连接|建议外设/说明|
|---|---|---|---|
|电机PWM|PA0|J_MCU_R.5 → J_TB_L.1|TIM2_CH1，目标25kHz，默认0占空比|
|电机AIN1|PA1|J_MCU_R.6 → J_TB_L.3|GPIO输出|
|电机AIN2|PA5|J_MCU_R.10 → J_TB_L.2|GPIO输出|
|TB使能STBY|PB0|J_MCU_R.13 → J_TB_L.4|外接10k下拉至GND，上电保持低|
|语音USART2 TX|PA2|J_MCU_R.7 → JP_ASR_TX → ASR PA3/RX1|交叉连接，不是TX接TX|
|语音USART2 RX|PA3|J_MCU_R.8 ← JP_ASR_RX ← ASR PA2/TX1|3.3V UART；协议及波特率待确认|
|手势中断|PA4|J_MCU_R.9 → J_GESTURE.5|EXTI4；极性按模块手册确认|
|编码器A|PA6|J_MCU_R.11 → J_ENC.3|TIM3_CH1/编码器模式或EXTI|
|编码器B|PA7|J_MCU_R.12 → J_ENC.5|TIM3_CH2；需滤波/方向校准|
|共享I2C SCL|PB6|J_MCU_L.7 → OLED.3、GESTURE.3|I2C1，初始100kHz|
|共享I2C SDA|PB7|J_MCU_L.6 → OLED.4、GESTURE.4|I2C1|
|舵机PWM|PB8|J_MCU_L.5 → SERVO1.3|TIM4_CH3，50Hz|
|DHT11 DATA|PB9|J_MCU_L.4 → J_DHT11.2|外接4.7k上拉至3.3V|
|按键1|PB13|J_MCU_L.19 → J_KEY1.2|电源启停逻辑；并非切断主电源|
|按键2|PB14|J_MCU_L.18 → J_KEY2.2|模式/摇头请求|
|蜂鸣器驱动|PB15|J_MCU_L.17 → R10 → Q1基极|不能直接由GPIO带5V蜂鸣器|
|核心板LED|PC13|核心板自身LED，母板不接此引脚|常见低电平点亮，须核实际核心板|
|可选调试UART|PA9/PA10|母板对应J_MCU_L.15/.14均NC|可在核心板另接3.3V USB-TTL；不是已连母板接口|

PB12在母板NC，**没有ENC_SW**。不得使用旧固件里PB12编码器按键定义。

## 3. 各模块逐针接线

### 3.1 TB6612（只使用A通道）

按用户已确认模块两排针序列出；不能套用其他商家模块的镜像照片。左排从上到下：

|母板脚|模块脚|接向|
|---|---|---|
|J_TB_L.1|PWMA|STM32 PA0|
|J_TB_L.2|AIN2|STM32 PA5|
|J_TB_L.3|AIN1|STM32 PA1|
|J_TB_L.4|STBY|STM32 PB0，并10k下拉GND|
|J_TB_L.5|BIN1|GND|
|J_TB_L.6|BIN2|GND|
|J_TB_L.7|PWMB|GND|
|J_TB_L.8|GND|GND|

右排从上到下：J_TB_R.1 VM→5V；.2 VCC→3.3V；.3 GND→GND；.4 AO1→电机端1；.5 AO2→电机端2；.6 BO2和.7 BO1悬空；.8 GND→GND。MOTO1.1=AO1、.2=AO2，电机不直接接MCU。VM附近放220µF电解及100nF去耦，注意电解极性。

TB电流、130电机堵转电流和5V适配器能力没有完成实测认证。禁止首次启动即100%占空比，禁止带扇叶进行初步驱动测试。不要把3A保险丝当电机过流保护。

### 3.2 ASR语音模块（两排各8针）

|位置|模块标记（从上到下）|母板接法|
|---|---|---|
|J_VOICE_L.1|GND|GND|
|J_VOICE_L.2|5V|5V经JP_ASR|
|J_VOICE_L.3|PB5|NC，不接|
|J_VOICE_L.4|PB6|NC，不接|
|J_VOICE_L.5|PA2/TX1|经JP_ASR_RX接STM32 PA3/RX|
|J_VOICE_L.6|PA3/RX1|经JP_ASR_TX接STM32 PA2/TX|
|J_VOICE_L.7|PA5|NC|
|J_VOICE_L.8|PA6|NC|
|J_VOICE_R.1|PA4|NC|
|J_VOICE_R.2|GND|GND|
|J_VOICE_R.3|3V3|NC，模块输出不得并到母板3.3V|
|J_VOICE_R.4|PA0|NC|
|J_VOICE_R.5|PA1|NC|
|J_VOICE_R.6|PC4|NC|
|J_VOICE_R.7|SPK−|SPK1.2|
|J_VOICE_R.8|SPK+|SPK1.1|

SPK+/SPK−是差分桥接扬声器输出，**SPK−不是GND**，不得接地。扬声器阻抗/功率须按实物ASR板确认。ASR固件必须把通讯配置在UART1 PA2/PA3，不能默认USB对应的另一组串口就是通讯接口。尚未确认命令字、帧格式、波特率，不允许代码agent自行宣称某协议为现有协议。

### 3.3 OLED与PAJ7620共用I2C

- OLED：J_OLED.1=GND，.2=3.3V，.3=SCL/PB6，.4=SDA/PB7。
- 用户确认：正对OLED显示面，四针在上方，左至右 **GND VCC SCL SDA**。面包板逐标签接线即可，不用为了外壳旋转模块。最终母板安装才需要根据排针方位在平面旋转180°，显示方向由软件配置。
- PAJ7620：J_GESTURE.1=3.3V、.2=GND、.3=SCL/PB6、.4=SDA/PB7、.5=INT/PA4。
- SCL、SDA各4.7k上拉到3.3V。先查模块自带上拉，避免无意并联成过低电阻，更不能上拉到5V。先以100kHz调试，检查ACK、超时、总线卡死恢复。
- OLED常见7位地址0x3C或0x3D、PAJ7620常见0x73，需要实际扫描确认；区分7位地址和库API要求的左移格式。不要把0x78直接当7位地址。
- OLED模块在3.3V输入下能否正常工作需按具体板上稳压/旁路确认，不能因不亮就把I2C上拉改5V。

### 3.4 编码器、按键、DHT11、舵机

|接口|逐针连接|注意|
|---|---|---|
|J_ENC上2P|1=3.3V，2=GND|不是5V；实物逻辑兼容性需核|
|J_ENC下3P|3=A→PA6，4=C→GND，5=B→PA7|无SW引脚；两排为2P+3P，不是连续5P|
|J_KEY1|1=GND，2=SIG→PB13，3=3.3V|按下电平由模块电路/实测确认，再决定上拉和软件极性|
|J_KEY2|1=GND，2=SIG→PB14，3=3.3V|同上|
|J_DHT11|1=3.3V，2=DATA→PB9，3=GND|指3针模块，不等同裸DHT11四脚次序；核模块3.3V工作能力|
|SERVO1|1=GND，2=5V，3=PWM→PB8|动力独立配电、共地；核实实物线序，不仅凭线颜色|

用户舵机为**连续旋转型**：50Hz脉冲控制方向/速度，不能当0～180°位置舵机；约1500µs只可作待校准停止起点。没有位置反馈、限位开关或机械保护时，不实现或承诺准确限角扫风。默认执行器禁用，收到用户显式测试命令后才启用。勿上电自动连续转动。

### 3.5 蜂鸣器与电源小电路

- BZ1正端→5V；负端→Q1集电极C。Q1发射极E→GND，基极B经1k电阻R10接PB15。按**具体2N3904原厂引脚图**辨认E/B/C，不能只凭TO-92外形；PCB的编号为1=E、2=B、3=C。
- D3跨蜂鸣器：阴极K→5V、阳极A→Q1集电极；母板D3.1=K，D3.2=A。上电初态PB15低。
- 母板输入链：DC1.1=5V_RAW → F1 → 5V_FUSED → AO4409漏极D(5/6/7/8)，源极S(1/2/3)→受保护5V，栅极G4→GND；DC1.2=GND。此方向用于反接保护，**不是反流隔离**。
- U3 TI TLV1117LV33DCYR：1=GND，2及散热片=3.3V，3=5V；输入/输出各10µF陶瓷并100nF相关去耦，不能使用旧错误C15849(1µF/0603)代替设计10µF/0805。面包板不可直接插SOT-223/SOIC，需合适转接板；若用其他电源模块，先验电压和电流预算，记录其不是原PCB电源链。
- D4为5V电源指示；D5为3.3V电源指示，分别经1k限流到GND，不是MCU可控灯。

## 4. 面包板分步测试建议

1. 不装电机/舵机/ASR，先核供电与SWD；核心板心跳和可选USART1日志。
2. 单独测按键和编码器，打印状态/增量；确认消抖、极性、方向，不带执行器。
3. 接I2C并扫描；先OLED，再PAJ，加入错误/掉线恢复。
4. 接DHT11，做校验和、超时、采样限速（不快于约1秒，推荐2秒）。
5. 加蜂鸣器驱动，短时提示，不允许持续长鸣。
6. ASR独立供电与串口协议确认后再接UART；先用PC串口工具/模拟帧测试解析，未知协议用明确标记的mock，不能冒称真模块联调成功。
7. 完成电气检查、有合适供电与保护后，电机空载短时低占空比测试；最后测试舵机停止脉宽和方向。每次改线断电。
8. 分清“编译通过”“主机测试通过”“已烧录”“实物测试通过”，没有实测不得写功能已验证。

## 5. 给另一个 Agent 的提示词（整段复制）

```text
你是STM32嵌入式固件工程师。请先完整阅读本Markdown并以其附录的已交付PCB网络为硬件依据，为桌面智能风扇编写可以在面包板上逐模块测试的固件。外壳工作已暂停。不要改PCB引脚来迁就示例。

工作目录：D:\smart_fans。用户WSL中已有单片机开源开发工具链；先只读检查 wsl.exe -l -v，确认发行版，再检查 arm-none-eabi-gcc、cmake、ninja/make、openocd、st-info/探针工具和现有工程。不要假定已安装的版本/发行版名，不要擅自apt升级或重装。Windows D盘对应常见 /mnt/d，E盘对应 /mnt/e，必须实际验证路径。调试器USB是否已通过usbipd传入WSL要检查；不可未经用户许可detach/attach设备或直接烧录。

参考资料（只读，不改用户原文件）：
1. E:\桌面\原理图：各实际模块原理图、说明和OLED结构资料；优先按实际模块型号与用户确认针序，不能把芯片datasheet等同模块接口。
2. E:\文档\dev_references\STM32资料，尤其 程序源码\程序源码\STM32Project-有注释版。
3. D:\smart_fans\artifacts\simulation_review\user_reference_code_review.md：已记录教学示例移植冲突。
4. D:\smart_fans\firmware：现有代码可审查复用，但不是完成品，先读main.c、config/pins.h、构建配置；ENC_SW/PB12已过时，BTN_Pin可能未定义。不要据注释判断功能已实现。
5. D:\smart_fans\artifacts\native_pcb_review\candidate_tlv1117\native_pin_nets.json 和同目录 fan_ctrl_revB.kicad_pcb：实际网络依据。

必须锁定：PA0 TIM2_CH1电机PWM25kHz；PA1/PA5方向；PB0 STBY且上电低；PA2/PA3 USART2语音；PA4手势INT；PA6/PA7编码器；PB6/PB7 I2C1；PB8 TIM4_CH3舵机50Hz；PB9 DHT11；PB13/PB14按键；PB15蜂鸣器。保留SWD。不要启用PB12编码器按键。

示例陷阱：教学电机用PA4/PA5、PA2 TIM2_CH3，不可照搬；教学OLED用PB8/PB9，不可照搬；教学编码器用PB0/PB1，不可照搬；教学舵机用PA1 TIM2_CH2及角度映射，不适用当前连续旋转舵机。先验证HSE/PLL/APB实际时钟，再算定时器频率，注意APB分频下timer clock倍频；不要假定所有时钟恒为72MHz。

开发要求：
- 先输出引脚资源表、构建方案和待确认项，再实现能编译的最小工程，逐模块加驱动。保留现有用户代码，修改前读文件，不盲目重写整个项目。
- 默认安全状态：STBY低、PWM0、蜂鸣器关闭、执行器禁用；启用电机前先设方向和0占空比。连续舵机无位置反馈，禁止伪装角度定位/自动限角扫风。1500us需校准，不是保证停止值。
- 给每个模块独立测试模式，先日志和mock，不自动启动执行器。I2C ACK/超时/恢复，DHT校验和/超时，编码器消抖/原子读计数，按键非阻塞消抖/长短按，UART环形缓冲/帧解析/溢出与错误处理。
- ASR波特率、命令格式、实际语音固件未知，先查资料或问用户；若自定义协议必须标为待双方实现，不声称原模块支持。手势、旋钮、按键、语音统一进入事件/控制状态机，避免各驱动直接抢写PWM。
- 用户没有确认具备限流电源/测量仪器，不引导首次上电即满载。不要让电机/舵机走面包板轨或MCU电源脚。
- 交付完整源码、明确依赖版本、WSL可复现编译命令、bin/elf/map及体积报告、烧录命令但未经授权不执行、面包板逐步测试清单、已知限制。
- 对协议解析、按键状态机和安全控制逻辑做主机单元测试。实际运行构建并记录结果；无法构建就记录真实错误，不能输出虚假的PASS。没有用户实测反馈，不能把编译通过写成硬件验证通过。
```

## 6. 全部PCB焊盘—网络附录

这是PCB焊盘编号，**不是芯片物理脚号**。对MCU务必结合第2节PA/PB名称；安装孔也列入以完整记录。NC表示不连接，多个NC并不相互短接。同一编号重复（例如U3.2）是同网散热焊盘。坐标左右不能从焊盘编号推断。

PCB SHA256：`3341183e1b76a875c8ae71b7134a121bded68481aa67c9ad78303b58f91eaf3a`

|位号|PCB焊盘号|网络|
|---|---|---|
|J_OLED|1|GND|
|J_OLED|2|+3.3V|
|J_OLED|3|I2C1_SCL|
|J_OLED|4|I2C1_SDA|
|C2|1|+5V|
|C2|2|GND|
|J_KEY1|1|GND|
|J_KEY1|2|KEY1_SIG|
|J_KEY1|3|+3.3V|
|H1|1|GND|
|JP_ASR|1|+5V|
|JP_ASR|2|+5V_ASR|
|J_ENC|1|+3.3V|
|J_ENC|2|GND|
|J_ENC|3|ENC_A|
|J_ENC|4|GND|
|J_ENC|5|ENC_B|
|JP_ASR_TX|1|VOICE_TX|
|JP_ASR_TX|2|ASR_RX1|
|C4|1|+5V|
|C4|2|GND|
|D5|1|LED_3V3_K|
|D5|2|+3.3V|
|R_DHT|1|+3.3V|
|R_DHT|2|DHT11_DATA|
|J_DHT11|1|+3.3V|
|J_DHT11|2|DHT11_DATA|
|J_DHT11|3|GND|
|U3|1|GND|
|U3|2|+3.3V|
|U3|2|+3.3V|
|U3|3|+5V|
|SERVO1|1|GND|
|SERVO1|2|+5V|
|SERVO1|3|SERVO_PWM|
|C1|1|+5V|
|C1|2|GND|
|DC1|1|+5V_RAW|
|DC1|2|GND|
|F1|1|+5V_RAW|
|F1|2|+5V_FUSED|
|JP_USB|1|+5V|
|JP_USB|2|+5V_MCU|
|C6|1|+3.3V|
|C6|2|GND|
|H2|1|GND|
|D4|1|LED_5V_K|
|D4|2|+5V|
|C_VM_MLCC|1|+5V|
|C_VM_MLCC|2|GND|
|Q_PWR|1|+5V|
|Q_PWR|2|+5V|
|Q_PWR|3|+5V|
|Q_PWR|4|GND|
|Q_PWR|5|+5V_FUSED|
|Q_PWR|6|+5V_FUSED|
|Q_PWR|7|+5V_FUSED|
|Q_PWR|8|+5V_FUSED|
|H4|1|GND|
|R1|1|LED_5V_K|
|R1|2|GND|
|J_MCU_L|1|NC|
|J_MCU_L|2|GND|
|J_MCU_L|3|+5V_MCU|
|J_MCU_L|4|DHT11_DATA|
|J_MCU_L|5|SERVO_PWM|
|J_MCU_L|6|I2C1_SDA|
|J_MCU_L|7|I2C1_SCL|
|J_MCU_L|8|NC|
|J_MCU_L|9|NC|
|J_MCU_L|10|NC|
|J_MCU_L|11|NC|
|J_MCU_L|12|NC|
|J_MCU_L|13|NC|
|J_MCU_L|14|NC|
|J_MCU_L|15|NC|
|J_MCU_L|16|NC|
|J_MCU_L|17|BUZZER_CTRL|
|J_MCU_L|18|KEY2_SIG|
|J_MCU_L|19|KEY1_SIG|
|J_MCU_L|20|NC|
|J_VOICE_L|1|GND|
|J_VOICE_L|2|+5V_ASR|
|J_VOICE_L|3|NC|
|J_VOICE_L|4|NC|
|J_VOICE_L|5|ASR_TX1|
|J_VOICE_L|6|ASR_RX1|
|J_VOICE_L|7|NC|
|J_VOICE_L|8|NC|
|R10|1|BUZZER_CTRL|
|R10|2|BUZ_BASE|
|J_GESTURE|1|+3.3V|
|J_GESTURE|2|GND|
|J_GESTURE|3|I2C1_SCL|
|J_GESTURE|4|I2C1_SDA|
|J_GESTURE|5|GEST_INT|
|R_SCL|1|+3.3V|
|R_SCL|2|I2C1_SCL|
|C5|1|+5V|
|C5|2|GND|
|SPK1|1|VOICE_SPK_P|
|SPK1|2|VOICE_SPK_N|
|R2|1|LED_3V3_K|
|R2|2|GND|
|Q1|1|GND|
|Q1|2|BUZ_BASE|
|Q1|3|BUZ_DRV|
|R_SDA|1|+3.3V|
|R_SDA|2|I2C1_SDA|
|C_VM|1|+5V|
|C_VM|2|GND|
|C3|1|+5V|
|C3|2|GND|
|D3|1|+5V|
|D3|2|BUZ_DRV|
|JP_ASR_RX|1|VOICE_RX|
|JP_ASR_RX|2|ASR_TX1|
|J_KEY2|1|GND|
|J_KEY2|2|KEY2_SIG|
|J_KEY2|3|+3.3V|
|J_VOICE_R|1|NC|
|J_VOICE_R|2|GND|
|J_VOICE_R|3|NC|
|J_VOICE_R|4|NC|
|J_VOICE_R|5|NC|
|J_VOICE_R|6|NC|
|J_VOICE_R|7|VOICE_SPK_N|
|J_VOICE_R|8|VOICE_SPK_P|
|H3|1|GND|
|J_TB_L|1|TB_PWMA|
|J_TB_L|2|TB_AIN2|
|J_TB_L|3|TB_AIN1|
|J_TB_L|4|TB_STBY|
|J_TB_L|5|GND|
|J_TB_L|6|GND|
|J_TB_L|7|GND|
|J_TB_L|8|GND|
|R_STBY|1|TB_STBY|
|R_STBY|2|GND|
|J_MCU_R|1|NC|
|J_MCU_R|2|NC|
|J_MCU_R|3|NC|
|J_MCU_R|4|NC|
|J_MCU_R|5|TB_PWMA|
|J_MCU_R|6|TB_AIN1|
|J_MCU_R|7|VOICE_TX|
|J_MCU_R|8|VOICE_RX|
|J_MCU_R|9|GEST_INT|
|J_MCU_R|10|TB_AIN2|
|J_MCU_R|11|ENC_A|
|J_MCU_R|12|ENC_B|
|J_MCU_R|13|TB_STBY|
|J_MCU_R|14|NC|
|J_MCU_R|15|NC|
|J_MCU_R|16|NC|
|J_MCU_R|17|NC|
|J_MCU_R|18|NC|
|J_MCU_R|19|GND|
|J_MCU_R|20|GND|
|MOTO1|1|TB_AO1|
|MOTO1|2|TB_AO2|
|BZ1|1|+5V|
|BZ1|2|BUZ_DRV|
|C7|1|+3.3V|
|C7|2|GND|
|J_TB_R|1|+5V|
|J_TB_R|2|+3.3V|
|J_TB_R|3|GND|
|J_TB_R|4|TB_AO1|
|J_TB_R|5|TB_AO2|
|J_TB_R|6|NC|
|J_TB_R|7|NC|
|J_TB_R|8|GND|

## 7. 同网络连接清单

以下从相同PCB提取，便于追查一根线的所有端点。NC不归为共同网络。

- **+3.3V**：J_OLED.2、J_KEY1.3、J_ENC.1、D5.2、R_DHT.1、J_DHT11.1、U3.2、U3.2、C6.1、J_GESTURE.1、R_SCL.1、R_SDA.1、J_KEY2.3、C7.1、J_TB_R.2
- **+5V**：C2.1、JP_ASR.1、C4.1、U3.3、SERVO1.2、C1.1、JP_USB.1、D4.2、C_VM_MLCC.1、Q_PWR.1、Q_PWR.2、Q_PWR.3、C5.1、C_VM.1、C3.1、D3.1、BZ1.1、J_TB_R.1
- **+5V_ASR**：JP_ASR.2、J_VOICE_L.2
- **+5V_FUSED**：F1.2、Q_PWR.5、Q_PWR.6、Q_PWR.7、Q_PWR.8
- **+5V_MCU**：JP_USB.2、J_MCU_L.3
- **+5V_RAW**：DC1.1、F1.1
- **ASR_RX1**：JP_ASR_TX.2、J_VOICE_L.6
- **ASR_TX1**：J_VOICE_L.5、JP_ASR_RX.2
- **BUZZER_CTRL**：J_MCU_L.17、R10.1
- **BUZ_BASE**：R10.2、Q1.2
- **BUZ_DRV**：Q1.3、D3.2、BZ1.2
- **DHT11_DATA**：R_DHT.2、J_DHT11.2、J_MCU_L.4
- **ENC_A**：J_ENC.3、J_MCU_R.11
- **ENC_B**：J_ENC.5、J_MCU_R.12
- **GEST_INT**：J_GESTURE.5、J_MCU_R.9
- **GND**：J_OLED.1、C2.2、J_KEY1.1、H1.1、J_ENC.2、J_ENC.4、C4.2、J_DHT11.3、U3.1、SERVO1.1、C1.2、DC1.2、C6.2、H2.1、C_VM_MLCC.2、Q_PWR.4、H4.1、R1.2、J_MCU_L.2、J_VOICE_L.1、J_GESTURE.2、C5.2、R2.2、Q1.1、C_VM.2、C3.2、J_KEY2.1、J_VOICE_R.2、H3.1、J_TB_L.5、J_TB_L.6、J_TB_L.7、J_TB_L.8、R_STBY.2、J_MCU_R.19、J_MCU_R.20、C7.2、J_TB_R.3、J_TB_R.8
- **I2C1_SCL**：J_OLED.3、J_MCU_L.7、J_GESTURE.3、R_SCL.2
- **I2C1_SDA**：J_OLED.4、J_MCU_L.6、J_GESTURE.4、R_SDA.2
- **KEY1_SIG**：J_KEY1.2、J_MCU_L.19
- **KEY2_SIG**：J_MCU_L.18、J_KEY2.2
- **LED_3V3_K**：D5.1、R2.1
- **LED_5V_K**：D4.1、R1.1
- **SERVO_PWM**：SERVO1.3、J_MCU_L.5
- **TB_AIN1**：J_TB_L.3、J_MCU_R.6
- **TB_AIN2**：J_TB_L.2、J_MCU_R.10
- **TB_AO1**：MOTO1.1、J_TB_R.4
- **TB_AO2**：MOTO1.2、J_TB_R.5
- **TB_PWMA**：J_TB_L.1、J_MCU_R.5
- **TB_STBY**：J_TB_L.4、R_STBY.1、J_MCU_R.13
- **VOICE_RX**：JP_ASR_RX.1、J_MCU_R.8
- **VOICE_SPK_N**：SPK1.2、J_VOICE_R.7
- **VOICE_SPK_P**：SPK1.1、J_VOICE_R.8
- **VOICE_TX**：JP_ASR_TX.1、J_MCU_R.7
