"""Plot the buzzer flyback LTspice transient results.

Reads buzzer_flyback.raw (ASCII rawfile written by LTspice) and writes
buzzer_flyback_waveforms.png next to it.

Usage:  python plot_waveforms.py
"""
import os
import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "buzzer_flyback.raw")
OUT = os.path.join(HERE, "buzzer_flyback_waveforms.png")

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 10.5,
    "axes.titlesize": 11.5,
    "axes.labelsize": 10.5,
    "legend.fontsize": 9,
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
})

C_RED = "#C62828"
C_GREEN = "#2E7D32"
C_BLUE = "#1565C0"
C_PURPLE = "#6A1B9A"
C_ORANGE = "#EF6C00"
C_GRAY = "#546E7A"


def read_raw(path):
    """Parse an LTspice ASCII rawfile -> (names, array[points, vars])."""
    with open(path, "r", errors="replace") as f:
        text = f.read()
    cut = text.index("Values:")
    header, body = text[:cut], text[cut + 7:]
    nvars = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    npts = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    names = []
    for line in header.rsplit("Variables:", 1)[1].strip().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            names.append(parts[1])
    toks = body.split()
    if len(toks) != npts * (nvars + 1):
        raise ValueError("rawfile size mismatch: %d tokens for %d points" % (len(toks), npts))
    data = np.array(toks, dtype=float).reshape(npts, nvars + 1)
    return names, data[:, 1:]


def main():
    names, vals = read_raw(RAW)
    idx = {n.upper(): k for k, n in enumerate(names)}

    def col(key):
        return vals[:, idx[key.upper()]]

    t_us = col("time") * 1e6
    v_prot = col("V(coll_prot)")
    v_unprot = col("V(coll_unprot)")
    v_pb14 = col("V(pb14)")
    i_l1 = col("I(LBUZ1)") * 1e3
    i_l2 = col("I(LBUZ2)") * 1e3
    i_d1 = col("I(D_CLAMP1)") * 1e3
    ib1 = col("Ib(Q1)") * 1e3

    vcc = 5.0
    v_clamp = float(v_prot[t_us > 50.5].max())
    v_peak = float(v_unprot.max())
    t_peak = float(t_us[v_unprot.argmax()])
    v_min = float(v_unprot.min())
    t_recover = float(t_us[v_unprot.argmin()])
    i_off = float(np.interp(50.0, t_us, i_l1))
    i_diode = float(i_d1.max())
    t_over = t_us[v_unprot > 25.0]
    t_over_us = float(t_over.max() - t_over.min()) if t_over.size else 0.0
    ib_on = float(np.interp(45.0, t_us, ib1))
    ib_peak = float(ib1.max())
    i_l2_min = float(i_l2.min())
    t_l2_min = float(t_us[i_l2.argmin()])

    # the diode only conducts during flyback; mask elsewhere so the trace stays readable
    i_d1_plot = np.where((t_us > 49.0) & (t_us < 101.0), i_d1, np.nan)

    fig, ax = plt.subplots(2, 2, figsize=(13.6, 9.4))
    (a1, a2), (a3, a4) = ax

    def shade(axis, right=120):
        axis.axvspan(0, 50, color="#FFE082", alpha=0.20, lw=0)
        axis.axvspan(50, min(100, right), color="#90CAF9", alpha=0.15, lw=0)
        axis.axvline(50, color=C_GRAY, ls=":", lw=1.1)
        axis.axvline(100, color=C_GRAY, ls=":", lw=1.1)
        axis.set_xlim(0, right)

    # ---------------- (1) full-scale collector voltage ----------------
    shade(a1)
    a1.plot(t_us, v_unprot, color=C_RED, lw=1.1, label="无钳位 V(COLL_UNPROT)")
    a1.plot(t_us, v_prot, color=C_GREEN, lw=1.8, label="加 1N4148W V(COLL_PROT)")
    a1.axhline(25, color=C_RED, ls="--", lw=1.0, alpha=0.55, label="S8050 极限 $V_{CEO}$ = 25 V")
    a1.axhline(vcc, color=C_BLUE, ls=":", lw=1.2, alpha=0.8, label="5 V 电源轨")
    a1.set_ylim(-35, 365)
    a1.set_xlabel("时间 t [µs]")
    a1.set_ylabel("集电极电压 [V]")
    a1.set_title("(1) 全量程：无钳位反峰 %.1f V，有钳位仅 %.2f V" % (v_peak, v_clamp), pad=6)
    a1.legend(loc="upper left", framealpha=0.93)
    a1.annotate("反峰峰值 %.1f V\n@ %.2f µs" % (v_peak, t_peak),
                xy=(t_peak, v_peak), xytext=(60, 285),
                color=C_RED, fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2))
    a1.annotate("钳位后 %.2f V" % v_clamp,
                xy=(74, v_clamp), xytext=(62, 120),
                color=C_GREEN, fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_GREEN, lw=1.3))

    # ---------------- (2) zoom on the clamp ----------------
    shade(a2, right=104)
    a2.plot(t_us, v_unprot, color=C_RED, lw=1.1, label="无钳位（%.0f V 超出量程 ↑）" % v_peak)
    a2.plot(t_us, v_prot, color=C_GREEN, lw=2.0, label="加 1N4148W（钳位）")
    a2.axhline(25, color=C_RED, ls="--", lw=1.0, alpha=0.55, label="$V_{CEO}$ = 25 V")
    a2.axhline(v_clamp, color=C_GREEN, ls="-.", lw=1.0, alpha=0.85)
    a2.axhline(vcc, color=C_BLUE, ls=":", lw=1.2, alpha=0.8, label="5 V 电源轨")
    a2.set_ylim(-20, 30)
    a2.set_xlim(44, 104)
    a2.set_xlabel("时间 t [µs]")
    a2.set_ylabel("集电极电压 [V]")
    a2.set_title("(2) 关断瞬间放大：钳位电平 $V_{CC}+V_F$ = %.2f V" % v_clamp, pad=6)
    a2.legend(loc="upper right", framealpha=0.93)
    a2.annotate("%.3f V" % v_clamp, xy=(82, v_clamp), xytext=(84, 12),
                color=C_GREEN, fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_GREEN, lw=1.3))
    a2.annotate("超出 25 V 达 %.2f µs" % t_over_us,
                xy=(50.9, 25.6), xytext=(55, 22.5),
                color=C_RED, fontsize=9.5,
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.1))
    a2.annotate("最低 %.1f V @ %.2f µs" % (v_min, t_recover),
                xy=(t_recover, v_min), xytext=(58, -16),
                color=C_RED, fontsize=9.5,
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.1))

    # ---------------- (3) coil / flyback currents ----------------
    shade(a3)
    a3.plot(t_us, i_l1, color=C_GREEN, lw=1.9, label="I(LBUZ1) 有钳位线圈电流")
    a3.plot(t_us, i_l2, color=C_RED, lw=1.0, alpha=0.85, label="I(LBUZ2) 无钳位线圈电流")
    a3.plot(t_us, i_d1_plot, color=C_BLUE, lw=1.5, ls="--", label="I(D_CLAMP1) 续流电流")
    a3.axhline(0, color="k", lw=0.8)
    a3.set_ylim(-32, 42)
    a3.set_xlabel("时间 t [µs]")
    a3.set_ylabel("电流 [mA]")
    a3.set_title("(3) 线圈电流：关断瞬间 %.1f mA，二极管接管 %.1f mA" % (i_off, i_diode), pad=6)
    a3.legend(loc="lower right", framealpha=0.93)
    a3.annotate("能量经 D_CLAMP1 回馈 5 V",
                xy=(56, i_diode * 0.92), xytext=(63, 30), fontsize=9.5,
                color=C_BLUE,
                arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=1.1))
    a3.annotate("无钳位：无续流回路，电流跌至 %.0f mA (@ %.1f µs)" % (i_l2_min, t_l2_min),
                xy=(52.5, i_l2_min * 0.85), xytext=(8, -27), fontsize=9.5, color=C_RED,
                arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.1))

    # ---------------- (4) drive and base current ----------------
    shade(a4)
    a4.plot(t_us, ib1, color=C_ORANGE, lw=2.2, label="Ib(Q1) 基极电流 [mA]")
    a4.axhline(0, color="k", lw=0.8)
    a4.set_xlabel("时间 t [µs]")
    a4.set_ylabel("基极电流 [mA]")
    a4.set_ylim(-0.45, 3.6)
    a4.set_title("(4) 驱动时序：PB14 = 3.3 V 时 Ib = %.2f mA，可靠饱和" % ib_on, pad=6)
    a4.legend(loc="upper right", framealpha=0.93)
    a4.annotate("PB14 = 3.3 V\n(3.3 V - $V_{BE}$)/1 k\n= %.2f mA" % ib_on,
                xy=(25, ib_on), xytext=(9, 1.15), fontsize=9.5, color=C_ORANGE,
                arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=1.2))
    a4.annotate("PB14 = 0 V：Ib → 0\n10 k 下拉保证完全关断", xy=(62, 0.02), xytext=(57, 0.55),
                fontsize=9.5, color=C_GRAY,
                arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.2))
    a4.annotate("第二个周期重新导通", xy=(101.2, ib_peak), xytext=(86, 2.15),
                fontsize=9, color=C_GRAY,
                arrowprops=dict(arrowstyle="->", color=C_GRAY, lw=1.0))

    fig.suptitle("智能风扇 RevA · 蜂鸣器驱动感性反峰钳位仿真  |  LTspice 26.1.1 瞬态分析\n"
                 "S8050 驱动 5 mH 蜂鸣器线圈：1N4148W 续流把 %.1f V 反峰钳位到 %.2f V，"
                 "低于 $V_{CEO}$=25 V" % (v_peak, v_clamp),
                 fontsize=13.5, y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT)
    print("wrote", OUT)
    print("clamp=%.4f V  peak=%.1f V @ %.3f us  i_off=%.1f mA  i_diode=%.1f mA  Ib_on=%.2f/%.2f mA"
          % (v_clamp, v_peak, t_peak, i_off, i_diode, ib_on, ib_peak))


if __name__ == "__main__":
    main()
