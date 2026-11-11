"""
Script: tools/test_perfect_placement.py
Solves layout with real module dimensions and verified clearances.
"""
import math

def test_config(BOARD_W, BOARD_H, hole_inset=5.0):
    HOLES = [
        {"name": "H1", "x": hole_inset, "y": hole_inset, "r": 4.5},
        {"name": "H2", "x": BOARD_W - hole_inset, "y": hole_inset, "r": 4.5},
        {"name": "H3", "x": hole_inset, "y": BOARD_H - hole_inset, "r": 4.5},
        {"name": "H4", "x": BOARD_W - hole_inset, "y": BOARD_H - hole_inset, "r": 4.5},
    ]

    # Real Physical Envelopes
    # Note: On front buttons (13.5 x 19.6mm) and encoder (26 x 19mm):
    # The pin headers plug in at one edge, and the body extends towards the front!
    # If the front edge of the module reaches the board edge (Y = BOARD_H - 1.0mm),
    # then the center of the module is at Y = BOARD_H - 1.0 - H/2.
    
    # Let's test a 95x95 board:
    # STM32: 22.86w x 53.34h. If centered at X = 47.5, Y = 38.0 -> Y in [11.3, 64.7]
    # To the left of STM32: X in [0, 36.0]
    # - TB6612 (21.5w x 19.0h) at X=16.0, Y=26.0 -> Y in [16.5, 35.5]
    # - DHT11 (15.5w x 12.0h) at X=16.0, Y=44.0 -> Y in [38.0, 50.0]
    # To the right of STM32: X in [59.0, 95.0]
    # - ASR-PRO (30.0w x 28.0h) at X=78.0, Y=25.0 -> Y in [11.0, 39.0]
    
    # Front Components:
    # - OLED (27.0w x 27.5h): at X=78.0, Y=56.0 -> Y in [42.25, 69.75]
    #   ASR-PRO ends at Y=39.0. OLED starts at Y=42.25. Gap = 3.25mm!
    # - PAJ7620 (20.0w x 15.0h): at X=18.0, Y=60.0 -> Y in [52.5, 67.5]
    #   DHT11 ends at Y=50.0. PAJ starts at Y=52.5. Gap = 2.5mm!
    
    # Bottom Row: Y from 70 to 95 (25mm height!)
    # - KEY1 (13.5w x 19.6h): at X=18.0, Y=82.0 -> Y in [72.2, 91.8]
    #   PAJ ends at Y=67.5. KEY1 starts at Y=72.2. Gap = 4.7mm!
    # - KEY2 (13.5w x 19.6h): at X=36.0, Y=82.0 -> Y in [72.2, 91.8]
    #   KEY1 <-> KEY2 horizontal gap: (36 - 18) - 13.5 = 4.5mm!
    # - EC11 Encoder (26.0w x 19.0h): at X=59.0, Y=82.0 -> Y in [72.5, 91.5]
    #   KEY2 <-> EC11 horizontal gap: (59 - 36) - (13.5+26)/2 = 23 - 19.75 = 3.25mm!
    #   EC11 <-> OLED: EC11 ends at X=72.0. OLED is at X in [64.5, 91.5]...
    #   Wait, does EC11 overlap with OLED horizontally?
    #   EC11 is at X=59 (X in [46.0, 72.0]). OLED is at X=78 (X in [64.5, 91.5]).
    #   They overlap horizontally from 64.5 to 72.0 (dx = -7.5mm)!
    #   BUT IN Y:
    #   OLED ends at Y = 56.0 + 13.75 = 69.75mm!
    #   EC11 starts at Y = 82.0 - 9.5 = 72.5mm!
    #   Vertical gap between OLED bottom and EC11 top: 72.5 - 69.75 = 2.75mm >= 2.0mm!
    #   So they are completely separated by 2.75mm vertically! Zero collision!
    
    modules = [
        # Top Power Group (Y: 5 ~ 14)
        {"id": "DC1", "name": "DC-005", "x": 16.0, "y": 8.0, "w": 9.0, "h": 14.0},
        {"id": "D2", "name": "SS24", "x": 25.0, "y": 7.5, "w": 4.5, "h": 2.5},
        {"id": "C1", "name": "100uF", "x": 31.0, "y": 7.5, "w": 5.0, "h": 5.0},
        {"id": "U2", "name": "XL1509", "x": 38.0, "y": 7.5, "w": 5.0, "h": 4.0},
        {"id": "D1", "name": "SS24_SW", "x": 45.0, "y": 7.5, "w": 4.5, "h": 2.5},
        {"id": "L1", "name": "47uH", "x": 52.0, "y": 7.5, "w": 5.8, "h": 5.2},
        {"id": "C3", "name": "220uF", "x": 60.0, "y": 7.5, "w": 6.3, "h": 6.3},
        {"id": "U3", "name": "AMS1117", "x": 68.0, "y": 7.5, "w": 6.5, "h": 3.5},
        {"id": "C5", "name": "10uF", "x": 75.0, "y": 7.5, "w": 2.5, "h": 3.5},

        # Actuators & Buzzer
        {"id": "MOTO1", "name": "130 Motor", "x": 10.0, "y": 18.0, "w": 5.0, "h": 5.0},
        {"id": "SERVO1", "name": "MG90S Servo", "x": 18.0, "y": 18.0, "w": 7.6, "h": 4.0},
        {"id": "BZ1_GRP", "name": "Buzzer", "x": 28.0, "y": 18.0, "w": 8.0, "h": 8.0},

        # Middle Left: TB6612 & DHT11
        {"id": "TB6612", "name": "TB6612", "x": 16.0, "y": 30.0, "w": 21.5, "h": 19.0},
        {"id": "DHT11", "name": "DHT11", "x": 16.0, "y": 47.0, "w": 15.5, "h": 12.0},

        # Center: STM32 Blue Pill
        {"id": "STM32", "name": "STM32 Blue Pill", "x": 47.5, "y": 38.0, "w": 22.86, "h": 53.34},

        # Right: ASR-PRO Voice Board
        {"id": "ASR_PRO", "name": "ASR-PRO", "x": 78.0, "y": 24.5, "w": 30.0, "h": 28.0},

        # Front Upper: PAJ7620 & OLED
        {"id": "GESTURE", "name": "PAJ7620", "x": 18.0, "y": 62.0, "w": 20.0, "h": 15.0},
        {"id": "OLED", "name": "0.96 OLED", "x": 78.0, "y": 55.0, "w": 27.0, "h": 27.5},

        # Front Lower: Buttons & Encoder (with REAL 19.6mm depth!)
        {"id": "KEY1", "name": "KEY1 Power", "x": 18.0, "y": 82.0, "w": 13.5, "h": 19.6},
        {"id": "KEY2", "name": "KEY2 Swing", "x": 36.0, "y": 82.0, "w": 13.5, "h": 19.6},
        {"id": "ENCODER", "name": "EC11 Encoder", "x": 59.0, "y": 82.0, "w": 26.0, "h": 19.0}
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
            if dist < h["r"] + 0.5:
                issues.append(f"HOLE COLLISION: {m['id']} and {h['name']} dist={dist:.2f} < {h['r']+0.5:.2f}")

    n = len(modules)
    for i in range(n):
        for j in range(i+1, n):
            m1 = modules[i]
            m2 = modules[j]
            dx = abs(m1["x"] - m2["x"]) - (m1["w"] + m2["w"])/2.0
            dy = abs(m1["y"] - m2["y"]) - (m1["h"] + m2["h"])/2.0
            # If both dx < 1.5 and dy < 1.5, they collide!
            if dx < 1.5 and dy < 1.5:
                issues.append(f"COLLISION: {m1['id']} and {m2['id']} (dx={dx:.2f}mm, dy={dy:.2f}mm)")
                
    return issues, modules

if __name__ == "__main__":
    for size in [92.0, 94.0, 95.0, 96.0]:
        iss, mods = test_config(size, size, hole_inset=5.0)
        print(f"Board size {size}x{size} mm: {len(iss)} issues")
        for s in iss:
            print("  -", s)
