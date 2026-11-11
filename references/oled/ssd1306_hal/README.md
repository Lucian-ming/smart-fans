# OLED (SSD1306 0.96") 驱动参考

## 1. 硬件规格
- 尺寸：0.96 英寸，分辨率 128x64 单色/双色 OLED
- 接口：I²C（4-pin：GND, VCC, SCL, SDA）
- I2C 从机地址：`0x3C`（7-bit） / `0x78`（8-bit 写地址）
- 总线挂载：接 PB6 (SCL) 与 PB7 (SDA)，与 PAJ7620U2 手势模块（`0x73`）共用 I2C1 总线。

## 2. 界面设计借鉴（融合 Reference 1 与 Reference 2）
- **状态总览行**：工作模式（MANUAL / AUTO-TEMP / GESTURE / SLEEP）+ RTC 当前时间。
- **环境监控行**：温度读数（如 `Temp: 26.5 ℃`）与目标温控阈值。
- **风扇输出行**：当前风速档位（0~4 档 或 0~100% 进度条显示）。
- **转速回读行**：FG 测速实时 RPM 读数（如 `RPM: 1850`）或堵转报警提示（`FAULT: STALL`）。
