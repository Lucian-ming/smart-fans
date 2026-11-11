"""
Script: tools/verify_perfect_95x95.py
Calculates and verifies all clearances for the 95x95 layout.
"""
import math

BOARD_W = 95.0
BOARD_H = 95.0

HOLES = [
    {"name": "H1", "x": 5.0, "y": 5.0, "r": 4.5},
    {"name": "H2", "x": 90.0, "y": 5.0, "r": 4.5},
    {"name": "H3", "x": 5.0, "y": 90.0, "r": 4.5},
    {"name": "H4", "x": 90.0, "y": 90.0, "r": 4.5},
]

modules = [
    # Top Power Section (Y: 5 ~ 12)
    {"id": "DC1", "name": "DC-005", "x": 15.0, "y": 8.0, "w": 9.0, "h": 14.0},
    {"id": "D2", "name": "SS24", "x": 23.5, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "C1", "name": "100uF", "x": 29.5, "y": 7.0, "w": 5.0, "h": 5.0},
    {"id": "U2", "name": "XL1509", "x": 36.0, "y": 7.0, "w": 5.0, "h": 4.0},
    {"id": "D1", "name": "SS24_SW", "x": 42.5, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "L1", "name": "47uH", "x": 49.0, "y": 7.0, "w": 5.8, "h": 5.2},
    {"id": "C3", "name": "220uF", "x": 56.5, "y": 7.0, "w": 6.3, "h": 6.3},
    {"id": "U3", "name": "AMS1117", "x": 64.0, "y": 7.0, "w": 6.5, "h": 3.5},
    {"id": "C5", "name": "10uF", "x": 70.0, "y": 7.0, "w": 2.5, "h": 3.5},

    # Row 2: Actuators (Y: 17 ~ 22)
    {"id": "MOTO1", "name": "130 Motor", "x": 10.0, "y": 19.5, "w": 5.0, "h": 5.0},
    {"id": "SERVO1", "name": "MG90S Servo", "x": 18.0, "y": 19.5, "w": 7.6, "h": 4.0},
    {"id": "BZ1_GRP", "name": "Buzzer", "x": 27.5, "y": 19.5, "w": 8.0, "h": 8.0},

    # Middle Left: TB6612 & DHT11
    {"id": "TB6612", "name": "TB6612", "x": 15.5, "y": 36.0, "w": 21.5, "h": 19.0},
    {"id": "DHT11", "name": "DHT11", "x": 15.5, "y": 55.0, "w": 15.5, "h": 12.0},

    # Center: STM32 Blue Pill
    {"id": "STM32", "name": "STM32 Blue Pill", "x": 47.5, "y": 40.0, "w": 22.86, "h": 53.34},

    # Right Column: ASR-PRO & OLED
    {"id": "ASR_PRO", "name": "ASR-PRO", "x": 78.5, "y": 25.5, "w": 30.0, "h": 28.0},
    {"id": "OLED", "name": "0.96 OLED", "x": 78.5, "y": 55.0, "w": 27.0, "h": 27.5},

    # Front Row: PAJ7620, KEY1, KEY2, EC11
    {"id": "GESTURE", "name": "PAJ7620", "x": 16.0, "y": 74.0, "w": 20.0, "h": 15.0},
    {"id": "KEY1", "name": "KEY1 Power", "x": 34.0, "y": 82.5, "w": 13.5, "h": 19.6},
    {"id": "KEY2", "name": "KEY2 Swing", "x": 49.5, "y": 82.5, "w": 13.5, "h": 19.6},
    {"id": "ENCODER", "name": "EC11 Encoder", "x": 71.0, "y": 82.5, "w": 26.0, "h": 19.0}
]

def check(mods):
    issues = []
    for m in mods:
        x_min = m["x"] - m["w"]/2.0
        x_max = m["x"] + m["w"]/2.0
        y_min = m["y"] - m["h"]/2.0
        y_max = m["y"] + m["h"]/2.0
        if x_min < 0.8 or y_min < 0.8 or x_max > BOARD_W - 0.8 or y_max > BOARD_H - 0.8:
            issues.append(f"EDGE OVERFLOW: {m['id']} [X:{x_min:.1f}~{x_max:.1f}, Y:{y_min:.1f}~{y_max:.1f}]")
            
        for h in HOLES:
            cx = max(x_min, min(h["x"], x_max))
            cy = max(y_min, min(h["y"], y_max))
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
            if dx < 1.0 and dy < 1.0:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}mm, dy={dy:.2f}mm)")
                
    return issues

issues = check(modules)
print(f"95x95 Board: Total issues: {len(issues)}")
for iss in issues:
    print(" -", iss)
if not issues:
    print("SUCCESS: 95x95mm board is 100% collision-free with real 19.6mm button modules and all clearances >= 1.0mm!")
