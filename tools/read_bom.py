import csv

with open('hardware/fabrication/bom/BOM_SmartFan_RevA.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total BOM rows: {len(rows)}")
for r in rows:
    lcsc = r.get('LCSC_Part', '')
    des = r.get('Designator', '')
    comment = r.get('Comment', '')
    footprint = r.get('Footprint', '')
    qty = r.get('Quantity', '')
    price = r.get('UnitPrice', '')
    print(f"{des:15s} | {comment:32s} | {lcsc:15s} | {footprint:22s} | {qty} | {price}")
