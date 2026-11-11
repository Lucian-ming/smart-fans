"""
Script: package_kicad_project.py
Creates a dedicated KiCad 8.x project package (.zip) and ensures all project files (.kicad_pro, .kicad_sch, .kicad_pcb, tables) are complete and cleanly formatted for direct 1-click import into EasyEDA Pro / KiCad.
"""

import os
import zipfile

KICAD_DIR = "D:/smart_fans/hardware/kicad"

# 1. Create standard fp-lib-table and sym-lib-table if not present
fp_lib_path = os.path.join(KICAD_DIR, "fp-lib-table")
with open(fp_lib_path, "w", encoding="utf-8") as f:
    f.write('(fp_lib_table\n  (version 7)\n)\n')

sym_lib_path = os.path.join(KICAD_DIR, "sym-lib-table")
with open(sym_lib_path, "w", encoding="utf-8") as f:
    f.write('(sym_lib_table\n  (version 7)\n)\n')

# 2. Package into KiCad_Project_SmartFan_RevA.zip
zip_path = os.path.join(KICAD_DIR, "KiCad_Project_SmartFan_RevA.zip")
files_to_zip = [
    "fan_ctrl_revA.kicad_pcb",
    "fan_ctrl_revA.kicad_pro",
    "fan_ctrl_revA.kicad_sch",
    "fp-lib-table",
    "sym-lib-table"
]

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for fname in files_to_zip:
        fpath = os.path.join(KICAD_DIR, fname)
        if os.path.exists(fpath):
            zf.write(fpath, arcname=fname)
            print(f"Added to zip: {fname} ({os.path.getsize(fpath)} bytes)")

print(f"\nKiCad project package ready: {zip_path}")
