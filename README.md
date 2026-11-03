# 智能风扇 Smart Fan

一台能感知环境温度、按需自动调速，并支持**语音、手势、旋钮/按键**控制与 OLED 显示的智能风扇（v1 不联网）。
项目覆盖完整链路：**需求 → 电路设计（KiCad）→ PCB 打样 → 焊接 → 3D 外壳打印 → 固件与上位机开发 → 整机装配与测试**。

> 当前状态：项目骨架已初始化（2026-11-03），选型已确认：**12 V DC 4-pin PWM 风扇 + STM32F103C8T6**，v1 不联网。详见 [需求文档](docs/01-requirements.md)。

## 目录结构

| 路径 | 放什么 | 什么时候用 |
| --- | --- | --- |
| [docs/](docs/) | 需求、架构、路线图、装配/打印说明、实验日志 | 贯穿全程，动手前先看 |
| [hardware/kicad/](hardware/kicad/) | KiCad 原理图 / PCB / 自建库 | 画板、改板、导出生产文件 |
| [hardware/datasheets/](hardware/datasheets/) | 芯片、风扇、传感器的数据手册（PDF） | 选型、查引脚、查电气参数 |
| [hardware/fabrication/](hardware/fabrication/) | 交给板厂的 Gerber / BOM / 坐标文件 | 每次打样固定一份快照 |
| [mechanical/cad/](mechanical/cad/) | 外壳 3D 源文件（FreeCAD / Fusion 等） | 修改结构 |
| [mechanical/step/](mechanical/step/) | 导出给协作方/加工方的 STEP | 与 PCB、风扇做干涉检查 |
| [mechanical/stl/](mechanical/stl/) | 可直接切片打印的 STL | 打印 |
| [mechanical/print-profiles/](mechanical/print-profiles/) | 切片参数（PrusaSlicer / Orca 等） | 复现同一批打印效果 |
| [firmware/](firmware/) | STM32F103 固件（PlatformIO + STM32Cube HAL） | 写代码、烧录、调试 |
| [shared/protocol/](shared/protocol/) | 串口命令协议（v1），固件与工具共用 | 联调前先定协议 |
| [software/](software/) | 串口调试上位机（可选，Python） | 看曲线、批量测试 |
| [references/](references/) | 官方/社区参考例程（语音、手势、OLED、传感器…），不参与编译 | 移植时对照，先跑通再抽片段 |
| [tools/](tools/) | BOM 整理、固件打包、日志分析等脚本 | 减少重复手工操作 |

## 推荐开发顺序

1. **需求与选型** — 定下风扇类型、供电方式、主控、传感器 → `docs/01-requirements.md`
2. **硬件** — 原理图 → PCB → 检查 → 下单打样 → 到货焊接 → 上电测试
3. **机械** — 先打印 1:1 关键件试配合（PCB 定位柱、风扇孔位），再整体打印
4. **软件** — 先打通"温度 → PWM → 风扇转速"最小闭环，再加联网与 App
5. **集成** — 整机装配、老化测试、记录问题 → 迭代下一版

> 硬件与外壳不要并行到"全部完成"再合并：PCB 尺寸一变，外壳就得重画。建议 PCB 定版（至少尺寸与安装孔冻结）后再开外壳。

## 工程约定

- 版本：硬件用 `revA / revB`，每次投板在 `hardware/fabrication/` 建日期快照目录。
- 文件命名：`功能_版本.扩展名`，小写加下划线，如 `fan_ctrl_revA.kicad_pcb`。
- 固件版本：`firmware/platformio.ini` 中的 `FW_VERSION` 宏，烧录后串口打印。
- 每次实验（尤其是失败）追加一条记录到 [docs/logs/](docs/logs/)。

## 已确认选型

| 项目 | 决定 |
| --- | --- |
| 风扇 | 12 V DC 4-pin PWM（12025），PWM 25 kHz + FG 测速 |
| 主控 | STM32F103C8T6（64 KB Flash / 20 KB RAM） |
| 传感器 | DS18B20 单总线 |
| 交互 | 旋转编码器 + 0.96" OLED（I²C）+ 蜂鸣器 |
| 语音 | SU-03T / ASR-PRO 离线语音模块（UART2，词条在厂商平台配置） |
| 手势 | PAJ7620U2（I²C1，与 OLED 共用总线） |
| 联网 | v1 不做，仅 UART1 调试 |

详见 [需求文档](docs/01-requirements.md) 与 [引脚分配](docs/hardware/pinmap.md)。
