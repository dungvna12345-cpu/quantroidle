import os

godot_temp = r"C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
godot_dt = r"D:\desktop\TIXUNG~1\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe"
proj = r"c:\Users\Windows\AppData\Roaming\Claude\scratch-workspaces\e148ac75-2845-43e9-b137-2b90181e426d\1d0710ae-232d-430a-a247-055c032d9668\scratch-2026-10-28-f9adf7\QuanTroIdle"

bat_content = f"""@echo off
set "GODOT={godot_temp}"
if not exist "%GODOT%" set "GODOT={godot_dt}"
start "" "%GODOT%" --path "{proj}"
"""

desktop_bat = r"D:\desktop\CHAY_GAME.bat"
with open(desktop_bat, "w", encoding="utf-8") as f:
    f.write(bat_content)

print(f"Updated {desktop_bat} successfully!")
