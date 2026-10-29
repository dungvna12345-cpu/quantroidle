import win32process
import win32gui
import win32con
import time
import os
import sys

godot = r"D:\desktop\TIXUNG~1\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe"
if not os.path.exists(godot):
    godot = r"C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
proj = r"c:\Users\Windows\AppData\Roaming\Claude\scratch-workspaces\e148ac75-2845-43e9-b137-2b90181e426d\1d0710ae-232d-430a-a247-055c032d9668\scratch-2026-10-28-f9adf7\QuanTroIdle"

cmd = f'"{godot}" --path "{proj}"'

si = win32process.STARTUPINFO()
si.lpDesktop = r"WinSta0\Default"

try:
    hProc, hThread, pid, tid = win32process.CreateProcess(
        None, cmd, None, None, False, win32process.CREATE_NEW_CONSOLE, None, proj, si
    )
    print(f"Launched Godot PID on WinSta0\\Default: {pid}")
except Exception as e:
    print(f"Failed to launch on WinSta0\\Default: {e}")
    # Fallback standard launch
    hProc, hThread, pid, tid = win32process.CreateProcess(
        None, cmd, None, None, False, 0, None, proj, win32process.STARTUPINFO()
    )
    print(f"Fallback launched PID: {pid}")
