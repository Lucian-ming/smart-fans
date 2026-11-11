"""
Script: tools/generate_fan_ctrl_revB_v2.py
Complete generation of:
1. KiCad Schematic: hardware/kicad/fan_ctrl_revB.kicad_sch
2. KiCad PCB: hardware/kicad/fan_ctrl_revB.kicad_pcb (90x90 mm, R3 corners, 0 pad overlap, 0 collisions)
3. Genuine RS-274X Gerber & Excellon Drill files in hardware/fabrication/gerber_revB/
4. Production ZIP archive: D:/下载/Gerber_fan_ctrl_revB_2026-11-04.zip
5. BOM: D:/下载/BOM_SmartFan_RevB.xlsx & docs/hardware/bom.md
6. High-Resolution Visual Layout: D:/下载/fan_ctrl_revB_layout.png
"""

import os
import sys
import math
import zipfile
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import matplotlib.pyplot as plt
import matplotlib.patches as patches

sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

ROOT_DIR = r"D:\smart_fans"
KICAD_DIR = os.path.join(ROOT_DIR, "hardware", "kicad")
FAB_DIR = os.path.join(ROOT_DIR, "hardware", "fabrication", "gerber_revB")
DOWNLOAD_DIR = r"D:\下载"
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "hardware")

os.makedirs(KICAD_DIR, exist_ok=True)
os.makedirs(FAB_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

BOARD_W = 90.0
BOARD_H = 90.0
CORNER_R = 3.0
OFFSET_X = 100.0
OFFSET_Y = 100.0

print(f"Initializing fan_ctrl_revB generation: Board {BOARD_W}x{BOARD_H} mm...")
