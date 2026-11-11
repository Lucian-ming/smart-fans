"""
Script: tools/test_90x90_layout.py
Tests collision-free placement for fan_ctrl_revB on 90x90 mm board.
"""

import math

BOARD_W = 90.0
BOARD_H = 90.0

HOLES = [
    {"name": "H1", "x": 5.0, "y": 5.0, "r": 4.5},
    {"name": "H2", "x": 85.0, "y": 5.0, "r": 4.5},
    {"name": "H3", "x": 5.0, "y": 85.0, "r": 4.5},
    {"name": "H4", "x": 85.0, "y": 85.0, "r": 4.5}
]

# Physical Modules and Components
# All coordinates are (cx, cy, width, height)
modules = [
    # Top Row: Power & Connectors (Y: 6 ~ 18)
    {"id": "DC1", "name": "DC-005 12V", "x": 16.0, "y": 10.0, "w": 9.5, "h": 14.0},
    {"id": "D2", "name": "SS24 防反接", "x": 24.0, "y": 10.0, "w": 4.5, "h": 2.5},
    {"id": "C1", "name": "100uF 25V电解", "x": 30.0, "y": 10.0, "w": 5.0, "h": 5.0},
    {"id": "C2", "name": "100nF 0805", "x": 35.0, "y": 10.0, "w": 2.0, "h": 1.25},
    {"id": "U2", "name": "XL1509-5.0 (SOIC-8)", "x": 41.5, "y": 10.0, "w": 5.0, "h": 4.0},
    {"id": "D1", "name": "SS24 续流", "x": 47.5, "y": 10.0, "w": 4.5, "h": 2.5},
    {"id": "L1", "name": "47uH CD54电感", "x": 54.5, "y": 10.0, "w": 5.8, "h": 5.2},
    {"id": "C3", "name": "220uF 16V电解", "x": 62.0, "y": 10.0, "w": 6.3, "h": 6.3},
    {"id": "C4", "name": "100nF 0805", "x": 67.5, "y": 10.0, "w": 2.0, "h": 1.25},
    {"id": "U3", "name": "AMS1117-3.3 (SOT-223)", "x": 73.0, "y": 10.0, "w": 6.5, "h": 3.5},
    {"id": "C5_C6", "name": "10uF 0805 x2", "x": 78.5, "y": 10.0, "w": 2.5, "h": 4.5},

    # Row 2: Actuator Headers & Buzzer (Y: 20 ~ 26)
    {"id": "MOTO1", "name": "130电机接口 XH2.54", "x": 12.0, "y": 22.0, "w": 6.0, "h": 6.0},
    {"id": "SERVO1", "name": "MG90S舵机针座 1x3P", "x": 22.0, "y": 22.0, "w": 7.6, "h": 4.0},
    {"id": "BZ1_GRP", "name": "蜂鸣器与驱动回路", "x": 33.0, "y": 22.0, "w": 12.0, "h": 12.0},
    {"id": "SPK1", "name": "喇叭接口 XH2.54", "x": 72.0, "y": 20.0, "w": 6.0, "h": 6.0},
    {"id": "MIC1", "name": "咪头接口 XH2.54", "x": 80.0, "y": 20.0, "w": 6.0, "h": 6.0},

    # Middle Zone: Processing Modules (Y: 30 ~ 68)
    # Left: TB6612 (21.5w x 19.0h) and DHT11 (15.5w x 12.0h)
    {"id": "TB6612", "name": "TB6612 驱动模块", "x": 16.0, "y": 38.0, "w": 22.0, "h": 20.0},
    {"id": "DHT11", "name": "DHT11 模块", "x": 16.0, "y": 56.0, "w": 16.0, "h": 13.0},

    # Center: STM32 Blue Pill (22.8w x 53.0h)
    {"id": "STM32", "name": "STM32 蓝板", "x": 45.0, "y": 45.0, "w": 23.0, "h": 53.0},

    # Right: ASR-PRO 14P Voice Board (30.0w x 28.0h)
    {"id": "ASR_PRO", "name": "ASR-PRO 语音板", "x": 73.0, "y": 38.0, "w": 28.0, "h": 28.0},

    # Front Zone: 2-Row Ergonomic Interactive Layout (Y: 66 ~ 85)
    # Upper Row (Visual & Gesture):
    {"id": "GESTURE", "name": "PAJ7620 手势模块", "x": 20.0, "y": 71.0, "w": 20.5, "h": 15.5},
    {"id": "OLED", "name": "0.96寸 OLED 屏", "x": 72.0, "y": 68.0, "w": 27.5, "h": 27.0},

    # Lower Row (Physical Touch & Knobs):
    {"id": "KEY1", "name": "按键1【电源】", "x": 15.0, "y": 83.0, "w": 14.0, "h": 10.0},
    {"id": "KEY2", "name": "按键2【摇头模式】", "x": 31.0, "y": 83.0, "w": 14.0, "h": 10.0},
    {"id": "ENCODER", "name": "360° 旋转编码器", "x": 50.0, "y": 81.0, "w": 22.0, "h": 15.0}
]

def check(mods):
    issues = []
    for m in mods:
        x_min = m["x"] - m["w"]/2.0
        x_max = m["x"] + m["w"]/2.0
        y_min = m["y"] - m["h"]/2.0
        y_max = m["y"] + m["h"]/2.0
        if x_min < 1.0 or y_min < 1.0 or x_max > BOARD_W - 1.0 or y_max > BOARD_H - 1.0:
            issues.append(f"EDGE OVERFLOW: {m['id']} [X:{x_min:.1f}~{x_max:.1f}, Y:{y_min:.1f}~{y_max:.1f}]")
            
        for h in HOLES:
            cx = max(m["x"] - m["w"]/2.0, min(h["x"], m["x"] + m["w"]/2.0))
            cy = max(m["y"] - m["h"]/2.0, min(h["y"], m["y"] + m["h"]/2.0))
            dist = math.hypot(h["x"] - cx, h["y"] - cy)
            if dist < h["r"] + 0.5:
                issues.append(f"HOLE COLLISION: {m['id']} and {h['name']} dist={dist:.2f} < {h['r']+0.5:.2f}")

    n = len(mods)
    for i in range(n):
        for j in range(i+1, n):
            m1 = mods[i]
            m2 = mods[j]
            dx = abs(m1["x"] - m2["x"]) - (m1["w"] + m2["w"])/2.0
            dy = abs(m1["y"] - m2["y"]) - (m1["h"] + m2["h"])/2.0
            if dx < 0.8 and dy < 0.8:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}, dy={dy:.2f})")
                
    return issues

issues = check(modules)
print(f"Board: {BOARD_W}x{BOARD_H} mm | Total issues: {len(issues)}")
for iss in issues:
    print(" -", iss)
if not issues:
    print("SUCCESS: 90x90mm board is 100% collision-free!")
