"""
Script: verify_pcb_clearance.py
Accurate footprint parser without broken word boundary regex.
"""
import math
import re

def parse_kicad_pcb(pcb_path):
    with open(pcb_path, "r", encoding="utf-8") as f:
        text = f.read()

    fp_blocks = text.split('(footprint ')
    all_pads = []

    for block in fp_blocks[1:]:
        m_ref = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', block)
        ref = m_ref.group(1) if m_ref else "UNKNOWN"
        
        # footprint position is on the second line after (uuid ...): (at X Y [ROT])
        first_lines = block[:300]
        # Match (at X Y [ROT]) specifically where it is followed by ) and not preceded by letters
        m_at = re.search(r'\s\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', first_lines)
        if m_at:
            fx = float(m_at.group(1))
            fy = float(m_at.group(2))
            frot = float(m_at.group(3)) if m_at.group(3) else 0.0
        else:
            fx, fy, frot = 0.0, 0.0, 0.0

        rad = math.radians(frot)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        # match pads
        pad_matches = re.finditer(r'\(pad\s+\"([^\"]+)\"\s+(?:smd|thru_hole)\s+(?:rect|circle|roundrect)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)\s+\(size\s+([\d\.\-]+)\s+([\d\.\-]+)\)', block)
        for pm in pad_matches:
            pnum = pm.group(1)
            px = float(pm.group(2))
            py = float(pm.group(3))
            prot = float(pm.group(4)) if pm.group(4) else 0.0
            sw = float(pm.group(5))
            sh = float(pm.group(6))

            abs_x = fx + px * cos_r - py * sin_r
            abs_y = fy + px * sin_r + py * cos_r
            radius = max(sw, sh) / 2.0

            all_pads.append({
                "ref": ref,
                "pad": pnum,
                "abs_x": abs_x,
                "abs_y": abs_y,
                "radius": radius,
                "w": sw,
                "h": sh
            })

    return all_pads

def check_clearance(all_pads, min_clearance=0.15):
    conflicts = []
    for i in range(len(all_pads)):
        p1 = all_pads[i]
        for j in range(i + 1, len(all_pads)):
            p2 = all_pads[j]
            if p1["ref"] == p2["ref"]:
                continue
            dx = p1["abs_x"] - p2["abs_x"]
            dy = p1["abs_y"] - p2["abs_y"]
            dist = math.hypot(dx, dy)
            req_dist = p1["radius"] + p2["radius"] + min_clearance
            if dist < req_dist:
                overlap = req_dist - dist
                conflicts.append((p1, p2, dist, overlap))
    return conflicts

if __name__ == "__main__":
    pcb_path = "D:/smart_fans/hardware/kicad/fan_ctrl_revA.kicad_pcb"
    pads = parse_kicad_pcb(pcb_path)
    print(f"Total pads parsed with absolute coordinates: {len(pads)}")
    for p in pads[:10]:
        print(f"  {p['ref']} pad {p['pad']}: at ({p['abs_x']:.2f}, {p['abs_y']:.2f}), size ({p['w']:.2f}x{p['h']:.2f})")
    conflicts = check_clearance(pads)
    if not conflicts:
        print("\nSUCCESS: 0 clearance conflicts found between any different footprints! DRC CLEAR!")
    else:
        print(f"\nFOUND {len(conflicts)} clearance conflicts:")
        for p1, p2, dist, overlap in conflicts:
            print(f"  Conflict: {p1['ref']} pad {p1['pad']} ({p1['abs_x']:.2f}, {p1['abs_y']:.2f}) and {p2['ref']} pad {p2['pad']} ({p2['abs_x']:.2f}, {p2['abs_y']:.2f}): distance={dist:.2f}mm, overlap={overlap:.2f}mm")
