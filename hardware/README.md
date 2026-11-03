# hardware/

| 子目录 | 内容 | 说明 |
| --- | --- | --- |
| [kicad/](kicad/) | KiCad 工程：原理图、PCB、自建符号/封装库 | 唯一电路设计源文件 |
| [datasheets/](datasheets/) | 芯片、风扇、传感器数据手册（PDF） | 文件名用型号，如 `STM32F103C8T6_datasheet.pdf` |
| [fabrication/](fabrication/) | 发给板厂的文件与回传资料 | 每次投板建日期快照 |

## fabrication/ 快照规则

每次下单前新建目录并完整存放，不要覆盖上一版：

```
fabrication/
├── revA_2026-11-10/
│   ├── gerber/          # 打样必交：GTL/GBL/GTS/GBS/GTO/GBO/GKO + 钻孔
│   ├── bom/             # 物料清单（含位号、型号、封装、数量）
│   └── assembly/        # 坐标文件（CPL/Pick&Place），贴片厂用
└── revB_2026-12-01/
```

**规则**：没有 `gerber/` 的目录不算一版；下单前用在线 Gerber 查看器（如 KiCad 的 Gerber Viewer）逐层核对。
