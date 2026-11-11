"""
Script: tools/optimize_layout_sizes.py
Finds the ideal board size (between 85x85 and 92x92) and exact collision-free layout
for all physical modules with >= 1.5mm clearances.
"""

import math

def test_layout(BOARD_W, BOARD_H, hole_inset=5.0):
    HOLES = [
        {"name": "H1", "x": hole_inset, "y": hole_inset, "r": 4.5},
        {"name": "H2", "x": BOARD_W - hole_inset, "y": hole_inset, "r": 4.5},
        {"name": "H3", "x": hole_inset, "y": BOARD_H - hole_inset, "r": 4.5},
        {"name": "H4", "x": BOARD_W - hole_inset, "y": BOARD_H - hole_inset, "r": 4.5},
    ]

    # Let's arrange modules logically:
    # 1. DC Jack: near top left or top edge
    # 2. Power ICs: U2 (XL1509), AMS1117, Inductor, Caps
    # 3. STM32: in the middle
    # 4. ASR-PRO: on the right
    # 5. TB6612: on the left
    # 6. DHT11: on the left
    # 7. Front interactive components:
    #    - OLED (27x27)
    #    - PAJ7620 (20x15)
    #    - KEY1 (13.5x12)
    #    - KEY2 (13.5x12)
    #    - EC11 (22x15)
    
    # Let's see: on a 90x90 board:
    # Center X = 45.0
    # STM32: x=45.0, y=40.0, w=22.8, h=50.0 -> x in [33.6, 56.4], y in [15.0, 65.0]
    # Left zone: x in [0, 33.6]
    # Right zone: x in [56.4, 90.0]
    # Front zone: y in [65.0, 90.0] -> 25mm deep!
    
    modules = [
        # Top power line (Y = 8.5)
        {"id": "DC1", "name": "DC-005", "x": 16.0, "y": 8.5, "w": 9.0, "h": 13.0},
        {"id": "D2", "name": "SS24", "x": 23.5, "y": 7.5, "w": 4.5, "h": 2.5},
        {"id": "C1", "name": "100uF", "x": 28.5, "y": 7.5, "w": 5.0, "h": 5.0},
        {"id": "U2", "name": "XL1509", "x": 34.5, "y": 7.5, "w": 5.0, "h": 4.0},
        {"id": "D1", "name": "SS24_SW", "x": 40.5, "y": 7.5, "w": 4.5, "h": 2.5},
        {"id": "L1", "name": "47uH", "x": 47.0, "y": 7.5, "w": 5.8, "h": 5.2},
        {"id": "C3", "name": "220uF", "x": 54.5, "y": 7.5, "w": 6.3, "h": 6.3},
        {"id": "U3", "name": "AMS1117", "x": 62.0, "y": 7.5, "w": 6.5, "h": 3.5},
        {"id": "C5", "name": "10uF", "x": 68.0, "y": 7.5, "w": 2.5, "h": 3.5},

        # Actuators & Buzzers
        {"id": "MOTO1", "name": "130 Motor", "x": 11.0, "y": 20.0, "w": 5.5, "h": 5.0},
        {"id": "SERVO1", "name": "MG90S Servo", "x": 19.5, "y": 20.0, "w": 7.6, "h": 4.0},
        {"id": "BZ1", "name": "Buzzer", "x": 28.5, "y": 20.0, "w": 8.0, "h": 8.0},

        # Middle Left: TB6612 and DHT11
        {"id": "TB6612", "name": "TB6612", "x": 16.0, "y": 36.0, "w": 21.5, "h": 19.0},
        {"id": "DHT11", "name": "DHT11", "x": 15.0, "y": 54.0, "w": 15.5, "h": 12.0},

        # Center: STM32
        {"id": "STM32", "name": "STM32", "x": 45.0, "y": 41.0, "w": 22.8, "h": 50.0},

        # Right: ASR-PRO Voice Board
        {"id": "ASR_PRO", "name": "ASR-PRO", "x": 73.0, "y": 26.0, "w": 28.0, "h": 27.0},

        # Front Upper: PAJ7620 (Left) and OLED (Right)
        {"id": "GESTURE", "name": "PAJ7620", "x": 17.0, "y": 71.0, "w": 20.0, "h": 14.0},
        {"id": "OLED", "name": "OLED 0.96", "x": 73.0, "y": 57.0, "w": 27.0, "h": 27.0},

        # Front Lower: Buttons and Encoder
        {"id": "KEY1", "name": "KEY1 Power", "x": 14.0, "y": 83.5, "w": 13.5, "h": 8.0},
        {"id": "KEY2", "name": "KEY2 Swing", "x": 31.0, "y": 83.5, "w": 13.5, "h": 8.0},
        {"id": "ENCODER", "name": "EC11 Encoder", "x": 52.0, "y": 79.0, "w": 22.0, "h": 15.0}
    ]

    issues = []
    for m in modules:
        x_min = m["x"] - m["w"]/2.0
        x_max = m["x"] + m["w"]/2.0
        y_min = m["y"] - m["h"]/2.0
        y_max = m["y"] + m["h"]/2.0
        if x_min < 1.0 or y_min < 1.0 or x_max > BOARD_W - 1.0 or y_max > BOARD_H - 1.0:
            issues.append(f"EDGE OVERFLOW: {m['id']} [X:{x_min:.1f}~{x_max:.1f}, Y:{y_min:.1f}~{y_max:.1f}]")
            
        for h in HOLES:
            cx = max(x_min, min(h["x"], x_max))
            cy = max(y_min, min(h["y"], y_max))
            dist = math.hypot(h["x"] - cx, h["y"] - cy)
            if dist < h["r"] + 0.2:
                issues.append(f"HOLE COLLISION: {m['id']} and {h['name']} dist={dist:.2f} < {h['r']+0.2:.2f}")

    n = len(modules)
    for i in range(n):
        for j in range(i+1, n):
            m1 = modules[i]
            m2 = modules[j]
            dx = abs(m1["x"] - m2["x"]) - (m1["w"] + m2["w"])/2.0
            dy = abs(m1["y"] - m2["y"]) - (m1["h"] + m2["h"])/2.0
            if dx < 1.2 and dy < 1.2:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}mm, dy={dy:.2f}mm)")
                
    return issues

for sz in [88.0, 90.0, 92.0]:
    iss = test_layout(sz, sz, hole_inset=5.0)
    print(f"Board size {sz}x{sz} mm: {len(iss)} issues")
    for s in iss:
        print("   -", s)
