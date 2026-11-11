with open('hardware/kicad/fan_ctrl_revA.kicad_pcb', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Match pads directly
pads = re.findall(r'\(pad\s+\"([^\"]+)\"\s+(\S+)\s+(\S+)\s+\(at\s+([\d\.\-]+)\s+([\d\.\-]+)(?:\s+([\d\.\-]+))?\)[\s\S]*?\(layers\s+([^\)]+)\)(?:[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"\))?', text)
print("Regex match pads count:", len(pads))

# Let's count all (pad ...) occurrences in the file
all_pad_lines = [line for line in text.split('\n') if '(pad ' in line]
print("Lines with (pad :", len(all_pad_lines))

# Count nets in pads
pad_nets = re.findall(r'\(pad[\s\S]*?\(net\s+(\d+)\s+\"([^\"]*)\"', text)
print("Pad net matches:", len(pad_nets))
