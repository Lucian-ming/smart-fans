with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re
pad_blocks = re.findall(r'\(pad\s+.*?\)', text)
gnd_count = text.count('(net 1 "GND")')
print("GND pad count:", gnd_count)

# Let's count pads for each net
net_counts = {}
for m in re.finditer(r'\(net\s+(\d+)\s+\"([^\"]*)\"\)', text):
    n = m.group(1)
    name = m.group(2)
    net_counts[n] = (name, net_counts.get(n, (name, 0))[1] + 1)

for n, (name, cnt) in sorted(net_counts.items(), key=lambda x: int(x[0])):
    print(f"Net {n} ({name}): {cnt} references")
