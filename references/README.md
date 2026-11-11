# 参考例程与开源项目整理 (references/)

本目录系统整理了与本项目（智能风扇：温控 + 手势 + 语音 + 遥控 + OLED + 3D外壳）直接相关的开源参考工程与模块化驱动参考。

---

## 1. 完整开源工程参考 (Reference Projects)

| 目录 | 来源项目 | 核心主控 | 关键资源与包含内容 | 推荐等级 |
| --- | --- | --- | --- | --- |
| **[01_bishe_voice_fan/](01_bishe_voice_fan/)** | [毕设-智能语音风扇](https://oshwhub.com/maicostow/bi-she-zhi-neng-yu-yin-feng-shan) | **STM32F103C8T6** | • 嘉立创EDA专业版 PCB 工程 (`.epro2`)<br>• 完整立创 BOM 采购表 (`.xlsx`)<br>• 3D 外壳 STL（底座、箱盖、支架）<br>• Keil HAL 完整源码 + ASR-PRO 语音配置 (`.hd`) + 蓝牙 App | ⭐⭐⭐⭐⭐ (基准方案) |
| **[02_aben_fan_pro/](02_aben_fan_pro/)** | [AbenFanPro](https://makerworld.com/en/models/839366-abenfanpro-a-smart-fan-that-s-also-a-game-console) | **ESP32-S3** | • MakerWorld 高度精致的 3D 外壳与风道设计<br>• U8g2 极简风 OLED 菜单系统源码<br>• AHT20 温湿度与风扇分级调速架构 | ⭐⭐⭐⭐ (外壳与UI参考) |
| **[03_smart_fan/](03_smart_fan/)** | [Smart Fan智能风扇](https://oshwhub.com/fishee/smartfan-intelligent-fan) | **STM32F103C8T6** | • DS18B20 单总线高精度数字测温<br>• SU-03T 离线语音与串口协议<br>• 手动/定时/温控 三模状态机切换架构 | ⭐⭐⭐⭐ (温控与状态机参考) |
| **[04_szu_smart_fan/](04_szu_smart_fan/)** | [深大智能风扇](https://oshwhub.com/ivy1999/zhi-neng-yu-yin-feng-shan) | **STM32F103C8T6** | • 电池/外部供电 ADC 电压分压监测与保护电路<br>• 多源控制冲突仲裁机制 | ⭐⭐⭐ (电源检测参考) |
| **[05_gesture_sensor/](05_gesture_sensor/)** | [IntelliFan & PAJ7620U2](05_gesture_sensor/SOURCE.md) | **通用传感器** | • PAJ7620U2 原生 9 种非接触手势识别协议<br>• I²C 共享总线与外壳光学透光开孔设计规范 | ⭐⭐⭐⭐⭐ (手势方案基准) |

---

## 2. 模块化驱动与算法参考 (Modular Drivers)

按技术模块拆解，供固件开发时直接抽取移植（位于相应子目录）：

- **[speech/asr_pro/](speech/asr_pro/)**：ASR-PRO / 天问语音串口帧解析、唤醒词与播报 ACK 字典。
- **[gesture/paj7620u2/](gesture/paj7620u2/)**：PAJ7620U2 寄存器初始化表、9 种手势位掩码与 STM32 HAL 读取逻辑。
- **[oled/ssd1306_hal/](oled/ssd1306_hal/)**：0.96 寸 SSD1306 I2C 硬件通信与界面布局模板。
- **[temperature/ds18b20/](temperature/ds18b20/)**：DS18B20 单总线微秒级时序与温度转换。
- **[temperature/ntc/](temperature/ntc/)**：MF58 100k NTC 热敏电阻 ADC 采样与 Steinhart-Hart 对数查表公式。
- **[fan/pwm_4pin_tach/](fan/pwm_4pin_tach/)**：Intel 标准 4-Pin 25 kHz PWM 定时器配置与 FG 测速捕获算法。
