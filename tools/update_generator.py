with open('tools/generate_clean_routed_pcb.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the footprints part extraction
old_str = "out_lines.append(footprints_part.strip())"
new_str = """# Filter out any existing segments or vias from footprints_part
cleaned_fps = [l for l in footprints_part.split('\\n') if not l.strip().startswith('(segment') and not l.strip().startswith('(via')]
out_lines.append('\\n'.join(cleaned_fps).strip())"""

code = code.replace(old_str, new_str)
with open('tools/generate_clean_routed_pcb.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated generate_clean_routed_pcb.py")
