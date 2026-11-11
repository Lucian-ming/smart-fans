import re

with open("tools/build_perfect_revB_v3.py", "r", encoding="utf-8") as f:
    code = f.read()

# Normalize to LF for easy replacement
code = code.replace("\r\n", "\n")

# 1. 3D Model in Footprint export
old_footprint_end = """        lines.append('  )')

    # Tracks"""

new_footprint_end = """        m_path = get_3d_model(fp)
        if m_path:
            lines.append(f'    (model "{m_path}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')

        lines.append('  )')

    # Tracks"""

assert old_footprint_end in code, "Could not find footprint end"
code = code.replace(old_footprint_end, new_footprint_end)

# 2. Zone filled polygon in export_kicad_pcb
old_zone = """        lines.append('    (filled_polygon')
        lines.append('      (pts')
        lines.append(f'        (xy {x0+1.0} {y0+1.0})')
        lines.append(f'        (xy {x1-1.0} {y0+1.0})')
        lines.append(f'        (xy {x1-1.0} {y1-1.0})')
        lines.append(f'        (xy {x0+1.0} {y1-1.0})')
        lines.append('      )')
        lines.append('    )')"""

new_zone = """        lines.append('    (filled_polygon')
        lines.append('      (pts')
        for pt in KEYHOLE_POLYS[zlayer]:
            lines.append(f'        (xy {pt[0]:.4f} {pt[1]:.4f})')
        lines.append('      )')
        lines.append('    )')"""

assert old_zone in code, "Could not find old zone filled polygon"
code = code.replace(old_zone, new_zone)

# 3. Gerber area fill in export_gerber_and_drill
old_gerber_fill = """        # Flash Ground Copper Area Fill (G36 / G37)
        cu_lines.append("G36*")
        cu_lines.append(f"X{fmt_gerber(x0+1.0)}Y{fmt_gerber(y0+1.0)}D02*")
        cu_lines.append(f"X{fmt_gerber(x1-1.0)}Y{fmt_gerber(y0+1.0)}D01*")
        cu_lines.append(f"X{fmt_gerber(x1-1.0)}Y{fmt_gerber(y1-1.0)}D01*")
        cu_lines.append(f"X{fmt_gerber(x0+1.0)}Y{fmt_gerber(y1-1.0)}D01*")
        cu_lines.append(f"X{fmt_gerber(x0+1.0)}Y{fmt_gerber(y0+1.0)}D01*")
        cu_lines.append("G37*")"""

new_gerber_fill = """        # Flash Ground Copper Area Fill (G36 / G37)
        cu_lines.append("G36*")
        poly_pts = KEYHOLE_POLYS[layer]
        for i, pt in enumerate(poly_pts):
            op = "D02*" if i == 0 else "D01*"
            cu_lines.append(f"X{fmt_gerber(pt[0])}Y{fmt_gerber(pt[1])}{op}")
        cu_lines.append(f"X{fmt_gerber(poly_pts[0][0])}Y{fmt_gerber(poly_pts[0][1])}D01*")
        cu_lines.append("G37*")"""

assert old_gerber_fill in code, "Could not find old gerber fill"
code = code.replace(old_gerber_fill, new_gerber_fill)

# 4. Replace export_kicad_sch
old_sch_func = code[code.find("# 6. KiCad Schematic File Generator (.kicad_sch)"):code.find("# 7. Authentic RS-274X Gerber & Excellon Drill File Exporter")]

with open("tools/test_sch_gen.py", "r", encoding="utf-8") as f:
    sch_src = f.read()

# Extract generate_schematic body
sch_body = sch_src[sch_src.find("def generate_schematic():"):sch_src.find("if __name__ ==")]
# Convert to export_kicad_sch
sch_body = sch_body.replace("def generate_schematic():", "def export_kicad_sch():\n    sch_path = os.path.join(KICAD_DIR, 'fan_ctrl_revB.kicad_sch')")
sch_body = sch_body.replace("b.COMPONENTS", "COMPONENTS")
sch_body = sch_body.replace('return sch_content', 'with open(sch_path, "w", encoding="utf-8") as f:\n        f.write(sch_content)\n    print(f"KiCad Schematic exported successfully: {sch_path} ({len(lines)} lines)")\n    return sch_path')

new_sch_section = "# 6. KiCad Schematic File Generator (.kicad_sch)\n" + sch_body + "\nexport_kicad_sch()\n\n"

code = code.replace(old_sch_func, new_sch_section)

# 5. Rev B3 -> Rev B4 strings
code = code.replace("REV B3", "REV B4")
code = code.replace("Rev B3", "Rev B4")

with open("tools/build_perfect_revB_v3.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(code)

print("SUCCESS: tools/build_perfect_revB_v3.py successfully updated with all B4 enhancements!")
