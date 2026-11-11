"""
Script: tools/router_engine.py
Implements a 2-layer grid A* router.
"""
import math
import heapq
import re
import os

def solve_routing():
    # Grid definition: 100 to 185 mm with 0.5mm step
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

    # Build obstacle grid: grid[layer][gx][gy] = net_id (0 = free, >0 = occupied by net, -1 = blocked for all)
    # Layer 0: F.Cu, Layer 1: B.Cu
    grid = [[0 for _ in range(NY)] for _ in range(NX)], [[0 for _ in range(NY)] for _ in range(NX)]

    # Mark pad obstacles
    for p in pads:
        ax, ay = p['x'], p['y']
        # radius to block
        r = max(p['sx'], p['sy']) / 2.0 + 0.35  # clearance 0.35 mm
        gr = int(math.ceil(r / RES))
        cgx, cgy = xy2grid(ax, ay)
        for dx in range(-gr, gr + 1):
            for dy in range(-gr, gr + 1):
                gx, gy = cgx + dx, cgy + dy
                if 0 <= gx < NX and 0 <= gy < NY:
                    cx, cy = grid2xy(gx, gy)
                    if math.hypot(cx - ax, cy - ay) <= r:
                        # Pad occupies layers
                        if p['type'] == 'thru_hole' or '*.Cu' in p['layers']:
                            grid[0][gx][gy] = p['net'] if grid[0][gx][gy] == 0 else -1
                            grid[1][gx][gy] = p['net'] if grid[1][gx][gy] == 0 else -1
                        elif 'F.Cu' in p['layers']:
                            grid[0][gx][gy] = p['net'] if grid[0][gx][gy] == 0 else -1
                        elif 'B.Cu' in p['layers']:
                            grid[1][gx][gy] = p['net'] if grid[1][gx][gy] == 0 else -1

    print(f"Obstacle grid populated with {len(pads)} pads.")

    # A* Search function
    def astar(start_pt, target_pt, net_id, preferred_layer=0):
        # start_pt: (gx, gy, l), target_pt: (gx, gy, l) or target cells set
        sx, sy, sl = start_pt
        tx, ty = target_pt[:2]
        
        frontier = [(0, 0, sx, sy, sl, [(sx, sy, sl)])]
        cost_so_far = {(sx, sy, sl): 0}
        
        while frontier:
            f, cost, cx, cy, cl, path = heapq.heappop(frontier)
            
            if cx == tx and cy == ty:
                return path
            
            # Neighbors: 4 planar moves + layer change (via)
            # Planar moves
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < NX and 0 <= ny < NY:
                    cell_net = grid[cl][nx][ny]
                    if cell_net == 0 or cell_net == net_id:
                        # directional cost penalty (F.Cu prefers horizontal, B.Cu prefers vertical)
                        bend_penalty = 0.1
                        layer_penalty = 0.2 if cl != preferred_layer else 0.0
                        new_cost = cost + 1.0 + bend_penalty + layer_penalty
                        state = (nx, ny, cl)
                        if state not in cost_so_far or new_cost < cost_so_far[state]:
                            cost_so_far[state] = new_cost
                            h = (abs(nx - tx) + abs(ny - ty)) * 1.0
                            heapq.heappush(frontier, (new_cost + h, new_cost, nx, ny, cl, path + [state]))
            
            # Via (change layer)
            other_l = 1 - cl
            # Via needs clearance on both layers
            via_ok = (grid[cl][cx][cy] in (0, net_id)) and (grid[other_l][cx][cy] in (0, net_id))
            if via_ok:
                via_cost = cost + 5.0  # via penalty
                state = (cx, cy, other_l)
                if state not in cost_so_far or via_cost < cost_so_far[state]:
                    cost_so_far[state] = via_cost
                    h = (abs(cx - tx) + abs(cy - ty)) * 1.0
                    heapq.heappush(frontier, (via_cost + h, via_cost, cx, cy, other_l, path + [state]))
                    
        return None

    # Test route
    p1 = xy2grid(134.38, 116.0)
    p2 = xy2grid(166.0, 114.0)
    path = astar((p1[0], p1[1], 0), (p2[0], p2[1], 0), 5)
    print("Test route path length:", len(path) if path else "FAILED")

solve_routing()
