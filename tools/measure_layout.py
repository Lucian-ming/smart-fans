# -*- coding: utf-8 -*-
"""Measure module envelope rectangles from the layout PNG by color segmentation,
then map px -> mm using the 98x98 board outline."""
import numpy as np
from PIL import Image
from scipy import ndimage

im = Image.open(r"D:/下载/fan_ctrl_revB_layout.png").convert("RGB")
a = np.asarray(im)
H, W, _ = a.shape
print("image", W, H)

# board outline: the yellow frame. Detect yellow-ish pixels
r, g, b = a[:,:,0].astype(int), a[:,:,1].astype(int), a[:,:,2].astype(int)
yellow = (r > 150) & (g > 120) & (b < 110) & (r > b + 60)
ys, xs = np.where(yellow)
print("yellow bbox", xs.min(), xs.max(), ys.min(), ys.max())

# the board area is the region inside the yellow frame; use the frame bbox
bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
print("frame size px:", bx1-bx0, by1-by0, " => px/mm", (bx1-bx0)/98.0, (by1-by0)/98.0)

def px2mm(x, y):
    return ((x-bx0)/((bx1-bx0)/98.0), (y-by0)/((by1-by0)/98.0))

# sample the distinct flat colors of module envelopes
# take a coarse color histogram
flat = a.reshape(-1,3)
cols, counts = np.unique(flat, axis=0, return_counts=True)
order = np.argsort(-counts)
print("\nTop colors:")
for i in order[:25]:
    c = cols[i]; n = counts[i]
    print(f"  #{c[0]:02x}{c[1]:02x}{c[2]:02x}  {n}")

# module colors are semi-transparent fills; examine known centers
probe = {
 'STM32_blue': (40.38+11, 46.5),   # local mm
 'TB6612': (18, 38),
 'ASR': (80, 40),
 'OLED': (80, 72),
 'PAJ': (24, 72),
 'KEY1': (17.5, 83),
 'KEY2': (34, 83),
 'ENC': (53, 82),
}
print("\nprobe colors (mm->px):")
for k,(xmm,ymm) in probe.items():
    x = int(bx0 + xmm*(bx1-bx0)/98.0); y = int(by0 + ymm*(by1-by0)/98.0)
    print(f"  {k:11s} ({xmm},{ymm}) px({x},{y}) = #{a[y,x,0]:02x}{a[y,x,1]:02x}{a[y,x,2]:02x}")
