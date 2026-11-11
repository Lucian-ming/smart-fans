import json, math, itertools
D = json.load(open("tools/revb2.json"))
fps, segs, vias, nets = D['fps'], D['segs'], D['vias'], {int(k): v for k, v in D['nets'].items()}
byname = {f['ref']: f for f in fps if f['ref']}

print("== FOOTPRINT TABLE ==")
for f in sorted(fps, key=lambda z: str(z['ref'])):
    lc = f.get('lcsc') or '-'
    print(f"{str(f['ref']):8s} {str(f['val'])[:20]:20s} ({f['x']:7.2f},{f['y']:7.2f}) rot={f['rot']:5.1f} lib={f['lib'][:44]:44s} LCSC={lc:9s} pads={len(f['pads'])}")

print("\n== KEY PART PADS ==")
for r in ['J_MCU_L', 'J_MCU_R', 'U2', 'J_TB_L', 'J_TB_R', 'R_STBY', 'R_SCL', 'R_SDA',
          'C_VM', 'C_VM_MLCC', 'J_ENC', 'J_OLED', 'J_GESTURE', 'J_KEY1', 'J_KEY2', 'H1', 'H2', 'H3', 'H4', 'C5', 'C7']:
    f = byname.get(r)
    if not f:
        print(r, "MISSING")
        continue
    print(f"\n{r} {f['val']} at ({f['x']:.2f},{f['y']:.2f})")
    for p in f['pads']:
        print(f"   {p['num']:>3s} abs({p['x']:8.3f},{p['y']:8.3f}) rel({p['dx']:+6.2f},{p['dy']:+6.2f}) {p['w']}x{p['h']} net{p['net']} {p['netname']}")

print("\n== MOUNTING HOLES ==")
for r in ['H1', 'H2', 'H3', 'H4']:
    f = byname.get(r)
    if f:
        for p in f['pads']:
            print(r, f"({p['x']:.2f},{p['y']:.2f}) size {p['w']}x{p['h']} drill {p['drill']} net{p['net']} {p['netname']}")

holes = [(p['x'], p['y']) for r in ['H1', 'H2', 'H3', 'H4'] if r in byname for p in byname[r]['pads']]
print("\n== 4.5mm KEEPOUT CHECK ==")
worst = []
for hx, hy in holes:
    best = None
    for f in fps:
        if f['ref'] in ('H1', 'H2', 'H3', 'H4'):
            continue
        for p in f['pads']:
            d = math.hypot(p['x'] - hx, p['y'] - hy) - math.hypot(p['w'], p['h']) / 2
            if best is None or d < best[0]:
                best = (d, f"{f['ref']}.{p['num']}", math.hypot(p['x'] - hx, p['y'] - hy))
    print(f"hole ({hx:.1f},{hy:.1f}) nearest pad edge {best[0]:.2f}mm  ({best[1]}, center {best[2]:.2f}mm)")
    for s in segs:
        for t in (0, 0.5, 1):
            px = s['x1'] + t * (s['x2'] - s['x1'])
            py = s['y1'] + t * (s['y2'] - s['y1'])
            d = math.hypot(px - hx, py - hy)
            if d < 4.5:
                worst.append((d, s['net'], px, py))
print("segments inside 4.5mm:", len(worst))

print("\n== PAD-TO-PAD OVERLAP (different nets) ==")
alld = [(f['ref'], p) for f in fps for p in f['pads']]
bad = []
for (r1, a), (r2, b) in itertools.combinations(alld, 2):
    if a['net'] == b['net'] and a['net'] != 0:
        continue
    gx = abs(a['x'] - b['x']) - (a['w'] + b['w']) / 2
    gy = abs(a['y'] - b['y']) - (a['h'] + b['h']) / 2
    if gx < 0 and gy < 0:
        bad.append((max(gx, gy), r1, a['num'], r2, b['num'], a['netname'], b['netname']))
print("overlapping pad pairs:", len(bad))
for g, r1, n1, r2, n2, nm1, nm2 in sorted(bad)[:25]:
    print(f"   {r1}.{n1} vs {r2}.{n2}  overlap {g:.3f}mm  [{nm1} / {nm2}]")

print("\n== MIN PAD CLEARANCE (different nets, same layer F.Cu) ==")
cs = []
for (r1, a), (r2, b) in itertools.combinations(alld, 2):
    if a['net'] == b['net'] and a['net'] != 0:
        continue
    gx = abs(a['x'] - b['x']) - (a['w'] + b['w']) / 2
    gy = abs(a['y'] - b['y']) - (a['h'] + b['h']) / 2
    if gx < 0 and gy < 0:
        continue
    d = math.hypot(max(gx, 0), max(gy, 0))
    cs.append((d, r1, a['num'], r2, b['num'], a['netname'], b['netname']))
cs.sort()
print("5 tightest clearances:")
for c in cs[:6]:
    print(f"   {c[0]:.3f}mm  {c[1]}.{c[2]} vs {c[3]}.{c[4]}  [{c[5]}/{c[6]}]")

print("\n== SEGMENTS / VIAS ==")
print("segs", len(segs), "total len %.1fmm" % sum(math.hypot(s['x2'] - s['x1'], s['y2'] - s['y1']) for s in segs))
print("widths", sorted({s['w'] for s in segs}))
print("vias", len(vias), "nets", sorted({v['net'] for v in vias}))
