# 用户器件示例与当前RevB的只读核对

状态：仅源码审查；未烧录、未实测，不替代PCB/ERC/电气仿真。外部参考文件未修改。

参考根目录：[STM32Project-有注释版](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版>)。

| 项目 | 已读源码证据 | 当前板适配要求 |
|---|---|---|
| 电机方向 | [Motor.c:16–40](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/6-5 PWM驱动直流电机/Hardware/Motor.c#L16-L40>) 使用PA4/PA5，Speed正负决定方向 | 当前AIN1=PA1、AIN2=PA5；PA4为手势中断，绝不能照搬PA4输出 |
| 电机PWM | [PWM.c:17–43](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/6-5 PWM驱动直流电机/Hardware/PWM.c#L17-L43>) 使用PA2/TIM2_CH3、PSC35、ARR99、CCR初值0；若定时器72MHz则20kHz | 当前PWMA=PA0/TIM2_CH1；PA2属于ASR USART2。目标25kHz须按实际时钟重新计算，不能照搬20kHz配置。初始化期间STBY保持低，先设方向和零PWM，最后才允许使能 |
| 舵机 | [Servo.c:19–22](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/6-4 PWM驱动舵机/Hardware/Servo.c#L19-L22>) 将0–180°映射500–2500计数；[PWM.c:17–43](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/6-4 PWM驱动舵机/Hardware/PWM.c#L17-L43>) 为PA1/TIM2_CH2，PSC71、ARR19999，在72MHz下50Hz | 当前PB8/TIM4_CH3，用户是360°连续旋转型。角度映射不可用于定位，只可参考脉宽产生方法；停止脉宽需实物校准，不能声称无位置反馈可可靠限角 |
| OLED I2C | [OLED.c:5–22](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/1-4 OLED驱动函数模块/4针脚I2C版本/OLED.c#L5-L22>) 使用PB8/PB9开漏；[发送函数:55–65](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/1-4 OLED驱动函数模块/4针脚I2C版本/OLED.c#L55-L65>) 不读ACK，也无明确延时 | 当前共享I2C1为PB6/PB7；PB8是舵机，PB9是DHT11。必须改正确引脚，补ACK/超时/错误恢复及明确时序，不能用示例循环速度证明100kHz/400kHz符合性 |

当前固件定义见[pins.h](<D:/smart_fans/firmware/src/config/pins.h>)。其中ENC_SW/PB12仍是过期定义，与新五脚编码器无按键的事实不一致；该问题没有在本次只读审核中偷偷修改。已读[Encoder.c](<E:/文档/dev_references/STM32资料/程序源码/程序源码/STM32Project-有注释版/5-2 旋转编码器计次/Hardware/Encoder.c>)：PB0/PB1上拉、双下降沿EXTI读另一相；当前A/B是PA6/PA7，PB0是TB_STBY，禁止照搬。可考虑TIM3编码器模式及滤波，或重映射EXTI并加消抖。示例第3行计数变量未声明volatile，第69–70行读取后清零与ISR间存在丢增量窗口；移植时需临界区/原子交换，不能把一次电平复读当完整消抖。

结论：这些教学示例有参考价值，但直接复制会占用ASR串口、手势中断、舵机或DHT11引脚。应先按真实网表完成端口适配，再实现上电安全状态；未进行固件功能完成或整机合格声明。
