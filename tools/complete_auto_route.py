"""
Script: tools/complete_auto_route.py
Routes all non-GND nets on the PCB using grid maze routing and outputs valid KiCad track segments and vias.
"""
import math
import heapq
import re
import os

X_MIN, X_MAX = 99.0, 186.0
Y_MIN, Y_MAX = 99.0, 186.0
RES = 0.5
NX = int(round((X_MAX - X_MIN) / RES)) + 1
NY = int(round((Y_MAX - Y_MIN) / RES)) + 1

def xy2grid(x, y):
    gx = int(round((x - X_MIN) / RES))
    gy = int(round((y - Y_MIN) / RES))
    return max(0, min(NX - 1, gx)), max(0, min(NY - 1, gy))

def grid2xy(gx, gy):
    return X_MIN + gx * RES, Y_MIN + gy * RES

# Parse pads from fan_ctrl_revA.kicad_pcb
with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
fps = []
curr = None
for line in lines:
    if line.strip().startswith('(footprint '):
        curr = {'header': line, 'lines': []}
        fps.append(curr)
    elif curr is not None:
        curr['lines'].append(line)
        if line.strip() == ')':
            curr = None

pads = []
for fp in fps:
    full = "\n".join(fp['lines'])
    ref_m = re.search(r'\(fp_text\s+reference\s+\"([^\"]+)\"', full)
    ref = ref_m.group(1) if ref_m else "?"
    at_m = re.search(r'\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)', fp['header'] + "\n" + full)
    fx = float(at_m.group(1)) if at_m else 0
    fy = float(at_m.group(2)) if at_m else 0
    frot = float(at_m.group(3)) if at_m and at_m.group(3) else 0

    for pm in re.finditer(r'\(pad\s+\"([^\"]+)\"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)\s+\(size\s+([\d\.\-]+)\s+([\d\.\-]+)\)[\s\S]*?\(layers\s+([^\)]+)\)(?:[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"\))?', full):
        pnum = pm.group(1)
        ptype = pm.group(2)
        pshape = pm.group(3)
        lx = float(pm.group(4))
        ly = float(pm.group(5))
        sx = float(pm.group(7))
        sy = float(pm.group(8))
        layers = pm.group(9)
        nid = int(pm.group(10)) if pm.group(10) else 0
        nname = pm.group(11) if pm.group(11) else ""

        rad = math.radians(frot)
        ax = fx + (lx * math.cos(rad) - ly * math.sin(rad))
        ay = fy + (lx * math.sin(rad) + ly * math.cos(rad))
        pads.append({
            'ref': ref, 'num': pnum, 'type': ptype, 'shape': pshape,
            'x': ax, 'y': ay, 'sx': sx, 'sy': sy, 'layers': layers,
            'net': nid, 'netname': nname
        })

# Map pads by net
net_pads = {}
for p in pads:
    if p['net'] > 1: # ignore unconnected (0) and GND (1, handled by ground plane)
        net_pads.setdefault(p['net'], []).append(p)

print(f"Total non-GND nets to route: {len(net_pads)}")

# Obstacle grid: grid[layer][gx][gy]
grid = [[0 for _ in range(NY)] for _ in range(NX)], [[0 for _ in range(NY)] for _ in range(NX)]

# Populate obstacles
for p in pads:
    ax, ay = p['x'], p['y']
    r = max(p['sx'], p['sy']) / 2.0 + 0.30
    gr = int(math.ceil(r / RES))
    cgx, cgy = xy2grid(ax, ay)
    for dx in range(-gr, gr + 1):
        for dy in range(-gr, gr + 1):
            gx, gy = cgx + dx, cgy + dy
            if 0 <= gx < NX and 0 <= gy < NY:
                cx, cy = grid2xy(gx, gy)
                if math.hypot(cx - ax, cy - ay) <= r:
                    if p['type'] == 'thru_hole' or '*.Cu' in p['layers']:
                        grid[0][gx][gy] = p['net'] if grid[0][gx][gy] == 0 else -1
                        grid[1][gx][gy] = p['net'] if grid[1][gx][gy] == 0 else -1
                    elif 'F.Cu' in p['layers']:
                        grid[0][gx][gy] = p['net'] if grid[0][gx][gy] == 0 else -1
                    elif 'B.Cu' in p['layers']:
                        grid[1][gx][gy] = p['net'] if grid[1][gx][gy] == 0 else -1

def astar_route(src_pt, dst_pts, net_id, width):
    # dst_pts can be a set of (gx, gy, l) points already in this net tree
    sx, sy, sl = src_pt
    frontier = [(0, 0, sx, sy, sl, [(sx, sy, sl)])]
    visited = {(sx, sy, sl): 0}
    
    # target set
    dst_coords = {(gx, gy) for gx, gy, l in dst_pts}
    
    def min_h(gx, gy):
        return min(abs(gx - tx) + abs(gy - ty) for tx, ty in dst_coords)
    
    while frontier:
        f, cost, cx, cy, cl, path = heapq.heappop(frontier)
        
        if (cx, cy) in dst_coords:
            return path
        
        # 4 Planar moves
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < NX and 0 <= ny < NY:
                cell_val = grid[cl][nx][ny]
                if cell_val == 0 or cell_val == net_id:
                    new_cost = cost + 1.0
                    state = (nx, ny, cl)
                    if state not in visited or new_cost < visited[state]:
                        visited[state] = new_cost
                        h = min_h(nx, ny)
                        heapq.heappush(frontier, (new_cost + h, new_cost, nx, ny, cl, path + [state]))
        
        # Layer change via
        other_l = 1 - cl
        if grid[cl][cx][cy] in (0, net_id) and grid[other_l][cx][cy] in (0, net_id):
            via_cost = cost + 4.0
            state = (cx, cy, other_l)
            if state not in visited or via_cost < visited[state]:
                visited[state] = via_cost
                h = min_h(cx, cy)
                heapq.heappush(frontier, (via_cost + h, via_cost, cx, cy, other_l, path + [state]))
                
    return None

# Route nets by priority: power nets first, then signals
# Define width per net
net_widths = {
    2: 1.0,  # 12V
    23: 1.0, # XL1509 SW
    3: 0.8,  # 5V
    4: 0.5,  # 3.3V
    24: 0.5, # Buzzer drv
    25: 0.5  # Fan PWM drv
}

routed_segments = []
vias = []

success_count = 0
fail_count = 0

for nid, plist in sorted(net_pads.items(), key=lambda item: (0 if item[0] in [2, 23, 3, 4] else 1, item[0])):
    width = net_widths.get(nid, 0.3)
    nname = plist[0]['netname']
    
    # MST routing between pads in this net
    connected_points = []
    
    # Start with first pad
    p0 = plist[0]
    gx0, gy0 = xy2grid(p0['x'], p0['y'])
    # start layer: SMD on F.Cu starts at 0, thru_hole can start at 0
    l0 = 0 if 'F.Cu' in p0['layers'] or p0['type'] == 'thru_hole' else 1
    connected_points.append((gx0, gy0, l0))
    
    # Sequentially connect remaining pads to closest connected point
    remaining_pads = plist[1:]
    while remaining_pads:
        # find closest pad to connected_points
        best_p = None
        best_dist = 1e9
        for p in remaining_pads:
            gx, gy = xy2grid(p['x'], p['y'])
            d = min(abs(gx - cgx) + abs(gy - cgy) for cgx, cgy, cl in connected_points)
            if d < best_dist:
                best_dist = d
                best_p = p
        
        remaining_pads.remove(best_p)
        bgx, bgy = xy2grid(best_p['x'], best_p['y'])
        bl = 0 if 'F.Cu' in best_p['layers'] or best_p['type'] == 'thru_hole' else 1
        
        path = astar_route((bgx, bgy, bl), connected_points, nid, width)
        if path:
            success_count += 1
            # Mark path in grid and record segments
            for i in range(len(path) - 1):
                c1 = path[i]
                c2 = path[i + 1]
                if c1[2] != c2[2]:
                    # Via!
                    vx, vy = grid2xy(c1[0], c1[1])
                    vias.append((vx, vy, nid))
                else:
                    x1, y1 = grid2xy(c1[0], c1[1])
                    x2, y2 = grid2xy(c2[0], c2[1])
                    layer_str = "F.Cu" if c1[2] == 0 else "B.Cu"
                    routed_segments.append((nid, width, layer_str, x1, y1, x2, y2))
                
                # mark in grid
                grid[c1[2]][c1[0]][c1[1]] = nid
                grid[c2[2]][c2[0]][c2[1]] = nid
                connected_points.append(c1)
            connected_points.append(path[-1])
        else:
            fail_count += 1
            print(f"FAILED to route Net {nid} ({nname}) to {best_p['ref']}.{best_p['num']}")

print(f"Routing finished: {success_count} connections routed, {fail_count} failed.")
print(f"Total track segments: {len(routed_segments)}, Vias: {len(vias)}")
