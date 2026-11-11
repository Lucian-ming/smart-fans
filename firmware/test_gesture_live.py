import serial
import time
import sys
import io

# Ensure UTF-8 stdout on Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def monitor(port='COM12', baud=115200, duration=15):
    print(f"Connecting to {port} @ {baud}...")
    try:
        s = serial.Serial(port, baud, timeout=0.1)
    except Exception as e:
        print(f"Failed to open {port}: {e}")
        return

    time.sleep(0.1)
    # Clear buffer
    s.read_all()
    
    print("\n=======================================================")
    print(f"   PAJ7620 手势实时捕获监控已启动 (持续 {duration} 秒)   ")
    print("   请在手势传感器正上方 5~15cm 处进行手势操作：        ")
    print("   [^] 向上挥手  | [v] 向下挥手  | [>] 向右挥手        ")
    print("   [<] 向左挥手  | [+] 靠近推近  | [-] 远离拉起        ")
    print("   [CW] 顺时针画圆 | [CCW] 逆时针画圆 | [~] 连续晃手(Wave)")
    print("=======================================================\n")
    
    t0 = time.time()
    while time.time() - t0 < duration:
        line = s.readline()
        if line:
            text = line.decode('utf-8', errors='ignore').strip()
            if text:
                if "GESTURE" in text or "GEST" in text:
                    print(f"★ {text}")
                elif "--- System Status ---" in text or "State:" in text or "Last Event:" in text:
                    print(f"ℹ {text}")
                else:
                    print(f"  {text}")
        time.sleep(0.01)

    s.close()
    print("\n--- 监听结束 ---")

if __name__ == '__main__':
    dur = 15
    if len(sys.argv) > 1:
        dur = int(sys.argv[1])
    monitor(duration=dur)
