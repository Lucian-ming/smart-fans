# LTspice 仿真工程 — 蜂鸣器驱动感性反峰钳位

对应设计文档 [SCHEMATIC_DESIGN.md](../SCHEMATIC_DESIGN.md) 3.8 节（BZ1 / Q1 / D3）。

## 文件说明

| 文件 | 说明 |
| :--- | :--- |
| `buzzer_flyback.asc` | **LTspice 原理图（可直接打开、按 Run）** |
| `buzzer_flyback.cir` | 原始 SPICE 网表（纯文本，无图形界面） |
| `buzzer_flyback.net` | 与 `.cir` 同内容的网表副本 |
| `buzzer_flyback.raw` | 瞬态仿真数据（12082 点 × 31 变量，ASCII rawfile） |
| `buzzer_flyback.op.raw` | 直流工作点 |
| `buzzer_flyback_waveforms.png` | 由 `buzzer_flyback.raw` 绘制的波形图 |
| `plot_waveforms.py` | 波形图生成脚本（`python plot_waveforms.py`） |

## 使用方法

1. 双击 `buzzer_flyback.asc`（或在 LTspice 中 File → Open）；
2. 按 **Run**（工具栏跑步图标 / `Ctrl+R`）；
3. 波形窗口中点选 `V(COLL_PROT)`、`V(COLL_UNPROT)`、`I(LBUZ1)` 等信号查看。

`.tran 0.1u 120u 0 10n` 已写在原理图里，无需重新设置仿真参数；两个 `.model`（S8050、1N4148W）以 SPICE 指令形式内嵌在图纸下方。

## 电路结构

两个驱动器**共用**同一个 PB14 脉冲、同一个 5 V 电源，唯一差别是续流二极管：

```
                      +5V                        +5V
                       │                          │
            RBUZ1 100Ω │             RBUZ2 100Ω   │
                       │                          │
              LBUZ1 5mH │                LBUZ2 5mH │
                       ├── COLL_PROT              ├── COLL_UNPROT
                  ┌────┴────┐                ┌────┴────┐
              D_CLAMP1     │                │  CPAR2 35pF │
              1N4148W      │                │  (寄生电容) │
              (阳极朝集电极)│                │             │
                  └────┬────┘                └────┬────┘
                       │                          │
   PB14 ──1k──┬── B  Q1 S8050          PB14 ──1k──┬── B  Q2 S8050
              │                                    │
            10k                                  10k
              │                                    │
             GND                                  GND
```

- 左侧：**有钳位**（1N4148W 反并联在线圈两端，为反峰提供泄放回路）；
- 右侧：**无钳位**（仅保留 35 pF 集电极寄生电容，用于对比反峰电压）。

## 仿真结果（LTspice 26.1.1，真实引擎结果）

| 指标 | 有钳位 | 无钳位 |
| :--- | :--- | :--- |
| 关断瞬间集电极电压 | **5.758 V**（= 5 V + V_F） | **322.9 V** @ 51.14 µs |
| 超过 S8050 `V_CEO` = 25 V 的时间 | 0 | **1.47 µs** |
| 关断瞬间线圈电流 | 31.4 mA | 31.4 mA |
| 最低电压（反向摆幅） | — | −14.2 V @ 51.87 µs |

其他：
- 基极驱动 `Ib = (3.3 V − 0.75 V) / 1 kΩ ≈ 2.47 mA`，`Ic ≈ 29.5 mA`，强制 β≈12，S8050 深度饱和；
- 续流二极管峰值电流 31.8 mA，能量经 D_CLAMP1 回馈 5 V 电源轨；
- 线圈电流按 `I = (5 V / 100 Ω)·(1 − e^(−t/50 µs))` 上升，50 µs 时约 31 mA（τ = L/R = 50 µs，尚未到 50 mA 稳态值）。

## 与 `.cir` 网表的等价性

`buzzer_flyback.asc` 由 LTspice 批量模式生成的网表与原 `buzzer_flyback.cir` 拓扑一致，
仅有一处命名差异：二极管模型用 `1N4148W`（避免与 LTspice 自带 `standard.dio` 中
`1N4148` 的 tt=20n 版本冲突），其余参数完全相同。

实测对比：两套 `.raw` 的 29 条公共曲线逐点相减，**最大绝对误差 0.000e+00**（完全一致）。

## 与 SIMULATION_REPORT.md 的数值差异

`../SIMULATION_REPORT.md` 中记录的「无钳位反峰 782.9 V、线圈电流 50 mA」来自早期的
Python ODE 简化模型，与 LTspice 实际引擎结果（322.9 V、31.4 mA）不符，以本目录数据为准：

- 峰值偏低：真实集电极寄生电容（35 pF）+ S8050 的结电容与反向击穿导通了部分能量，
  且线圈电流只有 31.4 mA（不是稳态 50 mA），`½LI² ` 能量仅 2.47 mJ；
- 即便如此，322.9 V 仍是 25 V 极限的 **12.9 倍**，无钳位电路必然击穿 S8050 —— 结论不变。
