import subprocess
import sys
import os

godot_exe = r"C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
project_dir = r"c:\Users\Windows\AppData\Roaming\Claude\scratch-workspaces\e148ac75-2845-43e9-b137-2b90181e426d\1d0710ae-232d-430a-a247-055c032d9668\scratch-2026-10-28-f9adf7\QuanTroIdle"

print(f"Launching {godot_exe} with path {project_dir}")

# Use DETACHED_PROCESS so it stays running independently
DETACHED_PROCESS = 0x00000008
p = subprocess.Popen(
    [godot_exe, "--path", project_dir],
    creationflags=DETACHED_PROCESS,
    close_fds=True
)

print(f"Game launched successfully! PID: {p.pid}")
