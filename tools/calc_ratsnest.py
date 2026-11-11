with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Extract net definitions
nets = {}
for m in re.finditer(r'\(net\s+(\d+)\s+\"([^\"]*)\"\)', text[:2000]):
    nets[int(m.group(1))] = m.group(2)

# Extract pads
pad_lines = re.findall(r'\(pad\s+.*?\)', text)
# extract pad with net
pads = re.findall(r'\(pad\s+\"([^\"]+)\"[\s\S]*?\(net\s+(\d+)', text)

pad_by_net = {}
for p_num, net_id in pads:
    nid = int(net_id)
    pad_by_net.setdefault(nid, []).append(p_num)

total_ratsnest_lines = 0
for nid, plist in sorted(pad_by_net.items()):
    if nid == 0:
        continue
    req_conn = len(plist) - 1
    total_ratsnest_lines += req_conn
    print(f"Net {nid} ({nets.get(nid, '')}): {len(plist)} pads -> requires {req_conn} connections")

print(f"\nTotal required connections across all nets: {total_ratsnest_lines}")
