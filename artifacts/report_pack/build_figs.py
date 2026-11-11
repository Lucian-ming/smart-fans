# -*- coding: utf-8 -*-
"""生成报告用图：系统框图、电源拓扑、状态机、条件仿真、壳体渲染、面板开孔示意图。"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection

plt.rcParams["font.family"] = "Microsoft YaHei"
plt.rcParams["axes.unicode_minus"] = False
OUT = os.path.dirname(os.path.abspath(__file__)) + "/figs"
os.makedirs(OUT, exist_ok=True)

C_PWR = "#fdecea"; C_PWR_E = "#c0392b"
C_MCU = "#e8f0fe"; C_MCU_E = "#1a56db"
C_PER = "#f3f4f6"; C_PER_E = "#4b5563"
C_ACT = "#e9f7ef"; C_ACT_E = "#1e8449"
C_HMI = "#f4ecf7"; C_HMI_E = "#7d3c98"
C_VOICE = "#fef5e7"; C_VOICE_E = "#b9770e"


def box(ax, x, y, w, h, text, fc=C_PER, ec=C_PER_E, fs=9.5, bold=False, lw=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.8",
                       fc=fc, ec=ec, lw=lw, ls=ls, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=4, linespacing=1.5)
    return (x, y, w, h)


def arrow(ax, p1, p2, color="#333333", lw=1.4, style="-|>", ls="-", rad=0.0, label=None,
          lfs=7.6, lcolor="#333333", ldx=0, ldy=0, both=False):
    a = FancyArrowPatch(p1, p2, arrowstyle=("<|-|>" if both else style), mutation_scale=11,
                        color=color, lw=lw, ls=ls, shrinkA=1, shrinkB=1, zorder=2,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + ldx, (p1[1] + p2[1]) / 2 + ldy
        ax.text(mx, my, label, ha="center", va="center", fontsize=lfs, color=lcolor,
                zorder=5, bbox=dict(fc="white", ec="none", pad=1.2, alpha=0.9))


# ---------------- 图1 系统总体框图 ----------------
def fig_system():
    fig, ax = plt.subplots(figsize=(16.2, 10.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    # 电源链（左侧，自上而下）
    box(ax, 2, 88, 19, 8, "5V / 2A 适配器输入\n(4.75-5.25V)", C_PWR, C_PWR_E, bold=True)
    box(ax, 2, 76, 19, 7, "F1  3A 快断保险\nLittelfuse 0451003", C_PWR, C_PWR_E)
    box(ax, 2, 64, 19, 7, "Q_PWR  AO4409\nP-MOS 反接保护", C_PWR, C_PWR_E)
    box(ax, 2, 52, 19, 7, "+5V 动力轨\nC1 100uF / C3 220uF", "#fff5e6", C_PWR_E, bold=True)
    box(ax, 2, 38, 19, 8, "AMS1117-3.3\n(或 TLV1117LV33)", C_PWR, C_PWR_E)
    box(ax, 2, 26, 19, 7, "+3.3V 逻辑轨\nC7/C8 10uF + 100nF", "#fff5e6", C_PWR_E, bold=True)
    for y in (88, 76, 64):
        arrow(ax, (11.5, y - 0.3), (11.5, y - 5.6), color=C_PWR_E, lw=1.5)
    arrow(ax, (11.5, 51.7), (11.5, 46.4), color=C_PWR_E, lw=1.5)
    arrow(ax, (11.5, 37.7), (11.5, 33.4), color=C_PWR_E, lw=1.5)
    ax.text(12.3, 49.6, "5V", fontsize=7.6, color=C_PWR_E)
    ax.text(21.6, 55.0, "5V", fontsize=7.6, color=C_PWR_E)
    ax.text(21.6, 30.2, "3.3V", fontsize=7.6, color=C_PWR_E)

    # 主控
    box(ax, 26, 34, 28, 34,
        "STM32F103C8T6 最小系统板（蓝板）\n"
        "72MHz  Cortex-M3  64KB Flash / 20KB SRAM\n\n"
        "TIM2_CH1   电机 PWM 25kHz\n"
        "TIM3       EC11 硬件正交解码\n"
        "TIM4_CH3   舵机 50Hz\n"
        "I2C1       OLED / PAJ7620\n"
        "USART2     ASR-PRO 115200\n"
        "USART1     调试 CLI\n"
        "SWD        烧录 / 在线调试", C_MCU, C_MCU_E, fs=9.6)

    # 执行与人机接口（右侧上列）
    rows = [
        (78, "TB6612FNG 电机驱动\nA 通道驱动 130 电机\nPA0/PA1/PA5/PB0", C_ACT, C_ACT_E),
        (66, "MG90S 舵机（360 连续旋转）\nPWM 调速 + 定时换向\nPB8  TIM4_CH3", C_ACT, C_ACT_E),
        (54, "OLED 0.96inch 128x64\nI2C 地址 0x3C\nPB6/PB7  I2C1", C_HMI, C_HMI_E),
        (42, "PAJ7620U2 手势传感器\nI2C 0x73 + INT\nPA4  GEST_INT", C_HMI, C_HMI_E),
        (30, "DHT11 温湿度\n单总线，4.7k 上拉\nPB9", C_HMI, C_HMI_E),
        (18, "EC11 编码器 + KEY1/KEY2\nPA6/PA7 正交，PB13/PB14 按键", C_HMI, C_HMI_E),
        (6, "有源蜂鸣器\n2N3904 + 1N4148 续流\nPB15", C_PER, C_PER_E),
    ]
    for y, t, fc, ec in rows:
        box(ax, 60, y, 26, 9.5, t, fc, ec, fs=8.5)
        arrow(ax, (54.4, min(66.5, max(35.0, y + 4.8))), (59.6, y + 4.8),
              color="#555555", lw=1.1)

    # 语音子系统
    box(ax, 60, 90, 26, 8, "ASR-PRO 离线语音模块\nUART1 115200 / 天问 Block\nPA2/PA3  USART2", C_VOICE, C_VOICE_E, fs=8.5)
    arrow(ax, (46, 68.4), (62, 89.6), color="#b9770e", lw=1.4, rad=0.15)
    ax.text(47.4, 80.6, "USART2", fontsize=7.6, color="#b9770e")
    box(ax, 89, 90, 10.5, 7, "8Ω 2W 喇叭", C_VOICE, C_VOICE_E, fs=8.2)
    box(ax, 89, 81, 10.5, 7, "MAX7219 x2\n8x8 点阵眼", C_VOICE, C_VOICE_E, fs=7.8)
    box(ax, 89, 72, 10.5, 7, "咪头\n面板 φ2.5", C_VOICE, C_VOICE_E, fs=8.0)
    for y in (93.5, 84.5, 75.5):
        arrow(ax, (86.2, 93.0), (88.6, y), color=C_VOICE_E, lw=1.0)
    arrow(ax, (21.2, 55.5), (25.6, 59.6), color=C_PWR_E, lw=1.3)
    ax.text(21.6, 58.6, "5V\n(JP_USB)", fontsize=7.0, color=C_PWR_E)

    box(ax, 2, 8, 19, 9, "跳帽隔离\nJP_ASR / JP_ASR_TX\nJP_ASR_RX / JP_USB", "#eef2f7", "#34495e", fs=8.0)
    ax.text(50, 1.2, "注：+5V 动力轨供 TB6612 VM、舵机、ASR-PRO、蜂鸣器、点阵；+3.3V 逻辑轨供 OLED、手势、DHT11、EC11、按键、TB6612 VCC；全系统共地。",
            ha="center", fontsize=8.6, color="#333333")

    ax.set_title("图 1  智能风扇系统总体框图（Rev B4，单 5V 供电）", fontsize=15, fontweight="bold", pad=12)
    fig.savefig(f"{OUT}/fig01_system_block.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- 图2 电源拓扑 ----------------
def fig_power():
    fig, ax = plt.subplots(figsize=(14, 4.6))
    ax.set_xlim(0, 100); ax.set_ylim(0, 32); ax.axis("off")
    items = [
        (2, "5V/2A\n适配器"),
        (16, "F1\n3A 保险"),
        (30, "Q_PWR\nAO4409\n防反接"),
        (46, "+5V 轨\nC1 100µF\nC3/C_VM 220µF"),
        (64, "AMS1117-3.3\n/TLV1117LV"),
        (82, "+3.3V 轨\nC7/C8 10µF+100nF"),
    ]
    for x, t in items:
        box(ax, x, 14, 13, 11, t, C_PWR, C_PWR_E, fs=8.4, bold=(x in (46, 82)))
    for x in (15, 29, 45, 63, 81):
        arrow(ax, (x - 0.2, 19.5), (x + 1.0, 19.5), color=C_PWR_E, lw=1.6)
    ax.text(50, 8.6, "5V 域：TB6612 VM、MG90S、ASR-PRO、蜂鸣器、MAX7219    |    3.3V 域：OLED、PAJ7620、DHT11、EC11、按键、TB6612 VCC",
            ha="center", fontsize=8.6, color="#333333")
    ax.text(50, 4.4, "取消 12V 支路与 XL1509 降压；蓝板两处 3V3 保持 NC，3.3V 仅由母板 LDO 提供（禁止双源并联）",
            ha="center", fontsize=8.6, color=C_PWR_E)
    ax.set_title("图 2  电源链路拓扑（单 5V 输入）", fontsize=13, fontweight="bold", pad=8)
    fig.savefig(f"{OUT}/fig02_power_chain.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- 图3 状态机 ----------------
def fig_fsm():
    fig, ax = plt.subplots(figsize=(12, 7.4))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    st = {
        "POWER_OFF": (16, 74, "POWER_OFF\n待机：输出 0%，10s 后熄屏"),
        "MANUAL_RUN": (58, 74, "MANUAL_RUN\n手动：40% 起调，±10%/步"),
        "AUTO_TEMP": (58, 26, "AUTO_TEMP\n自动：按温度分 5 段调速"),
        "TEST_MODE": (16, 26, "TEST_MODE\nCLI 单模块自检（test ...）"),
    }
    for k, (x, y, t) in st.items():
        fc = C_MCU if k != "TEST_MODE" else C_PER
        ec = C_MCU_E if k != "TEST_MODE" else C_PER_E
        box(ax, x, y, 26, 13, t, fc, ec, fs=9.2, bold=True)

    arrow(ax, (42.5, 80), (57.6, 80), color="#1e8449", lw=1.8, rad=0.0)
    ax.text(50, 84.6, "KEY1 / 语音 FON / 手势 WAVE（target=40%）", ha="center", fontsize=7.6, color="#1e8449")
    arrow(ax, (57.6, 76), (42.5, 76), color="#c0392b", lw=1.8)
    ax.text(50, 72.8, "KEY1 再按 / 语音 FOFF", ha="center", fontsize=7.6, color="#c0392b")
    arrow(ax, (71, 73.2), (71, 39.5), color="#b9770e", lw=1.8, rad=0.0)
    ax.text(72.2, 56, "KEY2 长按 / 语音 FMODE", fontsize=7.6, color="#b9770e")
    arrow(ax, (71, 39.5), (71, 73.2), color="#b9770e", lw=1.8, rad=0.25)
    ax.text(59.0, 50, "再次长按\n或手动调速\n强制回手动", fontsize=7.4, color="#b9770e")
    arrow(ax, (29, 74), (29, 39.5), color="#555555", lw=1.4, ls="--", rad=0.0)
    ax.text(29.6, 56, "CLI 进入 / 退出", fontsize=7.4, color="#555555")
    ax.text(50, 10, "任意状态 EMERGENCY_STOP 或 target=0 即回待机；手动调速会强制退出自动模式。\n"
                    "自动模式只在 AUTO_TEMP 内按 24–26 / 26–28 / 28–30 / >30℃ 输出 30% / 50% / 75% / 100%，<24℃ 停转。",
            ha="center", fontsize=8.5, color="#333333", linespacing=1.8)
    ax.set_title("图 3  风扇主状态机（firmware/src/app/fan_fsm.c）", fontsize=13, fontweight="bold", pad=10)
    fig.savefig(f"{OUT}/fig03_fsm.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- 图4/5 条件仿真 ----------------
def fig_sim():
    d = json.load(open("D:/smart_fans/artifacts/simulation_review/conditional_simulation_results.json", encoding="utf-8"))
    sup = d["supply_cases"]
    i2c = d["i2c_cases"]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.0))
    ax = axes[0]
    groups = {}
    for c in sup:
        groups.setdefault(c["rloop"], []).append((c["vin"], c["v_loaded"], c["v_min"]))
    for r in sorted(groups):
        pts = sorted(groups[r])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, "o-", lw=1.8, ms=4.5, label=f"回路总阻 R = {r:.2f} Ω")
    ax.axhline(4.5, color="#c0392b", ls="--", lw=1.2)
    ax.text(4.77, 4.53, "TB6612 VM 下限 4.5V", fontsize=7.8, color="#c0392b")
    ax.set_xlabel("输入电压 Vin / V"); ax.set_ylabel("负载时母线电压 V_loaded / V")
    ax.set_title("(a) 供电回路：2A 负载下的母线电压", fontsize=10.5)
    ax.grid(alpha=0.3); ax.legend(fontsize=7.8, loc="lower right")
    ax.set_xlim(4.70, 5.30)

    ax = axes[1]
    g2 = {}
    for c in i2c:
        g2.setdefault(c["rpull"], []).append((c["cbus"] * 1e12, c["tr_30_70_s"] * 1e9))
    for rp in sorted(g2.keys()):
        pts = sorted(g2[rp])
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        ax.plot(xs, ys, "s-", lw=1.6, ms=3.6, label=f"上拉 {rp/1000:.2f}kΩ")
    ax.axhline(300, color="#c0392b", ls="--", lw=1.1)
    ax.axhline(1000, color="#b9770e", ls=":", lw=1.1)
    ax.text(60, 315, "快速模式 300ns", fontsize=7.6, color="#c0392b")
    ax.text(60, 1030, "标准模式 1000ns", fontsize=7.6, color="#b9770e")
    ax.set_xlabel("总线电容 C_bus / pF"); ax.set_ylabel("上升时间 t_r(30–70%) / ns")
    ax.set_title("(b) I2C 上升时间扫描（4.7k 上拉 + 模块并联合成 2.35k/1.57k）", fontsize=9.6)
    ax.grid(alpha=0.3); ax.legend(fontsize=7.8)
    ax.set_yscale("log")

    fig.suptitle("图 4  条件仿真结果（LTspice 扫描，2026-11-04；仅为设界分析，不是整机验收）",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(f"{OUT}/fig04_conditional_sim.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- 图5 壳体渲染（自写 z-buffer 光栅化） ----------------
def _project(v, elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    right = np.array([-math.sin(a), math.cos(a), 0.0])
    up = np.array([-math.sin(e) * math.cos(a), -math.sin(e) * math.sin(a), math.cos(e)])
    return v @ right, v @ up, v @ d, d


def _render(meshes_with_offsets, elev, azim, W=1500, H=1050, ss=2):
    verts, faces, colors, counts = [], [], [], []
    base_idx = 0
    for mesh, color, offset in meshes_with_offsets:
        v = np.asarray(mesh.vertices) + np.array(offset, float)
        f = np.asarray(mesh.faces)
        verts.append(v)
        faces.append(f + base_idx)
        base_idx += len(v)
        colors.append(np.array(matplotlib.colors.to_rgb(color)))
        counts.append(len(f))
    v = np.vstack(verts); f = np.vstack(faces)
    colors = np.repeat(np.array(colors), counts, axis=0)
    tri = v[f]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    n = n / ln[:, None]
    xs, ys, zs, d = _project(v, elev, azim)
    light = np.array([0.4, -0.3, 0.87]); light = light / np.linalg.norm(light)
    shade = 0.34 + 0.66 * np.clip(n @ light, 0, 1)
    face_col = np.clip(colors * shade[:, None], 0, 1)

    pad = 0.04
    x0, x1 = xs.min(), xs.max(); y0, y1 = ys.min(), ys.max()
    span = max(x1 - x0, y1 - y0) * (1 + pad)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    Ws, Hs = W * ss, H * ss
    px = (xs - cx) / span * Ws + Ws / 2
    py = Hs / 2 - (ys - cy) / span * Ws
    zbuf = np.full((Hs, Ws), -1e9, dtype=np.float32)
    img = np.ones((Hs, Ws, 3), dtype=np.float32)
    order = np.argsort(zs[f].mean(axis=1))
    for i in order:
        a, b, c = f[i]
        X = px[[a, b, c]]; Y = py[[a, b, c]]; Z = zs[[a, b, c]]
        xmin = max(int(np.floor(X.min())), 0); xmax = min(int(np.ceil(X.max())), Ws - 1)
        ymin = max(int(np.floor(Y.min())), 0); ymax = min(int(np.ceil(Y.max())), Hs - 1)
        if xmax < xmin or ymax < ymin:
            continue
        den = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(ymin, ymax + 1))
        w1 = ((Y[1] - Y[2]) * (gx - X[2]) + (X[2] - X[1]) * (gy - Y[2])) / den
        w2 = ((Y[2] - Y[0]) * (gx - X[2]) + (X[0] - X[2]) * (gy - Y[2])) / den
        w3 = 1 - w1 - w2
        m = (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6)
        if not m.any():
            continue
        z = w1 * Z[0] + w2 * Z[1] + w3 * Z[2]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = m & (z > sub)
        if not upd.any():
            continue
        sub[upd] = z[upd]
        img[ymin:ymax + 1, xmin:xmax + 1][upd] = face_col[i]
    from PIL import Image
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    im = im.resize((W, H), Image.LANCZOS)
    return im


def fig_case():
    import trimesh
    paths = {
        "base": "D:/smart_fans/mechanical/stl/print/SmartFan_Piece1_Base_Enclosure.stl",
        "lid": "D:/smart_fans/mechanical/stl/print/SmartFan_Piece3_Removable_Lid.stl",
        "bracket": "D:/smart_fans/mechanical/stl/print/SmartFan_Piece2_Fan_Gimbal_Bracket.stl",
    }
    m = {k: trimesh.load(v, force="mesh") for k, v in paths.items()}
    im1 = _render([(m["base"], "#b7c4d2", (0, 0, 0)), (m["lid"], "#d9c7a8", (0, 0, 8.1))], 26, -58)
    im2 = _render([(m["bracket"], "#9dc19a", (0, 0, 0))], 26, -62)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.4))
    for ax, im, t in zip(axes, [im1, im2],
                         ["(a) 下壳 + 可拆盖（装配示意）", "(b) 风扇/舵机摇臂支架 84×30×24mm"]):
        ax.imshow(im); ax.axis("off"); ax.set_title(t, fontsize=10.5)
    fig.suptitle("图 5  外壳三件模型（STL 独立复核：均水密、单壳体；合计 68.97cm³，低于 70cm³ 打印限额）",
                 fontsize=12.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT}/fig05_case_parts.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- 图6 面板开孔示意 ----------------
def fig_panel():
    n = np.array([0, math.sin(math.radians(25)), math.cos(math.radians(25))])
    d = np.array([0, math.cos(math.radians(25)), -math.sin(math.radians(25))])
    holes = [
        ("OLED 28×16.5", (80.5, 64.0, 26.803), (28.0, 16.5), "rect"),
        ("PAJ7620 φ10", (18.0, 76.0, 21.208), (10, 10), "circle"),
        ("KEY1 φ7", (36.0, 86.0, 21.75), (7, 7), "circle"),
        ("KEY2 φ7", (51.5, 86.0, 21.75), (7, 7), "circle"),
        ("EC11 φ9", (73.0, 88.0, 15.612), (9, 9), "circle"),
        ("MIC φ2.5", (92.0, 88.0, 15.612), (2.5, 2.5), "circle"),
    ]
    fig, ax = plt.subplots(figsize=(12.6, 5.9))
    ax.set_xlim(-3, 102); ax.set_ylim(30, 90); ax.set_aspect("equal")
    ax.add_patch(Rectangle((0, 36), 99, 44, fc="#f7f9fc", ec="#333333", lw=1.4, zorder=1))
    uv = {}
    for name, p, size, kind in holes:
        u = p[0]; v = float(d @ np.array(p)); uv[name] = (u, v)
        if kind == "rect":
            ax.add_patch(Rectangle((u - size[0] / 2, v - size[1] / 2), size[0], size[1],
                                   fc="white", ec="#1a56db", lw=1.8, zorder=3))
            ax.text(u, v, name, ha="center", va="center", fontsize=8.6, color="#1a2b4a", zorder=4)
        else:
            ax.add_patch(Circle((u, v), size[0] / 2, fc="white", ec="#1a56db", lw=1.8, zorder=3))
            off = {10: 15, 9: 14, 7: 12, 2.5: 8}.get(size[0], 12)
            ax.annotate(name, (u, v), textcoords="offset points", xytext=(0, off),
                        ha="center", fontsize=8.6, color="#1a2b4a")

    # 水平中心距（面板上方，画在框内）
    for (n1, n2, val) in [("KEY1 φ7", "KEY2 φ7", "15.5"), ("KEY2 φ7", "EC11 φ9", "21.5")]:
        (u1, v1), (u2, v2) = uv[n1], uv[n2]
        y = 85.5
        ax.annotate("", xy=(u1, y), xytext=(u2, y),
                    arrowprops=dict(arrowstyle="<->", color="#1e8449", lw=1.1, shrinkA=0, shrinkB=0))
        ax.text((u1 + u2) / 2, y + 1.2, val, fontsize=8.0, color="#1e8449", ha="center")
        for u in (u1, u2):
            ax.plot([u, u], [y - 0.8, y + 0.8], color="#1e8449", lw=0.8)

    # 垂直孔沿距：OLED 上沿到 EC11 下沿
    oled_top = uv["OLED 28×16.5"][1] + 16.5 / 2
    ec11_bot = uv["EC11 φ9"][1] - 9 / 2
    x = 92.0
    ax.annotate("", xy=(x, oled_top), xytext=(x, ec11_bot),
                arrowprops=dict(arrowstyle="<->", color="#c0392b", lw=1.1, shrinkA=0, shrinkB=0))
    ax.text(x + 1.8, (oled_top + ec11_bot) / 2, "13.73", fontsize=8.0, color="#c0392b", va="center")
    ax.text(x + 1.8, (oled_top + ec11_bot) / 2 - 2.6, "孔沿距", fontsize=7.4, color="#c0392b", va="center")

    ax.text(49.5, 31.6, "沿 25° 斜面展开：u = X 向，v = 沿坡面方向，单位 mm。孔均为沿坡面法向开孔。\n本图为示意，非加工图；加工尺寸以 STL 与 P2 复核报告为准。",
            ha="center", fontsize=8.0, color="#444444", linespacing=1.6)
    ax.set_xlabel("u / mm", labelpad=16); ax.set_ylabel("v / mm")
    ax.set_xticks([0, 20, 40, 60, 80, 99]); ax.grid(alpha=0.22)
    ax.set_title("图 6  前面板开孔布置示意图（25° 斜面，STL 实测中心投影）", fontsize=12.5, fontweight="bold")
    fig.savefig(f"{OUT}/fig06_panel_layout.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


fig_system()
fig_power()
fig_fsm()
fig_sim()
fig_case()
fig_panel()
print("ok")
