import os
import zipfile
import shutil

ROOT_DIR = "D:/smart_fans"
STL_DIR = os.path.join(ROOT_DIR, "mechanical/stl/print")
ZIP_DIR = os.path.join(ROOT_DIR, "mechanical")
DOWNLOAD_DIR = "d:/下载"

f1 = os.path.join(STL_DIR, "Part1_Base_Assembly_Kit_100mm.stl")
f2 = os.path.join(STL_DIR, "Part2_Fan_Gimbal_Kit_100mm.stl")

zip_path = os.path.join(ZIP_DIR, "3D_Print_JLC_Free_Coupon_2Pieces.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(f1, arcname="Part1_Base_Assembly_Kit_100mm.stl")
    zf.write(f2, arcname="Part2_Fan_Gimbal_Kit_100mm.stl")

# Copy to downloads
shutil.copy(zip_path, os.path.join(DOWNLOAD_DIR, "3D_Print_JLC_Free_Coupon_2Pieces.zip"))
shutil.copy(f1, os.path.join(DOWNLOAD_DIR, "Part1_Base_Assembly_Kit_100mm.stl"))
shutil.copy(f2, os.path.join(DOWNLOAD_DIR, "Part2_Fan_Gimbal_Kit_100mm.stl"))

print(f"Created package: {zip_path}")
print(f"Copied to {DOWNLOAD_DIR}:")
print(f"  - Part1_Base_Assembly_Kit_100mm.stl")
print(f"  - Part2_Fan_Gimbal_Kit_100mm.stl")
print(f"  - 3D_Print_JLC_Free_Coupon_2Pieces.zip")
