# mechanical/

## 目录职责

| 目录 | 内容 | 格式 |
| --- | --- | --- |
| [cad/](cad/) | 外壳 3D 源文件 | FreeCAD `.FCStd` / Fusion `.f3d`（保留特征树，能改尺寸） |
| [step/](step/) | 装配用 STEP | `.step`，含风扇与 PCB 简化模型，用于干涉检查 |
| [stl/print/](stl/print/) | 可直接切片的打印件 | 按件号命名，如 `P-01_front_shell.stl` |
| [stl/reference/](stl/reference/) | 参考模型（风扇、PCB、螺丝） | 从厂商下载或从 KiCad 3D 导出，**不用于打印** |
| [print-profiles/](print-profiles/) | 切片配置 | PrusaSlicer `.ini` / Orca `.json`，文件名带机器与材料 |
| [drawings/](drawings/) | 2D 尺寸图、装配爆炸图 | PDF / SVG |

## 建模约定

- 单位 mm，Z 轴向上，模型底面贴合 Z=0（方便切片）
- 每个零件一个 Body，命名与打印清单一致（P-01…）
- 关键尺寸用参数/表达式驱动（壁厚、孔径），便于改版
- 装配体里放**真实尺寸**的风扇与 PCB 模型（PCB 从 KiCad 导出 STEP），先做干涉检查再导出 STL

## 命名

```
P-01_front_shell_revA.stl
P-02_rear_shell_revA.stl
```

## 与其他部分的对齐点

| 需对齐 | 来源 | 检查方式 |
| --- | --- | --- |
| PCB 外形与安装孔 | `hardware/kicad/` | KiCad 导出 STEP 放入装配体 |
| 风扇孔距与厚度 | 风扇数据手册 | 建模时按手册，打印前用卡尺复核实物 |
| 接插件开口位置 | 原理图/PCB 布局 | 装配体剖面 + 试装 |
| 旋钮与编码器轴 | 编码器数据手册 | 打印旋钮后实装验证 |
