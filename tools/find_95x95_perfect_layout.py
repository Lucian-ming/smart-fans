"""
Script: tools/find_95x95_perfect_layout.py
Solves 100% collision-free placement on 95x95 mm board with clearances >= 2.0mm.
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

# Physical Modules on 95x95 board
# All dimensions: (cx, cy, w, h)
modules = [
    # Top Power Section (Y: 5 ~ 12 mm)
    {"id": "DC1", "name": "DC-005", "x": 15.0, "y": 8.0, "w": 9.0, "h": 14.0},
    {"id": "D2", "name": "SS24", "x": 23.5, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "C1", "name": "100uF", "x": 29.5, "y": 7.0, "w": 5.0, "h": 5.0},
    {"id": "U2", "name": "XL1509", "x": 36.0, "y": 7.0, "w": 5.0, "h": 4.0},
    {"id": "D1", "name": "SS24_SW", "x": 42.5, "y": 7.0, "w": 4.5, "h": 2.5},
    {"id": "L1", "name": "47uH", "x": 49.0, "y": 7.0, "w": 5.8, "h": 5.2},
    {"id": "C3", "name": "220uF", "x": 56.5, "y": 7.0, "w": 6.3, "h": 6.3},
    {"id": "U3", "name": "AMS1117", "x": 64.0, "y": 7.0, "w": 6.5, "h": 3.5},
    {"id": "C5", "name": "10uF", "x": 70.0, "y": 7.0, "w": 2.5, "h": 3.5},

    # Row 2: Actuators (Y: 17 ~ 22 mm)
    {"id": "MOTO1", "name": "130 Motor", "x": 10.0, "y": 19.5, "w": 5.0, "h": 5.0},
    {"id": "SERVO1", "name": "MG90S Servo", "x": 18.0, "y": 19.5, "w": 7.6, "h": 4.0},
    {"id": "BZ1_GRP", "name": "Buzzer", "x": 27.5, "y": 19.5, "w": 8.0, "h": 8.0},

    # Middle Left: TB6612 & DHT11
    # TB6612: 21.5w x 19.0h -> Y: 26.5 ~ 45.5
    {"id": "TB6612", "name": "TB6612", "x": 15.5, "y": 36.0, "w": 21.5, "h": 19.0},
    # DHT11: 15.5w x 12.0h -> Y: 49.0 ~ 61.0
    {"id": "DHT11", "name": "DHT11", "x": 15.5, "y": 55.0, "w": 15.5, "h": 12.0},

    # Center: STM32 Blue Pill (22.86w x 53.34h)
    # Centered at X=47.5, Y=40.0 -> X: 36.07 ~ 58.93, Y: 13.33 ~ 66.67
    {"id": "STM32", "name": "STM32 Blue Pill", "x": 47.5, "y": 40.0, "w": 22.86, "h": 53.34},

    # Middle Right: ASR-PRO Voice Board (30.0w x 28.0h)
    # Centered at X=79.0, Y=25.0 -> X: 64.0 ~ 94.0, Y: 11.0 ~ 39.0
    {"id": "ASR_PRO", "name": "ASR-PRO", "x": 78.5, "y": 25.0, "w": 30.0, "h": 28.0},

    # Front Upper: PAJ7620 & OLED Display
    # PAJ7620 (20.0w x 15.0h) at X=18.0, Y=70.0 -> X: 8.0 ~ 28.0, Y: 62.5 ~ 77.5
    {"id": "GESTURE", "name": "PAJ7620", "x": 18.0, "y": 70.0, "w": 20.0, "h": 15.0},
    # 0.96 OLED (27.0w x 27.5h) at X=79.0, Y=56.0 -> X: 65.5 ~ 92.5, Y: 42.25 ~ 69.75
    {"id": "OLED", "name": "0.96 OLED", "x": 78.5, "y": 56.0, "w": 27.0, "h": 27.5},

    # Front Lower: Buttons & Rotary Encoder (with real 19.6mm depth!)
    # KEY1 (13.5w x 19.6h) at X=18.0, Y=83.5 -> X: 11.25 ~ 24.75, Y: 73.7 ~ 93.3 (front edge at 93.3, leaves 1.7mm to board edge)
    # Gap from GESTURE (ends at 77.5): Wait! 83.5 - 9.8 = 73.7, GESTURE ends at 77.5! They overlap!
    # Where should KEY1 and GESTURE be?
    # GESTURE is at X=18. If KEY1 is also at X=18, they are in the same vertical column!
    # Why put KEY1 and GESTURE in the same column?!
    # Look at the board width: X from 0 to 95 mm!
    # On the front panel:
    # We have:
    # 1. PAJ7620 (20w x 15h)
    # 2. KEY1 (13.5w x 19.6h)
    # 3. KEY2 (13.5w x 19.6h)
    # 4. EC11 Encoder (26w x 19h)
    # 5. 0.96 OLED (27w x 27.5h)
]

print("Testing column arrangements...")
