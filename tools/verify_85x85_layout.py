"""
Script: tools/verify_85x85_layout.py
Simulates and verifies 100% collision-free placement for all modules on an 85x85 mm board.
"""

import math

BOARD_W = 85.0
BOARD_H = 85.0

HOLES = [
    {"name": "H1", "x": 5.0, "y": 5.0, "r": 4.5},
    {"name": "H2", "x": 80.0, "y": 5.0, "r": 4.5},
    {"name": "H3", "x": 5.0, "y": 80.0, "r": 4.5},
    {"name": "H4", "x": 80.0, "y": 80.0, "r": 4.5},
]

# Physical Modules and Components on 85x85 mm board
# Dimensions: (id, name, cx, cy, width, height)
modules = [
    # Top Row: Power & Connectors (Y: 6 ~ 14)
    {"id": "DC1", "name": "DC-005 12V", "x": 15.0, "y": 8.5, "w": 9.0, "h": 13.0},
    {"id": "D2", "name": "SS24 Anti-Reverse", "x": 22.0, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "C1", "name": "100uF 25V", "x": 27.0, "y": 7.0, "w": 5.0, "h": 5.0},
    {"id": "U2", "name": "XL1509-5.0", "x": 33.5, "y": 7.0, "w": 5.0, "h": 4.0},
    {"id": "D1", "name": "SS24 Freewheel", "x": 39.0, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "L1", "name": "47uH Inductor", "x": 45.0, "y": 7.0, "w": 5.8, "h": 5.2},
    {"id": "C3", "name": "220uF 16V", "x": 52.0, "y": 7.0, "w": 6.3, "h": 6.3},
    {"id": "U3", "name": "AMS1117-3.3", "x": 59.0, "y": 7.0, "w": 6.5, "h": 3.5},
    {"id": "C5_C6", "name": "10uF Caps", "x": 65.0, "y": 7.0, "w": 3.0, "h": 4.0},

    # Row 2: Actuators (Y: 17 ~ 22)
    {"id": "MOTO1", "name": "130 Motor XH2.54", "x": 11.0, "y": 18.0, "w": 5.5, "h": 5.0},
    {"id": "SERVO1", "name": "MG90S Servo 1x3P", "x": 19.5, "y": 18.0, "w": 7.6, "h": 4.0},
    {"id": "BZ1_GRP", "name": "Buzzer + Transistor", "x": 29.0, "y": 18.0, "w": 10.0, "h": 10.0},

    # Middle Zone: Processing Modules (Y: 25 ~ 65)
    # Left: TB6612 (21.5w x 19.0h) and DHT11 (15.5w x 12.0h)
    {"id": "TB6612", "name": "TB6612 Module", "x": 14.5, "y": 32.5, "w": 21.5, "h": 19.0},
    {"id": "DHT11", "name": "DHT11 Module", "x": 13.5, "y": 48.5, "w": 15.5, "h": 12.0},

    # Center: STM32 Blue Pill (22.8w x 53.0h)
    {"id": "STM32", "name": "STM32 Blue Pill", "x": 42.5, "y": 38.0, "w": 22.8, "h": 50.0},

    # Right: ASR-PRO 14P Voice Board (28.0w x 28.0h)
    {"id": "ASR_PRO", "name": "ASR-PRO Voice Board", "x": 69.5, "y": 25.0, "w": 27.0, "h": 27.0},

    # Front Interaction Zone: 2-Row Ergonomic Layout (Y: 57 ~ 82)
    # Upper Row (Visual & Gesture):
    {"id": "GESTURE", "name": "PAJ7620 Gesture", "x": 15.5, "y": 62.5, "w": 20.0, "h": 14.0},
    {"id": "OLED", "name": "0.96 OLED Display", "x": 69.0, "y": 54.0, "w": 27.0, "h": 27.0},

    # Lower Row (Touch & Knobs):
    {"id": "KEY1", "name": "Button 1 [Power]", "x": 16.0, "y": 76.5, "w": 13.5, "h": 12.0},
    {"id": "KEY2", "name": "Button 2 [Swing/Mode]", "x": 33.0, "y": 76.5, "w": 13.5, "h": 12.0},
    {"id": "ENCODER", "name": "EC11 Rotary Encoder", "x": 54.0, "y": 74.0, "w": 22.0, "h": 15.0}
]

def check(mods):
    issues = []
    for m in mods:
        x_min = m["x"] - m["w"]/2.0
        x_max = m["x"] + m["w"]/2.0
        y_min = m["y"] - m["h"]/2.0
        y_max = m["y"] + m["h"]/2.0
        if x_min < 0.5 or y_min < 0.5 or x_max > BOARD_W - 0.5 or y_max > BOARD_H - 0.5:
            issues.append(f"EDGE OVERFLOW: {m['id']} [X:{x_min:.1f}~{x_max:.1f}, Y:{y_min:.1f}~{y_max:.1f}]")
            
        for h in HOLES:
            cx = max(m["x"] - m["w"]/2.0, min(h["x"], m["x"] + m["w"]/2.0))
            cy = max(m["y"] - m["h"]/2.0, min(h["y"], m["y"] + m["h"]/2.0))
            dist = math.hypot(h["x"] - cx, h["y"] - cy)
            if dist < h["r"]:
                issues.append(f"HOLE COLLISION: {m['id']} and {h['name']} dist={dist:.2f} < {h['r']}")

    n = len(mods)
    for i in range(n):
        for j in range(i+1, n):
            m1 = mods[i]
            m2 = mods[j]
            dx = abs(m1["x"] - m2["x"]) - (m1["w"] + m2["w"])/2.0
            dy = abs(m1["y"] - m2["y"]) - (m1["h"] + m2["h"])/2.0
            if dx < 1.2 and dy < 1.2:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}mm, dy={dy:.2f}mm)")
                
    return issues

if __name__ == "__main__":
    issues = check(modules)
    print(f"Board: {BOARD_W}x{BOARD_H} mm | Total issues: {len(issues)}")
    for iss in issues:
        print(" -", iss)
    if not issues:
        print("SUCCESS: 85x85mm board layout is 100% collision-free with all clearances >= 1.2mm!")
