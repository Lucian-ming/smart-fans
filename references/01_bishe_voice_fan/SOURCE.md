# 毕设-智能语音风扇 (Reference 1)

- **项目链接**：[立创开源硬件平台 - 毕设-智能语音风扇](https://oshwhub.com/maicostow/bi-she-zhi-neng-yu-yin-feng-shan)
- **作者**：maicostow
- **开源协议**：CC BY-NC-SA 4.0
- **主控芯片**：STM32F103C8T6 (LQFP-48，72 MHz)

---

## 1. 资源清单与本地目录

本项目已完成完整离线解压与结构整理：

| 模块 | 本地路径 | 说明 |
| --- | --- | --- |
| **PCB工程** | `references/01_bishe_voice_fan/pcb/ProDoc_Smart_Fan_PCB_2026-11-03.epro2` | 嘉立创EDA专业版工程（原理图 + PCB） |
| **物料清单** | `references/01_bishe_voice_fan/bom/BOM_毕设-智能语音风扇.xlsx` | 包含立创商城（LCSC）器件编号与封装 |
| **3D外壳** | `references/01_bishe_voice_fan/3d_model/` | `底座.STL`、`射灯支架.STL`、`箱盖.STL` |
| **3D打印参考** | `mechanical/stl/reference/` | 同步存入机械结构参考库，方便切片比对 |
| **单片机固件** | `references/01_bishe_voice_fan/firmware/Voice_Fan/` | Keil MDK-ARM + STM32CubeMX HAL 源码 |
| **CubeMX工程** | `references/01_bishe_voice_fan/firmware/Voice_Fan/Voice_Fan.ioc` | STM32CubeMX 引脚与外设配置 |
| **语音配置** | `references/01_bishe_voice_fan/firmware/Voice_Fan/基于天问开发平台语音程序/智能语音风扇.hd` | 天问 Block / ASR-PRO 离线语音工程配置 |
| **手机上位机** | `references/01_bishe_voice_fan/firmware/Voice_Fan/手机软件/Voice_Fan.aia` | App Inventor 蓝牙手机端 App 源码 |

---

## 2. 硬件架构与选型解析

### 电源部分
- **输入**：DC-005 接口（12V 直流适配器输入）。
- **DCDC 降压**：采用 **XL1509-ADJ**（SOP-8），输入 12V 降为 5V，最大输出电流 2A，配合 47µH 功率电感与 SS24 肖特基二极管。能够承受语音模块播放大音量时的瞬态脉冲电流。
- **LDO 稳压**：采用 **AMS1117-3.3**（SOT-223），5V 降至 3.3V 给 STM32、OLED、蓝牙及传感器供电。

### 核心芯片与模块
- **主控 MCU**：STM32F103C8T6（LQFP48），板载 8 MHz HSE 晶振 + 32.768 kHz LSE 晶振（带 CR1220 纽扣电池座，支持硬件 RTC 掉电走时）。
- **语音识别**：板载 **ASR-PRO** 离线语音核心板，外接驻极体麦克风（GMI4522P-2C-60db）与 2-pin 扬声器插座（SPK1），与 STM32 通过串口（USART3: PB10/PB11）进行 115200 波特率通信。
- **风扇驱动**：采用低端 **AO3400A**（N-MOSFET，SOT-23）进行低边开关 PWM 调速（TIM1_CH1: PA8），支持常规 2-pin 直流有刷风扇。
- **照明驱动**：采用 AO3400A 驱动外部射灯/补光灯（TIM1_CH2: PA9）。
- **摇头舵机**：预留 3-pin 舵机接口（PB1: TIM3_CH4），可驱动 SG90 舵机实现左右自动摆头。
- **温度采集**：采用 **MF58 104F3950**（100k NTC 热敏电阻），分压后接入 PA5（ADC1_IN5），通过 Steinhart-Hart 公式与对数查表计算温度。
- **显示屏**：标准 0.96 寸 4-pin I2C OLED（SSD1306），接 PB8/PB9（I2C1 重映射）。
- **无线通信**：预留 **JDY-31** / HC-05 蓝牙串口透传模块插座（USART1 重映射 PB6/PB7）。
- **本地按键**：3 个独立轻触按键（PA0 模式切换、PA1 档位加、PA2 档位减）。

---

## 3. 语音与串口通信协议

天问平台配置文件（`智能语音风扇.hd`）中设定的核心指令集：
- 唤醒词：`“哈宝”`、`“你好哈宝”`
- 语音指令 -> 串口输出至单片机：
  - `FON\r\n`：开启风扇
  - `FOFF\r\n`：关闭风扇
  - `F+\r\n`：风速提高 10%
  - `F-\r\n`：风速降低 10%
  - `FMAX\r\n`：最大风速
  - `FMOD\r\n`：中等风速 (50%)
  - `FMIN\r\n`：最低风速 (10%)
  - `LON\r\n` / `LOFF\r\n`：开关照明
  - `L+\r\n` / `L-\r\n`：调光
- 单片机应答至语音模块（播报确认语音）：
  - 发送 `Fyes` -> 播报“风扇开启成功”
  - 发送 `Foff` -> 播报“风扇已关闭”
  - 发送 `Lyes` -> 播报“照明开启成功”
  - 发送 `Loff` -> 播报“照明已关闭”

---

## 4. 对本项目的直接复用与改进点

### 可直接复用
1. **电源架构**：XL1509-ADJ + AMS1117-3.3 方案非常成熟，物料极易购买（LCSC现货），2A能力足以驱动 ASR-PRO 喇叭与风扇。
2. **ASR-PRO 语音闭环**：`智能语音风扇.hd` 与通信帧格式可直接平移，词条已完全验证。
3. **外壳结构参考**：底座与箱盖的模型可作为外壳轮廓与装配定位的重要参考。
4. **OLED 显示与 RTC 时钟代码**：`page.c`、`oled.c` 及备份域 RTC 保存逻辑可直接参考。

### 本项目需改造/增强的关键点
1. **手势识别引入**：原工程无手势功能，需在 I2C 总线挂入 **PAJ7620U2**（地址 0x73），并将中断脚引至 PA4。
2. **风扇接口升级**：原工程仅支持 2-pin 风扇低边 MOS 驱动，无转速反馈。本项目需增加 **标准 4-pin PWM 风扇接口**（12V、GND、25kHz PWM、FG 测速输入带上拉），同时保留低边 MOS 兼容 2-pin 风扇。
3. **温度传感器扩展**：原工程为 NTC 模拟测温，本项目需求以 **DS18B20** 单总线数字测温为主，原理图上建议同时预留 DS18B20 与 NTC 焊盘。
4. **控制输入增强**：增加 **EC11 旋转编码器** 支持，旋转调速体验优于纯按键。
