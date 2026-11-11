# AbenFanPro (Reference 2)

- **PCB 工程**：[立创开源硬件平台 - aben-fan](https://oshwhub.com/rushairer/aben-fan)
- **3D 模型**：[MakerWorld - AbenFanPro](https://makerworld.com/en/models/839366-abenfanpro-a-smart-fan-that-s-also-a-game-console)
- **固件源码**：[GitHub - rushairer/AbenFan](https://github.com/rushairer/AbenFan)
- **作者**：rushairer
- **开源协议**：LGPL 3.0
- **主控芯片**：ESP32-S3

---

## 1. 资源清单与本地目录

本项目已提取完整的固件源码：

| 模块 | 本地路径 | 说明 |
| --- | --- | --- |
| **固件工程** | `references/02_aben_fan_pro/firmware/AbenFan/` | PlatformIO + Arduino 完整固件源码 |
| **菜单系统** | `references/02_aben_fan_pro/firmware/AbenFan/src/Menu.cpp` | 基于 U8g2 / MUIU8g2 的层级菜单系统 |
| **风扇控制库**| `references/02_aben_fan_pro/firmware/AbenFan/lib/Fan/` | 5 档调速（0~4 档）分级控制与状态封装 |
| **温湿度驱动**| `references/02_aben_fan_pro/firmware/AbenFan/lib/Thermometer/` | AHT20 I2C 驱动与校准偏移管理 |
| **小恐龙游戏**| `references/02_aben_fan_pro/firmware/AbenFan/lib/dino_game/` | 移植到 OLED 上的彩蛋游戏源码 |

---

## 2. 核心亮点与工程价值

### 1. 顶级的 3D 外壳结构设计（MakerWorld 爆款）
- 采用复古迷你电脑/街机显示器风格设计，外壳结构分为前面框、机身主体、后盖和风扇出风口。
- 器件内部公差配合极其紧凑精妙，针对 FDM 3D 打印做了充分的倒角、卡扣与沉头螺钉柱优化。
- 可直接借用其按键触感结构、OLED 视窗设计以及风道消音格栅理念。

### 2. 极佳的 OLED 人机交互界面（UI/UX）
- 基于 **U8g2** 库，界面包含：主状态页（大字体显示风速档位、温度、湿度、当前工作模式）、二级设置菜单、屏幕保护。
- 状态机结构清晰：按钮单击切换档位，长按进入菜单，超时自动切回主监控界面。

### 3. 多功能外设集成
- 温湿度：AHT20（I2C）
- 氛围灯：WS2812B RGB 灯珠
- 交互：双微动按键 + Type-C 供电与充放电管理

---

## 3. 对本项目的借鉴与差异比对

| 维度 | AbenFanPro (Ref 2) | 本项目 (Smart Fan v1) | 处理建议 |
| --- | --- | --- | --- |
| **主控** | ESP32-S3 (双核 240MHz, 带 Wi-Fi/BLE) | STM32F103C8T6 (Cortex-M3 72MHz) | 本项目定位高可靠嵌入式裸机，无操作系统开销 |
| **交互** | 双按键 + 蓝牙/网页 | **手势 (PAJ7620) + 语音 (ASR-PRO) + 编码器 + 按键** | 本项目具备多模态物理/非接触交互 |
| **风扇类型**| 5V 微型电机 (H桥驱动) | **12V 4-Pin PWM 机箱风扇** 或 12V 2-pin DC风扇 | 本项目风量大、支持 25kHz PWM 与 FG 真实转速测量 |
| **显示方案**| U8g2 + C++ 面向对象封装 | **C 语言 U8g2 / 精简 SSD1306 页面引擎** | 抽取其页面布局设计，使用 C 语言高效渲染 |
| **外壳方案**| MakerWorld 完整 3D 方案 | 在其基础上开出手势传感器透镜孔与麦克风拾音孔 | 借鉴其前面板排布与风扇固定方式 |
