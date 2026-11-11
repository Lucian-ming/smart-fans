import subprocess
import time
import sys

cmd = [
    r'D:\dev_tools\apps\OpenOCD\openocd.exe',
    '-f', r'D:\dev_tools\apps\OpenOCD\scripts\interface\stlink.cfg',
    '-c', 'transport select swd; adapter speed 1000',
    '-f', r'D:\dev_tools\apps\OpenOCD\scripts\target\stm32f1x.cfg',
    '-c', 'reset_config none; program D:/smart_fans/firmware/build/smart_fan.bin 0x08000000 verify reset exit'
]

print("Starting OpenOCD flash probe loop...")
for i in range(1, 16):
    print(f"[{i}/15] Attempting to connect to target via SWD...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print("\n========================================")
        print("FLASHING SUCCEEDED!")
        print("========================================")
        print(res.stdout)
        sys.exit(0)
    else:
        errs = [l.strip() for l in res.stderr.splitlines() if 'Error' in l or 'Info' in l]
        print("   Result:", " | ".join(errs[:2]))
    time.sleep(0.5)

print("\nCould not connect within 15 attempts.")
sys.exit(1)
