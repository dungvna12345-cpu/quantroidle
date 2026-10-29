@echo off
set "GODOT=C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
if not exist "%GODOT%" set "GODOT=D:\desktop\TIXUNG~1\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe"
start "" "%GODOT%" --path "%~dp0."
