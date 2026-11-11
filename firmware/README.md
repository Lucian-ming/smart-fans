# 智能桌面风扇固件 (Smart Fan Firmware)

基于 STM32F103C8T6 核心板与 fan_ctrl_revB 硬件网络设计，专为面包板逐模块安全测试与整机联调构建。

---

## 1. 硬件引脚分配与网络基准 (Strictly Locked)

| 引脚 | 网络标号 | 外设与模式 | 功能描述 | 上电初始安全状态 |
|---|---|---|---|---|
| **PA0** | `TB_PWMA` | TIM2_CH1 (25 kHz PWM) | 130直流电机转速控制 (超声频静音) | 占空比 0%，PWM 输出停顿 |
| **PA1** | `TB_AIN1` | GPIO Output PP | TB6612 电机正反转方向引脚 1 | 输出低电平 (LOW) |
| **PA5** | `TB_AIN2` | GPIO Output PP | TB6612 电机正反转方向引脚 2 | 输出低电平 (LOW) |
| **PB0** | `TB_STBY` | GPIO Output PP | TB6612 驱动芯片使能 (板载10k下拉) | **输出低电平 (LOW, 停机待命)** |
| **PA2** | `VOICE_TX` | USART2_TX (AF-PP, 115200 8N1) | 发送应答 ACK 到 ASR-PRO 语音模块 | 空闲高电平 |
| **PA3** | `VOICE_RX` | USART2_RX (Input Pullup, 中断+环形缓冲) | 接收 ASR-PRO 离线免唤醒词条指令 | 上拉输入，开中断 |
| **PA4** | `GEST_INT` | GPIO Input Pullup | PAJ7620U2 手势传感器低有效中断 | 上拉输入 |
| **PA6** | `ENC_A` | TIM3_CH1 (硬件编码器接口) | EC11 编码器 A 相 (带6级硬件数字滤波) | 上拉输入 |
| **PA7** | `ENC_B` | TIM3_CH2 (硬件编码器接口) | EC11 编码器 B 相 (带6级硬件数字滤波) | 上拉输入 |
| **PB6** | `I2C1_SCL` | GPIO Open-Drain (带总线死锁恢复) | 共享 I2C1 时钟线 (板载双4.7k上拉) | 初始高电平，开漏 |
| **PB7** | `I2C1_SDA` | GPIO Open-Drain (带总线死锁恢复) | 共享 I2C1 数据线 (SSD1306 + PAJ7620) | 初始高电平，开漏 |
| **PB8** | `SERVO_PWM` | TIM4_CH3 (50 Hz, 20ms周期) | MG90S 360° 连续旋转摇头舵机 | 占空比 0% (禁止输出脉冲) |
| **PB9** | `DHT11_DATA` | GPIO Open-Drain / In (DWT微秒延时) | DHT11 单总线温湿度数据线 | 初始高电平，开漏 |
| **PB13** | `KEY1_SIG` | GPIO Input Pullup (软件非阻塞消抖) | 独立按键 1：电源启停 / 模式切换 | 上拉输入，低有效 |
| **PB14** | `KEY2_SIG` | GPIO Input Pullup (软件非阻塞消抖) | 独立按键 2：摇头启停 / 急停复位 | 上拉输入，低有效 |
| **PB15** | `BUZZER_CTRL` | GPIO Output PP (驱动 2N3904 NPN) | 有源蜂鸣器驱动基极 | **输出低电平 (LOW, 静音)** |
| **PC13** | `LED_Pin` | GPIO Output PP (核心板板载) | 心跳指示灯 (低电平点亮，0.5s翻转) | 初始高电平 (灭) |
| **PA9** | `UART1_TX` | USART1_TX (115200 8N1) | 调试日志输出与交互测试控制台 TX | 输出 |
| **PA10** | `UART1_RX` | USART1_RX (115200 8N1) | 调试日志输出与交互测试控制台 RX | 输入 |
| **PA13** | `SWDIO` | SWD 调试数据线 | 保留系统仿真调试与烧录接口 | 系统保留 |
| **PA14** | `SWCLK` | SWD 调试时钟线 | 保留系统仿真调试与烧录接口 | 系统保留 |
| **PB12** | `ENC_SW` | **未启用 (Disabled)** | 五脚编码器无按键，明确不初始化 | 高阻/悬空 |

---

## 2. 编译与测试环境 (WSL Ubuntu)

### 2.1 依赖工具版本
- 交叉编译器：`arm-none-eabi-gcc` 9.2.1
- 构建系统：`cmake` 4.3.2 + `make` 4.2.1
- 宿主机测试编译器：`gcc` 13.1.0
- 目标调试器：`openocd` 0.10.0 (或外部 ST-Link Utility)

### 2.2 宿主机单元测试 (Host Unit Tests)
无需单片机硬件，在 WSL 中直接测试串口环形缓冲帧解析、按键消抖状态机、安全控制状态机：
```bash
cd /mnt/d/smart_fans/firmware/test
gcc -Wall -Wextra -I../src -I../include test_runner.c -o test_runner
./test_runner
```
**运行结果**：46 个核心逻辑断言全部通过（46 Run, 46 Passed, 0 Failed）。

### 2.3 目标固件交叉编译 (Target Build)
```bash
cd /mnt/d/smart_fans/firmware
rm -rf build && mkdir -p build && cd build
cmake ..
make -j4
```
**体积产物报告**：
- `smart_fan.elf` (713 KB 调试符号文件)
- `smart_fan.bin` (35,948 字节，Flash 占比 54.8%)
- `smart_fan.hex` (101 KB)
- `smart_fan.map` (402 KB 链接映射表)
- 内存开销：`text: 35828`, `data: 120`, `bss: 3504` (SRAM 占用仅 17.5%)

### 2.4 烧录命令 (请先获得用户许可，确认调试器已挂载)
> [!WARNING]
> 未经用户许可禁止擅自烧录或强行 attach 设备。
若在 WSL 中通过 OpenOCD 烧录（需 Windows 端执行 `usbipd attach --wsl --busid 2-1`）：
```bash
openocd -f interface/stlink-v2.cfg -f target/stm32f1x.cfg -c "program smart_fan.bin 0x08000000 verify reset exit"
```
若在 Windows 端，可直接使用 STM32CubeProgrammer 或 ST-Link CLI 烧录 `D:\smart_fans\firmware\build\smart_fan.hex`。

---

## 3. 串口交互测试控制台 (USART1 @ 115200 8N1)

连接核心板 PA9(TX) 和 PA10(RX) 至电脑 USB 转串口，波特率 115200。系统上电默认处于待命/安全测试态，可通过以下命令单独测试每个模块：

| 命令 | 参数说明 | 行为与安全测试目的 |
|---|---|---|
| `help` | 无 | 打印全部支持的调试命令清单 |
| `status` | 无 | 打印各传感器实时读数、执行器当前状态与时钟频率 |
| `safe` | 无 | **紧急停机**：立即将 STBY 拉低，电机 PWM 占空比归 0，舵机停止脉冲 |
| `test led [on\|off]` | `on`/`off`/不填(翻转) | 测试 PC13 蓝板心跳灯 |
| `test buz [on\|off\|beep]` | `beep`为双响 | 测试 PB15 蜂鸣器驱动 (经 2N3904) |
| `test key` | 无 | 读取 PB13 (KEY1) 与 PB14 (KEY2) 当前电平 (提示 PB12 已禁用) |
| `test enc` | 无 | 读取 EC11 编码器增量与累计步数 |
| `test dht` | 无 | 触发一次 PB9 DHT11 采样并打印温湿度及校验和 |
| `test i2c` | 无 | 执行 9 脉冲总线解锁恢复，并扫描 0x01~0x77 地址设备 |
| `test oled` | 无 | 初始化 SSD1306 并显示状态界面测试画幅 |
| `test gest` | 无 | 读取 PAJ7620 传感器 ID、手势标志与 PA4 INT 引脚电平 |
| `test voice <cmd>` | `FON`/`FOFF`/`F+`/`FMAX` | 模拟注入 ASR-PRO 语音词条，验证状态机响应与 ACK 应答 |
| `test motor <0-100> [fwd\|rev]` | 占空比与转向 | **受控测试电机**：严格执行“先设方向占空比，再开STBY”安全时序 |
| `test servo <stop\|cw\|ccw\|us <val>>` | 运动模式或脉宽 | 测试 MG90S 360° 连续旋转舵机 (500~2500us) |
| `test servo_cal <offset_us>` | 偏移微秒 (-200~+200) | 校准 360° 舵机停转机械中位 deadband |

---

## 4. 面包板逐模块安全测试清单与防坑指南

> [!CAUTION]
> 1. **严禁共用 MCU 3.3V 驱动动力执行器**：TB6612 电机供电 (VM) 与 MG90S 舵机 5V 严禁从单片机板载 3.3V LDO 取电，也不应直接穿过面包板细线触点承载大电流，必须使用独立且共地的 5V 电源！
> 2. **OLED 针脚极性确认**：市场上 0.96寸 I2C OLED 模块存在 `GND-VCC-SCL-SDA` 与 `VCC-GND-SCL-SDA` 两种互逆针序，插上面包板前务必查看模块丝印，接反将烧毁屏驱！
> 3. **DHT11 模块针序确认**：PCB 网络中 1脚为 3.3V、2脚为 DATA、3脚为 GND；某些现成模块 1脚为 DATA、2脚为 VCC。请按实物模块丝印插接。
> 4. **连续舵机特性**：MG90S 360° 为无定位连续马达，不具备角度位置反馈，系统不会虚假显示“当前几度”，停止时使用关闭 PWM 比较值以避免死区蠕动。

### 推荐逐模块通电顺序：
1. **第 1 步 (最小系统)**：仅插核心板 + USB转串口，输入 `status`，确认 PC13 闪烁、串口日志正常、时钟锁定 72 MHz。
2. **第 2 步 (人机交互)**：接 PB15 蜂鸣器 + PB13/PB14 按键，输入 `test buz beep` 与 `test key`，确认蜂鸣与按键消抖正常。
3. **第 3 步 (I2C 总线)**：接 PB6/PB7 至 OLED 与手势模块，输入 `test i2c`，查看是否正确扫描出 `0x3C` 与 `0x73`。再分别运行 `test oled` 与 `test gest`。
4. **第 4 步 (温湿度与编码器)**：接 PB9 DHT11 与 PA6/PA7 编码器，输入 `test dht` 与旋转旋钮 `test enc`。
5. **第 5 步 (语音模块)**：接 PA2/PA3 至 ASR-PRO，输入 `test voice FON` 查看状态转换与串口回传。
6. **第 6 步 (执行器动力)**：接独立限流 5V 电源，由低占空比 `test motor 20 fwd` 逐步递增测试电机与舵机。
