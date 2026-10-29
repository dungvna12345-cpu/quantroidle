"""
Quán Trọ Idle - iPhone Remote Touch Streamer (Hỗ trợ Public Internet & Wi-Fi LAN)
Tự động stream màn hình game Quán Trọ Idle sang iPhone qua Cloudflare Tunnel (HTTPS toàn cầu) hoặc Wi-Fi nội bộ.
Hỗ trợ cảm ứng vuốt chạm 1:1, chạy 35-45 FPS siêu mượt, mở được trên 4G/5G/bất kỳ mạng nào.
"""

import sys
import os
import time
import socket
import json
import threading
import io
import re
import subprocess
import ctypes
from ctypes import wintypes
from typing import Optional
import struct

# Cấu hình UTF-8 cho console Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import win32gui
import win32ui
import win32con
import win32process
import cv2
import numpy as np
import qrcode
from PIL import Image

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Cấu hình
PORT = 8080
FRAME_QUALITY = 82
TARGET_FPS = 38
GODOT_EXE = r"D:\desktop\TIXUNG~1\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64.exe"
PROJ_PATH = r"c:\Users\Windows\AppData\Roaming\Claude\scratch-workspaces\e148ac75-2845-43e9-b137-2b90181e426d\1d0710ae-232d-430a-a247-055c032d9668\scratch-2026-10-28-f9adf7\QuanTroIdle"
ARTIFACT_DIR = r"C:\Users\Windows\.gemini\antigravity-ide\brain\269fe7e7-c972-4d38-86aa-e7985d886949"

def get_lan_ip() -> str:
    """Lấy địa chỉ IPv4 nội bộ trong mạng Wi-Fi/LAN của máy tính"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

LAN_IP = get_lan_ip()
LOCAL_URL = f"http://{LAN_IP}:{PORT}"

# Trạng thái toàn cục
class StreamState:
    def __init__(self):
        self.hwnd: Optional[int] = None
        self.desk_name: Optional[str] = None
        self.client_w: int = 450
        self.client_h: int = 800
        self.latest_jpeg: Optional[bytes] = None
        self.lock = threading.Lock()
        self.running = True
        self.fps = 0.0
        self.frame_count = 0
        self.last_touch_time = 0.0
        self.public_url: Optional[str] = None
        self.tunnel_proc: Optional[subprocess.Popen] = None
        self.godot_socket: Optional[socket.socket] = None
        self.godot_connected: bool = False

state = StreamState()

def switch_to_desktop(desk_name: str):
    """Chuyển thread hiện tại sang desktop cụ thể"""
    try:
        hDesk = user32.OpenDesktopW(desk_name, 0, False, 0x10000000 | 0x01FF)
        if hDesk:
            user32.SetThreadDesktop(hDesk)
        return hDesk
    except Exception:
        return None

def switch_to_default_desktop():
    return switch_to_desktop(state.desk_name or 'Default')

def get_godot_pids() -> set:
    """Lấy danh sách PID của tất cả tiến trình Godot đang chạy"""
    pids = set()
    try:
        p = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Godot*', '/FO', 'CSV'], capture_output=True, text=True)
        for line in p.stdout.splitlines()[1:]:
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    pids.add(int(parts[1].strip('"\r\n ')))
                except Exception:
                    pass
    except Exception:
        pass
    return pids

def ensure_game_running():
    """Tự động khởi động game Quán Trọ Idle nếu chưa bật"""
    godot_pids = get_godot_pids()
    if not godot_pids:
        print("[Launcher] Đang khởi động game Quán Trọ Idle...")
        godot = GODOT_EXE
        if not os.path.exists(godot):
            godot = r"C:\Users\Windows\AppData\Local\Temp\qtprev\Godot_v4.7.2-stable_win64.exe"
        subprocess.Popen([godot, "--path", PROJ_PATH])
        time.sleep(2.5)

def find_game_window() -> Optional[int]:
    """Tìm chính xác HWND của cửa sổ game Quán Trọ Idle trên mọi desktop WinSta0"""
    ensure_game_running()
    godot_pids = get_godot_pids()
    found_hwnd = None
    found_desk = None

    def enum_desktops_cb(desk_name, lparam):
        nonlocal found_hwnd, found_desk
        hDesk = user32.OpenDesktopW(desk_name, 0, False, 0x10000000 | 0x01FF)
        if hDesk:
            def w_cb(hwnd, _):
                nonlocal found_hwnd, found_desk
                if found_hwnd:
                    return False
                tid, pid = win32process.GetWindowThreadProcessId(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if w > 200 and h > 300:
                    if pid in godot_pids:
                        found_hwnd = hwnd
                        found_desk = desk_name
                        return False
                    text = win32gui.GetWindowText(hwnd)
                    if ("Quán Trọ" in text or "QuanTro" in text) and not any(x in text for x in ["Visual Studio", "Antigravity", "Code [", "cmd.exe", "PowerShell"]):
                        found_hwnd = hwnd
                        found_desk = desk_name
                        return False
                return True
            try:
                win32gui.EnumDesktopWindows(hDesk, w_cb, None)
            except Exception:
                pass
            user32.CloseDesktop(hDesk)
        return 1

    EnumDesktopsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.LPCWSTR, wintypes.LPARAM)
    hWs = user32.OpenWindowStationW('WinSta0', False, 0x10000000 | 0x037F)
    if hWs:
        old_ws = user32.GetProcessWindowStation()
        user32.SetProcessWindowStation(hWs)
        user32.EnumDesktopsW(hWs, EnumDesktopsProc(enum_desktops_cb), 0)
        user32.SetProcessWindowStation(old_ws)
        user32.CloseWindowStation(hWs)

    if found_hwnd and found_desk:
        state.desk_name = found_desk
        switch_to_desktop(found_desk)
        try:
            user32.ShowWindow(found_hwnd, 9) # SW_RESTORE
            user32.SetWindowPos(found_hwnd, 0, 150, 80, 480, 850, 0x0040)
        except Exception:
            pass
        return found_hwnd

    return None

def godot_tcp_worker():
    """Nhận trực tiếp frame hình ảnh HD từ Godot StreamService qua TCP loopback và gửi touch input"""
    print("[DirectStream] Thread kết nối trực tiếp Godot StreamService (cổng 8999) đã chạy...")
    while state.running:
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(2.0)
            s.connect(('127.0.0.1', 8999))
            state.godot_socket = s
            state.godot_connected = True
            print("[DirectStream] 🔥 ĐÃ KẾT NỐI TRỰC TIẾP TỚI GODOT ENGINE (TCP 8999) - STREAM 35+ FPS!")
            
            fps_count = 0
            fps_start = time.time()
            
            while state.running:
                # Đọc 4 bytes độ dài (little-endian uint32)
                sz_data = b""
                while len(sz_data) < 4:
                    chunk = s.recv(4 - len(sz_data))
                    if not chunk:
                        raise ConnectionResetError("Godot ngắt kết nối")
                    sz_data += chunk
                sz = struct.unpack("<I", sz_data)[0]
                if sz == 0 or sz > 5000000:
                    continue
                
                # Đọc payload JPEG
                jpeg_data = bytearray()
                while len(jpeg_data) < sz:
                    chunk = s.recv(min(65536, sz - len(jpeg_data)))
                    if not chunk:
                        raise ConnectionResetError("Godot ngắt kết nối khi đang truyền ảnh")
                    jpeg_data.extend(chunk)
                    
                with state.lock:
                    state.latest_jpeg = bytes(jpeg_data)
                    state.frame_count += 1
                    
                fps_count += 1
                now = time.time()
                if now - fps_start >= 1.0:
                    state.fps = fps_count / (now - fps_start)
                    fps_count = 0
                    fps_start = now
        except Exception:
            state.godot_connected = False
            state.godot_socket = None
            if s:
                try:
                    s.close()
                except Exception:
                    pass
            time.sleep(1.0)

def capture_worker():
    """Thread chụp màn hình Godot liên tục và nén JPEG tốc độ cao (Fallback)"""
    switch_to_default_desktop()
    print("[Capture] Bắt đầu thread chụp màn hình (fallback)...")
    
    fps_frames = 0
    fps_start = time.time()
    
    cached_hwnd = None
    saveDC = None
    mfcDC = None
    saveBitMap = None
    hwndDC = None
    cached_ww = 0
    cached_wh = 0
    
    def cleanup_dc():
        nonlocal saveDC, mfcDC, saveBitMap, hwndDC
        try:
            if saveBitMap:
                win32gui.DeleteObject(saveBitMap.GetHandle())
            if saveDC:
                saveDC.DeleteDC()
            if mfcDC:
                mfcDC.DeleteDC()
            if hwndDC and cached_hwnd:
                win32gui.ReleaseDC(cached_hwnd, hwndDC)
        except Exception:
            pass
        saveDC = None
        mfcDC = None
        saveBitMap = None
        hwndDC = None

    while state.running:
        t0 = time.time()
        
        # Nếu đã có direct stream từ Godot, nhường luồng
        if state.godot_connected and state.latest_jpeg is not None:
            time.sleep(0.5)
            continue
        
        # Kiểm tra hoặc tìm lại HWND
        if not state.hwnd or not user32.IsWindow(state.hwnd):
            state.hwnd = find_game_window()
            cleanup_dc()
            if not state.hwnd:
                time.sleep(0.5)
                continue
            title = win32gui.GetWindowText(state.hwnd)
            print(f"[Capture] Đã kết nối cửa sổ Quán Trọ Idle: HWND {state.hwnd} ({title})")

        hwnd = state.hwnd
        wrect = win32gui.GetWindowRect(hwnd)
        ww = wrect[2] - wrect[0]
        wh = wrect[3] - wrect[1]

        crect = win32gui.GetClientRect(hwnd)
        cw = crect[2] - crect[0]
        ch = crect[3] - crect[1]

        if cw <= 10 or ch <= 10 or ww <= 10 or wh <= 10:
            time.sleep(0.1)
            continue

        state.client_w = cw
        state.client_h = ch

        # Tính offset client so với window (loại bỏ viền & title bar)
        pt = wintypes.POINT(0, 0)
        user32.ClientToScreen(hwnd, ctypes.byref(pt))
        ox = max(0, pt.x - wrect[0])
        oy = max(0, pt.y - wrect[1])

        # Khởi tạo hoặc cập nhật DC nếu kích thước thay đổi
        if cached_hwnd != hwnd or cached_ww != ww or cached_wh != wh or saveDC is None:
            cleanup_dc()
            try:
                hwndDC = win32gui.GetDC(hwnd)
                mfcDC = win32ui.CreateDCFromHandle(hwndDC)
                saveDC = mfcDC.CreateCompatibleDC()
                saveBitMap = win32ui.CreateBitmap()
                saveBitMap.CreateCompatibleBitmap(mfcDC, ww, wh)
                saveDC.SelectObject(saveBitMap)
                cached_hwnd = hwnd
                cached_ww = ww
                cached_wh = wh
            except Exception as e:
                cleanup_dc()
                time.sleep(0.2)
                continue

        # Chụp bằng PrintWindow PW_RENDERFULLCONTENT = 2
        try:
            res = user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
            if not res:
                time.sleep(0.05)
                continue

            bmpstr = saveBitMap.GetBitmapBits(True)
            arr = np.frombuffer(bmpstr, dtype=np.uint8).reshape((wh, ww, 4))
            
            # Cắt chuẩn xác khu vực game client
            crop = arr[oy:oy+ch, ox:ox+cw, :3]
            
            # Mã hoá JPEG siêu tốc bằng OpenCV
            _, buf = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
            jpeg_bytes = buf.tobytes()

            with state.lock:
                state.latest_jpeg = jpeg_bytes
                state.frame_count += 1
                
            fps_frames += 1
            now = time.time()
            if now - fps_start >= 1.0:
                state.fps = round(fps_frames / (now - fps_start), 1)
                fps_frames = 0
                fps_start = now

        except Exception:
            cleanup_dc()
            time.sleep(0.1)

        # Điều tiết FPS
        elapsed = time.time() - t0
        target_sleep = max(0.001, (1.0 / TARGET_FPS) - elapsed)
        time.sleep(target_sleep)

    cleanup_dc()
    print("[Capture] Dừng thread chụp.")

def handle_touch(action: str, norm_x: float, norm_y: float):
    """Ánh xạ toạ độ chuẩn hoá từ màn hình iPhone sang cửa sổ game trên PC"""
    state.last_touch_time = time.time()
    
    # 1. Ưu tiên gửi trực tiếp vào Godot qua TCP socket (siêu mượt, không phụ thuộc cửa sổ/desktop)
    if state.godot_connected and state.godot_socket:
        try:
            if action in ('down', 'd', 'start'):
                code = 1
            elif action in ('up', 'u', 'end'):
                code = 2
            else:
                code = 3
            pkt = struct.pack('<Bff', code, float(norm_x), float(norm_y))
            state.godot_socket.sendall(pkt)
            return
        except Exception:
            state.godot_connected = False
            state.godot_socket = None

    # 2. Fallback gửi qua Windows PostMessage nếu direct stream chưa bật
    if not state.hwnd or not user32.IsWindow(state.hwnd):
        return

    cw = state.client_w
    ch = state.client_h

    gx = max(0, min(cw - 1, int(norm_x * cw)))
    gy = max(0, min(ch - 1, int(norm_y * ch)))
    lParam = (gy << 16) | (gx & 0xFFFF)

    switch_to_default_desktop()
    hwnd = state.hwnd

    if action in ('down', 'd', 'start'):
        try:
            if user32.GetForegroundWindow() != hwnd:
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        user32.PostMessageW(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
        user32.PostMessageW(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
    elif action in ('move', 'm'):
        user32.PostMessageW(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, lParam)
    elif action in ('up', 'u', 'end'):
        user32.PostMessageW(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

def update_qr(url_to_use: str):
    """Cập nhật ảnh QR code và hiển thị trên màn hình"""
    try:
        os.makedirs("tools", exist_ok=True)
        qr = qrcode.QRCode(border=2)
        qr.add_data(url_to_use)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("tools/qr_iphone.png")
        
        # Copy vào artifacts để tiện view
        if os.path.exists(ARTIFACT_DIR):
            img.save(os.path.join(ARTIFACT_DIR, "qr_iphone.png"))
            
        print("\n--- MÃ QR MỚI (QUÉT BẰNG CAMERA IPHONE) ---")
        qr.print_ascii(invert=True)
        print("-------------------------------------------\n")
    except Exception as e:
        print("[QR] Update error:", e)

def tunnel_worker():
    """Khởi động Cloudflare Tunnel để tạo link Public Internet toàn cầu"""
    cf_exe = "tools/cloudflared.exe"
    if not os.path.exists(cf_exe):
        print("[Tunnel] Không tìm thấy tools/cloudflared.exe, dùng chế độ mạng nội bộ.")
        return

    print("[Tunnel] Đang khởi tạo Cloudflare Tunnel (Public Internet)...")
    try:
        proc = subprocess.Popen(
            [cf_exe, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        state.tunnel_proc = proc

        for _ in range(80):
            line = proc.stderr.readline()
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                state.public_url = m.group(0)
                print("\n" + "="*68)
                print("  🌐 ĐÃ KÍCH HOẠT ĐƯỜNG TRUYỀN PUBLIC INTERNET (HTTPS):")
                print(f"  👉  {state.public_url}")
                print("  (Có thể chơi trên iPhone từ bất kỳ đâu: 4G, 5G, Wi-Fi ngoài quán)")
                print("="*68 + "\n")
                update_qr(state.public_url)
                break
            time.sleep(0.05)

        # Giữ process chạy
        proc.wait()
    except Exception as e:
        print("[Tunnel] Lỗi tunnel:", e)

# Khởi tạo FastAPI App
app = FastAPI(title="Quan Tro Idle - iPhone Public Streamer")

HTML_CLIENT = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Quán Trọ Idle">
  <meta name="theme-color" content="#12100e">
  <title>Quán Trọ Idle - iPhone Remote</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      user-select: none;
      touch-action: none;
    }
    body, html {
      width: 100%;
      height: 100%;
      overflow: hidden;
      background-color: #12100e;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      position: fixed;
    }
    #game-container {
      position: relative;
      width: 100%;
      height: 100%;
      max-width: calc(100vh * (9 / 16));
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 40px rgba(0,0,0,0.85);
      background: #181512;
    }
    #stream-view {
      width: 100%;
      height: 100%;
      object-fit: contain;
      display: block;
      pointer-events: none;
    }
    #touch-layer {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 10;
      cursor: pointer;
    }
    /* Top Status Bar */
    #hud-top {
      position: absolute;
      top: env(safe-area-inset-top, 8px);
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 20;
      pointer-events: none;
      opacity: 0.92;
      transition: opacity 0.3s;
    }
    .hud-badge {
      background: rgba(26, 23, 20, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: #fff;
      font-size: 11px;
      font-weight: 600;
      padding: 6px 11px;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, 0.16);
      display: flex;
      align-items: center;
      gap: 7px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px #22c55e;
    }
    .btn-group {
      pointer-events: auto;
      display: flex;
      gap: 6px;
    }
    .hud-btn {
      background: rgba(26, 23, 20, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: #f3efe6;
      border: 1px solid rgba(255, 255, 255, 0.2);
      font-size: 11px;
      font-weight: 500;
      padding: 6px 10px;
      border-radius: 12px;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .hud-btn:active {
      background: #e08a3c;
      color: #fff;
    }
    /* Touch Feedback ripple */
    .ripple {
      position: absolute;
      border-radius: 50%;
      transform: translate(-50%, -50%) scale(0);
      background: rgba(245, 176, 65, 0.35);
      border: 2px solid rgba(255, 255, 255, 0.85);
      pointer-events: none;
      animation: rippleEffect 0.35s ease-out;
      z-index: 15;
    }
    @keyframes rippleEffect {
      0% { width: 10px; height: 10px; opacity: 1; transform: translate(-50%, -50%) scale(0.5); }
      100% { width: 50px; height: 50px; opacity: 0; transform: translate(-50%, -50%) scale(1.6); }
    }
    /* Bottom Safe Area Spacer */
    #hud-bottom {
      position: absolute;
      bottom: env(safe-area-inset-bottom, 8px);
      pointer-events: none;
      z-index: 20;
      color: rgba(255, 255, 255, 0.45);
      font-size: 10px;
      text-align: center;
      letter-spacing: 0.3px;
    }
  </style>
</head>
<body>
  <div id="game-container">
    <img id="stream-view" src="/stream.mjpg" alt="Quán Trọ Idle Screen" />
    <div id="touch-layer"></div>

    <div id="hud-top">
      <div class="hud-badge">
        <span class="dot" id="net-dot"></span>
        <span id="fps-label">Đang kết nối...</span>
      </div>
      <div class="btn-group">
        <button class="hud-btn" onclick="toggleFullScreen()">⛶ Toàn màn hình</button>
        <button class="hud-btn" onclick="reloadStream()">🔄 Tải lại</button>
      </div>
    </div>

    <div id="hud-bottom">Quán Trọ Idle • Public Online Stream</div>
  </div>

  <script>
    const touchLayer = document.getElementById('touch-layer');
    const streamView = document.getElementById('stream-view');
    const netDot = document.getElementById('net-dot');
    const fpsLabel = document.getElementById('fps-label');

    // WebSocket cho cảm ứng độ trễ siêu thấp (<5ms)
    let ws = null;
    function connectWS() {
      const loc = window.location;
      const wsUrl = (loc.protocol === 'https:' ? 'wss://' : 'ws://') + loc.host + '/ws';
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        netDot.style.background = '#22c55e';
        netDot.style.boxShadow = '0 0 8px #22c55e';
        fpsLabel.innerText = 'Trực tuyến (Public)';
      };

      ws.onclose = () => {
        netDot.style.background = '#ef4444';
        netDot.style.boxShadow = '0 0 8px #ef4444';
        fpsLabel.innerText = 'Đang kết nối lại...';
        setTimeout(connectWS, 1500);
      };

      ws.onerror = () => {
        ws.close();
      };
    }
    connectWS();

    function sendTouch(action, clientX, clientY) {
      const rect = touchLayer.getBoundingClientRect();
      const normX = (clientX - rect.left) / rect.width;
      const normY = (clientY - rect.top) / rect.height;

      if (normX >= 0 && normX <= 1 && normY >= 0 && normY <= 1) {
        const payload = JSON.stringify({ t: action, x: normX, y: normY });
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(payload);
        } else {
          // HTTP POST fallback
          fetch('/touch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload
          }).catch(()=>{});
        }
      }
    }

    function createRipple(x, y) {
      const r = document.createElement('div');
      r.className = 'ripple';
      r.style.left = x + 'px';
      r.style.top = y + 'px';
      touchLayer.appendChild(r);
      setTimeout(() => r.remove(), 400);
    }

    // Touch Event Listeners
    touchLayer.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const t = e.touches[0];
      const rect = touchLayer.getBoundingClientRect();
      createRipple(t.clientX - rect.left, t.clientY - rect.top);
      sendTouch('d', t.clientX, t.clientY);
      if (navigator.vibrate) navigator.vibrate(10);
    }, { passive: false });

    touchLayer.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const t = e.touches[0];
      sendTouch('m', t.clientX, t.clientY);
    }, { passive: false });

    touchLayer.addEventListener('touchend', (e) => {
      e.preventDefault();
      if (e.changedTouches.length > 0) {
        const t = e.changedTouches[0];
        sendTouch('u', t.clientX, t.clientY);
      }
    }, { passive: false });

    touchLayer.addEventListener('touchcancel', (e) => {
      e.preventDefault();
      if (e.changedTouches.length > 0) {
        const t = e.changedTouches[0];
        sendTouch('u', t.clientX, t.clientY);
      }
    }, { passive: false });

    // Mouse Listeners cho PC browser test
    let isMouseDown = false;
    touchLayer.addEventListener('mousedown', (e) => {
      isMouseDown = true;
      const rect = touchLayer.getBoundingClientRect();
      createRipple(e.clientX - rect.left, e.clientY - rect.top);
      sendTouch('d', e.clientX, e.clientY);
    });
    window.addEventListener('mousemove', (e) => {
      if (isMouseDown) {
        sendTouch('m', e.clientX, e.clientY);
      }
    });
    window.addEventListener('mouseup', (e) => {
      if (isMouseDown) {
        isMouseDown = false;
        sendTouch('u', e.clientX, e.clientY);
      }
    });

    function reloadStream() {
      streamView.src = '/stream.mjpg?t=' + Date.now();
    }

    function toggleFullScreen() {
      const doc = window.document;
      const docEl = doc.documentElement;
      const requestFullscreen = docEl.requestFullscreen || docEl.webkitRequestFullScreen || docEl.mozRequestFullScreen;
      const cancelFullscreen = doc.exitFullscreen || doc.webkitExitFullscreen || doc.mozCancelFullScreen;

      if (!doc.fullscreenElement && !doc.webkitFullscreenElement) {
        if (requestFullscreen) requestFullscreen.call(docEl);
      } else {
        if (cancelFullscreen) cancelFullscreen.call(doc);
      }
    }

    // Cập nhật thông số FPS từ server
    setInterval(async () => {
      try {
        const res = await fetch('/status');
        const data = await res.json();
        if (data && data.fps !== undefined) {
          fpsLabel.innerText = `${data.fps} FPS • Quán Trọ`;
        }
      } catch (e) {}
    }, 1500);
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTML_CLIENT

@app.get("/stream.mjpg")
async def get_stream():
    """MJPEG stream mượt mà cho Safari trên iOS"""
    def frame_generator():
        last_frame_id = -1
        while state.running:
            with state.lock:
                current_id = state.frame_count
                frame_data = state.latest_jpeg

            if frame_data and current_id != last_frame_id:
                last_frame_id = current_id
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n"
                )
            else:
                time.sleep(0.01)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/frame.jpg")
async def get_frame():
    with state.lock:
        data = state.latest_jpeg
    if data:
        return Response(content=data, media_type="image/jpeg")
    return Response(content=b"", status_code=404)

@app.get("/qr.png")
async def get_qr():
    url = state.public_url or LOCAL_URL
    qr = qrcode.QRCode(border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/status")
async def get_status():
    return {
        "status": "running" if state.hwnd else "searching_window",
        "fps": state.fps,
        "hwnd": state.hwnd,
        "width": state.client_w,
        "height": state.client_h,
        "local_url": LOCAL_URL,
        "public_url": state.public_url
    }

@app.post("/touch")
async def post_touch(req: Request):
    data = await req.json()
    action = data.get("t", "u")
    x = float(data.get("x", 0.0))
    y = float(data.get("y", 0.0))
    handle_touch(action, x, y)
    return {"ok": True}

@app.websocket("/ws")
async def websocket_touch(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            text = await ws.receive_text()
            data = json.loads(text)
            action = data.get("t", "u")
            x = float(data.get("x", 0.0))
            y = float(data.get("y", 0.0))
            handle_touch(action, x, y)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

def print_banner():
    banner = f"""
======================================================================
    QUÁN TRỌ IDLE - MÁY CHỦ STREAM TRỰC TIẾP LÊN IPHONE
======================================================================
  🏠 Địa chỉ nội bộ Wi-Fi (cùng mạng):
  👉  {LOCAL_URL}
"""
    print(banner)
    update_qr(LOCAL_URL)

def main():
    # Khởi động direct stream từ Godot engine (TCP 8999)
    godot_th = threading.Thread(target=godot_tcp_worker, daemon=True)
    godot_th.start()

    # Khởi động capture thread (fallback)
    cap_thread = threading.Thread(target=capture_worker, daemon=True)
    cap_thread.start()

    print_banner()

    # Khởi động Cloudflare Tunnel thread
    tunnel_th = threading.Thread(target=tunnel_worker, daemon=True)
    tunnel_th.start()

    # Chạy uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

if __name__ == "__main__":
    main()
