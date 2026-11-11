"""
Update BOM CSV and Excel files with corrected resistor counts and designators.
"""
import openpyxl
import csv

csv_path = 'hardware/fabrication/bom/BOM_SmartFan_RevA.csv'
xlsx_path = 'hardware/fabrication/bom/BOM_SmartFan_RevA.xlsx'
rev_csv = 'hardware/fabrication/revA_2026-11-03/bom/BOM_SmartFan_RevA.csv'
rev_xlsx = 'hardware/fabrication/revA_2026-11-03/bom/BOM_SmartFan_RevA.xlsx'

with open(csv_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'R1, R2' in line:
        line = '23,"R1, R2, R10",1 kΩ 贴片电阻 1% 1/8W,R0805,3,C17513,厚声/国巨,贴片电阻,限流分压,0.05,LED 限流与 Q1 基极限流\n'
    elif 'R3~R6' in line:
        line = '24,R3~R6 R11,4.7 kΩ 贴片电阻 1% 1/8W,R0805,5,C25900,厚声/国巨,贴片电阻,信号上拉,0.05,DS18B20、I2C SCL/SDA、风扇 FG 与 PWM 上拉\n'
    elif 'R7, R8' in line:
        line = '25,"R7, R8, R12",10 kΩ 贴片电阻 1% 1/8W,R0805,3,C25879,厚声/国巨,贴片电阻,下拉保护,0.05,Q1/Q2 栅极/基极下拉、手势 INT 上拉\n'
    new_lines.append(line)

with open(csv_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
with open(rev_csv, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

wb = openpyxl.Workbook()
ws = wb.active
ws.title = 'BOM_SmartFan_RevA'

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    for r_idx, row in enumerate(reader, 1):
        for c_idx, val in enumerate(row, 1):
            try:
                if c_idx == 1 or c_idx == 5:
                    cell_val = int(val)
                elif c_idx == 10:
                    cell_val = float(val)
                else:
                    cell_val = val
            except ValueError:
                cell_val = val
            ws.cell(row=r_idx, column=c_idx, value=cell_val)

wb.save(xlsx_path)
wb.save(rev_xlsx)
print('Successfully updated BOM CSV and XLSX files!')
