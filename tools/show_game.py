import subprocess
import time
import ctypes
from ctypes import wintypes
import os

user32 = ctypes.windll.user32

godot = r"D:\desktop\TIXUNG~1\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe"
if not os.path.exists(godot):
    godot = r"C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
proj = r"c:\Users\Windows\AppData\Roaming\Claude\scratch-workspaces\e148ac75-2845-43e9-b137-2b90181e426d\1d0710ae-232d-430a-a247-055c032d9668\scratch-2026-10-28-f9adf7\QuanTroIdle"

# Kill any existing instances first
subprocess.run(["taskkill", "/f", "/im", "Godot*"], capture_output=True)

log_file = open(os.path.join(proj, "godot_run.log"), "w", encoding="utf-8")

# Launch
p = subprocess.Popen([godot, "--path", proj], stdout=log_file, stderr=subprocess.STDOUT)
print("Godot process launched! PID:", p.pid, flush=True)

current_hwnd = None
hwnd_file = os.path.join(proj, "tools", "game_hwnd.txt")
os.makedirs(os.path.join(proj, "tools"), exist_ok=True)

print("Monitoring game window...", flush=True)

while p.poll() is None:
    # Nếu cửa sổ hiện tại vẫn còn và hợp lệ, chỉ cần nghỉ
    if current_hwnd and user32.IsWindow(current_hwnd) and user32.IsWindowVisible(current_hwnd):
        time.sleep(1.0)
        continue

    global new_hwnd
    new_hwnd = None
    def enum_cb(hwnd, _):
        global new_hwnd
        if user32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == p.pid:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w >= 300 and h >= 400:
                    new_hwnd = hwnd
                    return False
        return True

    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumProc(enum_cb), 0)

    if new_hwnd and new_hwnd != current_hwnd:
        current_hwnd = new_hwnd
        print(f"Captured/Updated game window HWND: {current_hwnd}", flush=True)
        try:
            with open(hwnd_file, "w") as f:
                f.write(str(current_hwnd))
        except Exception as e:
            print("Failed to write game_hwnd.txt:", e)

        user32.ShowWindow(current_hwnd, 9) # SW_RESTORE
        user32.SetWindowPos(current_hwnd, -1, 150, 80, 480, 850, 0x0040) # HWND_TOPMOST, SWP_SHOWWINDOW
        user32.SetForegroundWindow(current_hwnd)
        time.sleep(0.5)
        user32.SetWindowPos(current_hwnd, -2, 150, 80, 480, 850, 0x0040) # HWND_NOTOPMOST
        print("Window placed in foreground successfully!", flush=True)

    time.sleep(0.5)

print(f"Godot process exited with code {p.poll()}", flush=True)
