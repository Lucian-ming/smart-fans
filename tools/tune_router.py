with open('tools/generate_clean_routed_pcb.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Increase obstacle clearance radius to 0.55mm so gap is always > 0.25mm
code = code.replace("r = max(p['sx'], p['sy']) / 2.0 + 0.35", "r = max(p['sx'], p['sy']) / 2.0 + 0.55")

with open('tools/generate_clean_routed_pcb.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated obstacle radius in generate_clean_routed_pcb.py")
