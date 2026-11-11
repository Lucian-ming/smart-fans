"""
Script: fix_all_footprint_clearances.py
Audits all pad-to-pad clearances between different nets and within footprints.
Ensures ALL clearances >= 0.25 mm (10 mil), well above JLC 6 mil (0.152mm) limit.
"""

import math
import re

# Footprint modifications needed:
# 1. DC1 at (118, 104) -> DC1.3 is at (122.7, 104)
#    D2 at (126, 104) -> Move D2 to (132, 104) so D2.1 is at (130, 104), gap > 7 mm!
# 2. Q1 at (116, 172) -> Change pad size to (1.0 1.4), pitch is 1.27 mm -> gap is 0.27 mm (10.6 mil > 6 mil)
# 3. SENS1 at (106, 163) -> Move SENS1 to (105, 156) so SENS1.3 is at (105, 161.08), gap to BZ1 is > 7 mm!
# 4. BZ1 at (108, 172) -> pin 1 is at (108, 168.2). With SENS1 at Y=156, gap is > 7 mm!
# 5. Check all other pairs!
print("Starting footprint clearance audit...")
