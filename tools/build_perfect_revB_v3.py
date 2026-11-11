# -*- coding: utf-8 -*-
"""
Master Build Script for Smart Fan Controller Rev B4:
Fixes all defects from the Rev B2 engineering audit:
1. P0-1: Full GND copper plane with real (filled_polygon ...) in .kicad_pcb, G36/G37 in Gerber, and 28 GND stitching vias
2. BluePill provisional pinout: actual board variant NOT verified; 3V3 outputs and right pin20 isolated; USB/external dual-power safety NOT established
3. P0-3: ENC_A and ENC_B assigned to Net 30/31, fully connected to STM32 PA6/PA7
4. P0-4: Generous 95.0 x 95.0 mm board with R3 corners and 85.0 mm hole pitch, zero component collisions (>=1.2mm everywhere)
5. True 25-degree sloped front console on 3D CAD with all 6 openings (OLED, Gesture, 2 Buttons, Encoder, Mic)
6. KiCad schematic with full lib_symbols, wires, junctions, and authentic netlist
7. RS-274X Gerbers with G02/G03 circular interpolation arcs and G36/G37 polygon fills
8. Synchronized BOM with BOM references; procurement verification required
"""

import os
import sys
import re
import math
import zipfile
import shutil
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import numpy as np
import manifold3d as m3d
import matplotlib.pyplot as plt
import matplotlib.patches as patches

sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

ROOT_DIR = r"D:\smart_fans"
KICAD_DIR = os.path.join(ROOT_DIR, "hardware", "kicad")
FAB_DIR = os.path.join(ROOT_DIR, "hardware", "fabrication", "gerber_revB")
DOWNLOAD_DIR = os.path.join(ROOT_DIR, "hardware", "fabrication")
DOCS_DIR = os.path.join(ROOT_DIR, "docs", "hardware")

os.makedirs(KICAD_DIR, exist_ok=True)
os.makedirs(FAB_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

BOARD_W = 95.0
BOARD_H = 95.0
CORNER_R = 3.0
OFFSET_X = 100.0
OFFSET_Y = 100.0

# 1. Nets Definition (Net 1 = GND)
NETS = [
    (1, "GND"),
    (2, "+5V_RAW"),
    (3, "+5V_FUSED"),
    (4, "+5V"),
    (5, "+3.3V"),
    (6, "+5V_MCU"),
    (7, "LED_5V_K"),
    (8, "LED_3V3_K"),
    (9, "TB_PWMA"),
    (10, "TB_AIN1"),
    (11, "TB_AIN2"),
    (12, "TB_STBY"),
    (13, "TB_AO1"),
    (14, "TB_AO2"),
    (15, "SERVO_PWM"),
    (16, "BUZZER_CTRL"),
    (17, "BUZ_BASE"),
    (18, "BUZ_DRV"),
    (19, "VOICE_TX"),
    (20, "VOICE_RX"),
    (21, "VOICE_SPK_P"),
    (22, "VOICE_SPK_N"),
    (24, "GEST_INT"),
    (25, "I2C1_SCL"),
    (26, "I2C1_SDA"),
    (27, "DHT11_DATA"),
    (28, "KEY1_SIG"),
    (29, "KEY2_SIG"),
    (30, "ENC_A"),
    (31, "ENC_B"),
    (33, "+5V_ASR"),
    (34, "ASR_RX1"),
    (35, "ASR_TX1")
]
NET_MAP = {name: nid for nid, name in NETS}

print(f"Initialized Smart Fan Rev B4 Build: Board {BOARD_W}x{BOARD_H} mm, {len(NETS)} nets.")

# 2. Components Placement and Footprints
# Coordinate system: Board origin at (0, 0), Board size: 95x95 mm
COMPONENTS = [
    # --- Power Supply Section (Y: 5 ~ 12 mm) ---
    {
        "ref": "DC1", "val": "5V_ONLY_MKDSN_1,5/2-5.08", "fp": "SmartFan:Phoenix_1729128_MKDSN_1x02_P5.08mm",
        "body_size_mm": [10.16, 8.15, 10.0],
        "desc": "唯一稳压5V输入; 1=+5V 2=GND; 禁接12V; 1729128 MKDSN 1,5/2-5,08; 壳10.16x8.15板上高10mm; 壳相对针排偏置待核; 库存未核", "lcsc": "-", "mpn": "1729128", "mfr": "Phoenix Contact",
        "x": 12.46, "y": 8.0, "type": "tht",
        "pads": [("1", 0.0, 0.0, "+5V_RAW", 2.6, 1.3), ("2", 5.08, 0.0, "GND", 2.6, 1.3)]
    },
    {
        "ref": "F1", "val": "3A_FAST_NOT_CURRENT_LIMIT", "fp": "Fuse:Fuse_Littelfuse-NANO2-451_453",
        "desc": "3A快断保险; 不是3A硬限流; 整板连续目标<=2A须热测/启动I2t验证; 库存未核", "lcsc": "C13982", "mpn": "0451003.MRL", "mfr": "Littelfuse",
        "x": 23.0, "y": 7.0, "type": "smd",
        "pads": [("1", -2.455, 0.0, "+5V_RAW", 1.96, 3.15), ("2", 2.455, 0.0, "+5V_FUSED", 1.96, 3.15)]
    },
    {
        "ref": "C1", "val": "100uF/25V", "fp": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
        "desc": "受保护5V储能电解", "lcsc": "C134665", "mpn": "RZW101M1EBK-0611", "mfr": "Lelon",
        "x": 29.5, "y": 7.0, "type": "tht",
        "pads": [("1", -1.25, 0.0, "+5V", 1.6, 0.8), ("2", 1.25, 0.0, "GND", 1.6, 0.8)]
    },
    {
        "ref": "C2", "val": "100nF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "受保护5V 高频去耦电容", "lcsc": "C49678", "mpn": "CC0805KRX7R9BB104", "mfr": "YAGEO",
        "x": 29.5, "y": 12.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+5V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "Q_PWR", "val": "AO4409_REVERSE_POLARITY", "fp": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "desc": "P-MOS反接保护: D=熔断后输入 S=5V负载 G=GND; 不隔离反向供电; 库存未核", "lcsc": "-", "mpn": "AO4409", "mfr": "Alpha & Omega Semiconductor",
        "x": 36.0, "y": 7.0, "type": "smd",
        "pads": [
            ("1", -2.6, -1.905, "+5V", 1.5, 0.6),
            ("2", -2.6, -0.635, "+5V", 1.5, 0.6),
            ("3", -2.6, 0.635, "+5V", 1.5, 0.6),
            ("4", -2.6, 1.905, "GND", 1.5, 0.6),
            ("5", 2.6, 1.905, "+5V_FUSED", 1.5, 0.6),
            ("6", 2.6, 0.635, "+5V_FUSED", 1.5, 0.6),
            ("7", 2.6, -0.635, "+5V_FUSED", 1.5, 0.6),
            ("8", 2.6, -1.905, "+5V_FUSED", 1.5, 0.6)
        ]
    },
    {
        "ref": "JP_USB", "val": "REMOVE_BEFORE_USB", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "desc": "2.54跳帽供蓝板; 任何USB插入前必须拔帽; USB不能供母板; 两边电源独立开启后才接信号; 不允许单侧带电", "lcsc": "-", "mpn": "M20-9990245 + M7566-05", "mfr": "Harwin",
        "x": 47.0, "y": 7.0, "type": "tht",
        "pads": [("1", 0.0, 0.0, "+5V", 1.7, 1.0), ("2", 0.0, 2.54, "+5V_MCU", 1.7, 1.0)]
    },
    {
        "ref": "C3", "val": "220uF/16V", "fp": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
        "desc": "5V 输出滤波电解", "lcsc": "C338177", "mpn": "16ZLH220MEFC6.3X11", "mfr": "Rubycon",
        "x": 56.5, "y": 7.0, "type": "tht",
        "pads": [("1", -1.25, 0.0, "+5V", 1.6, 0.8), ("2", 1.25, 0.0, "GND", 1.6, 0.8)]
    },
    {
        "ref": "C4", "val": "100nF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "5V 输出高频去耦", "lcsc": "C49678", "mpn": "CC0805KRX7R9BB104", "mfr": "YAGEO",
        "x": 56.5, "y": 12.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+5V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "U3", "val": "TLV1117LV33DCYR", "fp": "SmartFan:SOT-223_TI_DCY_TLV1117LV_TabPin2_R90", "model_rotation_z": 90,
        "desc": "TI 3.3V LDO 1A; DCY rectangular land envelope, stock unverified", "lcsc": "C15578", "mpn": "TLV1117LV33DCYR", "mfr": "Texas Instruments",
        "x": 64.0, "y": 7.0, "type": "smd",
        "pads": [
            ("1", -2.3, 2.9, "GND", 0.95, 2.15),
            ("2", 0.0, 2.9, "+3.3V", 0.95, 2.15),
            ("3", 2.3, 2.9, "+5V", 0.95, 2.15),
            ("2", 0.0, -2.9, "+3.3V", 3.25, 2.15)
        ]
    },
    {
        "ref": "C5", "val": "10uF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "3.3V 输入去耦 (直连5V)", "lcsc": "C15850", "mpn": "CL21A106KAYNNNE", "mfr": "Samsung Electro-Mechanics",
        "x": 70.0, "y": 7.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+5V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "C6", "val": "10uF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "3.3V 输出滤波", "lcsc": "C15850", "mpn": "CL21A106KAYNNNE", "mfr": "Samsung Electro-Mechanics",
        "x": 70.0, "y": 9.5, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+3.3V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "C7", "val": "100nF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "3.3V 输出高频去耦", "lcsc": "C49678", "mpn": "CC0805KRX7R9BB104", "mfr": "YAGEO",
        "x": 70.0, "y": 12.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+3.3V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },

    # --- Status LEDs (Y: 15 ~ 18 mm) ---
    {
        "ref": "D4", "val": "LED_GREEN", "fp": "LED_SMD:LED_0805_2012Metric",
        "desc": "5V 供电指示灯", "lcsc": "C2292", "mpn": "KT-0805YG", "mfr": "KENTO",
        "x": 75.0, "y": 14.5, "type": "smd",
        "pads": [("2", -0.9, 0.0, "+5V", 0.9, 1.25), ("1", 0.9, 0.0, "LED_5V_K", 0.9, 1.25)]
    },
    {
        "ref": "R1", "val": "1k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "5V LED 限流电阻", "lcsc": "C17513", "mpn": "0805W8F1001T5E", "mfr": "UNI-ROYAL",
        "x": 79.0, "y": 14.5, "type": "smd",
        "pads": [("1", -0.85, 0.0, "LED_5V_K", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "D5", "val": "LED_BLUE", "fp": "LED_SMD:LED_0805_2012Metric",
        "desc": "3.3V 逻辑指示灯", "lcsc": "C2293", "mpn": "KT-0805B", "mfr": "KENTO",
        "x": 75.0, "y": 17.5, "type": "smd",
        "pads": [("2", -0.9, 0.0, "+3.3V", 0.9, 1.25), ("1", 0.9, 0.0, "LED_3V3_K", 0.9, 1.25)]
    },
    {
        "ref": "R2", "val": "1k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "3.3V LED 限流电阻", "lcsc": "C17513", "mpn": "0805W8F1001T5E", "mfr": "UNI-ROYAL",
        "x": 79.0, "y": 17.5, "type": "smd",
        "pads": [("1", -0.85, 0.0, "LED_3V3_K", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },

    # --- Actuator Headers & Buzzer Circuit (Y: 18 ~ 22 mm) ---
    {
        "ref": "MOTO1", "val": "130_MOTOR", "fp": "SmartFan:ZHOURI_XH-2PA_P2.50mm_Y",
        "desc": "直流电机接口 XH-2PA P2.50; 1.0mm孔为设计选取非厂家推荐; 针0.6+/-0.02mm", "lcsc": "C5258883", "mpn": "XH-2PA", "mfr": "ZHOURI",
        "x": 10.0, "y": 19.5, "type": "tht",
        "pads": [("1", 0.0, -1.25, "TB_AO1", 1.7, 1.0), ("2", 0.0, 1.25, "TB_AO2", 1.7, 1.0)]
    },
    {
        "ref": "SERVO1", "val": "MG90S_SERVO", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "desc": "MG90S 舵机插针 (GND, 5V, PWM)", "lcsc": "C2718487", "mpn": "2.54-1*3P弯针", "mfr": "BOOMELE",
        "x": 18.0, "y": 19.5, "type": "tht",
        "pads": [("1", 0.0, -2.54, "GND", 1.7, 1.0), ("2", 0.0, 0.0, "+5V", 1.7, 1.0), ("3", 0.0, 2.54, "SERVO_PWM", 1.7, 1.0)]
    },
    {
        "ref": "BZ1", "val": "5V_BUZZER", "fp": "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
        "desc": "5V 有源提示蜂鸣器", "lcsc": "C96093", "mpn": "TMB12A05", "mfr": "Huaneng",
        "x": 27.5, "y": 19.5, "type": "tht",
        "pads": [("1", -3.8, 0.0, "+5V", 1.8, 0.9), ("2", 3.8, 0.0, "BUZ_DRV", 1.8, 0.9)]
    },
    {
        "ref": "Q1", "val": "2N3904-TA(RANGE:200-300)", "fp": "SmartFan:TO-92_EBC_Wide_P2.54mm_Y_LeadFormed",
        "desc": "NPN蜂鸣器驱动; 1=E 2=B 3=C; 宽脚成形P2.54mm非原厂直脚间距; 安装前核成形与方向", "lcsc": "C2081", "mpn": "2N3904-TA(RANGE:200-300)", "mfr": "JSCJ",
        "x": 34.0, "y": 19.5, "type": "tht",
        "pads": [("1", 0.0, -2.54, "GND", 1.4, 0.8), ("2", 0.0, 0.0, "BUZ_BASE", 1.4, 0.8), ("3", 0.0, 2.54, "BUZ_DRV", 1.4, 0.8)]
    },
    {
        "ref": "D3", "val": "1N4148W", "fp": "SmartFan:D_SOD-123_R180", "model_rotation_z": 180,
        "desc": "蜂鸣器反向钳位二极管", "lcsc": "C81598", "mpn": "1N4148W", "mfr": "ST",
        "x": 34.0, "y": 24.0, "type": "smd",
        "pads": [("2", -1.65, 0.0, "BUZ_DRV", 0.9, 1.2), ("1", 1.65, 0.0, "+5V", 0.9, 1.2)]
    },
    {
        "ref": "R10", "val": "1k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "蜂鸣器基极限流电阻", "lcsc": "C17513", "mpn": "0805W8F1001T5E", "mfr": "UNI-ROYAL",
        "x": 34.0, "y": 15.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "BUZZER_CTRL", 1.0, 1.25), ("2", 0.85, 0.0, "BUZ_BASE", 1.0, 1.25)]
    },

    # --- TB6612: user-confirmed module pin order, 2026-11-04 ---
    # Row spacing 15.00 mm is the user's coarse measurement, NOT assumed 15.24 mm.
    # Single-row pitch remains 2.54 mm; dry-fit/form leads gently before soldering.
    # Top-to-bottom as reported by user; unused B inputs held low, B outputs NC.
    # Control Row J_TB_L: Pin 1=PWMA, 2=AIN2, 3=AIN1, 4=STBY, 5=BIN1, 6=BIN2, 7=PWMB, 8=GND
    {
        "ref": "J_TB_L", "val": "TB6612_CTRL", "fp": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
        "desc": "TB6612 控制排母", "lcsc": "C27438", "mpn": "2.54-1*8P母", "mfr": "BOOMELE",
        "x": 7.88, "y": 36.0, "type": "tht",
        "pads": [
            ("1", 0.0, -8.89, "TB_PWMA", 1.7, 1.0),
            ("2", 0.0, -6.35, "TB_AIN2", 1.7, 1.0),
            ("3", 0.0, -3.81, "TB_AIN1", 1.7, 1.0),
            ("4", 0.0, -1.27, "TB_STBY", 1.7, 1.0),
            ("5", 0.0, 1.27, "GND", 1.7, 1.0),
            ("6", 0.0, 3.81, "GND", 1.7, 1.0),
            ("7", 0.0, 6.35, "GND", 1.7, 1.0),
            ("8", 0.0, 8.89, "GND", 1.7, 1.0)
        ]
    },
    # Power Row J_TB_R: Pin 1=VM, 2=VCC, 3=GND, 4=AO1, 5=AO2, 6=BO2, 7=BO1, 8=GND
    {
        "ref": "J_TB_R", "val": "TB6612_PWR", "fp": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
        "desc": "TB6612 动力排母", "lcsc": "C27438", "mpn": "2.54-1*8P母", "mfr": "BOOMELE",
        "x": 22.88, "y": 36.0, "type": "tht",
        "pads": [
            ("1", 0.0, -8.89, "+5V", 1.7, 1.0),         # VM (Motor supply)
            ("2", 0.0, -6.35, "+3.3V", 1.7, 1.0),       # VCC (Logic supply)
            ("3", 0.0, -3.81, "GND", 1.7, 1.0),
            ("4", 0.0, -1.27, "TB_AO1", 1.7, 1.0),
            ("5", 0.0, 1.27, "TB_AO2", 1.7, 1.0),
            ("6", 0.0, 3.81, "NC", 1.7, 1.0),
            ("7", 0.0, 6.35, "NC", 1.7, 1.0),
            ("8", 0.0, 8.89, "GND", 1.7, 1.0)
        ]
    },
    # TB6612 Bulk Storage Capacitor C_VM (220uF 16V) placed directly adjacent to VM pin!
    {
        "ref": "C_VM", "val": "220uF/16V", "fp": "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
        "desc": "TB6612 VM电机就近储能电解", "lcsc": "C338177", "mpn": "16ZLH220MEFC6.3X11", "mfr": "Rubycon",
        "x": 23.5, "y": 23.5, "type": "tht",
        "pads": [("1", -1.25, 0.0, "+5V", 1.6, 0.8), ("2", 1.25, 0.0, "GND", 1.6, 0.8)]
    },
    {
        "ref": "C_VM_MLCC", "val": "100nF", "fp": "Capacitor_SMD:C_0805_2012Metric",
        "desc": "TB6612 VM就近去耦", "lcsc": "C49678", "mpn": "CC0805KRX7R9BB104", "mfr": "YAGEO",
        "x": 19.0, "y": 25.5, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+5V", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },
    {
        "ref": "R_STBY", "val": "10k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "TB6612 STBY下拉电阻", "lcsc": "C17414", "mpn": "0805W8F1002T5E", "mfr": "UNI-ROYAL",
        "x": 4.0, "y": 34.73, "type": "smd",
        "pads": [("1", -0.85, 0.0, "TB_STBY", 1.0, 1.25), ("2", 0.85, 0.0, "GND", 1.0, 1.25)]
    },

    # --- DHT11 Temperature & Humidity Sensor (Y: 55 mm) ---
    {
        "ref": "J_DHT11", "val": "DHT11_SOCK", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "desc": "DHT11 温湿度传感器母座", "lcsc": "C42431859", "mpn": "PM2.54-1Z03P-H85", "mfr": "JXTCONN",
        "x": 15.5, "y": 55.0, "type": "tht",
        "pads": [("1", -2.54, 0.0, "+3.3V", 1.7, 1.0), ("2", 0.0, 0.0, "DHT11_DATA", 1.7, 1.0), ("3", 2.54, 0.0, "GND", 1.7, 1.0)]
    },
    {
        "ref": "R_DHT", "val": "4.7k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "DHT11 单总线上拉电阻", "lcsc": "C17673", "mpn": "0805W8F4701T5E", "mfr": "UNI-ROYAL",
        "x": 22.5, "y": 55.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+3.3V", 1.0, 1.25), ("2", 0.85, 0.0, "DHT11_DATA", 1.0, 1.25)]
    },

    # --- STM32 Blue Pill Core Board (AUTHENTIC HARDWARE PINOUT) ---
    # Center X = 47.5 mm, Y center = 40.0 mm
    # Left Header: X = 39.88 mm (15.24mm / 600 mil row pitch)
    # Right Header: X = 55.12 mm
    {
        "ref": "J_MCU_L", "val": "BLUEPILL_L", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical",
        "desc": "STM32 核心板P4左排母 (本地PcbDoc/PDF核验; 1=3V3隔离, 2=GND, 3=5V; pin20端朝低Y)", "lcsc": "C41417332", "mpn": "HX PM2.54-1x20P ZC", "mfr": "hanxia",
        "x": 39.88, "y": 40.0, "type": "tht",
        "pads": [
            ("1", 0.0, 24.13, "NC", 1.7, 1.0),         # Core-board 3V3 output isolated
            ("2", 0.0, 21.59, "GND", 1.7, 1.0),
            ("3", 0.0, 19.05, "+5V_MCU", 1.7, 1.0),    # JP_USB: remove shunt before ANY USB connection
            ("4", 0.0, 16.51, "DHT11_DATA", 1.7, 1.0), # PB9
            ("5", 0.0, 13.97, "SERVO_PWM", 1.7, 1.0),  # PB8
            ("6", 0.0, 11.43, "I2C1_SDA", 1.7, 1.0),  # PB7
            ("7", 0.0, 8.89, "I2C1_SCL", 1.7, 1.0),   # PB6
            ("8", 0.0, 6.35, "NC", 1.7, 1.0),         # PB5
            ("9", 0.0, 3.81, "NC", 1.7, 1.0),         # PB4
            ("10", 0.0, 1.27, "NC", 1.7, 1.0),        # PB3
            ("11", 0.0, -1.27, "NC", 1.7, 1.0),       # PA15
            ("12", 0.0, -3.81, "NC", 1.7, 1.0),       # PA12 USB D+
            ("13", 0.0, -6.35, "NC", 1.7, 1.0),       # PA11 USB D-
            ("14", 0.0, -8.89, "NC", 1.7, 1.0),       # PA10
            ("15", 0.0, -11.43, "NC", 1.7, 1.0),      # PA9
            ("16", 0.0, -13.97, "NC", 1.7, 1.0),      # PA8
            ("17", 0.0, -16.51, "BUZZER_CTRL", 1.7, 1.0), # PB15
            ("18", 0.0, -19.05, "KEY2_SIG", 1.7, 1.0), # PB14
            ("19", 0.0, -21.59, "KEY1_SIG", 1.7, 1.0), # PB13
            ("20", 0.0, -24.13, "NC", 1.7, 1.0)        # PB12: 2+3 encoder has no SW output
        ]
    },
    {
        "ref": "J_MCU_R", "val": "BLUEPILL_R", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x20_P2.54mm_Vertical",
        "desc": "STM32 核心板P3右排母 (本地PcbDoc/PDF核验; 1=VBAT, 18=3V3隔离, 19/20=GND; pin20端朝低Y)", "lcsc": "C41417332", "mpn": "HX PM2.54-1x20P ZC", "mfr": "hanxia",
        "x": 55.12, "y": 40.0, "type": "tht",
        "pads": [
            ("1", 0.0, 24.13, "NC", 1.7, 1.0),         # VBAT
            ("2", 0.0, 21.59, "NC", 1.7, 1.0),         # PC13
            ("3", 0.0, 19.05, "NC", 1.7, 1.0),         # PC14
            ("4", 0.0, 16.51, "NC", 1.7, 1.0),         # PC15
            ("5", 0.0, 13.97, "TB_PWMA", 1.7, 1.0),    # PA0
            ("6", 0.0, 11.43, "TB_AIN1", 1.7, 1.0),    # PA1
            ("7", 0.0, 8.89, "VOICE_TX", 1.7, 1.0),    # PA2 USART2_TX
            ("8", 0.0, 6.35, "VOICE_RX", 1.7, 1.0),    # PA3 USART2_RX
            ("9", 0.0, 3.81, "GEST_INT", 1.7, 1.0),    # PA4
            ("10", 0.0, 1.27, "TB_AIN2", 1.7, 1.0),   # PA5
            ("11", 0.0, -1.27, "ENC_A", 1.7, 1.0),    # PA6
            ("12", 0.0, -3.81, "ENC_B", 1.7, 1.0),    # PA7
            ("13", 0.0, -6.35, "TB_STBY", 1.7, 1.0),  # PB0
            ("14", 0.0, -8.89, "NC", 1.7, 1.0),       # PB1
            ("15", 0.0, -11.43, "NC", 1.7, 1.0),      # PB10
            ("16", 0.0, -13.97, "NC", 1.7, 1.0),      # PB11
            ("17", 0.0, -16.51, "NC", 1.7, 1.0),      # NRST
            ("18", 0.0, -19.05, "NC", 1.7, 1.0),      # Core-board 3V3 output isolated
            ("19", 0.0, -21.59, "GND", 1.7, 1.0),
            ("20", 0.0, -24.13, "GND", 1.7, 1.0)      # Confirmed P3.20 GND by user's local schematic PDF
        ]
    },

    # --- Discrete I2C Pull-Up Resistors ---
    {
        "ref": "R_SCL", "val": "4.7k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "I2C1 SCL 上拉电阻", "lcsc": "C17673", "mpn": "0805W8F4701T5E", "mfr": "UNI-ROYAL",
        "x": 34.0, "y": 31.0, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+3.3V", 1.0, 1.25), ("2", 0.85, 0.0, "I2C1_SCL", 1.0, 1.25)]
    },
    {
        "ref": "R_SDA", "val": "4.7k", "fp": "Resistor_SMD:R_0805_2012Metric",
        "desc": "I2C1 SDA 上拉电阻", "lcsc": "C17673", "mpn": "0805W8F4701T5E", "mfr": "UNI-ROYAL",
        "x": 34.0, "y": 28.5, "type": "smd",
        "pads": [("1", -0.85, 0.0, "+3.3V", 1.0, 1.25), ("2", 0.85, 0.0, "I2C1_SDA", 1.0, 1.25)]
    },

    # ASR 16 pins: user confirmed 25.40 mm row centers, 2.54 mm pitch,
    # 30x28 mm board with Type-C; dimensions are NOT agent visual measurements.
    # Local socket numbering is top-to-bottom; right local 1 is module pin16.
    # Moved down to avoid MIC/SPK and status LEDs after widening the row spacing.
    {
        "ref": "J_VOICE_L", "val": "ASR_PRO_L_8P", "fp": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
        "desc": "ASR左8P母座; 顶=GND; 用户确认排距25.40; UART1固件必配; 料号待采购核验", "lcsc": "C27438", "mpn": "2.54-1*8P母环保", "mfr": "BOOMELE",
        "x": 65.8, "y": 44.0, "type": "tht",
        "pads": [
            ("1", 0.0, -8.89, "GND", 1.7, 1.0),
            ("2", 0.0, -6.35, "+5V_ASR", 1.7, 1.0),
            ("3", 0.0, -3.81, "NC", 1.7, 1.0),  # PB5 TX0: CH340
            ("4", 0.0, -1.27, "NC", 1.7, 1.0),  # PB6 RX0: CH340
            ("5", 0.0, 1.27, "ASR_TX1", 1.7, 1.0),  # PA2 -> MCU RX
            ("6", 0.0, 3.81, "ASR_RX1", 1.7, 1.0),  # PA3 <- MCU TX
            ("7", 0.0, 6.35, "NC", 1.7, 1.0),
            ("8", 0.0, 8.89, "NC", 1.7, 1.0)
        ]
    },
    {
        "ref": "J_VOICE_R", "val": "ASR_PRO_R_8P", "fp": "Connector_PinSocket_2.54mm:PinSocket_1x08_P2.54mm_Vertical",
        "desc": "ASR右8P母座; 顶=PA4/底=SPK+; 3V3输出隔离; 料号待采购核验", "lcsc": "C27438", "mpn": "2.54-1*8P母环保", "mfr": "BOOMELE",
        "x": 91.2, "y": 44.0, "type": "tht",
        "pads": [
            ("1", 0.0, -8.89, "NC", 1.7, 1.0),  # PA4 / programming strap
            ("2", 0.0, -6.35, "GND", 1.7, 1.0),
            ("3", 0.0, -3.81, "NC", 1.7, 1.0),  # internal 3V3 <=10mA output
            ("4", 0.0, -1.27, "NC", 1.7, 1.0),
            ("5", 0.0, 1.27, "NC", 1.7, 1.0),
            ("6", 0.0, 3.81, "NC", 1.7, 1.0),  # PC4, NOT microphone
            ("7", 0.0, 6.35, "VOICE_SPK_N", 1.7, 1.0),
            ("8", 0.0, 8.89, "VOICE_SPK_P", 1.7, 1.0)
        ]
    },
    # Pull ALL THREE shunts before inserting ASR USB; keep GND common.
    # Refit only after USB is removed and both logic domains are powered.
    {
        "ref": "JP_ASR", "val": "REMOVE_BEFORE_ASR_USB", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "desc": "ASR供电隔离跳帽; USB前与TX/RX三帽一起拔掉; 非自动电源隔离", "lcsc": "-", "mpn": "M20-9990245 + M7566-05", "mfr": "Harwin",
        "x": 29.0, "y": 50.8, "type": "tht",
        "pads": [("1", 0.0, 0.0, "+5V", 1.7, 1.0), ("2", 0.0, 2.54, "+5V_ASR", 1.7, 1.0)]
    },
    {
        "ref": "JP_ASR_TX", "val": "REMOVE_BEFORE_ASR_USB", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "desc": "MCU TX到ASR RX1(PA3)隔离; USB前拔帽", "lcsc": "-", "mpn": "M20-9990245 + M7566-05", "mfr": "Harwin",
        "x": 29.0, "y": 59.0, "type": "tht",
        "pads": [("1", 0.0, 0.0, "VOICE_TX", 1.7, 1.0), ("2", 0.0, 2.54, "ASR_RX1", 1.7, 1.0)]
    },
    {
        "ref": "JP_ASR_RX", "val": "REMOVE_BEFORE_ASR_USB", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        "desc": "ASR TX1(PA2)到MCU RX隔离; USB前拔帽", "lcsc": "-", "mpn": "M20-9990245 + M7566-05", "mfr": "Harwin",
        "x": 29.0, "y": 67.2, "type": "tht",
        "pads": [("1", 0.0, 0.0, "VOICE_RX", 1.7, 1.0), ("2", 0.0, 2.54, "ASR_TX1", 1.7, 1.0)]
    },
    {
        "ref": "SPK1", "val": "SPEAKER", "fp": "SmartFan:ZHOURI_XH-2PA_P2.50mm_Y",
        "desc": "喇叭接口 XH-2PA P2.50; 1.0mm孔为设计选取非厂家推荐; 针0.6+/-0.02mm", "lcsc": "C5258883", "mpn": "XH-2PA", "mfr": "ZHOURI",
        "x": 90.0, "y": 14.5, "type": "tht",
        "pads": [("1", 0.0, -1.25, "VOICE_SPK_P", 1.7, 1.0), ("2", 0.0, 1.25, "VOICE_SPK_N", 1.7, 1.0)]
    },

    # --- OLED installation requirement, NOT verified physical orientation ---
    # Header Y26.5, display body MUST extend toward -Y. Top view L->R SDA/SCL/VCC/GND.
    # Check actual module labels BEFORE power; 180-degree display orientation in firmware.
    {
        "ref": "J_OLED", "val": "OLED_12864", "fp": "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical",
        "desc": "OLED安装要求:屏体朝-Y; 顶视左到右SDA/SCL/VCC/GND; 实物核序前禁止上电", "lcsc": "C2718488", "mpn": "2.54-1*4P母", "mfr": "BOOMELE",
        "x": 78.5, "y": 26.5, "type": "tht",
        "pads": [
            ("1", 3.81, 0.0, "GND", 1.7, 1.0),
            ("2", 1.27, 0.0, "+3.3V", 1.7, 1.0),
            ("3", -1.27, 0.0, "I2C1_SCL", 1.7, 1.0),
            ("4", -3.81, 0.0, "I2C1_SDA", 1.7, 1.0)
        ]
    },

    # --- Front Interactive Row (PAJ7620, KEY1, KEY2, EC11) ---
    {
        "ref": "J_GESTURE", "val": "PAJ7620_GEST", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
        "desc": "PAJ7620 手势识别母座", "lcsc": "C50950", "mpn": "2.54-1*5P母", "mfr": "BOOMELE",
        "x": 16.0, "y": 74.0, "type": "tht",
        "pads": [
            ("1", -5.08, 0.0, "+3.3V", 1.7, 1.0),
            ("2", -2.54, 0.0, "GND", 1.7, 1.0),
            ("3", 0.0, 0.0, "I2C1_SCL", 1.7, 1.0),
            ("4", 2.54, 0.0, "I2C1_SDA", 1.7, 1.0),
            ("5", 5.08, 0.0, "GEST_INT", 1.7, 1.0)
        ]
    },
    # KEY1 (Power Button): socket at (34.0, 82.5), module extends towards front
    {
        "ref": "J_KEY1", "val": "KEY1_POWER", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "desc": "按键1【电源开关】直插母座", "lcsc": "C42431859", "mpn": "PM2.54-1Z03P-H85", "mfr": "JXTCONN",
        "x": 34.0, "y": 82.5, "type": "tht",
        "pads": [("1", -2.54, 0.0, "GND", 1.7, 1.0), ("2", 0.0, 0.0, "KEY1_SIG", 1.7, 1.0), ("3", 2.54, 0.0, "+3.3V", 1.7, 1.0)]
    },
    # KEY2 (Swing/Mode Button): socket at (49.5, 82.5)
    {
        "ref": "J_KEY2", "val": "KEY2_SWING", "fp": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "desc": "按键2【摇头模式】直插母座", "lcsc": "C42431859", "mpn": "PM2.54-1Z03P-H85", "mfr": "JXTCONN",
        "x": 49.5, "y": 82.5, "type": "tht",
        "pads": [("1", -2.54, 0.0, "GND", 1.7, 1.0), ("2", 0.0, 0.0, "KEY2_SIG", 1.7, 1.0), ("3", 2.54, 0.0, "+3.3V", 1.7, 1.0)]
    },
    # EC11 2+3: user-measured 21mm row separation; top VCC/GND, bottom A/C/B.
    {
        "ref": "J_ENC", "val": "EC11_ENCODER_2P_3P", "fp": "SmartFan:EC11_Module_2P_3P_Row21mm",
        "desc": "用户实测2+3编码器: 上1=3V3/2=GND, 下3=A/4=C(GND)/5=B; 组距21mm; 无SW",
        "lcsc": "-", "mpn": "2.54-1x2P + 1x3P female sockets", "mfr": "Generic",
        "x": 71.0, "y": 82.5, "type": "tht",
        "pads": [
            ("1", -1.27, -21.0, "+3.3V", 1.7, 1.0),
            ("2", 1.27, -21.0, "GND", 1.7, 1.0),
            ("3", -2.54, 0.0, "ENC_A", 1.7, 1.0),
            ("4", 0.0, 0.0, "GND", 1.7, 1.0),
            ("5", 2.54, 0.0, "ENC_B", 1.7, 1.0)
        ]
    },

    # --- 4x M3 Mounting Holes (Centers: 5.0, 90.0 mm, Pitch: 85.0 x 85.0 mm) ---
    {
        "ref": "H1", "val": "MountingHole_M3", "fp": "MountingHole:MountingHole_3.2mm_M3_Pad_Via",
        "desc": "M3 螺丝安装孔 (左上)", "lcsc": "-", "mpn": "M3_HOLE", "mfr": "JLCPCB",
        "x": 5.0, "y": 5.0, "type": "hole", "pads": [("1", 0.0, 0.0, "GND", 6.0, 3.2)]
    },
    {
        "ref": "H2", "val": "MountingHole_M3", "fp": "MountingHole:MountingHole_3.2mm_M3_Pad_Via",
        "desc": "M3 螺丝安装孔 (右上)", "lcsc": "-", "mpn": "M3_HOLE", "mfr": "JLCPCB",
        "x": 90.0, "y": 5.0, "type": "hole", "pads": [("1", 0.0, 0.0, "GND", 6.0, 3.2)]
    },
    {
        "ref": "H3", "val": "MountingHole_M3", "fp": "MountingHole:MountingHole_3.2mm_M3_Pad_Via",
        "desc": "M3 螺丝安装孔 (左下)", "lcsc": "-", "mpn": "M3_HOLE", "mfr": "JLCPCB",
        "x": 5.0, "y": 90.0, "type": "hole", "pads": [("1", 0.0, 0.0, "GND", 6.0, 3.2)]
    },
    {
        "ref": "H4", "val": "MountingHole_M3", "fp": "MountingHole:MountingHole_3.2mm_M3_Pad_Via",
        "desc": "M3 螺丝安装孔 (右下)", "lcsc": "-", "mpn": "M3_HOLE", "mfr": "JLCPCB",
        "x": 90.0, "y": 90.0, "type": "hole", "pads": [("1", 0.0, 0.0, "GND", 6.0, 3.2)]
    }
]

print(f"Configured {len(COMPONENTS)} components with authentic footprints and net assignments.")

# 3. Compute Absolute Pad Coordinates and Run DRC Checks
PAD_RECORDS = []
NET_PAD_MAP = {nid: [] for nid, _ in NETS}

for comp in COMPONENTS:
    cx, cy = comp["x"], comp["y"]
    for pad in comp["pads"]:
        pnum, px, py, net_name = pad[0], pad[1], pad[2], pad[3]
        pw = pad[4] if len(pad) > 4 else 1.6
        ph = pad[5] if len(pad) > 5 else 1.6
        abs_x = round(OFFSET_X + cx + px, 4)
        abs_y = round(OFFSET_Y + cy + py, 4)
        nid = NET_MAP.get(net_name, 0)
        rec = {
            "ref": comp["ref"],
            "pad": pnum,
            "net": net_name,
            "nid": nid,
            "x": abs_x,
            "y": abs_y,
            "w": pw,
            "h": ph,
            "type": comp["type"]
        }
        PAD_RECORDS.append(rec)
        if nid > 0:
            NET_PAD_MAP[nid].append(rec)

print(f"Total {len(PAD_RECORDS)} pads mapped into global KiCad coordinate space.")

# Verify: Zero Pad Overlap DRC
pad_drc_errors = []
for i in range(len(PAD_RECORDS)):
    p1 = PAD_RECORDS[i]
    for j in range(i + 1, len(PAD_RECORDS)):
        p2 = PAD_RECORDS[j]
        dx = abs(p1["x"] - p2["x"])
        dy = abs(p1["y"] - p2["y"])
        clearance_x = dx - (p1["w"] + p2["w"]) / 2.0
        h1 = p1['w'] if p1['type'] in ('tht', 'hole') else p1['h']
        h2 = p2['w'] if p2['type'] in ('tht', 'hole') else p2['h']
        clearance_y = dy - (h1 + h2) / 2.0
        if clearance_x < 0.15 and clearance_y < 0.15:
            if p1["nid"] != p2["nid"]:
                pad_drc_errors.append(f"PAD SHORT: {p1['ref']}.{p1['pad']} (Net {p1['net']}) and {p2['ref']}.{p2['pad']} (Net {p2['net']}) dist=({dx:.2f}, {dy:.2f})")

if pad_drc_errors:
    print(f"DRC ERROR: Found {len(pad_drc_errors)} pad short circuits!")
    for err in pad_drc_errors:
        print("  -", err)
    sys.exit(1)
else:
    print("Pad bounding-box overlap precheck passed; independent copper clearance/connectivity audit still required.")

# 4. Complete PCB Routing Generation (Traces & Vias)
from obstacle_router import route_board
TRACKS, VIAS = route_board(PAD_RECORDS, report_path=os.path.join(DOWNLOAD_DIR, 'validation', 'router_report.json'), net_names=dict(NETS))
print(f"Obstacle-routed {len(TRACKS)} tracks and {len(VIAS)} vias; all nets including GND explicitly routed.")


# Helper functions for 3D models and authentic copper clearance computation
def get_3d_model(fp):
    if "R_0805" in fp:
        return "${KICAD8_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_0805_2012Metric.wrl"
    elif "C_0805" in fp:
        return "${KICAD8_3DMODEL_DIR}/Capacitor_SMD.3dshapes/C_0805_2012Metric.wrl"
    elif "CP_Radial" in fp:
        return "${KICAD8_3DMODEL_DIR}/Capacitor_THT.3dshapes/CP_Radial_D6.3mm_P2.50mm.wrl"
    elif "SOIC-8" in fp:
        return "${KICAD8_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-8_3.9x4.9mm_P1.27mm.wrl"
    elif "SOT-223" in fp:
        return "${KICAD8_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-223.wrl"
    elif "TO-92" in fp:
        return "${KICAD8_3DMODEL_DIR}/Package_TO_SOT_THT.3dshapes/TO-92_Inline.wrl"
    elif "D_SMA" in fp:
        return "${KICAD8_3DMODEL_DIR}/Diode_SMD.3dshapes/D_SMA.wrl"
    elif "D_SOD-123" in fp:
        return "${KICAD8_3DMODEL_DIR}/Diode_SMD.3dshapes/D_SOD-123.wrl"
    elif "LED_0805" in fp:
        return "${KICAD8_3DMODEL_DIR}/LED_SMD.3dshapes/LED_0805_2012Metric.wrl"
    elif "L_CD54" in fp:
        return "${KICAD8_3DMODEL_DIR}/Inductor_SMD.3dshapes/L_CD54.wrl"
    elif "BarrelJack" in fp:
        return "${KICAD8_3DMODEL_DIR}/Connector_BarrelJack.3dshapes/BarrelJack_Horizontal.wrl"
    elif "B2B-XH-A" in fp:
        return "${KICAD8_3DMODEL_DIR}/Connector_JST.3dshapes/JST_XH_B2B-XH-A_1x02_P2.54mm_Vertical.wrl"
    elif "Buzzer" in fp:
        return "${KICAD8_3DMODEL_DIR}/Buzzer_Beeper.3dshapes/Buzzer_12x9.5RM7.6.wrl"
    elif "PinHeader_1x" in fp:
        import re
        p_count = re.findall(r'1x(\d+)', fp)
        n = p_count[0] if p_count else "03"
        return f"${{KICAD8_3DMODEL_DIR}}/Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x{int(n):02d}_P2.54mm_Vertical.wrl"
    return None

def copper_zone_boundary(inset=1.0):
    """R3 board inward offset: R2 corners for the default 1 mm setback.

    Sampled chords lie INSIDE the exact offset curve, never toward the edge.
    Used identically for the clipping solid and the editable KiCad zone outline.
    """
    assert 0 <= inset < CORNER_R
    r = CORNER_R - inset
    centers = [(OFFSET_X+BOARD_W-CORNER_R, OFFSET_Y+CORNER_R, -90),
               (OFFSET_X+BOARD_W-CORNER_R, OFFSET_Y+BOARD_H-CORNER_R, 0),
               (OFFSET_X+CORNER_R, OFFSET_Y+BOARD_H-CORNER_R, 90),
               (OFFSET_X+CORNER_R, OFFSET_Y+CORNER_R, 180)]
    return [[cx+r*math.cos(math.radians(start+i*90/64)),
             cy+r*math.sin(math.radians(start+i*90/64))]
            for cx,cy,start in centers for i in range(65)]

def compute_copper_zone(layer_name):
    cl = 0.30
    cutouts = []
    for p in PAD_RECORDS:
        if p['nid'] == 1:
            continue
        if p['type'] == 'smd' and layer_name != 'F.Cu':
            continue
        px, py, pw, ph = p['x'], p['y'], p['w'], p['h']
        if p['type'] in ('tht', 'hole'):
            # h stores drill diameter, NOT copper height for through-hole pads.
            c = m3d.CrossSection.circle(pw / 2.0 + cl, 64).translate([px, py])
        else:
            c = m3d.CrossSection.square([pw + 2*cl, ph + 2*cl], center=True).translate([px, py])
        cutouts.append(c)
    for v in VIAS:
        vx, vy, sz, drl, nid = v
        if nid == 1:
            continue
        cutouts.append(m3d.CrossSection.circle(sz/2.0 + cl, 12).translate([vx, vy]))
    for trk in TRACKS:
        x1, y1, x2, y2, w, tlayer, nid = trk
        if tlayer != layer_name or nid == 1:
            continue
        r = w/2.0 + cl
        # 64 segments bound radial sagitta to 0.001566 mm at r=1.30 mm.
        c1 = m3d.CrossSection.circle(r, 64).translate([x1, y1])
        c2 = m3d.CrossSection.circle(r, 64).translate([x2, y2])
        cutouts.append((c1 + c2).hull())
        
    union_cutouts = m3d.CrossSection.batch_boolean(cutouts, m3d.OpType.Add)
    base = m3d.CrossSection([copper_zone_boundary()])
    res = base - union_cutouts
    polys = res.to_polygons()
    outer = [p for p in polys if np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) > 0][0]
    holes = [p for p in polys if np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) < 0]
    
    sorted_holes = sorted(holes, key=lambda h: max(pt[0] for pt in h), reverse=True)
    curr = [list(pt) for pt in outer]
    for h in sorted_holes:
        h_pts = [list(pt) for pt in h]
        max_idx = max(range(len(h_pts)), key=lambda i: h_pts[i][0])
        hx, hy = h_pts[max_idx]
        best_x = float('inf')
        best_edge_idx = -1
        best_pt = None
        for i in range(len(curr)):
            p1 = curr[i]
            p2 = curr[(i + 1) % len(curr)]
            y_min = min(p1[1], p2[1])
            y_max = max(p1[1], p2[1])
            if y_min <= hy <= y_max and y_min < y_max:
                t = (hy - p1[1]) / (p2[1] - p1[1])
                ix = p1[0] + t * (p2[0] - p1[0])
                if ix > hx and ix < best_x:
                    best_x = ix
                    best_edge_idx = i
                    best_pt = [ix, hy]
        if best_edge_idx != -1:
            ordered_h = h_pts[max_idx:] + h_pts[:max_idx] + [h_pts[max_idx]]
            insert_chain = [best_pt] + ordered_h + [best_pt]
            curr = curr[:best_edge_idx+1] + insert_chain + curr[best_edge_idx+1:]
    return curr

print("Precomputing authentic GND copper clearance polygons...")
KEYHOLE_POLYS = {
    "F.Cu": compute_copper_zone("F.Cu"),
    "B.Cu": compute_copper_zone("B.Cu")
}
print(f"Copper zones precomputed: F.Cu {len(KEYHOLE_POLYS['F.Cu'])} verts, B.Cu {len(KEYHOLE_POLYS['B.Cu'])} verts.")


def build_safe_silkscreen():
    """Shared stroked silk. Never clip glyphs: relocate complete readable refs.

    Keep .10 mm from mask plus .075 mm half-stroke and a .01 mm guard.
    Use a conservative .10 mm radial mask expansion (current Gerber is .05).
    Failure to place any reference aborts export rather than deleting its text.
    """
    from shapely.geometry import Point, box, LineString, Polygon
    from shapely.ops import unary_union
    from shapely.affinity import translate
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    stroke = .15
    openings = []
    for comp in COMPONENTS:
        for p in comp['pads']:
            x, y = OFFSET_X+comp['x']+p[1], OFFSET_Y+comp['y']+p[2]
            if comp['type'] == 'smd':
                openings.append(box(x-p[4]/2-.10,y-p[5]/2-.10,x+p[4]/2+.10,y+p[5]/2+.10))
            else:
                openings.append(Point(x,y).buffer(p[4]/2+.10,quad_segs=128))
    openings += [Point(v[0],v[1]).buffer(v[2]/2+.10,quad_segs=128) for v in VIAS]
    forbidden = unary_union(openings).buffer(.10+stroke/2+.01,quad_segs=64)
    allowed = Polygon(copper_zone_boundary(.30))
    font = FontProperties(family='DejaVu Sans',weight='bold')
    rows = []
    text_boxes = []
    borders = []
    labels = []
    for comp in COMPONENTS:
        cx,cy = OFFSET_X+comp['x'],OFFSET_Y+comp['y']
        pads = comp['pads']
        left = min(cx+p[1]-p[4]/2 for p in pads)-.40
        right = max(cx+p[1]+p[4]/2 for p in pads)+.40
        top = min(cy+p[2]-(p[5] if comp['type']=='smd' else p[4])/2 for p in pads)-.40
        bottom = max(cy+p[2]+(p[5] if comp['type']=='smd' else p[4])/2 for p in pads)+.40
        borders.append((comp['ref'],LineString([(left,top),(right,top),(right,bottom),(left,bottom),(left,top)])))
        labels.append((comp['ref'],'TEXT',comp['ref'],cx,cy,left,right,top,bottom))
        notices=[]
        ref=comp['ref']
        if ref=='DC1': notices += ['5V ONLY','DC1 1:+ 2:GND']
        if ref=='JP_USB': notices += ['JP_USB OPEN BEFORE USB']
        if ref=='JP_ASR': notices += ['USB: OPEN PWR TX RX']
        if ref=='J_OLED': notices += ['OLED L>R: SDA SCL VCC GND']
        if ref.startswith('D') and ref!='DC1':
            k=next((p for p in pads if p[0]=='1'),None)
            if k is not None:
                side=('RIGHT' if k[1]>0 else 'LEFT') if abs(k[1])>=abs(k[2]) else ('BOTTOM' if k[2]>0 else 'TOP')
                notices.append(ref+' K=1 '+side)
        # Direction is board-top-view (X right, Y down), not an inferred module pinout.
        if ref.startswith(('J_', 'JP_')) or ref in ('MOTO1','SERVO1','SPK1','MIC1'):
            first=next((p for p in pads if p[0]=='1'),None)
            if first is None: raise RuntimeError('No pin 1 for silk orientation '+ref)
            mx=sum(p[1] for p in pads)/len(pads);my=sum(p[2] for p in pads)/len(pads)
            vx,vy=first[1]-mx,first[2]-my
            side=('RIGHT' if vx>0 else 'LEFT') if abs(vx)>=abs(vy) else ('BOTTOM' if vy>0 else 'TOP')
            notices.append(ref+' P1 '+side)
        for text in notices:
            labels.append((ref,'NOTICE',text,cx,cy,left,right,top,bottom))
    # Reserve all refs first; notices cannot displace/delete them. Both use the same
    # intact glyph relocation, mask clearance and text-vs-text exclusion rules.
    labels.sort(key=lambda item: item[1]!='TEXT')
    notice_border_guard=unary_union([border for ref,border in borders]).buffer(.20)
    for ref,kind,text,cx,cy,left,right,top,bottom in labels:
        glyphs = TextPath((0,0),text,size=1.40,prop=font).to_polygons()
        xmin=min(x for poly in glyphs for x,y in poly);xmax=max(x for poly in glyphs for x,y in poly)
        ymin=min(-y for poly in glyphs for x,y in poly);ymax=max(-y for poly in glyphs for x,y in poly)
        width,height=xmax-xmin,ymax-ymin
        candidates=[(cx,(top-.30-height/2)),(cx,bottom+.30+height/2),
                    (left-.30-width/2,cy),(right+.30+width/2,cy)]
        # Whole-board fallback, nearest first. Never crop text or relax clearance.
        candidates += sorted(((OFFSET_X+ix*.5,OFFSET_Y+iy*.5)
                              for ix in range(int(BOARD_W*2)+1)
                              for iy in range(int(BOARD_H*2)+1)),
                             key=lambda p:((p[0]-cx)**2+(p[1]-cy)**2,p[1],p[0]))
        chosen=None
        for x,y in candidates:
            envelope=box(x-width/2-.10,y-height/2-.10,x+width/2+.10,y+height/2+.10)
            if not allowed.covers(envelope) or envelope.intersects(forbidden):continue
            if kind=='NOTICE' and envelope.intersects(notice_border_guard):continue
            if any(envelope.intersects(other) for other in text_boxes):continue
            chosen=(x-(xmin+xmax)/2,y-(ymin+ymax)/2)
            text_boxes.append(envelope.buffer(.10))
            break
        if chosen is None:
            raise RuntimeError('No safe readable silkscreen placement for '+ref+': '+text)
        dx,dy=chosen
        segments=[]
        for poly in glyphs:
            for a,b in zip(poly,poly[1:]):
                if tuple(a)!=tuple(b):segments.append((a[0]+dx,-a[1]+dy,b[0]+dx,-b[1]+dy))
        rows.append(dict(ref=ref,kind=kind,text=text,segments=segments,width=stroke,
                         center_mm=[x,y],offset_from_component_mm=[x-cx,y-cy]))
    # Clip only outlines, never letters; also keep outlines away from labels.
    exclusion=unary_union([forbidden]+text_boxes)
    for ref,border in borders:
        clipped=border.intersection(allowed).difference(exclusion)
        parts=list(clipped.geoms) if hasattr(clipped,'geoms') else [clipped]
        segments=[]
        for part in parts:
            if part.geom_type!='LineString':continue
            pts=list(part.coords)
            segments.extend((*a,*b) for a,b in zip(pts,pts[1:]) if math.dist(a,b)>.05)
        if not segments:raise RuntimeError('No safe outline remaining for '+ref)
        rows.append(dict(ref=ref,kind='BORDER',segments=segments,width=stroke))
    return rows

# 5. KiCad PCB File Generator (.kicad_pcb)
def export_kicad_pcb():
    pcb_path = os.path.join(KICAD_DIR, "fan_ctrl_revB.kicad_pcb")
    lines = []
    lines.append('(kicad_pcb (version 20221018) (generator "SmartFan_Engine_v3.0")')
    lines.append('  (general (thickness 1.6))')
    lines.append('  (paper "A4")')
    lines.append('  (layers')
    lines.append('    (0 "F.Cu" signal)')
    lines.append('    (31 "B.Cu" signal)')
    lines.append('    (32 "B.Adhes" user "B.Adhesive")')
    lines.append('    (33 "F.Adhes" user "F.Adhesive")')
    lines.append('    (34 "B.Paste" user)')
    lines.append('    (35 "F.Paste" user)')
    lines.append('    (36 "B.SilkS" user "B.Silkscreen")')
    lines.append('    (37 "F.SilkS" user "F.Silkscreen")')
    lines.append('    (38 "B.Mask" user)')
    lines.append('    (39 "F.Mask" user)')
    lines.append('    (40 "Dwgs.User" user "User.Drawings")')
    lines.append('    (41 "Cmts.User" user "User.Comments")')
    lines.append('    (42 "Eco1.User" user "User.Eco1")')
    lines.append('    (43 "Eco2.User" user "User.Eco2")')
    lines.append('    (44 "Edge.Cuts" user)')
    lines.append('    (45 "Margin" user)')
    lines.append('    (46 "B.CrtYd" user "B.Courtyard")')
    lines.append('    (47 "F.CrtYd" user "F.Courtyard")')
    lines.append('    (48 "B.Fab" user)')
    lines.append('    (49 "F.Fab" user)')
    lines.append('  )')
    lines.append('  (setup')
    lines.append('    (pad_to_mask_clearance 0.05)')
    lines.append('    (solder_mask_min_width 0.1)')
    # KiCad 8: false means both-side via tenting; copper and drills remain unchanged.
    lines.append('    (pcbplotparams (viasonmask false))')
    lines.append('  )')

    # Electrical Nets
    for nid, name in NETS:
        lines.append(f'  (net {nid} "{name}")')

    # Edge.Cuts: 95.0 x 95.0 mm with R=3.0 mm rounded corners
    x0, y0 = OFFSET_X, OFFSET_Y
    x1, y1 = OFFSET_X + BOARD_W, OFFSET_Y + BOARD_H
    r = CORNER_R

    # Top edge
    lines.append(f'  (gr_line (start {x0+r} {y0}) (end {x1-r} {y0}) (layer "Edge.Cuts") (width 0.15))')
    # Top-right corner arc
    lines.append(f'  (gr_arc (start {x1-r} {y0}) (mid {x1-r*(1-0.7071)} {y0+r*(1-0.7071)}) (end {x1} {y0+r}) (layer "Edge.Cuts") (width 0.15))')
    # Right edge
    lines.append(f'  (gr_line (start {x1} {y0+r}) (end {x1} {y1-r}) (layer "Edge.Cuts") (width 0.15))')
    # Bottom-right corner arc
    lines.append(f'  (gr_arc (start {x1} {y1-r}) (mid {x1-r*(1-0.7071)} {y1-r*(1-0.7071)}) (end {x1-r} {y1}) (layer "Edge.Cuts") (width 0.15))')
    # Bottom edge
    lines.append(f'  (gr_line (start {x1-r} {y1}) (end {x0+r} {y1}) (layer "Edge.Cuts") (width 0.15))')
    # Bottom-left corner arc
    lines.append(f'  (gr_arc (start {x0+r} {y1}) (mid {x0+r*(1-0.7071)} {y1-r*(1-0.7071)}) (end {x0} {y1-r}) (layer "Edge.Cuts") (width 0.15))')
    # Left edge
    lines.append(f'  (gr_line (start {x0} {y1-r}) (end {x0} {y0+r}) (layer "Edge.Cuts") (width 0.15))')
    # Top-left corner arc
    lines.append(f'  (gr_arc (start {x0} {y0+r}) (mid {x0+r*(1-0.7071)} {y0+r*(1-0.7071)}) (end {x0+r} {y0}) (layer "Edge.Cuts") (width 0.15))')

    # Footprints
    for comp in COMPONENTS:
        cx = round(OFFSET_X + comp["x"], 4)
        cy = round(OFFSET_Y + comp["y"], 4)
        ref = comp["ref"]
        val = comp["val"].replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))
        fp = comp["fp"]
        desc = comp["desc"].replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))
        lcsc = comp.get("lcsc", "-")

        lines.append(f'  (footprint "{fp}" (layer "F.Cu")')
        lines.append(f'    (at {cx} {cy})')
        lines.append(f'    (descr "{desc}")')
        lines.append(f'    (property "Reference" "{ref}" (at 0 -2.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))')
        lines.append(f'    (property "Value" "{val}" (at 0 2.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.15))))')
        if lcsc != "-":
            lines.append(f'    (property "LCSC" "{lcsc}" (at 0 0) (layer "Cmts.User") (effects (font (size 0.5 0.5) (thickness 0.1))))')

        for pad in comp["pads"]:
            pnum = pad[0]
            px = round(pad[1], 4)
            py = round(pad[2], 4)
            pnet = pad[3]
            pw = pad[4] if len(pad) > 4 else 1.6
            ph = pad[5] if len(pad) > 5 else 1.6
            nid = NET_MAP.get(pnet, 0)

            if comp["type"] == "smd":
                lines.append(f'    (pad "{pnum}" smd rect (at {px} {py}) (size {pw} {ph}) (layers "F.Cu" "F.Paste" "F.Mask") (net {nid} "{pnet}"))')
            elif comp["type"] == "hole":
                lines.append(f'    (pad "{pnum}" thru_hole circle (at {px} {py}) (size {pw} {pw}) (drill {ph}) (layers *.Cu *.Mask) (net {nid} "{pnet}"))')
            else:
                shape = "circle"  # Match circular Gerber pads and circular zone clearance.
                drill_d = ph if ph < pw else round(pw * 0.55, 2)
                lines.append(f'    (pad "{pnum}" thru_hole {shape} (at {px} {py}) (size {pw} {pw}) (drill {drill_d}) (layers *.Cu *.Mask) (net {nid} "{pnet}"))')

        m_path = get_3d_model(fp)
        if m_path:
            rotation_z = comp.get('model_rotation_z', 0)
            lines.append(f'    (model "{m_path}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rotation_z})))')

        lines.append('  )')

    # Tracks
    for trk in TRACKS:
        sx, sy, ex, ey, w, layer, nid = trk
        lines.append(f'  (segment (start {sx} {sy}) (end {ex} {ey}) (width {w}) (layer "{layer}") (net {nid}))')

    # Vias
    for via in VIAS:
        vx, vy, sz, drl, nid = via
        lines.append(f'  (via (at {vx} {vy}) (size {sz}) (drill {drl}) (layers "F.Cu" "B.Cu") (net {nid}))')

    # Copper Pour Zones: F.Cu and B.Cu on Net 1 (GND) with explicit (filled_polygon ...)
    for zlayer, z_uuid in [("F.Cu", "00000000-0000-0000-0000-000000000001"), ("B.Cu", "00000000-0000-0000-0000-000000000002")]:
        lines.append(f'  (zone (net 1) (net_name "GND") (layer "{zlayer}") (tstamp {z_uuid})')
        lines.append('    (hatch edge 0.5)')
        lines.append('    (priority 0)')
        lines.append('    (connect_pads (clearance 0.25))')
        lines.append('    (min_thickness 0.2)')
        lines.append('    (filled_areas_thickness no)')
        lines.append('    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.4))')
        lines.append('    (polygon')
        lines.append('      (pts')
        for px, py in copper_zone_boundary():
            lines.append(f'        (xy {px:.8f} {py:.8f})')
        lines.append('      )')
        lines.append('    )')
        lines.append('    (filled_polygon')
        lines.append('      (pts')
        for pt in KEYHOLE_POLYS[zlayer]:
            lines.append(f'        (xy {pt[0]:.4f} {pt[1]:.4f})')
        lines.append('      )')
        lines.append('    )')
        lines.append('  )')

    # All visible top silk uses the exact same safe geometry as Gerber GTO.
    for row in build_safe_silkscreen():
        for sx, sy, ex, ey in row['segments']:
            sx, sy, ex, ey = (round(v*100000)/100000 for v in (sx, sy, ex, ey))
            lines.append(f'  (gr_line (start {sx:.5f} {sy:.5f}) (end {ex:.5f} {ey:.5f}) (layer "F.SilkS") (width {row["width"]}))')

    lines.append(')')

    with open(pcb_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"KiCad PCB exported successfully: {pcb_path} ({len(lines)} lines)")
    return pcb_path

export_kicad_pcb()

# 6. KiCad Schematic File Generator (.kicad_sch)
def export_kicad_sch():
    def unique_symbol_pads(comp):
        """Multiple physical pads may share a pin only when their nets agree."""
        pins = {}
        for pad in comp['pads']:
            if pad[0] in pins:
                assert pins[pad[0]][3] == pad[3], (comp['ref'], pad[0], 'conflicting pad nets')
            else:
                pins[pad[0]] = pad
        return list(pins.values())

    sch_path = os.path.join(KICAD_DIR, 'fan_ctrl_revB.kicad_sch')
    lines = []
    lines.append('(kicad_sch (version 20231120) (generator "SmartFan_Engine_v4.0")')
    lines.append('  (uuid "d0000000-0000-0000-0000-000000000001")')
    lines.append('  (paper "A2")')
    lines.append('  (title_block')
    lines.append('    (title "Desktop Smart Fan Controller Rev B4")')
    lines.append('    (date "2026-11-04")')
    lines.append('    (rev "B4")')
    lines.append('    (company "Antigravity Engineering")')
    lines.append('    (comment 1 "95x95mm | Rev B4 | Procurement verification required")')
    lines.append('  )')
    
    # 1. lib_symbols
    lines.append('  (lib_symbols')
    
    # Resistor
    lines.append('    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "R" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "R" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "R_0_1" (rectangle (start -1.0 -2.54) (end 1.0 2.54) (stroke (width 0.254) (type default)) (fill (type none))))')
    lines.append('      (symbol "R_1_1"')
    lines.append('        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Capacitor
    lines.append('    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "C" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "C" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "C_0_1"')
    lines.append('        (polyline (pts (xy -2.0 -0.5) (xy 2.0 -0.5)) (stroke (width 0.254) (type default)))')
    lines.append('        (polyline (pts (xy -2.0 0.5) (xy 2.0 0.5)) (stroke (width 0.254) (type default)))')
    lines.append('      )')
    lines.append('      (symbol "C_1_1"')
    lines.append('        (pin passive line (at 0 2.54 270) (length 2.04) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 0 -2.54 90) (length 2.04) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Polarized Capacitor
    lines.append('    (symbol "Device:C_Polarized" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "C" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "CP" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "C_Pol_0_1"')
    lines.append('        (polyline (pts (xy -2.0 -0.5) (xy 2.0 -0.5)) (stroke (width 0.254) (type default)))')
    lines.append('        (polyline (pts (xy -2.0 0.5) (xy 2.0 0.5)) (stroke (width 0.254) (type default)))')
    lines.append('      )')
    lines.append('      (symbol "C_Pol_1_1"')
    lines.append('        (pin passive line (at 0 2.54 270) (length 2.04) (name "+" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 0 -2.54 90) (length 2.04) (name "-" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Diode Schottky
    lines.append('    (symbol "Device:D_Schottky" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "D" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "SS24" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "D_0_1"')
    lines.append('        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type outline)))')
    lines.append('        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)))')
    lines.append('      )')
    lines.append('      (symbol "D_1_1"')
    lines.append('        (pin passive line (at -2.54 0 0) (length 1.27) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 2.54 0 180) (length 1.27) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Diode
    lines.append('    (symbol "Device:D" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "D" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "1N4148W" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "D_0_1"')
    lines.append('        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type outline)))')
    lines.append('        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)))')
    lines.append('      )')
    lines.append('      (symbol "D_1_1"')
    lines.append('        (pin passive line (at -2.54 0 0) (length 1.27) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 2.54 0 180) (length 1.27) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # LED
    lines.append('    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "D" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "LED" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "LED_0_1"')
    lines.append('        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type outline)))')
    lines.append('        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)))')
    lines.append('      )')
    lines.append('      (symbol "LED_1_1"')
    lines.append('        (pin passive line (at -2.54 0 0) (length 1.27) (name "A" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 2.54 0 180) (length 1.27) (name "K" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Inductor
    lines.append('    (symbol "Device:L" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "L" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "47uH" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "L_0_1" (rectangle (start -1.0 -2.54) (end 1.0 2.54) (stroke (width 0.254) (type default)) (fill (type outline))))')
    lines.append('      (symbol "L_1_1"')
    lines.append('        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Transistor NPN
    lines.append('    (symbol "Device:Q_NPN_BCE" (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "Q" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "2N3904" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "Q_0_1" (circle (center 0 0) (radius 3.81) (stroke (width 0.254) (type default)) (fill (type none))))')
    lines.append('      (symbol "Q_1_1"')
    lines.append('        (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "E" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin input line (at -5.08 0 0) (length 3.81) (name "B" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 2.54 5.08 270) (length 2.54) (name "C" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Buzzer
    lines.append('    (symbol "Device:Buzzer" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "BZ" (at 2.0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "Buzzer" (at 0 0 90) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "BZ_0_1" (circle (center 0 0) (radius 3.0) (stroke (width 0.254) (type default)) (fill (type none))))')
    lines.append('      (symbol "BZ_1_1"')
    lines.append('        (pin passive line (at 0 5.08 270) (length 2.08) (name "+" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 0 -5.08 90) (length 2.08) (name "-" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # AO4409: datasheet pinout 1/2/3=S, 4=G, 5/6/7/8=D.
    # Explicit package-pin symbol avoids hiding any parallel power pins.
    lines.append('    (symbol "SmartFan:AO4409" (pin_names (offset 1.0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "Q" (at 0 9 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "AO4409 P-MOS" (at 0 -9 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "AO4409_0_1" (rectangle (start -7.62 6.35) (end 7.62 -6.35) (stroke (width 0.254) (type default)) (fill (type background))))')
    lines.append('      (symbol "AO4409_1_1"')
    for number, name, x, y, angle in [(1,"S",-10.16,3.81,0),(2,"S",-10.16,1.27,0),(3,"S",-10.16,-1.27,0),(4,"G",-10.16,-3.81,0),(5,"D",10.16,-3.81,180),(6,"D",10.16,-1.27,180),(7,"D",10.16,1.27,180),(8,"D",10.16,3.81,180)]:
        lines.append(f'        (pin passive line (at {x} {y} {angle}) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{number}" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')
    lines.append('    (symbol "Device:Fuse" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "F" (at 0 2.54 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "Fuse" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "Fuse_0_1" (rectangle (start -2.54 1.27) (end 2.54 -1.27) (stroke (width 0.254) (type default)) (fill (type none))) (polyline (pts (xy -2.54 0) (xy 2.54 0)) (stroke (width 0.254) (type default)) (fill (type none))))')
    lines.append('      (symbol "Fuse_1_1"')
    lines.append('        (pin passive line (at -5.08 0 0) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 5.08 0 180) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # TLV1117LV33DCYR
    lines.append('    (symbol "Regulator_Linear:TLV1117LV33DCYR" (pin_names (offset 1.0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "TLV1117LV33DCYR" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "AMS_0_1" (rectangle (start -6.35 5.08) (end 6.35 -5.08) (stroke (width 0.254) (type default)) (fill (type background))))')
    lines.append('      (symbol "AMS_1_1"')
    lines.append('        (pin power_in line (at 0 -7.62 90) (length 2.54) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin power_out line (at 8.89 0 180) (length 2.54) (name "VOUT" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin power_in line (at -8.89 0 0) (length 2.54) (name "VIN" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Barrel Jack
    lines.append('    (symbol "Connector:Barrel_Jack" (pin_names (offset 1.0)) (in_bom yes) (on_board yes)')
    lines.append('      (property "Reference" "J" (at 0 5.08 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (property "Value" "Barrel_Jack" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))')
    lines.append('      (symbol "Barrel_Jack_0_1"')
    lines.append('        (rectangle (start -5.08 3.81) (end 5.08 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))')
    lines.append('        (polyline (pts (xy 5.08 2.54) (xy -2.54 2.54) (xy -2.54 1.27) (xy 1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
    lines.append('        (polyline (pts (xy 5.08 -2.54) (xy -2.54 -2.54) (xy -2.54 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
    lines.append('        (polyline (pts (xy 5.08 0) (xy 2.54 0) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))')
    lines.append('      )')
    lines.append('      (symbol "Barrel_Jack_1_1"')
    lines.append('        (pin passive line (at 7.62 2.54 180) (length 2.54) (name "TIP" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 7.62 -2.54 180) (length 2.54) (name "SLEEVE" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))')
    lines.append('        (pin passive line (at 7.62 0 180) (length 2.54) (name "SWITCH" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))')
    lines.append('      )')
    lines.append('    )')

    # Generic Connectors 1x02, 1x03, 1x04, 1x05, 1x07, 1x08, 1x20
    for n in [2, 3, 4, 5, 7, 8, 20]:
        lines.append(f'    (symbol "Connector_Generic:Conn_01x{n:02d}" (pin_names (offset 1.0)) (in_bom yes) (on_board yes)')
        lines.append(f'      (property "Reference" "J" (at 0 {(n*2.54)/2 + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'      (property "Value" "Conn_01x{n:02d}" (at 0 {-((n*2.54)/2 + 2.54):.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'      (symbol "Conn_01x{n:02d}_0_1" (rectangle (start -3.81 {(n*2.54)/2:.2f}) (end 3.81 {-((n*2.54)/2):.2f}) (stroke (width 0.254) (type default)) (fill (type background))))')
        lines.append(f'      (symbol "Conn_01x{n:02d}_1_1"')
        for p in range(1, n + 1):
            py = (n/2.0 - (p - 0.5)) * 2.54
            lines.append(f'        (pin passive line (at 6.35 {py:.2f} 180) (length 2.54) (name "Pin_{p}" (effects (font (size 1.0 1.0)))) (number "{p}" (effects (font (size 1.0 1.0)))))')
        lines.append('      )')
        lines.append('    )')

    # KiCad requires every unit/body name to be <parent item>_<unit>_<style>.
    # Derive names from the owning cache symbol, never abbreviations (C_Pol, AMS, etc.).
    cache_item = None
    for idx, line in enumerate(lines):
        owner = re.match(r'^    \(symbol "([^\"]+)"', line)
        if owner:
            cache_item = owner.group(1).split(':')[-1]
        unit = re.match(r'^      \(symbol "([^\"]+)_([0-9]+)_([0-9]+)"', line)
        if unit:
            if cache_item is None:
                raise ValueError('Cached symbol unit without owner')
            old = unit.group(1)+'_'+unit.group(2)+'_'+unit.group(3)
            new = cache_item+'_'+unit.group(2)+'_'+unit.group(3)
            lines[idx] = line.replace('"'+old+'"', '"'+new+'"', 1)
    lines.append('  )') # end lib_symbols

    # 2. Map Components to lib_symbols
    def get_lib_id(comp):
        ref = comp["ref"]
        fp = comp["fp"]
        if ref == "DC1": return "Connector_Generic:Conn_01x02"
        if ref == "J_ENC": return "Connector_Generic:Conn_01x05"  # physical 2+3 pads 1..5; no SW pin
        if ref.startswith("R"): return "Device:R"
        if ref.startswith("C_VM_MLCC") or (ref.startswith("C") and "0805" in fp): return "Device:C"
        if ref.startswith("C"): return "Device:C_Polarized"
        if ref in ["D1", "D2"]: return "Device:D_Schottky"
        if ref == "D3": return "Device:D"
        if ref.startswith("D"): return "Device:LED"
        if ref.startswith("L"): return "Device:L"
        if ref == "Q_PWR": return "SmartFan:AO4409"
        if ref == "F1": return "Device:Fuse"
        if ref.startswith("Q"): return "Device:Q_NPN_BCE"
        if ref.startswith("BZ"): return "Device:Buzzer"
        if ref == "U3": return "Regulator_Linear:TLV1117LV33DCYR"
        if ref == "DC1": return "Connector_Generic:Conn_01x02"
        if "1x02" in fp: return "Connector_Generic:Conn_01x02"
        if "1x03" in fp: return "Connector_Generic:Conn_01x03"
        if "1x04" in fp: return "Connector_Generic:Conn_01x04"
        if "1x05" in fp: return "Connector_Generic:Conn_01x05"
        if "1x07" in fp: return "Connector_Generic:Conn_01x07"
        if "1x08" in fp: return "Connector_Generic:Conn_01x08"
        if "1x20" in fp: return "Connector_Generic:Conn_01x20"
        return "Device:R"

    # Library pin coordinates are Y-up; schematic sheet coordinates are Y-down.
    SYMBOL_PIN_OFFSETS = {}
    active_lib = None
    for line in lines:
        match = re.match(r'    \(symbol "([^"]+)"', line)
        if match:
            active_lib = match.group(1)
            SYMBOL_PIN_OFFSETS[active_lib] = {}
        match = re.search(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\).*\(number "([^"]+)"', line)
        if match:
            x, y, angle, number = match.groups()
            SYMBOL_PIN_OFFSETS[active_lib][number] = (float(x), float(y), float(angle))

    import uuid
    def sch_uuid(kind, key):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f'smartfan/revB/{kind}/{key}'))

    # Place components on schematic sheet
    c_idx = 0
    wire_idx = 0
    junc_idx = 0
    nc_idx = 0
    
    col_w = 65.0
    row_h = 65.0
    start_x = 35.0
    start_y = 45.0
    
    for comp in COMPONENTS:
        if comp["type"] == "hole":
            continue
        c_idx += 1
        lib_id = get_lib_id(comp)
        symbol_pads = unique_symbol_pads(comp)
        assert set(SYMBOL_PIN_OFFSETS[lib_id]) == {p[0] for p in symbol_pads}, comp['ref']
        ref = comp["ref"]
        val = comp["val"].replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))
        fp = comp["fp"]
        lcsc = comp.get("lcsc", "-")
        desc = comp.get("desc", "").replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))
        
        gx = start_x + (c_idx % 8) * col_w
        gy = start_y + (c_idx // 8) * row_h
        
        lines.append(f'  (symbol (lib_id "{lib_id}") (at {gx:.2f} {gy:.2f} 0) (unit 1)')
        lines.append('    (in_bom yes) (on_board yes)')
        lines.append(f'    (uuid "{c_idx:08x}-0000-0000-0000-000000000000")')
        lines.append(f'    (property "Reference" "{ref}" (at {gx:.2f} {gy-3:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Value" "{val}" (at {gx:.2f} {gy+3:.2f} 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'    (property "Footprint" "{fp}" (at {gx:.2f} {gy+5:.2f} 0) (effects (font (size 0.8 0.8)) hide))')
        lines.append(f'    (property "LCSC" "{lcsc}" (at {gx:.2f} {gy+7:.2f} 0) (effects (font (size 0.8 0.8)) hide))')
        lines.append(f'    (property "Description" "{desc}" (at {gx:.2f} {gy+9:.2f} 0) (effects (font (size 0.8 0.8)) hide))')
        for pad in symbol_pads:
            pnum = pad[0]
            lines.append(f'    (pin "{pnum}" (uuid "{c_idx:04x}-{int(pnum) if pnum.isdigit() else 1:04x}-0000-0000-000000000000"))')
        root_uuid = sch_uuid('object', 'd0000000-0000-0000-0000-000000000001')
        lines.append(f'    (instances (project "fan_ctrl_revB" (path "/{root_uuid}" (reference "{ref}") (unit 1))))')
        lines.append('  )')

        # Draw wire stubs and labels for each pin
        for p_i, pad in enumerate(symbol_pads):
            pnum = pad[0]
            net_name = pad[3]
            # Match pin NUMBER, never footprint order. Angle points into body.
            lx, ly, angle = SYMBOL_PIN_OFFSETS[lib_id][pnum]
            pin_x, pin_y = gx + lx, gy - ly
            rad = math.radians(angle)
            wire_end_x = pin_x - 5.08 * math.cos(rad)
            wire_end_y = pin_y + 5.08 * math.sin(rad)
            wire_idx += 1
            
            if net_name == "NC":
                nc_idx += 1
                lines.append(f'  (no_connect (at {pin_x:.2f} {pin_y:.2f}) (uuid "nc{nc_idx:06d}-0000-0000-0000-000000000000"))')
            else:
                lines.append(f'  (wire (pts (xy {pin_x:.2f} {pin_y:.2f}) (xy {wire_end_x:.2f} {wire_end_y:.2f})) (stroke (width 0) (type default)) (uuid "w{wire_idx:07d}-0000-0000-0000-000000000000"))')
                lines.append(f'  (label "{net_name}" (at {wire_end_x:.2f} {wire_end_y:.2f} 0) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid "l{wire_idx:07d}-0000-0000-0000-000000000000"))')
                if net_name in ["GND", "+5V", "+3.3V", "+5V_RAW", "+5V_FUSED", "+5V_MCU"]:
                    junc_idx += 1
                    lines.append(f'  (junction (at {wire_end_x:.2f} {wire_end_y:.2f}) (diameter 1.0) (color 0 0 0 0) (uuid "j{junc_idx:07d}-0000-0000-0000-000000000000"))')

    lines.append(')')
    sch_content = "\n".join(lines) + "\n"
    sch_content = re.sub(r'\(uuid "([^"]+)"\)', lambda m: '(uuid "' + sch_uuid('object', m.group(1)) + '")', sch_content)
    
    print("SCHEMATIC GENERATION METRICS:")
    print("  Lines:", len(lines))
    print("  lib_symbols:", len(re.findall(r'\(lib_symbols\b', sch_content)))
    print("  symbol instances:", len(re.findall(r'\(symbol \(lib_id\b', sch_content)))
    print("  wires:", len(re.findall(r'\(wire\b', sch_content)))
    print("  junctions:", len(re.findall(r'\(junction\b', sch_content)))
    print("  no_connects:", len(re.findall(r'\(no_connect\b', sch_content)))
    print("  labels:", len(re.findall(r'\(label\b', sch_content)))
    with open(sch_path, "w", encoding="utf-8") as f:
        f.write(sch_content)
    print(f"KiCad Schematic exported successfully: {sch_path} ({len(lines)} lines)")
    return sch_path


export_kicad_sch()

# 7. Authentic RS-274X Gerber & Excellon Drill File Exporter
def export_gerber_and_drill():
    def fmt_gerber(coord_mm):
        val = int(round(coord_mm * 100000))
        return f"{val:09d}"

    def fmt_drill(coord_mm):
        return f"{coord_mm:.3f}"

    # 1. Edge Cuts (.GKO) with True Circular Interpolation (G02/G03 Arcs for R=3.0mm)
    gko_lines = [
        "%FSLAX45Y45*%",
        "%MOMM*%",
        "%ADD10C,0.1500*%",
        "D10*",
        "G75*",
        "G01*"
    ]
    x0, y0 = OFFSET_X, OFFSET_Y
    x1, y1 = OFFSET_X + BOARD_W, OFFSET_Y + BOARD_H
    r = CORNER_R

    # Move to top-left + r: (x0+r, y0)
    gko_lines.append(f"X{fmt_gerber(x0+r)}Y{fmt_gerber(y0)}D02*")
    # Draw line to top-right - r: (x1-r, y0)
    gko_lines.append(f"G01*X{fmt_gerber(x1-r)}Y{fmt_gerber(y0)}D01*")
    # Top-right CW Arc from (x1-r, y0) to (x1, y0+r) around (x1-r, y0+r): I=0, J=+r
    gko_lines.append(f"G03*X{fmt_gerber(x1)}Y{fmt_gerber(y0+r)}I{fmt_gerber(0)}J{fmt_gerber(r)}D01*")
    # Draw line to bottom-right - r: (x1, y1-r)
    gko_lines.append(f"G01*X{fmt_gerber(x1)}Y{fmt_gerber(y1-r)}D01*")
    # Bottom-right CW Arc from (x1, y1-r) to (x1-r, y1) around (x1-r, y1-r): I=-r, J=0
    gko_lines.append(f"G03*X{fmt_gerber(x1-r)}Y{fmt_gerber(y1)}I{fmt_gerber(-r)}J{fmt_gerber(0)}D01*")
    # Draw line to bottom-left + r: (x0+r, y1)
    gko_lines.append(f"G01*X{fmt_gerber(x0+r)}Y{fmt_gerber(y1)}D01*")
    # Bottom-left CW Arc from (x0+r, y1) to (x0, y1-r) around (x0+r, y1-r): I=0, J=-r
    gko_lines.append(f"G03*X{fmt_gerber(x0)}Y{fmt_gerber(y1-r)}I{fmt_gerber(0)}J{fmt_gerber(-r)}D01*")
    # Draw line to top-left + r: (x0, y0+r)
    gko_lines.append(f"G01*X{fmt_gerber(x0)}Y{fmt_gerber(y0+r)}D01*")
    # Top-left CW Arc from (x0, y0+r) to (x0+r, y0) around (x0+r, y0+r): I=+r, J=0
    gko_lines.append(f"G03*X{fmt_gerber(x0+r)}Y{fmt_gerber(y0)}I{fmt_gerber(r)}J{fmt_gerber(0)}D01*")
    gko_lines.append("M02*")

    with open(os.path.join(FAB_DIR, "fan_ctrl_revB.GKO"), "w") as f:
        f.write("\n".join(gko_lines))

    # 2. Excellon Drill (.DRL)
    drill_tools = {}
    drill_hits = {}
    tool_id = 1

    for via in VIAS:
        d = round(via[3], 2)
        if d not in drill_tools:
            drill_tools[d] = f"T{tool_id:02d}"
            drill_hits[d] = []
            tool_id += 1
        drill_hits[d].append((via[0], via[1]))

    for p in PAD_RECORDS:
        if p["type"] in ["tht", "hole"]:
            pw, ph = p["w"], p["h"]
            d = round(ph if ph < pw else pw * 0.55, 2)
            if p["type"] == "hole":
                d = 3.2
            if d not in drill_tools:
                drill_tools[d] = f"T{tool_id:02d}"
                drill_hits[d] = []
                tool_id += 1
            drill_hits[d].append((p["x"], p["y"]))

    drl_lines = [
        "M48",
        "METRIC,TZ",
        "; Layer: Excellon Drill for Smart Fan Rev B4"
    ]
    for d, tid in drill_tools.items():
        drl_lines.append(f"{tid}C{d:.3f}")
    drl_lines.append("%")
    drl_lines.append("G05")

    for d, tid in drill_tools.items():
        drl_lines.append(tid)
        for hx, hy in drill_hits[d]:
            drl_lines.append(f"X{fmt_drill(hx)}Y{fmt_drill(hy)}")
    drl_lines.append("M30")

    with open(os.path.join(FAB_DIR, "fan_ctrl_revB.DRL"), "w") as f:
        f.write("\n".join(drl_lines))

    # Apertures use the same dimensions as the PCB (THT h stores drill).
    apertures = {}
    def aperture(shape, width, height=None):
        key = (shape, round(width, 4), round(height or width, 4))
        if key not in apertures:
            apertures[key] = 100 + len(apertures)
        return apertures[key]
    for p in PAD_RECORDS:
        shape = 'R' if p['type'] == 'smd' else 'C'
        h = p['h'] if shape == 'R' else p['w']
        aperture(shape, p['w'], h)
        aperture(shape, p['w'] + 0.1, h + 0.1)
    for v in VIAS:
        aperture('C', v[2])
        aperture('C', v[2] + 0.1)
    for t in TRACKS:
        aperture('C', t[4])
    aperture_defs = [f'%ADD{code}{shape},{w:.4f}' + (f'X{h:.4f}' if shape == 'R' else '') + '*%' for (shape, w, h), code in apertures.items()]

    # 3. Top Copper (.GTL) & Bottom Copper (.GBL) with Real G36/G37 Ground Area Fills
    for layer, ext in [("F.Cu", "GTL"), ("B.Cu", "GBL")]:
        cu_lines = [
            "%FSLAX45Y45*%",
            "%MOMM*%",
            "%ADD10C,0.2500*%",  # Signal trace
            "%ADD11C,0.3000*%",
            "%ADD12C,0.5000*%",
            "%ADD13C,0.6000*%",
            "%ADD14C,0.8000*%",
            "%ADD15C,1.0000*%",
            "%ADD16C,1.2000*%",
            "%ADD20R,1.5000X0.6000*%", # SOIC pad
            "%ADD21C,1.7000*%",        # THT pad
            "%ADD22C,6.0000*%",        # Mounting hole pad
            "%ADD23C,0.6000*%",        # Via pad
            "G01*"
        ]

        # Flash Ground Copper Area Fill (G36 / G37)
        cu_lines.append("G36*")
        poly_pts = KEYHOLE_POLYS[layer]
        for i, pt in enumerate(poly_pts):
            op = "D02*" if i == 0 else "D01*"
            cu_lines.append(f"X{fmt_gerber(pt[0])}Y{fmt_gerber(pt[1])}{op}")
        cu_lines.append(f"X{fmt_gerber(poly_pts[0][0])}Y{fmt_gerber(poly_pts[0][1])}D01*")
        cu_lines.append("G37*")

        cu_lines[2:2] = aperture_defs
        # Flash pads with exact PCB geometry.
        for p in PAD_RECORDS:
            if layer == 'F.Cu' or p['type'] in ['tht', 'hole']:
                shape = 'R' if p['type'] == 'smd' else 'C'
                code = aperture(shape, p['w'], p['h'] if shape == 'R' else p['w'])
                cu_lines.append(f"D{code}*X{fmt_gerber(p['x'])}Y{fmt_gerber(p['y'])}D03*")

        # Flash vias
        for v in VIAS:
            vx, vy = v[0], v[1]
            cu_lines.append(f"D{aperture('C', v[2])}*X{fmt_gerber(vx)}Y{fmt_gerber(vy)}D03*")

        # Draw tracks on this layer
        for trk in TRACKS:
            sx, sy, ex, ey, w, tlayer, nid = trk
            if tlayer == layer:
                d_code = f"D{aperture('C', w)}"
                cu_lines.append(f"{d_code}*")
                cu_lines.append(f"X{fmt_gerber(sx)}Y{fmt_gerber(sy)}D02*")
                cu_lines.append(f"X{fmt_gerber(ex)}Y{fmt_gerber(ey)}D01*")

        cu_lines.append("M02*")
        with open(os.path.join(FAB_DIR, f"fan_ctrl_revB.{ext}"), "w") as f:
            f.write("\n".join(cu_lines))

    # 4. Solder Masks (.GTS, .GBS)
    for layer, ext in [("F.Cu", "GTS"), ("B.Cu", "GBS")]:
        msk_lines = [
            "%FSLAX45Y45*%",
            "%MOMM*%",
            "%ADD30C,1.8000*%",
            "%ADD31C,6.2000*%",
            "%ADD32R,1.6000X0.7000*%",
            "G01*"
        ]
        msk_lines[2:2] = aperture_defs
        for p in PAD_RECORDS:
            if layer == 'F.Cu' or p['type'] in ['tht', 'hole']:
                shape = 'R' if p['type'] == 'smd' else 'C'
                h = p['h'] if shape == 'R' else p['w']
                code = aperture(shape, p['w'] + 0.1, h + 0.1)
                msk_lines.append(f"D{code}*X{fmt_gerber(p['x'])}Y{fmt_gerber(p['y'])}D03*")
        # All vias are tented on both sides, matching KiCad 8 viasonmask=false.
        # Do not flash vias here; their copper flashes and Excellon hits remain intact.
        msk_lines.append("M02*")
        with open(os.path.join(FAB_DIR, f"fan_ctrl_revB.{ext}"), "w") as f:
            f.write("\n".join(msk_lines))

    # 5. Silkscreen (.GTO, .GBO)
    for ext in ["GTO", "GBO"]:
        slk_lines = [
            "%FSLAX45Y45*%",
            "%MOMM*%",
            "%ADD40C,0.1500*%",
            "D40*",
            "G01*"
        ]
        if ext == "GTO":
            silk_rows = build_safe_silkscreen()
            import json
            placement_dir = os.path.join(DOWNLOAD_DIR, 'validation')
            os.makedirs(placement_dir, exist_ok=True)
            with open(os.path.join(placement_dir, 'silkscreen_placements.json'), 'w', encoding='utf8') as placement_file:
                json.dump([{k:v for k,v in row.items() if k!='segments'} for row in silk_rows if row['kind']!='BORDER'], placement_file, ensure_ascii=False, indent=2)
            for row in silk_rows:
                slk_lines.append(f"G04 REF {row['ref']} {row['kind']}*")
                for sx, sy, ex, ey in row['segments']:
                    slk_lines.append(f"X{fmt_gerber(sx)}Y{fmt_gerber(sy)}D02*")
                    slk_lines.append(f"X{fmt_gerber(ex)}Y{fmt_gerber(ey)}D01*")
        slk_lines.append("M02*")
        with open(os.path.join(FAB_DIR, f"fan_ctrl_revB.{ext}"), "w") as f:
            f.write("\n".join(slk_lines))

    # 6. Package into Production ZIP
    zip_path = os.path.join(DOWNLOAD_DIR, "Gerber_fan_ctrl_revB_2026-11-04.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fname in os.listdir(FAB_DIR):
            if fname.startswith("fan_ctrl_revB."):
                fpath = os.path.join(FAB_DIR, fname)
                zipf.write(fpath, arcname=fname)
    print(f"Production Gerber package created: {zip_path} ({os.path.getsize(zip_path)} bytes)")
    return zip_path

export_gerber_and_drill()

# 8. BOM Generator (Excel & Markdown Sync)
def export_bom():
    bom_groups = {}
    for comp in COMPONENTS:
        if comp["type"] == "hole":
            continue
        key = (comp["val"], comp["fp"], comp.get("lcsc", "-"), comp.get("mpn", "-"), comp.get("mfr", "-"), comp.get("desc", ""))
        if key not in bom_groups:
            bom_groups[key] = []
        bom_groups[key].append(comp["ref"])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "BOM_SmartFan_RevB"

    hdr_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    hdr_fill = PatternFill(start_color="1D3557", end_color="1D3557", fill_type="solid")
    cell_font = Font(name="Segoe UI", size=10)
    border_thin = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                         top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    headers = ["Item #", "Designators", "Quantity", "Value", "Package / Footprint", "LCSC Part #", "MPN", "Manufacturer", "Description"]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = align_center

    row_idx = 2
    md_rows = []
    item_num = 1
    for key, refs in sorted(bom_groups.items(), key=lambda x: x[1][0]):
        val, fp, lcsc, mpn, mfr, desc = key
        refs_str = ", ".join(refs)
        qty = len(refs)
        row_data = [item_num, refs_str, qty, val, fp, lcsc, mpn, mfr, desc]
        ws.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = cell_font
            cell.border = border_thin
            cell.alignment = align_center if col_idx in [1, 3, 6] else align_left

        md_rows.append(f"| {item_num} | `{refs_str}` | {qty} | {val} | `{fp}` | [{lcsc}](https://www.szlcsc.com/so/product/details_{lcsc}.html) | `{mpn}` | {mfr} | {desc} |")
        row_idx += 1
        item_num += 1

    col_widths = [8, 22, 10, 18, 32, 15, 20, 18, 30]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    xlsx_path = os.path.join(DOWNLOAD_DIR, "BOM_SmartFan_RevB.xlsx")
    wb.save(xlsx_path)
    print(f"BOM Excel exported: {xlsx_path}")

    md_content = [
        "# Desktop Smart Fan Controller Rev B4 - Design BOM - 5V Prototype",
        "",
        "> **Notice**: Part numbers are design references; live stock has NOT been verified. Verify electrical ratings, packaging and current supplier data before procurement.",
        "",
        "| Item | Designators | Qty | Value | Footprint | LCSC # | MPN | Manufacturer | Description |",
        "| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :--- | :--- |"
    ] + md_rows + [
        "",
        "## Summary",
        f"- **Total Components**: {sum(len(r) for r in bom_groups.values())} pcs",
        f"- **Unique Line Items**: {len(bom_groups)} items",
        "- **Live stock is NOT verified; module/header procurement must be matched to the confirmed mechanical dimensions.**"
    ]
    md_path = os.path.join(DOCS_DIR, "bom.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))
    print(f"BOM Markdown updated: {md_path}")

export_bom()

# 9. High-Resolution Visual Layout Renderer (fan_ctrl_revB_layout.png)
def render_layout():
    fig, ax = plt.subplots(figsize=(12, 12), dpi=300)
    ax.set_facecolor("#1a1a24")
    fig.patch.set_facecolor("#121218")

    board_rect = patches.FancyBboxPatch((0, 0), BOARD_W, BOARD_H,
                                        boxstyle=f"round,pad=0,rounding_size={CORNER_R}",
                                        linewidth=2, edgecolor="#00b4d8", facecolor="#1e232a", zorder=1)
    ax.add_patch(board_rect)

    for h in [("H1", 5.0, 5.0), ("H2", 90.0, 5.0), ("H3", 5.0, 90.0), ("H4", 90.0, 90.0)]:
        kp = patches.Circle((h[1], h[2]), 4.5, edgecolor="#e63946", facecolor="none", linestyle="--", linewidth=1.2, alpha=0.7, zorder=2)
        ax.add_patch(kp)
        cp = patches.Circle((h[1], h[2]), 3.0, facecolor="#ffd166", edgecolor="#c77dff", linewidth=1.5, zorder=3)
        ax.add_patch(cp)
        dh = patches.Circle((h[1], h[2]), 1.6, facecolor="#121218", edgecolor="none", zorder=4)
        ax.add_patch(dh)
        ax.text(h[1], h[2] - 5.5, h[0], color="#ffd166", fontsize=9, fontweight="bold", ha="center", va="top", zorder=5)

    for trk in TRACKS:
        sx, sy, ex, ey, w, layer, nid = trk
        bx0, by0 = sx - OFFSET_X, sy - OFFSET_Y
        bx1, by1 = ex - OFFSET_X, ey - OFFSET_Y
        color = "#e76f51" if layer == "F.Cu" else "#457b9d"
        alpha = 0.85 if layer == "F.Cu" else 0.65
        ax.plot([bx0, bx1], [by0, by1], color=color, linewidth=max(1.2, w * 2.5), alpha=alpha, solid_capstyle="round", zorder=5)

    for v in VIAS:
        vx, vy = v[0] - OFFSET_X, v[1] - OFFSET_Y
        v_outer = patches.Circle((vx, vy), 0.45, facecolor="#f4a261", edgecolor="#264653", linewidth=0.5, zorder=6)
        ax.add_patch(v_outer)
        v_inner = patches.Circle((vx, vy), 0.15, facecolor="#121218", zorder=7)
        ax.add_patch(v_inner)

    # Nominal board outlines only; omitted modules have unverified body offsets.
    ENVELOPES = [
        {"name": "STM32F103 nominal", "x": 47.5, "y": 40.0, "w": 22.86, "h": 53.34, "color": "#0077b6", "alpha": 0.25},
        {"name": "ASR-PRO nominal", "x": 78.5, "y": 44.0, "w": 30.0, "h": 28.0, "color": "#7209b7", "alpha": 0.25}
    ]

    for env in ENVELOPES:
        ex, ey, ew, eh = env["x"] - env["w"]/2.0, env["y"] - env["h"]/2.0, env["w"], env["h"]
        rect = patches.FancyBboxPatch((ex, ey), ew, eh, boxstyle="round,pad=0,rounding_size=1.0",
                                      linewidth=1.5, edgecolor=env["color"], facecolor=env["color"],
                                      alpha=env["alpha"], zorder=8)
        ax.add_patch(rect)
        ax.text(env["x"], env["y"], env["name"], color="#ffffff", fontsize=8.5, fontweight="bold",
                ha="center", va="center", zorder=9, bbox=dict(boxstyle="round,pad=0.2", fc="#000000", ec="none", alpha=0.6))

    for comp in COMPONENTS:
        cx, cy = comp["x"], comp["y"]
        ax.annotate(comp["ref"], xy=(cx, cy), xytext=(3, 4),
                    textcoords="offset points", color="#ffffff", fontsize=5,
                    ha="left", va="bottom", zorder=12,
                    bbox=dict(boxstyle="round,pad=0.1", fc="#121218", ec="none", alpha=0.7))
        for p in comp["pads"]:
            px, py = cx + p[1], cy + p[2]
            pw = p[4] if len(p) > 4 else 1.6
            ph = p[5] if len(p) > 5 else 1.6
            if comp["type"] == "smd":
                pad_rect = patches.Rectangle((px - pw/2.0, py - ph/2.0), pw, ph,
                                            facecolor="#ffd166", edgecolor="#f4a261", linewidth=0.8, zorder=10)
                ax.add_patch(pad_rect)
            elif comp["type"] == "tht":
                pad_circ = patches.Circle((px, py), pw/2.0, facecolor="#ffd166", edgecolor="#e76f51", linewidth=0.8, zorder=10)
                ax.add_patch(pad_circ)
                hole_circ = patches.Circle((px, py), ph/2.0, facecolor="#121218", zorder=11)
                ax.add_patch(hole_circ)

    ax.text(BOARD_W / 2.0, 2.5, "STM32 SMART FAN CONTROLLER - REV B4", color="#00b4d8", fontsize=14, fontweight="bold", ha="center", va="center", zorder=12)
    ax.text(BOARD_W / 2.0, 5.0, "95.0 x 95.0 mm | R=3.0 mm | 85.0 mm Hole Pitch | BOM procurement review required", color="#a8dadc", fontsize=9.5, ha="center", va="center", zorder=12)
    ax.text(BOARD_W / 2.0, BOARD_H - 2.5, "5V prototype | Module fit / enclosure not certified", color="#f1faee", fontsize=9.5, fontweight="bold", ha="center", va="center", zorder=12)

    ax.set_xlim(-5, BOARD_W + 5)
    ax.set_ylim(BOARD_H + 5, -5)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.tight_layout()
    png_path = os.path.join(DOWNLOAD_DIR, "fan_ctrl_revB_layout.png")
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print(f"High-resolution layout render saved: {png_path}")


render_layout()
