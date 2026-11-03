# 引脚分配表

> 版本：v0.3（加入语音与手势） · 2026-11-03
> 主控：**STM32F103C8T6**（LQFP48，64 KB Flash / 20 KB RAM）
> 风扇：**12 V DC 4-pin PWM**  ·  v1 **不联网**（无 Wi-Fi/BLE）

| 功能 | 信号 | 引脚 | 复用 | 方向 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 风扇 PWM | FAN_PWM | PA0 | TIM2_CH1 | 输出 | 25 kHz，PSC=71 / ARR=39（见 `firmware/README.md`） |
| 风扇转速反馈 | FAN_TACH | PA8 | TIM1_CH1 | 输入 | 4-pin 风扇 FG，开漏；4.7 kΩ 上拉到 3.3 V |
| 温度传感器 | TEMP_DATA | PA1 | GPIO | 双向 | DS18B20 单总线，4.7 kΩ 上拉到 3.3 V |
| OLED 时钟 | I2C1_SCL | PB6 | I2C1_SCL | 输出 | 4.7 kΩ 上拉；与手势传感器共用 |
| OLED 数据 | I2C1_SDA | PB7 | I2C1_SDA | 双向 | 4.7 kΩ 上拉 |
| 手势传感器中断 | GESTURE_INT | PA4 | GPIO/EXTI | 输入 | PAJ7620U2 的 INT，接外部上拉；也可轮询 |
| 编码器 A | ENC_A | PA6 | TIM3_CH1 | 输入 | 内部上拉；硬件正交解码 |
| 编码器 B | ENC_B | PA7 | TIM3_CH2 | 输入 | 内部上拉 |
| 编码器按键 | ENC_SW | PB12 | GPIO | 输入 | 内置上拉，低有效 |
| 备用按键 | BTN_MODE | PB13 | GPIO | 输入 | 上拉输入，低有效 |
| 蜂鸣器 | BUZZER | PB14 | GPIO | 输出 | 经三极管驱动，禁止直驱 |
| 心跳 LED | LED_STATUS | PC13 | GPIO | 输出 | 蓝板低电平点亮 |
| 调试 TX | UART1_TX | PA9 | USART1_TX | 输出 | 115200 8N1 |
| 调试 RX | UART1_RX | PA10 | USART1_RX | 输入 | 上拉输入 |
| 语音模块 TX | VOICE_TX | PA2 | USART2_TX | 输出 | SU-03T / ASR-PRO，3.3 V TTL |
| 语音模块 RX | VOICE_RX | PA3 | USART2_RX | 输入 | 用于向语音模块发播报指令 |
| 下载/调试 | SWDIO | PA13 | SWD | — | **必须保留排针** |
| 下载/调试 | SWCLK | PA14 | SWD | — | **必须保留排针** |
| 12 V 检测（可选） | VBAT_SENSE | PA5 | ADC12_IN5 | 输入 | 分压到 ≤ 3.3 V |

## 约束与注意事项

- **PA13/PA14（SWD）不可占用**，否则无法烧录；布线时留 4-pin 排针（3.3V/SWDIO/SWCLK/GND）。
- **BOOT0/BOOT1** 下载时用跳帽配置：正常运行时 BOOT0=0；串口 ISP 时 BOOT0=1。
- **PB6/PB7 是 I2C1 默认引脚**，不要再分配给其他功能；如需第二路 I²C 可用 PB10/PB11。
- **PA11/PA12** 为 USB DM/DP，v1 不用，可引出或不焊。
- **PA0/PA1 与 PA6/PA7** 分别用于 TIM2 与 TIM3，避免占用为普通 IO。
- **4-pin 风扇 PWM 输入为 5 V 逻辑**且内部上拉：MCU 直接输出 3.3 V 时，多数风扇可识别高电平但低电平下拉能力不足，建议 PCB 上预留「直连 / 经 NPN 开漏反相」两种方案（跳线选择，或默认用三极管方案并在固件中反相占空比）。
- 所有对外信号（按键、编码器、外部传感器）建议加 ESD 保护与 RC 滤波。
- **I²C1 上挂两个设备**：OLED（0x3C）+ PAJ7620（0x73），地址不冲突；上拉 4.7 kΩ，若走线较长降到 2.2 kΩ。
- **语音模块**：SU-03T/ASR-PRO 建议 5 V 供电、3.3 V TTL 电平；播报喇叭线远离 I²C 与 ADC 走线，避免识别/显示异常。
- **手势传感器**：PAJ7620U2 为 3.3 V 供电，INT 为开漏输出，需上拉；镜头开孔要避开外壳遮挡。

## 预留扩展（v1 不焊或只留焊盘）

| 功能 | 建议引脚 | 备注 |
| --- | --- | --- |
| 第二路风扇 PWM | PB8 / TIM4_CH3 | 双风扇场景，与编码器所用 TIM3 不冲突 |
| 外接 I²C 排针 | PB6/PB7 已有 | 4-pin：3.3V/SCL/SDA/GND |
| 人体感应模块 | PB0 | 高电平触发 |
| 另一路 UART 屏 | PB10/PB11（USART3） | 调试口与语音口已占用 |
| USB 调试 | PA11/PA12 | v1 不做 |
