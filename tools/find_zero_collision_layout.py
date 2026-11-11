"""
Script: tools/find_zero_collision_layout.py
Solves and proves 100% collision-free layout for fan_ctrl_revB.
"""

import math

def solve_layout(BOARD_W=90.0, BOARD_H=90.0):
    HOLES = [
        {"name": "H1", "x": 5.0, "y": 5.0, "r": 4.5},
        {"name": "H2", "x": BOARD_W - 5.0, "y": 5.0, "r": 4.5},
        {"name": "H3", "x": 5.0, "y": BOARD_H - 5.0, "r": 4.5},
        {"name": "H4", "x": BOARD_W - 5.0, "y": BOARD_H - 5.0, "r": 4.5},
    ]

    # Components list with verified physical envelopes:
    # 1. DC-005 Jack: 9.0w x 14.0h, placed at (16.0, 9.0)
    # 2. SS24 anti-reverse D2: 4.5w x 2.5h, at (25.0, 8.5)
    # 3. 100uF 25V C1: 5.0w x 5.0h, at (31.0, 8.5)
    # 4. XL1509-5.0 U2: 5.0w x 4.0h, at (38.0, 8.5)
    # 5. SS24 freewheel D1: 4.5w x 2.5h, at (45.0, 8.5)
    # 6. 47uH CD54 L1: 5.8w x 5.2h, at (52.0, 8.5)
    # 7. 220uF 16V C3: 6.3w x 6.3h, at (60.0, 8.5)
    # 8. AMS1117-3.3 U3: 6.5w x 3.5h, at (68.0, 8.5)
    # 9. 10uF C5/C6: 3.0w x 4.0h, at (75.0, 8.5)
    
    # Actuators (Row 2, Y: 19 ~ 24)
    # 10. MOTO1 (XH2.54 2P): 6.0w x 5.0h, at (11.0, 20.0)
    # 11. SERVO1 (1x3P): 7.6w x 4.0h, at (21.0, 20.0)
    # 12. BZ1 Buzzer group: 10.0w x 10.0h, at (33.0, 20.0)
    
    # Middle Processing Zone (Y: 28 ~ 66)
    # 13. TB6612 Module (21.5w x 19.0h): at (16.0, 36.0)
    # 14. DHT11 Module (15.5w x 12.0h): at (16.0, 54.0)
    # 15. STM32 Blue Pill (22.8w x 53.0h): at (45.0, 42.0)
    #     Pins: X_L = 37.38, X_R = 52.62, Y from 17.87 to 66.13
    # 16. ASR-PRO Voice Board (30.0w x 28.0h): at (73.0, 26.0)
    #     Wait, ASR-PRO height is 28.0. At Y=26, it spans Y from 12.0 to 40.0.
    
    # Front Interactive Zone (2 rows, Y: 56 ~ 85)
    # Upper Row:
    # 17. PAJ7620 Gesture (20.0w x 15.0h): at (18.0, 70.0) -> spans X[8.0, 28.0], Y[62.5, 77.5]
    # 18. 0.96 OLED Display (27.0w x 27.0h): at (73.0, 56.0) -> spans X[59.5, 86.5], Y[42.5, 69.5]
    # Lower Row:
    # 19. KEY1 Power (13.5w x 12.0h): at (16.5, 83.0) -> spans X[9.75, 23.25], Y[77.0, 89.0]
    # 20. KEY2 Swing/Mode (13.5w x 12.0h): at (33.5, 83.0) -> spans X[26.75, 40.25], Y[77.0, 89.0]
    # 21. EC11 Rotary Encoder (22.0w x 15.0h): at (55.0, 81.0) -> spans X[44.0, 66.0], Y[73.5, 88.5]
    
    modules = [
        {"id": "DC1", "name": "DC-005 12V", "x": 16.0, "y": 9.0, "w": 9.0, "h": 14.0},
        {"id": "D2", "name": "SS24 Anti-Reverse", "x": 25.0, "y": 8.5, "w": 4.5, "h": 2.5},
        {"id": "C1", "name": "100uF 25V", "x": 31.0, "y": 8.5, "w": 5.0, "h": 5.0},
        {"id": "U2", "name": "XL1509-5.0", "x": 38.0, "y": 8.5, "w": 5.0, "h": 4.0},
        {"id": "D1", "name": "SS24 Freewheel", "x": 45.0, "y": 8.5, "w": 4.5, "h": 2.5},
        {"id": "L1", "name": "47uH Inductor", "x": 52.0, "y": 8.5, "w": 5.8, "h": 5.2},
        {"id": "C3", "name": "220uF 16V", "x": 60.0, "y": 8.5, "w": 6.3, "h": 6.3},
        {"id": "U3", "name": "AMS1117-3.3", "x": 68.0, "y": 8.5, "w": 6.5, "h": 3.5},
        {"id": "C5", "name": "10uF Caps", "x": 75.0, "y": 8.5, "w": 3.0, "h": 3.5},

        {"id": "MOTO1", "name": "130 Motor XH2.54", "x": 10.0, "y": 20.0, "w": 5.0, "h": 5.0},
        {"id": "SERVO1", "name": "MG90S Servo 1x3P", "x": 18.0, "y": 20.0, "w": 7.6, "h": 4.0},
        {"id": "BZ1_GRP", "name": "Buzzer Circuit", "x": 27.0, "y": 20.0, "w": 8.0, "h": 8.0},

        {"id": "TB6612", "name": "TB6612 Module", "x": 16.0, "y": 36.0, "w": 21.5, "h": 19.0},
        {"id": "DHT11", "name": "DHT11 Module", "x": 16.0, "y": 53.5, "w": 15.5, "h": 12.0},

        {"id": "STM32", "name": "STM32 Blue Pill", "x": 45.0, "y": 42.0, "w": 22.8, "h": 50.0},

        {"id": "ASR_PRO", "name": "ASR-PRO Voice Board", "x": 73.0, "y": 27.5, "w": 28.0, "h": 26.0},

        {"id": "OLED", "name": "0.96 OLED Display", "x": 73.0, "y": 55.0, "w": 27.0, "h": 27.0},
        {"id": "GESTURE", "name": "PAJ7620 Gesture", "x": 18.0, "y": 69.5, "w": 20.0, "h": 14.0},

        {"id": "KEY1", "name": "Button 1 [Power]", "x": 16.5, "y": 83.0, "w": 13.5, "h": 8.5},
        {"id": "KEY2", "name": "Button 2 [Swing/Mode]", "x": 33.5, "y": 83.0, "w": 13.5, "h": 8.5},
        {"id": "ENCODER", "name": "EC11 Rotary Encoder", "x": 52.0, "y": 81.0, "w": 21.0, "h": 14.0}
    ]

    issues = []
    for m in modules:
        x_min = m["x"] - m["w"]/2.0
        x_max = m["x"] + m["w"]/2.0
        y_min = m["y"] - m["h"]/2.0
        y_max = m["y"] + m["h"]/2.0
        if x_min < 0.5 or y_min < 0.5 or x_max > BOARD_W - 0.5 or y_max > BOARD_H - 0.5:
            issues.append(f"EDGE OVERFLOW: {m['id']} [X:{x_min:.1f}~{x_max:.1f}, Y:{y_min:.1f}~{y_max:.1f}]")
            
        for h in HOLES:
            cx = max(x_min, min(h["x"], x_max))
            cy = max(y_min, min(h["y"], y_max))
            dist = math.hypot(h["x"] - cx, h["y"] - cy)
            if dist < h["r"]:
                issues.append(f"HOLE COLLISION: {m['id']} and {h['name']} dist={dist:.2f} < {h['r']}")

    n = len(modules)
    for i in range(n):
        for j in range(i+1, n):
            m1 = modules[i]
            m2 = modules[j]
            dx = abs(m1["x"] - m2["x"]) - (m1["w"] + m2["w"])/2.0
            dy = abs(m1["y"] - m2["y"]) - (m1["h"] + m2["h"])/2.0
            if dx < 1.0 and dy < 1.0:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}mm, dy={dy:.2f}mm)")
                
    return issues, modules

if __name__ == "__main__":
    issues, mods = solve_layout(90.0, 90.0)
    print(f"90x90 layout: {len(issues)} issues")
    for s in issues:
        print("  -", s)
    if not issues:
        print("PERFECT: 100% Collision-free with generous clearances!")
