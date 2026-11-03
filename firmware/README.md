# firmware/

STM32F103C8T6 固件（PlatformIO + STM32Cube HAL，C 语言）。当前为**可编译的骨架**：72 MHz 时钟、UART1 日志、心跳 LED。

## 快速开始

```bash
cd firmware
pio run                 # 编译
pio run -t upload       # 用 ST-Link 烧录（SWD：PA13/PA14 + GND + 3.3V）
pio device monitor      # 串口日志 115200（PA9/PA10 或板载 USB 转串口）
```

> 本机尚未安装 PlatformIO（`pio` 不在 PATH）。装好后首次 `pio run` 会自动下载 ststm32 平台与 HAL 包。
> 硬件连接：ST-Link 的 SWDIO→PA13、SWCLK→PA14、GND→GND、3.3V→3.3V。

## 工具链选择

| 方式 | 说明 |
| --- | --- |
| PlatformIO（当前采用） | 纯命令行、依赖自动管理，适合脚本化与 CI |
| STM32CubeIDE + CubeMX | 图形化配置引脚/时钟，生成工程；适合改外设后重新生成 |
| 两者混用 | 用 CubeMX 生成初始化代码，把 `src/app`、`src/drivers` 移植过去；HAL 层不变 |

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/main.c` | 入口：时钟、GPIO、UART 初始化 + 主循环 |
| `src/stm32f1xx_it.c` | 中断向量（SysTick 等），后续定时器/串口中断也放这里 |
| `src/config/` | 引脚分配、版本号、可调参数、编译期开关 |
| `src/hal/` | 外设薄封装：PWM、ADC、I²C、UART、输入捕获（换芯片主要改这里） |
| `src/drivers/` | 器件驱动：风扇、温度传感器、OLED、编码器、蜂鸣器 |
| `src/app/` | 业务逻辑：温控、状态机、参数存储、串口命令解析 |
| `include/` | 对外头文件 |
| `lib/` | 第三方库（或用 `lib_deps` 管理） |
| `test/` | PC 端单元测试（纯逻辑部分，用 native 平台） |

## 编码约定

- 语言：C11；编译开启 `-Wall -Wextra`，警告视为待修问题
- **app 层不直接写寄存器/调 HAL**，只通过 `hal/` 与 `drivers/` 接口，便于在 PC 上测试逻辑
- 全局状态收进 `app_ctx_t`，避免散落的全局变量
- 日志统一 `log_printf`（后续按 INFO/WARN/ERR 分级），不要在驱动里裸打日志
- 时间基准用 `HAL_GetTick()`，主循环非阻塞；禁止长 `HAL_Delay()`
- 每个驱动 `xxx_init()` 返回 `bool`/`HAL_StatusTypeDef`，失败必须上报，不允许静默
- 中断服务函数只做最短处理（置标志/存数据），业务在主循环完成

## 定时器分配

| 定时器 | 用途 | 时钟 | 说明 |
| --- | --- | --- | --- |
| TIM1 (APB2 72 MHz) | 风扇 FG 输入捕获 | 72 MHz | 测周期换算 RPM |
| TIM2 (APB1 36 MHz，定时器 ×2 = 72 MHz) | 风扇 PWM 25 kHz | 72 MHz | PSC=71 → 1 MHz，ARR=39 |
| TIM3 | 编码器接口（PA6/PA7） | 72 MHz | 硬件正交解码，无需中断 |
| SysTick | HAL 时基 | 1 kHz | `HAL_GetTick()` |

## 待实现（按顺序）

1. `hal/pwm`：TIM2_CH1 输出 25 kHz，占空比 0–100%
2. `drivers/fan`：设置占空比 + TIM1 捕获测 RPM + 堵转判定（有输出但连续 3 s 无脉冲）
3. `drivers/temp`：DS18B20 单总线（需微秒级延时）或 NTC + ADC 查表
4. `drivers/encoder`：TIM3 正交解码 + 按键消抖
5. `drivers/oled`：I²C1 + U8g2，显示温度/档位/模式/告警
6. `drivers/voice`：USART2 中断收字节 + 环形缓冲，按行解析词条（SU-03T 默认输出「词条编号」帧）
7. `drivers/gesture`：I²C1 读 PAJ7620 手势寄存器，INT 触发后读一次；加 300 ms 冷却防连击
8. `app/fan_control`：目标温度 + 滞回 + 占空比斜率限幅
9. `app/state_machine`：IDLE / MANUAL / AUTO / FAULT
10. `app/config_store`：参数存 Flash 末页（模拟 EEPROM），带校验与默认值兜底
11. `app/shell`：串口文本命令（`help`、`status`、`speed 60`、`mode auto`、`save`）

## 调试建议

- 先只焊 MCU + 电源 + SWD + UART，确认能烧录、串口有日志，再焊其余
- 用 `pio run -t upload` 前确认 BOOT0=0（从 Flash 启动）
- 烧录失败先查 SWD 接线与目标板供电，不要反复重试烧录
