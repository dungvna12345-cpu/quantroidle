# -*- coding: utf-8 -*-
"""Sinh toàn bộ sprite SVG cho Quán Trọ Idle.

Quy ước:
- Vẽ ở độ phân giải 2x (một ô isometric = 256x128 px). Trong game Sprite2D scale = 0.5.
- Mỗi sprite có điểm neo (anchor) = điểm chạm đất / tâm đáy. Ghi vào manifest.json:
  { "ten": [rong, cao, neo_x, neo_y] }
- Phong cách: chuyển màu, mặt sáng/mặt tối, bóng elip mờ, viền tối dày, bo tròn khớp nối.

Chạy:  python tools/gen_sprites.py
"""
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "sprites"
UI_DIR = ROOT / "assets" / "ui"
OUT_DIR.mkdir(parents=True, exist_ok=True)
UI_DIR.mkdir(parents=True, exist_ok=True)

OUT = "#6b4128"    # màu viền chung (nâu mềm)
SW = 4.5           # độ dày viền (2x)
HW, HH = 128.0, 64.0  # nửa rộng / nửa cao của một ô (2x)

manifest = {}


# ---------------------------------------------------------------- màu

def _rgb(c):
    c = c.lstrip("#")
    return [int(c[i:i + 2], 16) for i in (0, 2, 4)]


def _hex(r):
    return "#" + "".join("%02x" % max(0, min(255, int(round(v)))) for v in r)


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex([ra[i] + (rb[i] - ra[i]) * t for i in range(3)])


def lt(c, t):
    return mix(c, "#ffffff", t)


def dk(c, t):
    return mix(c, "#1a0e08", t)


def f(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def pts(p):
    return " ".join(f(x) + "," + f(y) for x, y in p)


# ---------------------------------------------------------------- canvas

class C:
    def __init__(self, w, h, ax, ay):
        self.w, self.h, self.ax, self.ay = w, h, ax, ay
        self.defs = []
        self.els = []
        self.n = 0

    # --- gradient
    def lg(self, c1, c2, x1=0, y1=0, x2=0, y2=1, mid=None):
        self.n += 1
        gid = "g%d" % self.n
        stops = '<stop offset="0" stop-color="%s"/>' % c1
        if mid:
            stops += '<stop offset="0.5" stop-color="%s"/>' % mid
        stops += '<stop offset="1" stop-color="%s"/>' % c2
        self.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                         % (gid, f(x1), f(y1), f(x2), f(y2), stops))
        return "url(#%s)" % gid

    def rg(self, stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None):
        self.n += 1
        gid = "g%d" % self.n
        s = "".join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>' % (f(o), c, f(a)) for o, c, a in stops)
        fxy = ""
        if fx is not None:
            fxy = ' fx="%s" fy="%s"' % (f(fx), f(fy))
        self.defs.append('<radialGradient id="%s" cx="%s" cy="%s" r="%s"%s>%s</radialGradient>'
                         % (gid, f(cx), f(cy), f(r), fxy, s))
        return "url(#%s)" % gid

    # --- primitive
    def _st(self, stroke, sw, extra):
        s = ""
        if stroke:
            s = ' stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"' % (stroke, f(sw))
        return s + (" " + extra if extra else "")

    def poly(self, p, fill, stroke=OUT, sw=SW, extra=""):
        self.els.append('<polygon points="%s" fill="%s"%s/>' % (pts(p), fill, self._st(stroke, sw, extra)))

    def pl(self, p, stroke=OUT, sw=SW, extra=""):
        self.els.append('<polyline points="%s" fill="none"%s/>' % (pts(p), self._st(stroke, sw, extra)))

    def path(self, d, fill, stroke=OUT, sw=SW, extra=""):
        self.els.append('<path d="%s" fill="%s"%s/>' % (d, fill, self._st(stroke, sw, extra)))

    def circ(self, x, y, r, fill, stroke=OUT, sw=SW, extra=""):
        self.els.append('<circle cx="%s" cy="%s" r="%s" fill="%s"%s/>' % (f(x), f(y), f(r), fill, self._st(stroke, sw, extra)))

    def ell(self, x, y, rx, ry, fill, stroke=OUT, sw=SW, extra=""):
        self.els.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"%s/>'
                        % (f(x), f(y), f(rx), f(ry), fill, self._st(stroke, sw, extra)))

    def rect(self, x, y, w, h, fill, rx=0, stroke=OUT, sw=SW, extra=""):
        self.els.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
                        % (f(x), f(y), f(w), f(h), f(rx), fill, self._st(stroke, sw, extra)))

    def line(self, x1, y1, x2, y2, stroke=OUT, sw=SW, extra=""):
        self.els.append('<line x1="%s" y1="%s" x2="%s" y2="%s"%s/>' % (f(x1), f(y1), f(x2), f(y2), self._st(stroke, sw, extra)))

    def raw(self, s):
        self.els.append(s)

    def group(self, transform):
        self.els.append('<g transform="%s">' % transform)

    def end(self):
        self.els.append("</g>")

    # --- iso helper: (x, y) theo ô, z theo px
    def iso(self, x, y, z=0.0):
        return (self.ax + (x - y) * HW, self.ay + (x + y) * HH - z)

    def shadow(self, x, y, rx, ry, a=0.32):
        fill = self.rg([(0, "#000000", a), (0.65, "#000000", a * 0.55), (1, "#000000", 0)])
        self.ell(x, y, rx, ry, fill, stroke=None)

    def box(self, x0, y0, x1, y1, z0, z1, col, top=None, outline=True, sw=SW, grad=True):
        """Khối hộp isometric có 3 mặt sáng/tối."""
        top = top or lt(col, 0.12)
        i = self.iso
        tp = [i(x0, y0, z1), i(x1, y0, z1), i(x1, y1, z1), i(x0, y1, z1)]
        lf = [i(x0, y1, z1), i(x1, y1, z1), i(x1, y1, z0), i(x0, y1, z0)]
        rt = [i(x1, y0, z1), i(x1, y1, z1), i(x1, y1, z0), i(x1, y0, z0)]
        if grad:
            self.poly(lf, self.lg(dk(col, 0.02), dk(col, 0.16)), stroke=None)
            self.poly(rt, self.lg(dk(col, 0.22), dk(col, 0.36)), stroke=None)
            self.poly(tp, self.lg(lt(top, 0.18), top, 0, 0, 1, 1), stroke=None)
        else:
            self.poly(lf, dk(col, 0.08), stroke=None)
            self.poly(rt, dk(col, 0.28), stroke=None)
            self.poly(tp, top, stroke=None)
        # cạnh sáng phía trước mặt trên
        self.pl([i(x0, y1, z1), i(x1, y1, z1), i(x1, y0, z1)], stroke=lt(top, 0.5), sw=sw * 0.45, extra='stroke-opacity="0.8"')
        if outline:
            self.pl([i(x1, y1, z1), i(x1, y1, z0)], stroke=OUT, sw=sw * 0.45, extra='stroke-opacity="0.55"')
            self.poly([i(x0, y0, z1), i(x1, y0, z1), i(x1, y0, z0), i(x1, y1, z0), i(x0, y1, z0), i(x0, y1, z1)],
                      "none", sw=sw)

    def cyl(self, cx, cy, rx, ry, h, col, top=None, sw=SW):
        """Hình trụ đứng: (cx, cy) là tâm đáy trên màn hình."""
        top = top or lt(col, 0.15)
        side = self.lg(lt(col, 0.05), dk(col, 0.3), 0, 0, 1, 0, mid=col)
        d = "M%s,%s L%s,%s A%s,%s 0 0 0 %s,%s L%s,%s A%s,%s 0 0 0 %s,%s Z" % (
            f(cx - rx), f(cy - h), f(cx - rx), f(cy), f(rx), f(ry), f(cx + rx), f(cy), f(cx + rx), f(cy - h),
            f(rx), f(ry), f(cx - rx), f(cy - h))
        self.path(d, side, sw=sw)
        self.ell(cx, cy - h, rx, ry, self.lg(lt(top, 0.2), top), sw=sw)

    def save(self, name, folder=OUT_DIR):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
               '<defs>%s</defs>%s</svg>') % (self.w, self.h, self.w, self.h, "".join(self.defs), "".join(self.els))
        (folder / (name + ".svg")).write_text(svg, encoding="utf-8")
        if folder == OUT_DIR:
            manifest[name] = [self.w, self.h, self.ax, self.ay]


# ================================================================ NỀN

def diamond(c, inflate=2.0):
    return [(c.ax, c.ay - HH - inflate), (c.ax + HW + inflate * 2, c.ay), (c.ax, c.ay + HH + inflate),
            (c.ax - HW - inflate * 2, c.ay)]


def tile_canvas():
    return C(260, 132, 130, 66)


def floor_wood(name, base, seed):
    """Sàn ván gỗ lớn ấm áp, không kẻ viền ô để các ô liền mạch."""
    rnd = random.Random(seed)
    c = tile_canvas()
    c.poly(diamond(c), base, stroke=None)
    # 3 tấm ván chạy theo trục x, mỗi tấm sáng tối khác nhau một chút
    for k in range(3):
        y0, y1 = -0.5 + k / 3.0, -0.5 + (k + 1) / 3.0
        col = mix(base, lt(base, 0.12) if (k + seed) % 2 == 0 else dk(base, 0.05), 0.8)
        p = [c.iso(-0.5, y0), c.iso(0.5, y0), c.iso(0.5, y1), c.iso(-0.5, y1)]
        c.poly(p, c.lg(lt(col, 0.06), col, 0, 0, 1, 1), stroke=None)
        a1, b1 = c.iso(-0.5, y1), c.iso(0.5, y1)
        c.line(a1[0], a1[1], b1[0], b1[1], stroke=dk(base, 0.16), sw=2.4, extra='stroke-opacity="0.7"')
        a2, b2 = c.iso(-0.5, y0 + 0.03), c.iso(0.5, y0 + 0.03)
        c.line(a2[0], a2[1], b2[0], b2[1], stroke=lt(base, 0.35), sw=1.6, extra='stroke-opacity="0.6"')
        # mối nối đầu ván (thưa)
        if rnd.random() < 0.55:
            x = -0.5 + rnd.uniform(0.2, 0.8)
            u, v = c.iso(x, y0), c.iso(x, y1)
            c.line(u[0], u[1], v[0], v[1], stroke=dk(base, 0.14), sw=2, extra='stroke-opacity="0.6"')
    c.save(name)


def carpet_runner(name):
    """Thảm đỏ lối vào (chạy theo trục x)."""
    c = tile_canvas()
    c.poly(diamond(c), "#e9b77b", stroke=None)
    i = c.iso
    c.poly([i(-0.52, -0.36), i(0.52, -0.36), i(0.52, 0.36), i(-0.52, 0.36)], c.lg("#e2584a", "#c8443a", 0, 0, 1, 1),
           stroke=None)
    for y in (-0.27, 0.27):
        u, v = i(-0.52, y), i(0.52, y)
        c.line(u[0], u[1], v[0], v[1], stroke="#f6c95a", sw=3)
    c.save(name)


def wall_post(name):
    """Cột gỗ dựng ở góc / dọc tường."""
    c = C(70, 470, 35, 448)
    cx, cy = c.ax, c.ay
    h = 430
    c.rect(cx - 16, cy - h, 32, h, c.lg("#c98a55", "#93582f", 0, 0, 1, 0), rx=6, sw=4)
    c.rect(cx - 20, cy - h - 8, 40, 16, "#a8683d", rx=5, sw=4)
    c.rect(cx - 20, cy - 16, 40, 16, "#a8683d", rx=5, sw=4)
    c.line(cx - 6, cy - h + 14, cx - 6, cy - 24, stroke="#e2ad78", sw=3, extra='stroke-opacity="0.7"')
    c.save(name)


def floor_stone(name, base, seed):
    rnd = random.Random(seed)
    c = tile_canvas()
    c.poly(diamond(c), dk(base, 0.25), stroke=None)
    for gx in range(2):
        for gy in range(2):
            x0, y0 = -0.5 + gx * 0.5 + 0.03, -0.5 + gy * 0.5 + 0.03
            x1, y1 = x0 + 0.44, y0 + 0.44
            col = mix(base, lt(base, 0.25), rnd.random() * 0.8)
            p = [c.iso(x0, y0), c.iso(x1, y0), c.iso(x1, y1), c.iso(x0, y1)]
            c.poly(p, c.lg(lt(col, 0.15), dk(col, 0.05), 0, 0, 1, 1), stroke=dk(base, 0.4), sw=1.4,
                   extra='stroke-opacity="0.5"')
            a = c.iso(x0 + 0.06, y1 - 0.04)
            b = c.iso(x1 - 0.04, y1 - 0.04)
            c.line(a[0], a[1], b[0], b[1], stroke=lt(col, 0.4), sw=1.6, extra='stroke-opacity="0.6"')
    c.save(name)


def floor_tile_vip(name):
    c = tile_canvas()
    c.poly(diamond(c), c.lg("#8e2c3c", "#6d1d2d", 0, 0, 1, 1), stroke=None)
    i = c.iso
    c.poly([i(0, -0.32), i(0.32, 0), i(0, 0.32), i(-0.32, 0)], "#c9963e", stroke="#7a4f1a", sw=1.6)
    c.poly([i(0, -0.16), i(0.16, 0), i(0, 0.16), i(-0.16, 0)], "#f3d27a", stroke=None)
    c.poly(diamond(c, 0), "none", stroke="#d6a84c", sw=1.6, extra='stroke-opacity="0.55"')
    c.save(name)


def grass(name, seed):
    rnd = random.Random(seed)
    c = tile_canvas()
    c.poly(diamond(c), c.lg("#9fdc6a", "#86c955", 0, 0, 1, 1), stroke=None)
    for _ in range(9):
        x, y = rnd.uniform(-0.42, 0.42), rnd.uniform(-0.42, 0.42)
        if abs(x) + abs(y) > 0.55:
            continue
        p = c.iso(x, y)
        col = rnd.choice(["#6fb544", "#7cc24f", "#b6e27f"])
        c.path("M%s,%s q-3,-9 -7,-12 M%s,%s q2,-10 7,-13" % (f(p[0]), f(p[1]), f(p[0]), f(p[1])), "none",
               stroke=col, sw=2.6)
    if seed % 3 == 0:
        p = c.iso(rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2))
        c.circ(p[0], p[1] - 3, 3.2, "#fff6a8", stroke=None)
        c.circ(p[0] + 9, p[1] + 2, 2.8, "#ffb3c9", stroke=None)
    c.save(name)


def dirt(name, seed):
    rnd = random.Random(seed)
    c = tile_canvas()
    c.poly(diamond(c), c.lg("#e8c98e", "#d9b378", 0, 0, 1, 1), stroke=None)
    for _ in range(7):
        p = c.iso(rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4))
        if abs(p[0] - c.ax) / HW + abs(p[1] - c.ay) / HH > 0.85:
            continue
        r = rnd.uniform(3, 6)
        c.ell(p[0], p[1], r * 1.4, r * 0.8, rnd.choice(["#c99f62", "#f3dcaa", "#bf9358"]), stroke=None)
    c.save(name)


def floor_edge(name, side, col):
    """Bờ sàn dày ở cạnh trước: side 'l' (dọc trục x, mặt trước-trái) hoặc 'r'."""
    c = C(262, 110, 131, 40)
    i = c.iso
    t = 22
    if side == "l":
        p = [i(-0.5, 0.5, 0), i(0.5, 0.5, 0), i(0.5, 0.5, -t), i(-0.5, 0.5, -t)]
        fill = c.lg(dk(col, 0.1), dk(col, 0.3))
    else:
        p = [i(0.5, -0.5, 0), i(0.5, 0.5, 0), i(0.5, 0.5, -t), i(0.5, -0.5, -t)]
        fill = c.lg(dk(col, 0.28), dk(col, 0.45))
    c.poly(p, fill, stroke=OUT, sw=3)
    c.save(name)


# ================================================================ TƯỜNG

WALL_H = 360.0


def wall(name, side, kind, feature=None):
    """side 'l': tường dọc trục y tại x=-0.5 (mặt quay sang phải-xuống).
       side 'r': tường dọc trục x tại y=-0.5 (mặt quay sang trái-xuống).
       Neo = tâm ô chứa tường (ở sàn)."""
    # neo = iso(0,0) = tâm ô; cạnh tường cách tâm nửa ô
    if side == "l":
        a, b = (-0.5, -0.5), (-0.5, 0.5)
        c = C(160, 460, 144, 450)
    else:
        a, b = (-0.5, -0.5), (0.5, -0.5)
        c = C(160, 460, 16, 450)
    i = c.iso
    if kind == "a":
        upper, lower, beam = "#f8e4c6", "#d39a66", "#a8683d"
    else:
        upper, lower, beam = "#c46a4f", "#6e4a3a", "#4f3326"

    def q(z0, z1, inset=0.0):
        pa = (a[0] + (b[0] - a[0]) * inset, a[1] + (b[1] - a[1]) * inset)
        pb = (b[0] + (a[0] - b[0]) * inset, b[1] + (a[1] - b[1]) * inset)
        return [i(pa[0], pa[1], z0), i(pb[0], pb[1], z0), i(pb[0], pb[1], z1), i(pa[0], pa[1], z1)]

    shade = 0.0 if side == "l" else 0.12
    c.poly(q(0, WALL_H), c.lg(lt(dk(upper, shade), 0.1), dk(upper, shade + 0.08)), stroke=None)
    if kind == "b":
        # gạch
        rows = 9
        for r in range(rows):
            z = 70 + r * (WALL_H - 80) / rows
            p0 = q(z, z)[0]
            p1 = q(z, z)[1]
            c.line(p0[0], p0[1], p1[0], p1[1], stroke=dk(upper, 0.35), sw=2)
            for k in range(2):
                t = (k + (0.25 if r % 2 else 0.75)) / 2.0
                t = min(max(t, 0.05), 0.95)
                pa = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                z2 = z + (WALL_H - 80) / rows
                u, v = i(pa[0], pa[1], z), i(pa[0], pa[1], min(z2, WALL_H - 10))
                c.line(u[0], u[1], v[0], v[1], stroke=dk(upper, 0.35), sw=2)
    else:
        # vệt sáng nhẹ trên vữa
        p = q(150, 200, 0.2)
        c.poly(p, lt(upper, 0.35), stroke=None, extra='opacity="0.35"')
    # chân tường gỗ
    c.poly(q(0, 70), c.lg(lt(dk(lower, shade), 0.08), dk(lower, shade + 0.15)), stroke=None)
    for k in range(1, 4):
        t = k / 4.0
        pa = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        u, v = i(pa[0], pa[1], 6), i(pa[0], pa[1], 64)
        c.line(u[0], u[1], v[0], v[1], stroke=dk(lower, 0.3), sw=2.2)
    p0, p1 = q(70, 70)[0], q(70, 70)[1]
    c.line(p0[0], p0[1], p1[0], p1[1], stroke=beam, sw=7)
    # dầm trên
    c.poly(q(WALL_H - 16, WALL_H), dk(beam, shade), stroke=None)

    if feature == "window":
        z0, z1 = 150, 250
        c.poly(q(z0 - 8, z1 + 8, 0.16), "#8a5530", stroke=OUT, sw=3)
        c.poly(q(z0, z1, 0.22), c.lg("#d9f4ff", "#8fd0f0"), stroke=None)
        # phản chiếu
        g1 = q(z0 + 30, z1, 0.22)
        c.poly([g1[0], (g1[0][0] + (g1[1][0] - g1[0][0]) * 0.35, g1[0][1] + (g1[1][1] - g1[0][1]) * 0.35),
                (g1[3][0] + (g1[2][0] - g1[3][0]) * 0.15, g1[3][1] + (g1[2][1] - g1[3][1]) * 0.15), g1[3]],
               "#ffffff", stroke=None, extra='opacity="0.45"')
        m = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        u, v = i(m[0], m[1], z0), i(m[0], m[1], z1)
        c.line(u[0], u[1], v[0], v[1], stroke="#8a5530", sw=6)
        mm = q((z0 + z1) / 2, (z0 + z1) / 2, 0.22)
        c.line(mm[0][0], mm[0][1], mm[1][0], mm[1][1], stroke="#8a5530", sw=6)
        # bồn hoa
        c.poly(q(z0 - 26, z0 - 8, 0.1), "#c1603d", stroke=OUT, sw=3)
        for k in range(4):
            t = 0.2 + k * 0.2
            pa = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            u = i(pa[0], pa[1], z0 - 4)
            c.circ(u[0], u[1], 10, "#5fb84a", stroke=OUT, sw=2.5)
            c.circ(u[0], u[1] - 5, 5, ["#ff6b8b", "#ffd34d"][k % 2], stroke=None)
    elif feature == "door":
        z1 = 180
        c.poly(q(0, z1 + 10, 0.12), "#6b3f22", stroke=OUT, sw=3)
        c.poly(q(0, z1, 0.2), c.lg("#b77744", "#8a5530"), stroke=None)
        for k in range(1, 3):
            t = 0.2 + k * 0.2
            pa = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            u, v = i(pa[0], pa[1], 6), i(pa[0], pa[1], z1 - 6)
            c.line(u[0], u[1], v[0], v[1], stroke=dk("#8a5530", 0.3), sw=2.5)
        t = 0.7
        pa = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        u = i(pa[0], pa[1], 90)
        c.circ(u[0], u[1], 6, "#ffd34d", stroke=OUT, sw=2.5)
        # biển số phòng
        u = i((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z1 + 32)
        c.ell(u[0], u[1], 22, 14, "#f6d27a", stroke=OUT, sw=3)

    # viền ngoài
    c.poly(q(0, WALL_H), "none", stroke=OUT, sw=SW)
    c.save(name)


# ================================================================ ĐỒ VẬT

def obj_canvas(w, h, ay=None):
    return C(w, h, w / 2, ay if ay is not None else h - 40)


def table(name, tier):
    c = obj_canvas(240, 210, 150)
    c.shadow(c.ax, c.ay + 4, 100, 46)
    if tier == 1:
        top, leg = "#d7a066", "#8a5530"
        hgt = 70
        for lx, ly in [(-0.26, -0.26), (0.26, -0.26), (-0.26, 0.26), (0.26, 0.26)]:
            c.box(lx - 0.035, ly - 0.035, lx + 0.035, ly + 0.035, 0, hgt - 10, leg, sw=3)
        c.box(-0.34, -0.34, 0.34, 0.34, hgt - 12, hgt, top)
        # vân gỗ mặt bàn
        for k in (-0.12, 0.12):
            a, b = c.iso(-0.3, k, hgt), c.iso(0.3, k, hgt)
            c.line(a[0], a[1], b[0], b[1], stroke=dk(top, 0.18), sw=2)
    elif tier == 2:
        hgt = 74
        cx, cy = c.ax, c.ay
        c.cyl(cx, cy - 4, 14, 7, hgt - 10, "#6b3f22", sw=3)
        c.ell(cx, cy - 2, 40, 18, "#6b3f22", sw=3)
        c.cyl(cx, cy - hgt + 14, 88, 44, 14, "#b0703e", top="#c98450")
        # khăn trải bàn
        c.ell(cx, cy - hgt, 70, 34, "#fffaf0", stroke=dk("#fffaf0", 0.2), sw=2.5)
        c.ell(cx, cy - hgt, 52, 25, "none", stroke="#e7795a", sw=3, extra='stroke-dasharray="8 6"')
        c.ell(cx - 26, cy - hgt - 8, 22, 8, "#ffffff", stroke=None, extra='opacity="0.6"')
    else:
        hgt = 78
        cx, cy = c.ax, c.ay
        c.cyl(cx, cy - 4, 16, 8, hgt - 10, "#3d2a3a", sw=3)
        c.ell(cx, cy - 2, 44, 20, "#c9963e", sw=3)
        c.cyl(cx, cy - hgt + 18, 94, 47, 20, "#c4283e", top="#d83a50")
        c.ell(cx, cy - hgt + 18, 94, 47, "none", stroke="#f3d27a", sw=4,
              extra='stroke-dasharray="1 14" stroke-opacity="0.9"')
        c.ell(cx, cy - hgt, 94, 47, "none", stroke="#f3d27a", sw=4)
        c.ell(cx, cy - hgt, 66, 32, "#fff3d6", stroke="#c9963e", sw=3)
        # bình hoa nhỏ
        c.cyl(cx + 40, cy - hgt - 2, 8, 4, 18, "#4fa3e0", sw=2.5)
        c.circ(cx + 40, cy - hgt - 26, 8, "#ff6b8b", stroke=OUT, sw=2.5)
    c.save(name)


def chair(name, tier):
    c = obj_canvas(130, 200, 160)
    c.shadow(c.ax, c.ay + 2, 48, 22)
    cols = {1: "#c98b52", 2: "#9c5b30", 3: "#c4283e"}
    col = cols[tier]
    leg = "#7a4a2a" if tier < 3 else "#c9963e"
    for lx, ly in [(-0.17, -0.17), (0.17, -0.17), (-0.17, 0.17), (0.17, 0.17)]:
        c.box(lx - 0.025, ly - 0.025, lx + 0.025, ly + 0.025, 0, 44, leg, sw=2.5)
    c.box(-0.2, -0.2, 0.2, 0.2, 40, 52, col, sw=4)
    # lưng ghế (phía sau = y âm, x âm)
    c.box(-0.2, -0.2, 0.2, -0.13, 52, 120, col if tier != 3 else "#d83a50", sw=4)
    if tier == 3:
        a = c.iso(0, -0.13, 100)
        c.circ(a[0], a[1], 9, "#f3d27a", stroke=OUT, sw=3)
    c.save(name)


def kitchen_counter(name):
    c = obj_canvas(270, 230, 170)
    c.shadow(c.ax, c.ay + 4, 120, 50, 0.25)
    c.box(-0.5, -0.38, 0.5, 0.38, 0, 82, "#d9a066", top="#f1e2c6")
    i = c.iso
    # cửa tủ mặt trước
    for k in range(2):
        x0, x1 = -0.45 + k * 0.5, -0.07 + k * 0.5
        p = [i(x0, 0.38, 70), i(x1, 0.38, 70), i(x1, 0.38, 12), i(x0, 0.38, 12)]
        c.poly(p, c.lg("#e6b077", "#c98b52"), stroke=dk("#c98b52", 0.4), sw=2.5)
        u = i(x1 - 0.06, 0.38, 44)
        c.circ(u[0], u[1], 4, "#8a5530", stroke=None)
    c.save(name)


def stove(name):
    c = obj_canvas(270, 250, 190)
    c.shadow(c.ax, c.ay + 4, 120, 50, 0.25)
    c.box(-0.5, -0.38, 0.5, 0.38, 0, 82, "#6b6f78", top="#4a4d55")
    i = c.iso
    # cửa lò
    p = [i(-0.3, 0.38, 64), i(0.3, 0.38, 64), i(0.3, 0.38, 16), i(-0.3, 0.38, 16)]
    c.poly(p, c.lg("#3a3c42", "#2a2c30"), stroke=OUT, sw=3)
    p = [i(-0.2, 0.38, 52), i(0.2, 0.38, 52), i(0.2, 0.38, 28), i(-0.2, 0.38, 28)]
    c.poly(p, c.lg("#ffb347", "#ff6a2a"), stroke=None)
    for dx in (-0.12, 0.0, 0.12):
        u = i(dx, 0.38, 30)
        c.path("M%s,%s q-6,-10 0,-18 q6,8 0,18 Z" % (f(u[0]), f(u[1])), "#ffe27a", stroke=None)
    # bếp trên mặt
    for bx in (-0.22, 0.22):
        u = i(bx, 0, 82)
        c.ell(u[0], u[1], 34, 17, "#2c2c30", stroke=OUT, sw=3)
        c.ell(u[0], u[1], 22, 11, "none", stroke="#ff7b3a", sw=3)
    # tay nắm
    u = i(-0.32, 0.38, 72)
    v = i(0.32, 0.38, 72)
    c.line(u[0], u[1] + 0, v[0], v[1], stroke="#c0c6cf", sw=4)
    c.save(name)


def pot(name):
    c = obj_canvas(130, 130, 100)
    cx, cy = c.ax, c.ay
    c.cyl(cx, cy, 42, 20, 46, "#9aa5b1", top="#c7d0d9")
    c.ell(cx, cy - 46, 34, 15, c.lg("#f2a541", "#d9822b"), stroke=OUT, sw=3)
    c.ell(cx - 12, cy - 49, 9, 3, "#ffd27a", stroke=None)
    for s in (-1, 1):
        c.rect(cx + s * 44 - 7, cy - 38, 14, 8, "#5b5f66", rx=4, sw=3)
    c.save(name)


def cashier_counter(name):
    c = obj_canvas(270, 260, 200)
    c.shadow(c.ax, c.ay + 4, 120, 50, 0.25)
    c.box(-0.5, -0.4, 0.5, 0.4, 0, 86, "#b66f43", top="#e3b47c")
    i = c.iso
    # bảng trang trí mặt trước
    p = [i(-0.42, 0.4, 72), i(0.42, 0.4, 72), i(0.42, 0.4, 20), i(-0.42, 0.4, 20)]
    c.poly(p, c.lg("#8a5530", "#6b3f22"), stroke=OUT, sw=2.5)
    u = i(0, 0.4, 46)
    c.circ(u[0], u[1], 15, "#ffc93c", stroke=OUT, sw=3)
    c.circ(u[0], u[1], 8, "#f5a623", stroke=None)
    # máy tính tiền
    c.box(0.05, -0.25, 0.38, 0.12, 86, 120, "#e2e6ea", top="#f5f7f9", sw=3.5)
    c.box(0.12, -0.22, 0.3, -0.12, 120, 150, "#4fa3e0", sw=3)
    # bàn tính + sổ
    c.box(-0.38, -0.2, -0.08, 0.15, 86, 94, "#f6f1e3", sw=3)
    a, b = c.iso(-0.35, -0.02, 94), c.iso(-0.11, -0.02, 94)
    c.line(a[0], a[1], b[0], b[1], stroke="#c4283e", sw=3)
    c.save(name)


def shelf(name):
    c = obj_canvas(200, 300, 250)
    c.shadow(c.ax, c.ay + 2, 80, 34, 0.25)
    col = "#a96a3c"
    c.box(-0.42, -0.18, 0.42, 0.18, 0, 200, col, top=lt(col, 0.2))
    i = c.iso
    jars = ["#ff8f5a", "#7cc96b", "#ffd34d", "#4fa3e0", "#ef7fb0", "#a56be0"]
    for r, z in enumerate((30, 92, 154)):
        a, b = i(-0.42, 0.18, z), i(0.42, 0.18, z)
        c.line(a[0], a[1], b[0], b[1], stroke=dk(col, 0.4), sw=5)
        for k in range(3):
            u = i(-0.28 + k * 0.28, 0.12, z)
            jc = jars[(r * 3 + k) % len(jars)]
            c.cyl(u[0], u[1], 14, 6, 36, jc, sw=2.5)
            c.ell(u[0], u[1] - 38, 10, 4, "#e9d2a8", stroke=OUT, sw=2)
    c.save(name)


def plant_pot(name):
    c = obj_canvas(130, 200, 170)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 46, 18)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 34), f(cy - 50), f(cx + 34), f(cy - 50), f(cx + 26), f(cy),
                                               f(cx - 26), f(cy)), c.lg("#e07a4f", "#b25333", 0, 0, 1, 0), sw=4)
    c.rect(cx - 38, cy - 60, 76, 14, c.lg("#ec8a5f", "#c1603d"), rx=6, sw=4)
    leaves = [(-26, -78, 22), (24, -80, 22), (0, -100, 26), (-14, -122, 20), (16, -118, 20)]
    for x, y, r in leaves:
        c.circ(cx + x, cy + y, r + 3, OUT, stroke=None)
    for x, y, r in leaves:
        c.circ(cx + x, cy + y, r, c.rg([(0, "#8fe06a", 1), (1, "#4fa83a", 1)], 0.4, 0.35, 0.7), stroke=None)
    c.circ(cx - 8, cy - 126, 6, "#c4f59a", stroke=None)
    c.save(name)


def lantern(name):
    c = obj_canvas(110, 260, 230)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 30, 12)
    # cột đèn
    c.rect(cx - 5, cy - 150, 10, 150, c.lg("#5b3a22", "#3d2716", 0, 0, 1, 0), rx=4, sw=3)
    c.ell(cx, cy - 2, 22, 10, "#3d2716", sw=3)
    c.path("M%s,%s q20,-10 26,10" % (f(cx), f(cy - 150)), "none", stroke=OUT, sw=4)
    # lồng đèn đỏ
    lx, ly = cx + 26, cy - 112
    c.circ(lx, ly, 34, c.rg([(0, "#fff0a0", 1), (0.35, "#ffb84d", 1), (1, "#d6313f", 1)], 0.45, 0.4, 0.6), sw=4)
    c.ell(lx, ly, 34, 34, "none", stroke=dk("#d6313f", 0.3), sw=2, extra='stroke-opacity="0.6"')
    c.ell(lx, ly, 18, 34, "none", stroke=dk("#d6313f", 0.3), sw=2, extra='stroke-opacity="0.6"')
    c.rect(lx - 14, ly - 40, 28, 9, "#f3c84b", rx=3, sw=3)
    c.rect(lx - 14, ly + 31, 28, 9, "#f3c84b", rx=3, sw=3)
    c.path("M%s,%s l-4,22 M%s,%s l0,24 M%s,%s l4,22" % (f(lx - 6), f(ly + 40), f(lx), f(ly + 40), f(lx + 6), f(ly + 40)),
           "none", stroke="#ffcf4d", sw=3)
    c.save(name)


def painting(name, side, motif):
    c = C(240, 380, 120, 352)
    i = c.iso
    # tranh treo trên mặt tường, z từ 90 tới 180
    if side == "l":
        a, b = (-0.5, -0.32), (-0.5, 0.32)
    else:
        a, b = (-0.32, -0.5), (0.32, -0.5)
    z0, z1 = 150, 240

    def q(za, zb, inset):
        pa = (a[0] + (b[0] - a[0]) * inset, a[1] + (b[1] - a[1]) * inset)
        pb = (b[0] + (a[0] - b[0]) * inset, b[1] + (a[1] - b[1]) * inset)
        return [i(pa[0], pa[1], za), i(pb[0], pb[1], za), i(pb[0], pb[1], zb), i(pa[0], pa[1], zb)]
    c.poly(q(z0 - 6, z1 + 6, -0.04), "#c9963e", sw=4)
    if motif == 0:
        c.poly(q(z0, z1, 0.06), c.lg("#bfe9ff", "#f6e2b8"), stroke=None)
        m = q(z0, z0 + 50, 0.06)
        c.poly([m[0], m[1], (m[1][0] + (m[2][0] - m[1][0]) * 0.6, m[1][1] + (m[2][1] - m[1][1]) * 0.6),
                ((m[0][0] + m[1][0]) / 2, (m[3][1] + m[2][1]) / 2), m[3]], "#6cbf5a", stroke=None)
        s = q(z1 - 28, z1 - 28, 0.7)[0]
        c.circ(s[0], s[1], 9, "#ff9f43", stroke=None)
    else:
        c.poly(q(z0, z1, 0.06), c.lg("#ffe9c9", "#f5cf97"), stroke=None)
        m = q((z0 + z1) / 2, (z0 + z1) / 2, 0.5)[0]
        c.circ(m[0], m[1], 16, "#e85d5d", stroke=OUT, sw=2.5)
        c.path("M%s,%s q12,-26 26,-30" % (f(m[0] - 10), f(m[1] + 26)), "none", stroke="#5fb84a", sw=4)
    c.save(name)


def rug(name):
    c = C(520, 270, 260, 135)
    i = c.iso
    c.poly([i(-1, -1), i(1, -1), i(1, 1), i(-1, 1)], c.lg("#d65a4a", "#b8423a", 0, 0, 1, 1), stroke=OUT, sw=3.5)
    c.poly([i(-0.85, -0.85), i(0.85, -0.85), i(0.85, 0.85), i(-0.85, 0.85)], "none", stroke="#f2c14e", sw=4)
    c.poly([i(-0.5, 0), i(0, -0.5), i(0.5, 0), i(0, 0.5)], "#f2c14e", stroke=OUT, sw=2.5)
    c.poly([i(-0.25, 0), i(0, -0.25), i(0.25, 0), i(0, 0.25)], "#e8794f", stroke=None)
    c.save(name)


def tree(name, variant):
    c = obj_canvas(240, 330, 300)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 4, 80, 32, 0.28)
    c.path("M%s,%s q-4,-60 -2,-110 l24,0 q2,50 -2,110 Z" % (f(cx - 11), f(cy)), c.lg("#9a6438", "#6b4123", 0, 0, 1, 0),
           sw=4)
    if variant == 0:
        blobs = [(-46, -150, 50), (44, -150, 50), (0, -200, 62), (-26, -236, 40), (30, -232, 40)]
        light, dark = "#8fe06a", "#3f9a34"
    else:
        blobs = [(0, -130, 56), (0, -186, 50), (0, -236, 38)]
        light, dark = "#7fd88a", "#2f8a52"
    for x, y, r in blobs:
        c.circ(cx + x, cy + y, r + 4, OUT, stroke=None)
    for x, y, r in blobs:
        c.circ(cx + x, cy + y, r, c.rg([(0, light, 1), (1, dark, 1)], 0.35, 0.3, 0.75), stroke=None)
    for x, y, r in blobs[:3]:
        c.ell(cx + x - r * 0.3, cy + y - r * 0.4, r * 0.32, r * 0.18, "#ffffff", stroke=None, extra='opacity="0.25"')
    if variant == 0:
        for x, y in [(-30, -170), (26, -208), (40, -140)]:
            c.circ(cx + x, cy + y, 7, "#ff6b6b", stroke=OUT, sw=2.5)
    c.save(name)


def bush(name):
    c = obj_canvas(170, 150, 120)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 64, 24)
    blobs = [(-30, -26, 30), (30, -26, 30), (0, -46, 34)]
    for x, y, r in blobs:
        c.circ(cx + x, cy + y, r + 4, OUT, stroke=None)
    for x, y, r in blobs:
        c.circ(cx + x, cy + y, r, c.rg([(0, "#9ae273", 1), (1, "#4ea83a", 1)], 0.4, 0.3, 0.75), stroke=None)
    for x, y, col in [(-26, -40, "#ff8fb1"), (14, -62, "#ffd34d"), (34, -30, "#ff8fb1"), (-4, -26, "#ffffff"),
                      (-40, -18, "#ffd34d")]:
        for k in range(5):
            ang = k * 2 * math.pi / 5
            c.circ(cx + x + math.cos(ang) * 5, cy + y + math.sin(ang) * 5, 4, col, stroke=None)
        c.circ(cx + x, cy + y, 3, "#ffb347", stroke=None)
    c.save(name)


def fence(name, axis):
    c = C(280, 190, 140, 140)
    i = c.iso
    col = "#e6c08a"
    if axis == "x":
        a, b = (-0.5, 0.0), (0.5, 0.0)
    else:
        a, b = (0.0, -0.5), (0.0, 0.5)
    c.shadow(c.ax, c.ay + 4, 90, 26, 0.18)
    # thanh ngang
    for z in (30, 62):
        p0, p1 = i(a[0], a[1], z), i(b[0], b[1], z)
        c.line(p0[0], p0[1], p1[0], p1[1], stroke=OUT, sw=12)
        c.line(p0[0], p0[1], p1[0], p1[1], stroke=col, sw=7)
    for k in range(3):
        t = (k + 0.5) / 3.0
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        u = i(x, y, 0)
        c.path("M%s,%s l0,-78 l9,-12 l9,12 l0,78 Z" % (f(u[0] - 9), f(u[1])), c.lg(lt(col, 0.2), dk(col, 0.2), 0, 0, 1, 0),
               sw=3.5)
    c.save(name)


def gate(name):
    """Cổng vào đặt trên hàng rào dọc trục x (neo = tâm ô)."""
    c = C(320, 380, 160, 330)
    c.shadow(c.ax, c.ay + 4, 120, 36, 0.2)
    wood = "#a96a3c"
    for x in (-0.5, 0.5):
        c.box(x - 0.06, -0.06, x + 0.06, 0.06, 0, 210, wood, sw=4)
    c.box(-0.62, -0.08, 0.62, 0.08, 196, 218, "#8a5530", sw=4)
    # mái ngói: hai mái dốc + đầu hồi
    i = c.iso
    x0, x1, zb, zt = -0.72, 0.72, 214, 262
    c.poly([i(x0, -0.26, zb), i(x1, -0.26, zb), i(x1, 0, zt), i(x0, 0, zt)], c.lg("#c4423e", "#a8322f"), sw=4)
    c.poly([i(x0, 0.26, zb), i(x1, 0.26, zb), i(x1, 0, zt), i(x0, 0, zt)], c.lg("#e86a5f", "#c4423e"), sw=4)
    c.poly([i(x1, -0.26, zb), i(x1, 0.26, zb), i(x1, 0, zt)], "#9a2e2b", sw=4)
    for k in range(1, 6):
        t = x0 + (x1 - x0) * k / 6.0
        u, v = i(t, 0.26, zb), i(t, 0, zt)
        c.line(u[0], u[1], v[0], v[1], stroke=dk("#c4423e", 0.25), sw=2.5)
    # biển gỗ treo dưới xà
    c.box(-0.34, -0.02, 0.34, 0.02, 150, 188, "#f6d27a", sw=4)
    for x in (-0.24, 0.24):
        u, v = i(x, 0, 188), i(x, 0, 198)
        c.line(u[0], u[1], v[0], v[1], stroke=OUT, sw=3)
    c.save(name)


def bed(name):
    c = obj_canvas(270, 230, 180)
    c.shadow(c.ax, c.ay + 4, 116, 48, 0.25)
    c.box(-0.46, -0.32, 0.46, 0.32, 0, 40, "#a96a3c")
    c.box(-0.42, -0.28, 0.42, 0.28, 40, 58, "#f8f4ea", top="#ffffff")
    c.box(-0.42, -0.28, 0.1, 0.28, 58, 64, "#6fa8dc", top="#8fc1ea")
    c.box(0.18, -0.22, 0.38, 0.22, 58, 74, "#ffffff", top="#ffffff", sw=3.5)
    c.box(0.42, -0.32, 0.5, 0.32, 0, 110, "#8a5530")
    c.save(name)


def signpost(name):
    c = C(220, 260, 110, 230)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 40, 14)
    c.rect(cx - 7, cy - 150, 14, 150, c.lg("#9a6438", "#6b4123", 0, 0, 1, 0), rx=4, sw=3.5)
    c.rect(cx - 90, cy - 206, 180, 70, c.lg("#e7b06e", "#c98b52"), rx=14, sw=5)
    c.rect(cx - 80, cy - 198, 160, 54, "none", rx=10, stroke=lt("#e7b06e", 0.4), sw=2.5)
    c.save(name)


# ================================================================ NHÂN VẬT

SKIN = "#f9d2ad"


def person(name, outfit, hair_style, hair_col, sit=False, tray=False, hat=None, extra=None):
    """Nhân vật chibi đầu to nhìn 3/4 về phía phải-dưới. Neo = giữa hai chân."""
    w, h = 150, 220
    c = C(w, h, 75, 206)
    cx, by = c.ax, c.ay
    lift = 26 if sit else 0
    c.shadow(cx, by, 36, 12, 0.3)
    top, bottom = outfit["top"], outfit.get("bottom", "#4b3a5a")
    shoe = outfit.get("shoe", "#3b2a20")
    # chân
    if not sit:
        for lx in (-14, 4):
            c.rect(cx + lx, by - 40, 12, 36, c.lg(bottom, dk(bottom, 0.25), 0, 0, 1, 0), rx=5, sw=3.5)
            c.ell(cx + lx + 7, by - 4, 10, 6, shoe, sw=3)
    else:
        for lx in (-16, 4):
            c.rect(cx + lx, by - 52, 14, 26, c.lg(bottom, dk(bottom, 0.25), 0, 0, 1, 0), rx=6, sw=3.5)
            c.ell(cx + lx + 10, by - 26, 10, 6, shoe, sw=3)
    body_y = by - 40 - lift
    # thân
    long_dress = outfit.get("long", False) and not sit
    if long_dress:
        c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
            f(cx - 26), f(body_y - 48), f(cx - 34), f(body_y - 10), f(cx - 30), f(by - 14), f(cx + 30), f(by - 14),
            f(cx + 34), f(body_y - 10), f(cx + 26), f(body_y - 48)), c.lg(lt(top, 0.12), dk(top, 0.2), 0, 0, 1, 0), sw=4)
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
        f(cx - 24), f(body_y - 50), f(cx - 32), f(body_y - 20), f(cx - 26), f(body_y + 4),
        f(cx + 26), f(body_y + 4), f(cx + 32), f(body_y - 20), f(cx + 24), f(body_y - 50)),
        c.lg(lt(top, 0.15), dk(top, 0.18), 0, 0, 1, 0), sw=4)
    if outfit.get("apron"):
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 16), f(body_y - 34), f(cx + 16), f(body_y - 34),
                                                   f(cx + 20), f(body_y + 6), f(cx - 20), f(body_y + 6)),
               outfit["apron"], sw=3)
        c.rect(cx - 8, body_y - 20, 16, 10, dk(outfit["apron"], 0.15), rx=3, stroke=None)
    if outfit.get("vest"):
        v = outfit["vest"]
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 24), f(body_y - 48), f(cx - 4), f(body_y - 18),
                                                   f(cx - 4), f(body_y + 4), f(cx - 26), f(body_y + 4)), v, sw=3)
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx + 24), f(body_y - 48), f(cx + 4), f(body_y - 18),
                                                   f(cx + 4), f(body_y + 4), f(cx + 26), f(body_y + 4)), v, sw=3)
    if outfit.get("bow"):
        bx, bw = cx, body_y - 46
        c.path("M%s,%s l-12,-7 l0,14 Z M%s,%s l12,-7 l0,14 Z" % (f(bx), f(bw), f(bx), f(bw)), outfit["bow"], sw=2.5)
    if outfit.get("buttons"):
        for k in range(3):
            c.circ(cx + 2, body_y - 36 + k * 12, 2.6, outfit["buttons"], stroke=None)
    if outfit.get("trim"):
        c.path("M%s,%s L%s,%s" % (f(cx - 2), f(body_y - 50), f(cx - 2), f(body_y + 2)), "none", stroke=outfit["trim"], sw=4)
    # tay
    arm = outfit.get("arm", top)
    if tray:
        c.path("M%s,%s q16,4 30,-6" % (f(cx + 18), f(body_y - 40)), "none", stroke=OUT, sw=13)
        c.path("M%s,%s q16,4 30,-6" % (f(cx + 18), f(body_y - 40)), "none", stroke=arm, sw=8)
        c.circ(cx + 50, body_y - 47, 6, SKIN, sw=3)
        # khay
        c.ell(cx + 50, body_y - 56, 36, 11, c.lg("#d7dde4", "#a9b3be"), sw=3.5)
        c.ell(cx + 50, body_y - 58, 28, 7, "none", stroke="#ffffff", sw=2, extra='stroke-opacity="0.7"')
        c.path("M%s,%s q-6,14 2,24" % (f(cx - 24), f(body_y - 42)), "none", stroke=OUT, sw=13)
        c.path("M%s,%s q-6,14 2,24" % (f(cx - 24), f(body_y - 42)), "none", stroke=arm, sw=8)
        c.circ(cx - 21, body_y - 16, 6, SKIN, sw=3)
    else:
        for s in (-1, 1):
            x0 = cx + s * 24
            c.path("M%s,%s q%s,14 %s,26" % (f(x0), f(body_y - 44), f(s * 8), f(s * 4)), "none", stroke=OUT, sw=13)
            c.path("M%s,%s q%s,14 %s,26" % (f(x0), f(body_y - 44), f(s * 8), f(s * 4)), "none", stroke=arm, sw=8)
            c.circ(x0 + s * 4, body_y - 16, 6, SKIN, sw=3)
    # đầu
    hx, hy = cx + 2, body_y - 86
    r = 40
    if hair_style in ("long", "pony"):
        c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
            f(hx - 40), f(hy - 6), f(hx - 46), f(hy + 34), f(hx - 30), f(hy + 52), f(hx + 30), f(hy + 52),
            f(hx + 46), f(hy + 34), f(hx + 40), f(hy - 6)), dk(hair_col, 0.12), sw=4)
    if hair_style == "pony":
        c.ell(hx - 40, hy + 18, 14, 26, dk(hair_col, 0.08), sw=4)
    c.circ(hx, hy, r, c.rg([(0, lt(SKIN, 0.35), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.12), 1)], 0.42, 0.38, 0.6), sw=SW)
    # tai
    c.ell(hx - r + 2, hy + 6, 7, 10, SKIN, sw=3)
    # tóc
    hc = c.rg([(0, lt(hair_col, 0.3), 1), (1, hair_col, 1)], 0.4, 0.2, 0.8)
    if hair_style == "short":
        c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(hx - 42), f(hy + 4), f(hx - 46), f(hy - 46), f(hx), f(hy - 44), f(hx + 46), f(hy - 46), f(hx + 42),
            f(hy + 2), f(hx + 30), f(hy - 18), f(hx + 6), f(hy - 16), f(hx - 22), f(hy - 22), f(hx - 42), f(hy + 4)),
            hc, sw=4)
    elif hair_style == "spiky":
        d = "M%s,%s " % (f(hx - 42), f(hy + 2))
        for k in range(7):
            ang = math.pi + k * math.pi / 6
            ang2 = math.pi + (k + 0.5) * math.pi / 6
            d += "L%s,%s L%s,%s " % (f(hx + math.cos(ang2) * 56), f(hy + math.sin(ang2) * 52 - 4),
                                     f(hx + math.cos(ang + math.pi / 6) * 40), f(hy + math.sin(ang + math.pi / 6) * 40 - 2))
        d += "Q%s,%s %s,%s Z" % (f(hx), f(hy - 18), f(hx - 42), f(hy + 2))
        c.path(d, hc, sw=4)
    elif hair_style in ("bob", "long", "pony"):
        c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(hx - 44), f(hy + 22), f(hx - 50), f(hy - 50), f(hx + 2), f(hy - 46), f(hx + 52), f(hy - 46),
            f(hx + 44), f(hy + 18), f(hx + 36), f(hy + 18), f(hx + 30), f(hy - 14), f(hx - 6), f(hy - 24),
            f(hx - 32), f(hy - 16), f(hx - 36), f(hy + 22)), hc, sw=4)
    elif hair_style == "bun":
        c.circ(hx + 4, hy - 46, 18, hc, sw=4)
        c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(hx - 42), f(hy + 6), f(hx - 44), f(hy - 44), f(hx + 2), f(hy - 42), f(hx + 46), f(hy - 42), f(hx + 42),
            f(hy + 4), f(hx + 4), f(hy - 26), f(hx - 42), f(hy + 6)), hc, sw=4)
    elif hair_style == "bald":
        c.path("M%s,%s Q%s,%s %s,%s" % (f(hx - 40), f(hy), f(hx - 44), f(hy - 20), f(hx - 30), f(hy - 26)), "none",
               stroke=hair_col, sw=8)
    # mũ
    if hat == "chef":
        c.rect(hx - 30, hy - 52, 60, 18, "#ffffff", rx=6, sw=4)
        for x, y, rr in [(-20, -64, 17), (20, -64, 17), (0, -76, 21)]:
            c.circ(hx + x, hy + y, rr + 2.5, OUT, stroke=None)
        for x, y, rr in [(-20, -64, 17), (20, -64, 17), (0, -76, 21)]:
            c.circ(hx + x, hy + y, rr, c.rg([(0, "#ffffff", 1), (1, "#dfe4ec", 1)], 0.4, 0.3, 0.8), stroke=None)
        c.rect(hx - 28, hy - 50, 56, 14, c.lg("#ffffff", "#e3e8ef"), rx=5, stroke=None)
    elif hat == "cap":
        c.path("M%s,%s Q%s,%s %s,%s Z" % (f(hx - 42), f(hy - 10), f(hx), f(hy - 72), f(hx + 42), f(hy - 10)),
               c.lg(lt(outfit.get("hat", "#e85d5d"), 0.15), outfit.get("hat", "#e85d5d")), sw=4)
        c.ell(hx + 34, hy - 10, 26, 8, dk(outfit.get("hat", "#e85d5d"), 0.15), sw=4)
    elif hat == "non_la":
        c.poly([(hx - 70, hy - 18), (hx + 72, hy - 18), (hx + 2, hy - 78)], c.lg("#f6e3a1", "#d9b968", 0, 0, 1, 0), sw=4)
        c.line(hx - 40, hy - 32, hx + 40, hy - 32, stroke="#c9a14f", sw=2.5)
    elif hat == "khan_dong":
        c.ell(hx, hy - 34, 46, 18, c.lg("#8d3bb5", "#5d1f80"), sw=4)
        c.ell(hx, hy - 40, 40, 12, "none", stroke="#f3d27a", sw=3)
        c.path("M%s,%s l12,-10 l12,10" % (f(hx - 10), f(hy - 44)), "none", stroke="#f3d27a", sw=3)
    # mặt
    ex = hx + 8
    for dx in (-15, 15):
        c.ell(ex + dx, hy + 8, 6.5, 8.5, "#2b1a12", stroke=None)
        c.circ(ex + dx + 2, hy + 4.5, 2.6, "#ffffff", stroke=None)
    if extra == "glasses":
        for dx in (-15, 15):
            c.circ(ex + dx, hy + 8, 12, "none", stroke="#2b1a12", sw=3)
        c.line(ex - 3, hy + 6, ex + 3, hy + 6, stroke="#2b1a12", sw=3)
    if extra == "mustache":
        c.path("M%s,%s q-10,-8 -20,4 q10,2 20,-4 q10,-8 20,4 q-10,2 -20,-4 Z" % (f(ex), f(hy + 22)), "#3b2a20",
               stroke=None)
    c.ell(ex - 24, hy + 22, 7, 4.5, "#ff8f8f", stroke=None, extra='opacity="0.55"')
    c.ell(ex + 25, hy + 22, 7, 4.5, "#ff8f8f", stroke=None, extra='opacity="0.55"')
    if extra != "mustache":
        c.path("M%s,%s q7,7 14,0" % (f(ex - 7), f(hy + 22)), "none", stroke="#2b1a12", sw=3)
    c.save(name)


CUSTOMERS = [
    ("cust_1", {"top": "#e85d5d", "bottom": "#3d5a80"}, "short", "#3b2a20", None, None),
    ("cust_2", {"top": "#4fa3e0", "bottom": "#4b3a5a"}, "bob", "#6b4226", None, None),
    ("cust_3", {"top": "#7cc96b", "bottom": "#6b4f3a", "hat": "#f2a541"}, "short", "#2c2c3a", "cap", None),
    ("cust_4", {"top": "#f2a541", "bottom": "#4b3a5a"}, "pony", "#2c2c3a", None, None),
    ("cust_5", {"top": "#a56be0", "bottom": "#3d3d4a"}, "spiky", "#f0c05a", None, None),
    ("cust_6", {"top": "#ef7fb0", "bottom": "#5a4a6a"}, "long", "#b5532c", "non_la", None),
]


def characters():
    for n, o, hs, hc, hat, ex in CUSTOMERS:
        person(n, o, hs, hc, hat=hat, extra=ex)
        person(n + "_sit", o, hs, hc, sit=True, hat=hat, extra=ex)
    vip = {"top": "#7b2fa8", "bottom": "#3d1f52", "trim": "#f3d27a", "long": True}
    person("cust_vip", vip, "short", "#2c2c3a", hat="khan_dong", extra="mustache")
    person("cust_vip_sit", vip, "short", "#2c2c3a", sit=True, hat="khan_dong", extra="mustache")
    chef_o = {"top": "#f4f6fa", "bottom": "#3d3d4a", "buttons": "#3d3d4a", "apron": None}
    person("chef", chef_o, "short", "#3b2a20", hat="chef")
    waiter_o = {"top": "#ffffff", "bottom": "#2f2f3a", "vest": "#2f2f3a", "bow": "#e85d5d", "arm": "#ffffff"}
    person("waiter", waiter_o, "short", "#6b4226")
    person("waiter_tray", waiter_o, "short", "#6b4226", tray=True)
    cashier_o = {"top": "#fff1d6", "bottom": "#4b3a5a", "apron": "#5fb84a"}
    person("cashier", cashier_o, "bun", "#3b2a20", extra="glasses")
    recep_o = {"top": "#e8414f", "bottom": "#ffffff", "trim": "#f3d27a", "long": True}
    person("receptionist", recep_o, "long", "#2c2c3a")
    manager_o = {"top": "#3d5a80", "bottom": "#2f2f3a", "vest": "#2a3f5c", "bow": "#f2a541"}
    person("manager", manager_o, "bald", "#5a4a3a", extra="mustache")
    guest_o = {"top": "#9ad0c2", "bottom": "#4b3a5a"}
    person("guest", guest_o, "bob", "#2c2c3a")


# ================================================================ ICON & UI

def icon_canvas(s=128):
    return C(s, s, s / 2, s / 2)


def coin(name="coin", folder=OUT_DIR):
    c = icon_canvas()
    x, y = 64, 64
    c.circ(x, y + 5, 50, dk("#d98a12", 0.2), sw=5)
    c.circ(x, y, 50, c.rg([(0, "#fff2a8", 1), (0.6, "#ffc93c", 1), (1, "#e89b16", 1)], 0.38, 0.32, 0.7), sw=5)
    c.circ(x, y, 34, "none", stroke="#d98a12", sw=4)
    c.path("M%s,%s l8,-18 l8,18 l18,2 l-14,12 l4,18 l-16,-9 l-16,9 l4,-18 l-14,-12 Z" % (f(x - 8), f(y - 12)),
           "#ffe27a", stroke="#d98a12", sw=3)
    c.ell(x - 22, y - 26, 12, 6, "#ffffff", stroke=None, extra='opacity="0.75" transform="rotate(-35 %s %s)"'
          % (f(x - 22), f(y - 26)))
    c.save(name, folder)


def diamond_icon(name="diamond", folder=OUT_DIR):
    c = icon_canvas()
    top = [(30, 44), (98, 44), (114, 60), (64, 116), (14, 60)]
    c.poly(top, "#4fc3f7", sw=5)
    c.poly([(30, 44), (98, 44), (114, 60), (14, 60)], c.lg("#b3ecff", "#6fd6ff"), stroke=None)
    c.poly([(14, 60), (64, 116), (46, 60)], "#3aa7e0", stroke=None)
    c.poly([(114, 60), (64, 116), (82, 60)], "#2a8fcc", stroke=None)
    c.poly([(46, 60), (64, 116), (82, 60)], "#58c4f5", stroke=None)
    c.poly([(30, 44), (46, 60), (64, 44)], "#e6f9ff", stroke=None)
    c.poly([(64, 44), (82, 60), (98, 44)], "#9fe3ff", stroke=None)
    c.poly(top, "none", sw=5)
    c.circ(40, 50, 4, "#ffffff", stroke=None)
    c.save(name, folder)


def star_icon(name, col="#ffd34d", folder=UI_DIR):
    c = icon_canvas()
    d = ""
    for k in range(10):
        r = 56 if k % 2 == 0 else 24
        a = -math.pi / 2 + k * math.pi / 5
        d += ("M" if k == 0 else "L") + "%s,%s " % (f(64 + math.cos(a) * r), f(68 + math.sin(a) * r))
    c.path(d + "Z", c.rg([(0, lt(col, 0.5), 1), (1, dk(col, 0.12), 1)], 0.45, 0.4, 0.7), sw=5)
    c.save(name, folder)


def gear_icon(folder=UI_DIR):
    c = icon_canvas()
    d = ""
    n = 8
    for k in range(n * 2):
        r = 54 if k % 2 == 0 else 42
        for j in (-1, 1):
            a = k * math.pi / n + j * math.pi / n * 0.35
            d += ("M" if d == "" else "L") + "%s,%s " % (f(64 + math.cos(a) * r), f(64 + math.sin(a) * r))
    c.path(d + "Z", c.lg("#b9c2cc", "#7c8791"), sw=5)
    c.circ(64, 64, 18, "#ffffff", sw=5)
    c.save("gear", folder)


def lock_icon(folder=UI_DIR):
    c = icon_canvas()
    c.path("M38,60 L38,42 Q38,16 64,16 Q90,16 90,42 L90,60", "none", stroke=OUT, sw=16)
    c.path("M38,60 L38,42 Q38,16 64,16 Q90,16 90,42 L90,60", "none", stroke="#c0c6cf", sw=9)
    c.rect(24, 56, 80, 62, c.lg("#ffd34d", "#e89b16"), rx=14, sw=5)
    c.circ(64, 82, 9, OUT, stroke=None)
    c.rect(60, 84, 8, 18, OUT, rx=3, stroke=None)
    c.save("lock", folder)


def hand_icon(folder=UI_DIR):
    c = icon_canvas(160)
    # bàn tay chỉ lên (ngón trỏ)
    d = ("M70,20 Q70,8 82,8 Q94,8 94,20 L94,70 Q100,62 110,64 Q120,66 120,78 Q128,72 136,78 Q144,84 142,96 "
         "L140,120 Q136,150 106,152 L84,152 Q60,150 50,128 L34,98 Q28,86 38,82 Q48,78 56,90 L70,108 Z")
    c.path(d, c.lg("#ffffff", "#f1e3d3"), sw=6)
    c.path("M94,70 L94,96 M120,78 L120,100", "none", stroke=OUT, sw=3.5)
    c.save("hand", folder)


def tab_icons(folder=UI_DIR):
    # quán
    c = icon_canvas()
    c.rect(26, 56, 76, 54, c.lg("#f6e3bd", "#e3c894"), rx=6, sw=5)
    c.poly([(14, 62), (64, 20), (114, 62)], c.lg("#e86a5f", "#c4423e"), sw=5)
    c.rect(54, 76, 22, 34, "#a96a3c", rx=4, sw=4)
    c.rect(32, 70, 16, 16, "#bfe9ff", rx=3, sw=3.5)
    c.rect(82, 70, 16, 16, "#bfe9ff", rx=3, sw=3.5)
    c.save("tab_inn", folder)
    # nhân viên
    c = icon_canvas()
    c.path("M24,112 Q24,72 64,72 Q104,72 104,112 Z", c.lg("#4fa3e0", "#3077b3"), sw=5)
    c.circ(64, 46, 26, c.rg([(0, lt(SKIN, 0.3), 1), (1, SKIN, 1)]), sw=5)
    c.rect(36, 18, 56, 14, "#ffffff", rx=6, sw=4)
    c.circ(64, 14, 14, "#ffffff", sw=4)
    c.save("tab_staff", folder)
    # thực đơn
    c = icon_canvas()
    c.rect(22, 16, 84, 100, c.lg("#e85d5d", "#b8423a"), rx=10, sw=5)
    c.rect(34, 26, 62, 80, "#fff6e6", rx=6, sw=3.5)
    for k in range(4):
        c.line(44, 44 + k * 16, 86, 44 + k * 16, stroke="#c9a37a", sw=4)
    c.save("tab_menu", folder)
    # mở rộng (bản đồ)
    c = icon_canvas()
    c.poly([(14, 30), (46, 18), (82, 30), (114, 18), (114, 98), (82, 110), (46, 98), (14, 110)], "#f6e3bd", sw=5)
    c.poly([(46, 18), (82, 30), (82, 110), (46, 98)], "#e6cf9e", stroke=None)
    c.path("M24,88 Q50,60 70,76 Q90,92 104,50", "none", stroke="#e85d5d", sw=4, extra='stroke-dasharray="6 6"')
    c.circ(104, 46, 9, "#e85d5d", sw=3.5)
    c.poly([(14, 30), (46, 18), (82, 30), (114, 18), (114, 98), (82, 110), (46, 98), (14, 110)], "none", sw=5)
    c.save("tab_expand", folder)
    # nhiệm vụ
    c = icon_canvas()
    c.rect(28, 20, 72, 92, "#fff6e6", rx=8, sw=5)
    c.rect(46, 12, 36, 18, "#a96a3c", rx=6, sw=4)
    for k in range(3):
        y = 50 + k * 20
        c.path("M40,%d l6,6 l10,-12" % y, "none", stroke="#5fb84a", sw=5)
        c.line(64, y, 88, y, stroke="#c9a37a", sw=4)
    c.save("tab_quest", folder)


def misc_icons(folder=UI_DIR):
    c = icon_canvas()
    c.path("M80,22 L38,64 L80,106", "none", stroke=OUT, sw=26)
    c.path("M80,22 L38,64 L80,106", "none", stroke="#ffffff", sw=14)
    c.save("arrow_left", folder)
    c = icon_canvas()
    c.path("M48,22 L90,64 L48,106", "none", stroke=OUT, sw=26)
    c.path("M48,22 L90,64 L48,106", "none", stroke="#ffffff", sw=14)
    c.save("arrow_right", folder)
    c = icon_canvas()
    c.circ(64, 64, 52, c.lg("#ff7a6b", "#d9423a"), sw=5)
    c.path("M44,44 L84,84 M84,44 L44,84", "none", stroke="#ffffff", sw=12)
    c.save("close", folder)
    c = icon_canvas()
    c.path("M64,108 C20,78 12,52 24,36 C36,20 58,24 64,42 C70,24 92,20 104,36 C116,52 108,78 64,108 Z",
           c.rg([(0, "#ff9fae", 1), (1, "#e8414f", 1)], 0.4, 0.35, 0.7), sw=5)
    c.ell(42, 44, 10, 6, "#ffffff", stroke=None, extra='opacity="0.7"')
    c.save("heart", folder)
    c = icon_canvas()
    c.circ(64, 66, 50, c.lg("#ffffff", "#e6eef5"), sw=5)
    c.path("M64,34 L64,66 L86,80", "none", stroke=OUT, sw=7)
    c.save("clock", folder)
    c = icon_canvas()
    c.poly([(72, 10), (30, 72), (60, 72), (52, 118), (98, 52), (66, 52)], c.lg("#ffe27a", "#f5a623"), sw=5)
    c.save("bolt", folder)
    c = icon_canvas()
    c.path("M64,8 Q70,58 120,64 Q70,70 64,120 Q58,70 8,64 Q58,58 64,8 Z", "#fff6b0", stroke=None)
    c.save("sparkle", folder)
    c = icon_canvas()
    c.circ(64, 64, 50, c.rg([(0, "#ffffff", 0.95), (0.6, "#ffffff", 0.55), (1, "#ffffff", 0)]), stroke=None)
    c.save("puff", folder)
    c = icon_canvas()
    c.rect(32, 36, 64, 72, c.lg("#f2a541", "#c97d1e"), rx=16, sw=5)
    c.path("M44,36 Q64,8 84,36", "none", stroke=OUT, sw=12)
    c.path("M44,36 Q64,8 84,36", "none", stroke="#a0662a", sw=6)
    c.circ(64, 72, 16, "#ffd34d", sw=4)
    c.save("gold_bag", folder)
    c = icon_canvas()
    c.path("M28,40 L100,40 L92,108 L36,108 Z", c.lg("#ffd34d", "#e89b16"), sw=5)
    c.rect(20, 26, 88, 18, "#e85d5d", rx=6, sw=5)
    c.line(64, 26, 64, 108, stroke="#e85d5d", sw=10)
    c.save("gift", folder)
    c = icon_canvas()
    c.path("M30,104 L30,48 L64,22 L98,48 L98,104 Z", c.lg("#ffd34d", "#e89b16"), sw=5)
    c.path("M48,104 L48,72 L80,72 L80,104", "#a96a3c", sw=4)
    c.save("prestige", folder)
    c = icon_canvas()
    c.path("M50,92 L50,26 L104,14 L104,80", "none", stroke=OUT, sw=9)
    c.ell(38, 94, 18, 14, c.lg("#7b6cf0", "#5040c8"), sw=5)
    c.ell(92, 82, 18, 14, c.lg("#7b6cf0", "#5040c8"), sw=5)
    c.path("M50,40 L104,28", "none", stroke=OUT, sw=9)
    c.save("music", folder)
    c = icon_canvas()
    c.path("M22,48 L46,48 L74,24 L74,104 L46,80 L22,80 Z", c.lg("#ffffff", "#dfe6ee"), sw=5)
    c.path("M88,44 Q100,64 88,84", "none", stroke=OUT, sw=6)
    c.save("sound", folder)
    c = icon_canvas()
    c.rect(40, 18, 48, 92, c.lg("#5b5f66", "#3a3c42"), rx=10, sw=5)
    c.path("M22,46 l-8,18 l8,18 M106,46 l8,18 l-8,18", "none", stroke=OUT, sw=6)
    c.save("vibrate", folder)
    c = icon_canvas()
    c.path("M30,40 L98,40 L90,112 L38,112 Z", c.lg("#ff7a6b", "#d9423a"), sw=5)
    c.rect(22, 26, 84, 14, "#d9423a", rx=5, sw=5)
    c.save("trash", folder)
    c = icon_canvas()
    c.circ(64, 64, 52, c.lg("#7bd35b", "#4ea83a"), sw=5)
    c.path("M38,64 L56,82 L92,46", "none", stroke="#ffffff", sw=12)
    c.save("check", folder)
    c = icon_canvas()
    c.circ(64, 64, 50, c.lg("#ffffff", "#e8f0f8"), sw=5)
    c.path("M64,40 L64,88 M40,64 L88,64", "none", stroke="#5fb84a", sw=12)
    c.save("plus", folder)
    c = icon_canvas()
    c.circ(64, 64, 50, c.lg("#9ad0ff", "#4fa3e0"), sw=5)
    c.path("M64,28 L64,30 M64,52 L64,98", "none", stroke="#ffffff", sw=12)
    c.save("info", folder)


def bubbles():
    def bubble(name):
        c = C(120, 120, 60, 112)
        c.path("M60,112 L48,94 Q14,92 12,58 Q12,14 60,12 Q108,14 108,58 Q106,92 72,94 Z",
               c.lg("#ffffff", "#eef2f6"), sw=5)
        return c
    c = bubble("bubble")
    c.save("bubble")

    def face(name, col, mouth, brow=None):
        c = bubble(name)
        c.circ(60, 54, 30, c.rg([(0, lt(col, 0.4), 1), (1, col, 1)], 0.4, 0.35, 0.7), sw=4)
        c.ell(50, 48, 4, 5.5, "#2b1a12", stroke=None)
        c.ell(70, 48, 4, 5.5, "#2b1a12", stroke=None)
        c.path(mouth, "none", stroke="#2b1a12", sw=4)
        if brow:
            c.path(brow, "none", stroke="#2b1a12", sw=4)
        c.save(name)
    face("face_happy", "#ffd34d", "M46,62 Q60,76 74,62")
    face("face_neutral", "#ffc56b", "M48,68 L72,68")
    face("face_angry", "#ff7a5a", "M48,72 Q60,62 72,72", "M42,38 L56,44 M78,38 L64,44")
    c = bubble("face_heart")
    c.path("M60,82 C34,64 30,48 38,38 C46,28 58,32 60,42 C62,32 74,28 82,38 C90,48 86,64 60,82 Z",
           c.rg([(0, "#ff9fae", 1), (1, "#e8414f", 1)], 0.4, 0.35, 0.7), sw=4)
    c.save("face_heart")
    c = bubble("zzz")
    c.path("M38,40 L58,40 L38,64 L58,64 M64,30 L80,30 L64,50 L80,50", "none", stroke="#4fa3e0", sw=5)
    c.save("bubble_zzz")


# ---------------------------------------------------------------- món ăn

def dish_icons():
    def plate(c, x=64, y=84, rx=50, ry=20, col="#ffffff"):
        c.ell(x, y + 5, rx, ry, dk(col, 0.18), sw=4)
        c.ell(x, y, rx, ry, c.lg(col, dk(col, 0.06)), sw=4)
        c.ell(x, y, rx * 0.7, ry * 0.65, "none", stroke=dk(col, 0.1), sw=2.5)

    def bowl(c, col="#4fa3e0", soup="#f2c27a"):
        c.path("M14,62 Q18,112 64,112 Q110,112 114,62 Z", c.lg(lt(col, 0.15), dk(col, 0.15), 0, 0, 1, 0), sw=5)
        c.ell(64, 62, 50, 16, soup, sw=5)
        c.path("M28,92 Q64,104 100,92", "none", stroke="#ffffff", sw=3, extra='stroke-opacity="0.6"')

    # Trà đá
    c = icon_canvas()
    c.path("M36,24 L92,24 L84,112 L44,112 Z", c.lg("#ffe7b8", "#e7a64a"), sw=5)
    c.path("M38,40 L90,40 L84,112 L44,112 Z", c.lg("#f0b55a", "#c97d1e"), stroke=None, extra='opacity="0.85"')
    for x, y in [(50, 50), (70, 58), (58, 74)]:
        c.rect(x, y, 16, 16, "#e6f7ff", rx=3, sw=2.5, extra='opacity="0.9"')
    c.path("M36,24 L92,24 L84,112 L44,112 Z", "none", sw=5)
    c.line(76, 10, 66, 70, stroke="#e85d5d", sw=6)
    c.save("dish_tra_da")
    # Bánh mì
    c = icon_canvas()
    c.path("M14,78 Q16,48 64,40 Q112,34 116,62 Q116,88 64,94 Q16,100 14,78 Z", c.lg("#f6c36b", "#d98a2b"), sw=5)
    for k in range(3):
        c.path("M%d,%d q10,-10 22,-12" % (36 + k * 22, 70 - k * 4), "none", stroke="#fbe3a8", sw=5)
    c.path("M30,74 Q64,90 104,68", "none", stroke="#7cc96b", sw=6)
    c.path("M34,70 Q64,82 100,64", "none", stroke="#e85d5d", sw=4)
    c.save("dish_banh_mi")
    # Xôi
    c = icon_canvas()
    c.poly([(10, 88), (64, 62), (118, 88), (64, 116)], c.lg("#7cc96b", "#4ea83a"), sw=5)
    c.path("M28,84 Q30,40 64,36 Q98,40 100,84 Q64,100 28,84 Z", c.rg([(0, "#ffffff", 1), (1, "#f2ead4", 1)]), sw=5)
    for x, y in [(48, 58), (64, 50), (80, 62), (58, 72), (74, 76)]:
        c.circ(x, y, 3.5, "#d9c89e", stroke=None)
    c.path("M40,66 Q64,56 88,66", "none", stroke="#f2a541", sw=6)
    c.save("dish_xoi")
    # Cơm tấm
    c = icon_canvas()
    plate(c)
    c.ell(48, 72, 26, 16, c.rg([(0, "#ffffff", 1), (1, "#f2ead4", 1)]), sw=4)
    c.path("M66,68 Q76,54 104,62 Q110,78 86,84 Q70,86 66,68 Z", c.lg("#c76a2b", "#8a4518"), sw=4)
    c.path("M76,66 L98,72", "none", stroke="#e8a06a", sw=3)
    c.ell(42, 88, 12, 6, "#7cc96b", sw=3)
    c.ell(64, 92, 10, 5, "#ffd34d", sw=3)
    c.save("dish_com_tam")
    # Phở
    c = icon_canvas()
    bowl(c, "#ffffff", "#f6d38e")
    c.path("M34,60 Q50,66 64,58 Q80,52 94,60", "none", stroke="#fffaf0", sw=5)
    c.ell(48, 58, 10, 4, "#c76a4a", sw=2.5)
    c.ell(78, 60, 10, 4, "#c76a4a", sw=2.5)
    c.circ(64, 56, 4, "#5fb84a", stroke=None)
    c.circ(56, 64, 3, "#5fb84a", stroke=None)
    c.path("M88,10 L64,58 M100,16 L72,60", "none", stroke="#a96a3c", sw=5)
    c.path("M14,62 Q18,112 64,112 Q110,112 114,62", "none", stroke="#4fa3e0", sw=3, extra='stroke-dasharray="6 8"')
    c.save("dish_pho")
    # Bún chả
    c = icon_canvas()
    plate(c, 64, 92, 54, 20)
    c.ell(42, 78, 26, 14, "#fffaf0", sw=4)
    c.path("M28,78 q8,-6 14,0 q8,6 14,0", "none", stroke="#e9dfc8", sw=3)
    c.path("M74,44 Q74,92 110,86 Q118,60 98,46 Z", c.lg("#c4a26a", "#9a7a44"), sw=4)
    c.circ(90, 64, 9, "#8a4518", sw=3)
    c.circ(98, 78, 8, "#8a4518", sw=3)
    c.ell(56, 98, 10, 5, "#7cc96b", sw=3)
    c.save("dish_bun_cha")
    # Bánh xèo
    c = icon_canvas()
    plate(c)
    c.path("M18,80 Q22,40 64,38 Q106,40 110,80 Z", c.lg("#ffd34d", "#f2a541"), sw=4)
    for x, y in [(40, 62), (58, 52), (80, 60), (92, 72)]:
        c.circ(x, y, 4, "#e8a03a", stroke=None)
    c.path("M30,80 Q64,70 98,80", "none", stroke="#7cc96b", sw=5)
    c.save("dish_banh_xeo")
    # Lẩu
    c = icon_canvas()
    c.path("M16,56 Q18,110 64,110 Q110,110 112,56 Z", c.lg("#c0c6cf", "#7c8791", 0, 0, 1, 0), sw=5)
    c.ell(64, 56, 48, 16, "#e8414f", sw=5)
    c.ell(48, 54, 9, 4, "#ffffff", sw=2)
    c.ell(76, 58, 10, 4, "#7cc96b", sw=2)
    c.ell(64, 50, 8, 3, "#ffd34d", sw=2)
    for s in (-1, 1):
        c.rect(64 + s * 56 - 8, 62, 16, 10, "#5b5f66", rx=4, sw=3)
    for x in (44, 64, 84):
        c.path("M%d,36 q-6,-10 0,-20 q6,-10 0,-20" % x, "none", stroke="#ffffff", sw=4, extra='stroke-opacity="0.8"')
    c.save("dish_lau")
    # Cá kho
    c = icon_canvas()
    c.path("M16,58 Q20,112 64,112 Q108,112 112,58 Z", c.lg("#c1603d", "#8a3f22", 0, 0, 1, 0), sw=5)
    c.ell(64, 58, 48, 16, "#7a3a1c", sw=5)
    c.path("M34,58 Q56,44 82,56 L96,46 L94,66 L82,60 Q56,72 34,58 Z", c.lg("#e08a3a", "#b0581f"), sw=3.5)
    c.circ(42, 56, 3, "#2b1a12", stroke=None)
    c.rect(58, 18, 12, 28, "#c1603d", rx=5, sw=4)
    c.save("dish_ca_kho")
    # Vịt quay
    c = icon_canvas()
    plate(c, 64, 90, 56, 20)
    c.path("M22,82 Q20,44 62,42 Q100,40 108,70 Q108,90 64,92 Q26,94 22,82 Z", c.lg("#e08a3a", "#a8501a"), sw=4)
    c.path("M96,52 Q114,30 104,20 Q96,30 88,48", "#c76a2b", sw=4)
    c.ell(46, 56, 14, 6, "#ffd28a", stroke=None, extra='opacity="0.7"')
    c.circ(30, 88, 6, "#7cc96b", sw=2.5)
    c.save("dish_vit_quay")


def more_dish_icons():
    """14 món bổ sung, dựng từ các mẫu bát / đĩa / cốc với nhân khác nhau."""
    def plate(c, x=64, y=88, rx=54, ry=20, col="#ffffff"):
        c.ell(x, y + 5, rx, ry, dk(col, 0.18), sw=4)
        c.ell(x, y, rx, ry, c.lg(col, dk(col, 0.06)), sw=4)

    def bowl(c, col, soup, rim="#ffffff"):
        c.path("M14,60 Q18,112 64,112 Q110,112 114,60 Z", c.lg(lt(col, 0.15), dk(col, 0.18), 0, 0, 1, 0), sw=5)
        c.ell(64, 60, 50, 16, soup, sw=5)
        c.path("M26,92 Q64,104 102,92", "none", stroke=rim, sw=3, extra='stroke-opacity="0.6"')

    def noodles(c, col="#fffaf0", y=58):
        c.path("M30,%d q10,-6 20,0 q10,6 20,0 q10,-6 20,0 q10,6 14,0" % y, "none", stroke=col, sw=4)

    def chopsticks(c):
        c.path("M90,8 L66,56 M102,14 L74,58", "none", stroke="#a96a3c", sw=5)

    # Nước mía
    c = icon_canvas()
    c.path("M38,22 L90,22 L82,114 L46,114 Z", c.lg("#f4ffd8", "#c7e27a"), sw=5)
    c.path("M40,40 L88,40 L82,114 L46,114 Z", c.lg("#e3f59a", "#a8cf4a"), stroke=None, extra='opacity="0.9"')
    c.path("M38,22 L90,22 L82,114 L46,114 Z", "none", sw=5)
    c.ell(64, 40, 24, 5, "#fff8c0", stroke=None, extra='opacity="0.8"')
    c.circ(78, 30, 10, "#ffe27a", sw=3)
    c.line(52, 6, 60, 70, stroke="#5fb84a", sw=6)
    c.save("dish_nuoc_mia")
    # Gỏi cuốn
    c = icon_canvas()
    plate(c)
    for x in (40, 66, 92):
        c.path("M%d,90 Q%d,52 %d,46 Q%d,52 %d,90 Z" % (x - 14, x - 14, x, x + 14, x + 14), c.lg("#fdfaf2", "#ece4d0"), sw=4)
        c.circ(x - 2, 66, 5, "#ff9b8a", stroke=None)
        c.circ(x + 4, 76, 4, "#7cc96b", stroke=None)
    c.ell(100, 98, 14, 6, "#8a4a24", sw=3)
    c.save("dish_goi_cuon")
    # Chè ba màu
    c = icon_canvas()
    c.path("M34,24 L94,24 L84,114 L44,114 Z", "#ffffff", sw=5, extra='fill-opacity="0.6"')
    c.path("M38,84 L90,84 L84,114 L44,114 Z", "#c4483e", stroke=None)
    c.path("M37,60 L91,60 L90,84 L38,84 Z", "#7cc96b", stroke=None)
    c.path("M36,38 L92,38 L91,60 L37,60 Z", "#ffd34d", stroke=None)
    c.path("M34,24 L94,24 L84,114 L44,114 Z", "none", sw=5)
    c.ell(64, 30, 28, 8, "#fffaf0", sw=3)
    c.line(76, 6, 66, 60, stroke="#e85d5d", sw=5)
    c.save("dish_che")
    # Bánh cuốn
    c = icon_canvas()
    plate(c)
    for k in range(3):
        c.ell(40 + k * 24, 78 - (k % 2) * 6, 18, 12, c.lg("#fffdf6", "#efe6cf"), sw=4)
    c.circ(52, 64, 5, "#d98a4a", stroke=None)
    c.circ(76, 70, 4, "#d98a4a", stroke=None)
    c.path("M30,92 q30,8 64,0", "none", stroke="#7cc96b", sw=4)
    c.save("dish_banh_cuon")
    # Hủ tiếu
    c = icon_canvas()
    bowl(c, "#ffffff", "#f3d9a4")
    noodles(c)
    c.ell(44, 58, 9, 5, "#ff9b8a", sw=2.5)
    c.ell(84, 60, 8, 5, "#ff9b8a", sw=2.5)
    c.circ(64, 54, 5, "#7cc96b", stroke=None)
    chopsticks(c)
    c.save("dish_hu_tieu")
    # Nem rán
    c = icon_canvas()
    plate(c)
    for k in range(4):
        x = 32 + k * 18
        c.rect(x, 52 + (k % 2) * 6, 22, 38, c.lg("#f2b25a", "#c97a2e", 0, 0, 1, 0), rx=10, sw=3.5,
               extra='transform="rotate(-20 %d 70)"' % (x + 11))
    c.ell(100, 96, 12, 6, "#ffcf7a", sw=3)
    c.save("dish_nem_ran")
    # Bánh bèo
    c = icon_canvas()
    plate(c, col="#f4f0e6")
    for x, y in [(36, 72), (64, 64), (92, 72), (50, 92), (78, 92)]:
        c.ell(x, y, 15, 8, "#ffffff", sw=3)
        c.circ(x, y - 2, 4.5, "#ff9b5a", stroke=None)
    c.save("dish_banh_beo")
    # Cơm gà
    c = icon_canvas()
    plate(c)
    c.ell(46, 76, 26, 16, c.rg([(0, "#fff5c8", 1), (1, "#f2d88a", 1)]), sw=4)
    c.path("M66,70 Q76,48 104,58 Q112,76 90,86 Q72,90 66,70 Z", c.lg("#ffe0a0", "#e8a85a"), sw=4)
    c.circ(40, 94, 6, "#7cc96b", stroke=None)
    c.save("dish_com_ga")
    # Bún bò Huế
    c = icon_canvas()
    bowl(c, "#e85d5d", "#f08a3a")
    noodles(c, "#fff2e0")
    c.ell(46, 56, 10, 5, "#8a3f22", sw=2.5)
    c.ell(82, 60, 10, 5, "#8a3f22", sw=2.5)
    c.circ(64, 52, 4, "#7cc96b", stroke=None)
    c.ell(64, 64, 6, 3, "#ffd34d", stroke=None)
    chopsticks(c)
    c.save("dish_bun_bo_hue")
    # Mì Quảng
    c = icon_canvas()
    bowl(c, "#f2c14e", "#f6d36a")
    noodles(c, "#fff6c8")
    c.ell(48, 58, 9, 5, "#f08a7c", sw=2.5)
    c.path("M70,48 l20,6 l-6,10 Z", "#f6e3bd", sw=2.5)
    c.circ(84, 62, 4, "#7cc96b", stroke=None)
    c.save("dish_mi_quang")
    # Bò kho
    c = icon_canvas()
    bowl(c, "#7a4a2e", "#c4482e")
    for x, y in [(44, 58), (64, 54), (84, 60)]:
        c.rect(x - 8, y - 6, 16, 12, "#7a3a1c", rx=4, sw=2.5)
    c.circ(56, 64, 4, "#ff9b3a", stroke=None)
    c.path("M96,24 Q112,54 98,70 L118,70 Q124,40 106,20 Z", c.lg("#f2c27a", "#d98a2b"), sw=3)
    c.save("dish_bo_kho")
    # Bánh canh cua
    c = icon_canvas()
    bowl(c, "#4fa3e0", "#f6b56a")
    noodles(c, "#fff8ec")
    c.circ(64, 54, 12, "#e85d3a", sw=3)
    c.path("M50,48 l-8,-8 M78,48 l8,-8", "none", stroke="#e85d3a", sw=4)
    c.save("dish_banh_canh")
    # Chả cá
    c = icon_canvas()
    c.path("M14,74 Q16,104 64,106 Q112,104 114,74 Z", c.lg("#5c5550", "#3a3430", 0, 0, 1, 0), sw=5)
    c.ell(64, 74, 50, 18, "#6b6560", sw=5)
    for x, y in [(42, 70), (64, 66), (86, 72), (56, 80)]:
        c.rect(x - 10, y - 6, 20, 12, c.lg("#ffd34d", "#e8a020"), rx=4, sw=2.5)
    for x in (48, 74, 94):
        c.path("M%d,64 q-4,-10 2,-16" % x, "none", stroke="#7cc96b", sw=4)
    c.save("dish_cha_ca")
    # Cao lầu
    c = icon_canvas()
    bowl(c, "#3d6e9e", "#e8c27a")
    c.path("M30,58 L98,58 M34,64 L94,64", "none", stroke="#f6d38e", sw=5)
    c.ell(48, 54, 10, 5, "#b8582e", sw=2.5)
    c.ell(78, 54, 10, 5, "#b8582e", sw=2.5)
    c.rect(58, 44, 14, 10, "#fff2c8", rx=3, sw=2.5)
    c.circ(90, 50, 5, "#7cc96b", stroke=None)
    c.save("dish_cao_lau")


def event_icons(folder=UI_DIR):
    # cuộn giấy đơn đặt tiệc
    c = icon_canvas(160)
    c.shadow(80, 146, 52, 10, 0.25)
    c.rect(34, 26, 92, 112, c.lg("#fff6e0", "#f0dcb4"), rx=8, sw=5)
    c.rect(26, 18, 108, 18, c.lg("#c98a55", "#93582f"), rx=9, sw=5)
    c.rect(26, 128, 108, 18, c.lg("#c98a55", "#93582f"), rx=9, sw=5)
    for k in range(4):
        c.line(48, 54 + k * 18, 112 - (k % 2) * 20, 54 + k * 18, stroke="#c9a37a", sw=5)
    c.circ(108, 108, 16, "#e8414f", sw=4)
    c.save("icon_order", folder)
    # pháo hoa sự kiện
    c = icon_canvas(160)
    for k in range(12):
        a = k * math.pi / 6
        col = ["#ffd34d", "#ff6b8b", "#7bd35b", "#4fc3f7"][k % 4]
        c.line(80 + math.cos(a) * 18, 80 + math.sin(a) * 18, 80 + math.cos(a) * 60, 80 + math.sin(a) * 60,
               stroke=col, sw=8)
    c.circ(80, 80, 20, c.rg([(0, "#ffffff", 1), (1, "#ffd34d", 1)]), sw=4)
    c.save("icon_event", folder)


def chapter_thumbs(folder=UI_DIR):
    """Ảnh minh họa 5 chương: Phố Cổ, Hội An, Sài Gòn, Đà Lạt, Huế."""
    def base(c, sky1, sky2, ground):
        c.rect(6, 6, 228, 168, c.lg(sky1, sky2), rx=26, sw=6)
        c.path("M9,130 L231,130 L231,148 Q231,171 208,171 L32,171 Q9,171 9,148 Z", ground, stroke=None)
        c.rect(6, 6, 228, 168, "none", rx=26, sw=6)

    # 1. Phố Cổ: nhà ống mái ngói đỏ
    c = C(240, 180, 120, 90)
    base(c, "#ffe7b8", "#ffc98a", "#d9a46c")
    for k, (x, w, h, col) in enumerate([(30, 56, 70, "#f6e3bd"), (90, 60, 86, "#f2c98f"), (154, 56, 66, "#efd7a8")]):
        c.rect(x, 130 - h, w, h, col, rx=4, sw=4)
        c.poly([(x - 6, 132 - h), (x + w + 6, 132 - h), (x + w / 2, 104 - h)], "#c4483e", sw=4)
        c.rect(x + w / 2 - 10, 104, 20, 26, "#8a5530", rx=3, sw=3)
        c.rect(x + 8, 140 - h, 16, 14, "#bfe9ff", rx=2, sw=3)
    c.save("chapter_1", folder)
    # 2. Hội An: tường vàng + đèn lồng
    c = C(240, 180, 120, 90)
    base(c, "#cfe8ff", "#ffe2b0", "#c9a06a")
    c.rect(40, 62, 160, 68, c.lg("#ffd85a", "#f2b632"), rx=4, sw=4)
    c.poly([(30, 66), (210, 66), (190, 40), (50, 40)], "#7a4a2e", sw=4)
    for x in (70, 110, 150):
        c.rect(x, 86, 22, 44, "#2f7a5a", rx=3, sw=3)
    for x, col in [(48, "#e8414f"), (92, "#ffb347"), (136, "#e8414f"), (180, "#ff6bb3")]:
        c.line(x, 40, x, 52, stroke=OUT, sw=2)
        c.ell(x, 60, 10, 12, c.rg([(0, "#fff0a0", 1), (1, col, 1)]), sw=3)
    c.save("chapter_2", folder)
    # 3. Sài Gòn: nhà phố hiện đại, biển hiệu
    c = C(240, 180, 120, 90)
    base(c, "#ffd2a8", "#ff9f7a", "#a8a8b8")
    for x, h, col in [(24, 100, "#9fb5d6"), (70, 120, "#7fa0c8"), (130, 90, "#b6c8e2"), (176, 110, "#8fb0d6")]:
        c.rect(x, 130 - h, 42, h, col, rx=3, sw=4)
        for yy in range(int(140 - h), 120, 18):
            c.rect(x + 8, yy, 10, 10, "#fff6b0", rx=1, stroke=None)
            c.rect(x + 24, yy, 10, 10, "#fff6b0", rx=1, stroke=None)
    c.rect(78, 40, 66, 22, "#e8414f", rx=6, sw=3)
    c.save("chapter_3", folder)
    # 4. Đà Lạt: nhà gỗ giữa rừng thông, hoa tím
    c = C(240, 180, 120, 90)
    base(c, "#d8f0ff", "#b8e0f0", "#7cc96b")
    for x, h in [(34, 80), (198, 90), (180, 60)]:
        c.poly([(x - 20, 130), (x + 20, 130), (x, 130 - h)], "#2f7a52", sw=4)
    c.rect(78, 78, 84, 52, c.lg("#c98a55", "#93582f"), rx=4, sw=4)
    c.poly([(68, 82), (172, 82), (120, 46)], "#6b3f8a", sw=4)
    c.rect(110, 100, 20, 30, "#5a341f", rx=3, sw=3)
    for x in (60, 70, 170, 182, 150):
        c.circ(x, 140, 6, "#b07ae0", sw=2)
    c.save("chapter_4", folder)
    # 5. Huế: cổng thành mái vàng
    c = C(240, 180, 120, 90)
    base(c, "#ffe9c8", "#f6c2a0", "#c4483e")
    c.rect(40, 80, 160, 50, c.lg("#c4483e", "#93302a"), rx=3, sw=4)
    c.path("M110,130 L110,104 Q120,92 130,104 L130,130 Z", "#5a341f", sw=3)
    c.poly([(30, 84), (210, 84), (186, 62), (54, 62)], c.lg("#ffd34d", "#e89b16"), sw=4)
    c.poly([(70, 64), (170, 64), (150, 42), (90, 42)], c.lg("#ffd34d", "#e89b16"), sw=4)
    c.circ(120, 36, 7, "#ffd34d", sw=3)
    c.save("chapter_5", folder)


def progression_icons(folder=UI_DIR):
    """Icon cho mục tiêu chương, nghiên cứu, bộ sưu tập, vòng quay, rương."""
    # rương gỗ / bạc / vàng
    for name, body, band in [("chest_wood", "#b97a4c", "#7a4a2e"), ("chest_silver", "#b8c4d0", "#6f7d8c"),
                             ("chest_gold", "#ffcf4d", "#c98a1a")]:
        c = icon_canvas(160)
        c.shadow(80, 144, 60, 12, 0.3)
        c.rect(22, 70, 116, 70, c.lg(body, dk(body, 0.25)), rx=10, sw=5)
        c.path("M22,74 Q22,30 80,30 Q138,30 138,74 Z", c.lg(lt(body, 0.2), body), sw=5)
        for x in (44, 116):
            c.rect(x - 7, 32, 14, 106, band, rx=4, sw=3)
        c.rect(22, 68, 116, 12, band, rx=4, sw=3)
        c.rect(66, 66, 28, 34, c.lg("#ffe27a", "#e89b16"), rx=6, sw=4)
        c.circ(80, 80, 5, OUT, stroke=None)
        c.save(name, folder)
    # sách nghiên cứu (đơn vị Điểm nghiên cứu)
    c = icon_canvas(128)
    c.path("M14,30 Q40,18 64,30 L64,112 Q40,100 14,112 Z", c.lg("#6fb7f0", "#3a7fc4"), sw=5)
    c.path("M114,30 Q88,18 64,30 L64,112 Q88,100 114,112 Z", c.lg("#5aa6e6", "#2f6fa8"), sw=5)
    c.path("M26,46 Q42,40 54,46 M26,62 Q42,56 54,62 M74,46 Q86,40 102,46", "none", stroke="#e6f4ff", sw=4)
    c.circ(88, 78, 14, c.rg([(0, "#fff6a8", 1), (1, "#ffc93c", 1)]), sw=3.5)
    c.save("icon_rp", folder)
    # bình nghiên cứu
    c = icon_canvas(160)
    c.shadow(80, 146, 50, 10, 0.25)
    c.path("M62,20 L98,20 L98,60 L132,124 Q138,140 120,140 L40,140 Q22,140 28,124 L62,60 Z",
           c.lg("#e9f6ff", "#bfe0f5"), sw=5)
    c.path("M44,100 L116,100 L130,126 Q134,136 120,136 L40,136 Q26,136 30,126 Z", c.lg("#9b6bf0", "#6a3fc4"), stroke=None)
    c.path("M62,20 L98,20 L98,60 L132,124 Q138,140 120,140 L40,140 Q22,140 28,124 L62,60 Z", "none", sw=5)
    c.rect(56, 12, 48, 14, "#a8683d", rx=5, sw=4)
    for x, y, r in [(64, 116, 7), (90, 110, 5), (78, 92, 4)]:
        c.circ(x, y, r, "#ffffff", stroke=None, extra='opacity="0.7"')
    c.save("icon_research", folder)
    # bộ thẻ
    c = icon_canvas(160)
    c.shadow(80, 146, 56, 10, 0.25)
    for k, (dx, rot, col) in enumerate([(-22, -14, "#7fb6e8"), (0, 0, "#b98af0"), (22, 14, "#ffcf4d")]):
        c.group("rotate(%d 80 120)" % rot)
        c.rect(48 + dx, 22, 64, 96, c.lg(lt(col, 0.2), col), rx=10, sw=5)
        c.rect(56 + dx, 30, 48, 56, "#fff6e6", rx=6, stroke=None)
        c.circ(80 + dx, 54, 14, SKIN, sw=3)
        c.rect(66 + dx, 34, 28, 8, "#ffffff", rx=3, sw=2)
        c.end()
    c.save("icon_cards", folder)
    # vòng quay
    c = icon_canvas(160)
    cols = ["#ff6b6b", "#ffd34d", "#7bd35b", "#4fc3f7", "#b98af0", "#ff9f43", "#ef7fb0", "#5fd1c4"]
    c.circ(80, 80, 68, "#7a4628", sw=5)
    for k in range(8):
        a0 = k * math.pi / 4 - math.pi / 2
        a1 = a0 + math.pi / 4
        p0 = (80 + math.cos(a0) * 60, 80 + math.sin(a0) * 60)
        p1 = (80 + math.cos(a1) * 60, 80 + math.sin(a1) * 60)
        c.path("M80,80 L%s,%s A60,60 0 0 1 %s,%s Z" % (f(p0[0]), f(p0[1]), f(p1[0]), f(p1[1])), cols[k],
               stroke="#ffffff", sw=2)
    c.circ(80, 80, 14, c.rg([(0, "#fff6a8", 1), (1, "#ffc93c", 1)]), sw=4)
    c.poly([(68, 6), (92, 6), (80, 30)], "#e8414f", sw=4)
    c.save("icon_wheel", folder)
    # sao xám (chưa đạt)
    star_icon("star_empty", "#c9bfb2")


def chapter_props():
    """Đồ đặc trưng từng chương, đặt trong sảnh."""
    # Hà Nội: lồng chim trên chân gỗ
    c = obj_canvas(140, 280, 250)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 34, 12)
    c.rect(cx - 5, cy - 150, 10, 150, c.lg("#9a6438", "#6b4123", 0, 0, 1, 0), rx=4, sw=3.5)
    c.ell(cx, cy - 2, 26, 10, "#6b4123", sw=3)
    c.path("M%s,%s q30,-6 34,14" % (f(cx), f(cy - 150)), "none", stroke=OUT, sw=4)
    bx, by = cx + 34, cy - 100
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Z" % (f(bx - 30), f(by), f(bx), f(by - 70), f(bx + 30), f(by), f(bx - 30), f(by)),
           "#f6e3bd", sw=4, extra='fill-opacity="0.35"')
    for k in range(-2, 3):
        c.path("M%s,%s Q%s,%s %s,%s" % (f(bx + k * 12), f(by), f(bx + k * 6), f(by - 50), f(bx), f(by - 68)), "none",
               stroke="#a8683d", sw=2.5)
    c.ell(bx, by, 32, 8, "#a8683d", sw=3)
    c.ell(bx - 4, by - 26, 12, 9, "#ffd34d", sw=3)
    c.circ(bx + 6, by - 30, 3, OUT, stroke=None)
    c.save("prop_bird_cage")
    # Hà Nội: bàn trà thấp + ấm chén
    c = obj_canvas(200, 160, 120)
    c.shadow(c.ax, c.ay + 2, 80, 30)
    c.box(-0.32, -0.32, 0.32, 0.32, 0, 34, "#8a5530", top="#a8683d")
    t = c.iso(0, 0, 34)
    c.ell(t[0] - 10, t[1] - 14, 18, 14, c.lg("#f6f1e3", "#d8d0bc"), sw=3)
    c.path("M%s,%s q14,-4 16,6" % (f(t[0] + 8), f(t[1] - 16)), "none", stroke=OUT, sw=3)
    for dx in (22, 36):
        c.rect(t[0] + dx - 6, t[1] - 4, 12, 10, "#ffffff", rx=3, sw=2.5)
    c.save("prop_tea_table")
    # Hội An: cây đèn lồng nhiều màu
    c = obj_canvas(170, 300, 270)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 40, 14)
    c.rect(cx - 5, cy - 210, 10, 210, c.lg("#9a6438", "#6b4123", 0, 0, 1, 0), rx=4, sw=3.5)
    c.ell(cx, cy - 2, 28, 10, "#6b4123", sw=3)
    c.path("M%s,%s L%s,%s M%s,%s L%s,%s" % (f(cx - 60), f(cy - 196), f(cx + 60), f(cy - 196), f(cx - 50), f(cy - 130),
                                           f(cx + 50), f(cy - 130)), "none", stroke=OUT, sw=4)
    for x, y, col in [(-46, -170, "#e8414f"), (0, -180, "#ffb347"), (46, -170, "#ff6bb3"),
                      (-38, -104, "#7bd35b"), (38, -104, "#4fc3f7")]:
        lx, ly = cx + x, cy + y
        c.line(lx, ly - 22, lx, ly - 30 if y < -150 else ly - 26, stroke=OUT, sw=2.5)
        c.ell(lx, ly, 17, 20, c.rg([(0, "#fff0a0", 1), (1, col, 1)], 0.45, 0.4, 0.6), sw=3.5)
        c.rect(lx - 8, ly - 24, 16, 6, "#f3c84b", rx=2, sw=2)
        c.rect(lx - 8, ly + 18, 16, 6, "#f3c84b", rx=2, sw=2)
    c.save("prop_lantern_tree")
    # Sài Gòn: xe máy
    c = obj_canvas(240, 200, 160)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 96, 22)
    for wx in (-62, 58):
        c.circ(cx + wx, cy - 26, 26, "#3a3c42", sw=4)
        c.circ(cx + wx, cy - 26, 11, "#c0c6cf", sw=3)
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
        f(cx - 66), f(cy - 34), f(cx - 40), f(cy - 76), f(cx - 10), f(cy - 92), f(cx + 30), f(cy - 76), f(cx + 62), f(cy - 34),
        f(cx), f(cy - 44), f(cx - 66), f(cy - 34)), c.lg("#e8414f", "#b8282f"), sw=4)
    c.rect(cx - 44, cy - 98, 60, 16, "#3a2a20", rx=7, sw=3)
    c.path("M%s,%s L%s,%s L%s,%s" % (f(cx + 30), f(cy - 76), f(cx + 46), f(cy - 124), f(cx + 66), f(cy - 130)), "none",
           stroke=OUT, sw=6)
    c.circ(cx + 52, cy - 112, 8, "#fff6a8", sw=3)
    c.save("prop_scooter")
    # Sài Gòn: biển neon
    c = obj_canvas(170, 260, 230)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 34, 12)
    c.rect(cx - 5, cy - 120, 10, 120, "#5b5f66", rx=3, sw=3)
    c.rect(cx - 70, cy - 210, 140, 96, "#2a2440", rx=16, sw=5)
    c.rect(cx - 60, cy - 200, 120, 76, "none", rx=12, stroke="#ff4fb3", sw=5)
    c.path("M%s,%s q20,-34 40,0 q20,34 40,0" % (f(cx - 40), f(cy - 160)), "none", stroke="#4ff0ff", sw=6)
    c.circ(cx + 44, cy - 186, 6, "#ffe14f", stroke=None)
    c.save("prop_neon")
    # Đà Lạt: lò sưởi gạch
    c = obj_canvas(220, 260, 200)
    c.shadow(c.ax, c.ay + 2, 90, 30)
    c.box(-0.42, -0.2, 0.42, 0.2, 0, 150, "#b8604a", top="#9a4e3c")
    c.box(-0.48, -0.24, 0.48, 0.24, 150, 166, "#7a4a2e", top="#a8683d")
    f0 = c.iso(0, 0.2, 20)
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Z" % (f(f0[0] - 40), f(f0[1]), f(f0[0] - 40), f(f0[1] - 60), f(f0[0]),
           f(f0[1] - 96), f(f0[0] + 40), f(f0[1] - 60), f(f0[0] + 40), f(f0[1])), "#2a1a12", sw=3)
    for dx, h, col in [(-14, 44, "#ff7b3a"), (6, 58, "#ffb347"), (20, 36, "#ff7b3a")]:
        c.path("M%s,%s q-12,-%d 0,-%d q12,%d 0,%d Z" % (f(f0[0] + dx), f(f0[1] - 4), h // 2, h, h // 2, h), col, stroke=None)
    c.save("prop_fireplace")
    # Đà Lạt: chậu dã quỳ vàng
    c = obj_canvas(140, 200, 170)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 46, 18)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 32), f(cy - 48), f(cx + 32), f(cy - 48), f(cx + 24), f(cy),
                                               f(cx - 24), f(cy)), c.lg("#8a6a9e", "#5e4472", 0, 0, 1, 0), sw=4)
    for x, y in [(-26, -80), (24, -84), (0, -110), (-12, -136), (18, -124)]:
        c.line(cx, cy - 50, cx + x, cy + y + 10, stroke="#4ea83a", sw=4)
    for x, y in [(-26, -80), (24, -84), (0, -110), (-12, -136), (18, -124)]:
        for k in range(8):
            a = k * math.pi / 4
            c.ell(cx + x + math.cos(a) * 10, cy + y + math.sin(a) * 10, 7, 4, "#ffd34d", stroke=OUT, sw=1.5,
                  extra='transform="rotate(%d %s %s)"' % (k * 45, f(cx + x + math.cos(a) * 10), f(cy + y + math.sin(a) * 10)))
        c.circ(cx + x, cy + y, 6, "#c97a1a", sw=2)
    c.save("prop_daquy")
    # Huế: cột son vẽ rồng
    c = obj_canvas(110, 380, 350)
    cx, cy = c.ax, c.ay
    c.shadow(cx, cy + 2, 32, 12)
    c.rect(cx - 30, cy - 18, 60, 18, "#7a6a5e", rx=4, sw=3.5)
    c.rect(cx - 22, cy - 320, 44, 304, c.lg("#e8414f", "#a8282f", 0, 0, 1, 0), rx=8, sw=4)
    c.path("M%s,%s q24,-30 0,-60 q-24,-30 0,-60 q24,-30 0,-60" % (f(cx), f(cy - 60)), "none", stroke="#ffd34d", sw=6)
    c.rect(cx - 28, cy - 332, 56, 18, "#ffd34d", rx=4, sw=3.5)
    c.save("prop_red_pillar")
    # Huế: bình phong vàng
    c = obj_canvas(260, 240, 200)
    c.shadow(c.ax, c.ay + 2, 110, 26)
    for k in range(4):
        x0 = -0.6 + k * 0.3
        c.box(x0, -0.05, x0 + 0.28, 0.05, 0, 150, "#c4283e" if k % 2 else "#a8282f", top="#ffd34d")
        a = c.iso(x0 + 0.14, 0.05, 110)
        c.circ(a[0], a[1], 12, "#ffd34d", sw=3)
        b = c.iso(x0 + 0.14, 0.05, 56)
        c.path("M%s,%s q8,-12 16,0 q-8,12 -16,0 Z" % (f(b[0] - 8), f(b[1])), "#ffd34d", sw=2)
    c.save("prop_royal_screen")


def customer_badges(folder=UI_DIR):
    # khách khó tính (mặt nhăn), du lịch (máy ảnh), khách quen (tim vàng)
    c = icon_canvas(96)
    c.circ(48, 48, 40, c.rg([(0, "#ffb08a", 1), (1, "#e8603a", 1)]), sw=4)
    c.path("M30,34 L44,40 M66,34 L52,40", "none", stroke=OUT, sw=4)
    c.path("M34,66 Q48,56 62,66", "none", stroke=OUT, sw=4)
    c.save("badge_picky", folder)
    c = icon_canvas(96)
    c.rect(14, 30, 68, 46, c.lg("#5b5f66", "#3a3c42"), rx=10, sw=4)
    c.rect(32, 22, 28, 12, "#3a3c42", rx=3, sw=3)
    c.circ(48, 53, 15, "#9fd0f0", sw=4)
    c.circ(70, 40, 4, "#ffd34d", stroke=None)
    c.save("badge_tourist", folder)
    c = icon_canvas(96)
    c.path("M48,82 C16,60 12,40 22,28 C32,16 46,20 48,32 C50,20 64,16 74,28 C84,40 80,60 48,82 Z",
           c.rg([(0, "#fff2a8", 1), (1, "#f2a541", 1)]), sw=4)
    c.save("badge_regular", folder)


def story_characters():
    """Nhân vật cốt truyện + chân dung lớn cho màn hội thoại."""
    person("ba_tu", {"top": "#8a5a3a", "bottom": "#2f2f3a", "buttons": "#f6e3bd", "trim": "#c98a55"}, "bun", "#cfc8be",
           extra="glasses")
    person("lan", {"top": "#e8414f", "bottom": "#2f2f3a", "apron": "#ffffff"}, "pony", "#2c2c3a")
    person("phat", {"top": "#6b3fa0", "bottom": "#2a1f3a", "vest": "#4a2a7a", "bow": "#ffd34d", "buttons": "#ffd34d"},
           "short", "#141414", extra="mustache")


def story_portraits():
    """Chân dung lớn cho màn hội thoại: cùng hình nhân vật, xuất to gấp 2.4 lần."""
    import re
    for n in ["ba_tu", "lan", "phat", "chef", "cust_1", "cust_2", "cust_3", "cust_4", "cust_5", "cust_6", "cust_vip",
              "guest", "manager", "waiter", "cashier", "receptionist"]:
        src = (OUT_DIR / (n + ".svg")).read_text(encoding="utf-8")
        m = re.search(r'width="(\d+)" height="(\d+)"', src)
        w, h = int(m.group(1)), int(m.group(2))
        src = src.replace(m.group(0), 'width="%d" height="%d"' % (int(w * 2.4), int(h * 2.4)), 1)
        (UI_DIR / ("portrait_" + n + ".svg")).write_text(src, encoding="utf-8")


def nav_buttons(folder=UI_DIR):
    """Nền nút tròn thanh dưới: nổi khối, viền, bóng đổ, vệt sáng; bản 'sel' có vòng vàng."""
    for name, rim1, rim2, glow in [("nav_circle", "#e9cfa6", "#c99a64", None),
                                   ("nav_circle_sel", "#ffe27a", "#e89b16", "#fff0b0")]:
        c = C(240, 252, 120, 120)
        # bóng đổ mềm dưới đáy
        c.ell(120, 236, 92, 14, c.rg([(0, "#000000", 0.28), (1, "#000000", 0)]), stroke=None)
        if glow:
            c.circ(120, 120, 116, c.rg([(0.75, glow, 0.9), (1, glow, 0)]), stroke=None)
        # đế dày phía dưới (nổi khối)
        c.circ(120, 128, 104, dk(rim2, 0.25), stroke=None)
        # vành
        c.circ(120, 118, 104, c.lg(rim1, rim2), stroke=OUT, sw=5)
        # mặt nút
        c.circ(120, 114, 88, c.rg([(0, "#fffdf6", 1), (0.7, "#fbecd2", 1), (1, "#efd6ad", 1)], 0.5, 0.35, 0.7),
               stroke=dk(rim2, 0.1), sw=3)
        # vệt sáng phía trên
        c.path("M54,88 Q120,20 186,88 Q120,52 54,88 Z", "#ffffff", stroke=None, extra='opacity="0.55"')
        c.save(name, folder)




def area_thumbs():
    specs = [("area_hall", "#f0c187", "#f6e3bd"), ("area_garden", "#9fdc6a", "#7cc96b"),
             ("area_vip", "#8e2c3c", "#c9963e"), ("area_lodging", "#9fb5d6", "#f6e3bd")]
    for name, floor, wallc in specs:
        c = C(200, 170, 100, 128)
        i = c.iso

        def isos(x, y, z=0, s=0.36):
            return (c.ax + (x - y) * HW * s, c.ay + (x + y) * HH * s - z * s)
        c.shadow(100, 146, 92, 20, 0.2)
        c.poly([isos(-1, -1), isos(1, -1), isos(1, 1), isos(-1, 1)], floor, sw=4)
        c.poly([isos(-1, -1), isos(-1, 1), isos(-1, 1, 140), isos(-1, -1, 140)], dk(wallc, 0.05), sw=4)
        c.poly([isos(-1, -1), isos(1, -1), isos(1, -1, 140), isos(-1, -1, 140)], dk(wallc, 0.15), sw=4)
        if name == "area_garden":
            p = isos(0.3, 0.3)
            c.circ(p[0], p[1] - 30, 18, "#4ea83a", sw=3)
            c.rect(p[0] - 3, p[1] - 14, 6, 14, "#8a5530", stroke=None)
        elif name == "area_vip":
            p = isos(0.2, 0.2)
            c.ell(p[0], p[1] - 10, 26, 12, "#c4283e", sw=3)
            c.circ(p[0], p[1] - 40, 10, "#f3d27a", sw=3)
        elif name == "area_lodging":
            p = isos(0.2, 0.2)
            c.rect(p[0] - 24, p[1] - 18, 48, 20, "#ffffff", rx=4, sw=3)
            c.rect(p[0] - 24, p[1] - 18, 20, 20, "#6fa8dc", rx=4, sw=3)
        else:
            p = isos(0.2, 0.2)
            c.ell(p[0], p[1] - 12, 22, 10, "#d7a066", sw=3)
        c.save(name, UI_DIR)


def logo():
    c = C(420, 320, 210, 300)
    cx = 210
    c.shadow(cx, 290, 170, 26, 0.25)
    c.rect(70, 140, 280, 150, c.lg("#f6e3bd", "#e3c894"), rx=12, sw=6)
    c.poly([(40, 150), (210, 30), (380, 150)], c.lg("#e86a5f", "#b8423a"), sw=6)
    c.poly([(80, 150), (210, 60), (340, 150)], "none", stroke="#f6a39a", sw=4, extra='stroke-opacity="0.6"')
    c.rect(180, 200, 60, 90, c.lg("#b77744", "#8a5530"), rx=8, sw=5)
    for x in (95, 270):
        c.rect(x, 180, 56, 48, c.lg("#d9f4ff", "#8fd0f0"), rx=6, sw=5)
        c.line(x + 28, 180, x + 28, 228, stroke="#8a5530", sw=4)
    for x, col in [(70, "#ffd34d"), (350, "#ffd34d")]:
        c.circ(x, 120, 20, c.rg([(0, "#fff0a0", 1), (1, "#d6313f", 1)], 0.45, 0.4, 0.6), sw=4)
    c.save("logo", UI_DIR)


def ui_icons_v2(folder=UI_DIR):
    """Bộ icon giao diện mới: nút tròn đáy màn hình, cột menu, avatar."""
    # nồi hầm (Thực đơn)
    c = icon_canvas(160)
    c.shadow(80, 138, 60, 12, 0.25)
    c.path("M22,74 Q24,136 80,136 Q136,136 138,74 Z", c.lg("#7b746e", "#4c4642", 0, 0, 1, 0), sw=5)
    c.ell(80, 74, 58, 18, "#5a534e", sw=5)
    c.ell(80, 72, 46, 13, c.lg("#f2b25a", "#d9822b"), sw=3)
    for x, y, col in [(62, 68, "#e85d5d"), (86, 74, "#7cc96b"), (100, 66, "#ffd34d"), (74, 62, "#f6e3bd")]:
        c.circ(x, y, 7, col, sw=2.5)
    for sx in (-1, 1):
        c.rect(80 + sx * 66 - 9, 80, 18, 12, "#5a534e", rx=5, sw=4)
    c.path("M30,52 Q80,10 132,46 L126,58 Q80,26 36,62 Z", c.lg("#8a837d", "#5c5550"), sw=5)
    c.circ(84, 30, 9, "#5c5550", sw=4)
    c.save("icon_pot", folder)
    # chậu cây (Mở rộng / trang trí)
    c = icon_canvas(160)
    c.shadow(80, 146, 50, 10, 0.25)
    c.path("M48,96 L112,96 L104,144 L56,144 Z", c.lg("#a86a42", "#7a4a2e", 0, 0, 1, 0), sw=5)
    c.rect(42, 88, 76, 16, "#b97a4c", rx=6, sw=5)
    c.rect(77, 60, 6, 32, "#7a4a2e", stroke=None)
    for x, y, r in [(80, 40, 30), (52, 58, 24), (108, 58, 24), (66, 26, 20), (96, 28, 20)]:
        c.circ(x, y, r + 3, OUT, stroke=None)
    for x, y, r in [(80, 40, 30), (52, 58, 24), (108, 58, 24), (66, 26, 20), (96, 28, 20)]:
        c.circ(x, y, r, c.rg([(0, "#8fd86a", 1), (1, "#3f9a3a", 1)], 0.4, 0.3, 0.75), stroke=None)
    c.save("icon_plant", folder)
    # giỏ quà (Nhiệm vụ)
    c = icon_canvas(160)
    c.shadow(80, 146, 58, 10, 0.25)
    c.path("M40,70 Q80,8 120,70", "none", stroke=OUT, sw=14)
    c.path("M40,70 Q80,8 120,70", "none", stroke="#c4483e", sw=8)
    c.circ(66, 70, 20, c.rg([(0, "#fff2a8", 1), (1, "#e89b16", 1)]), sw=4)
    c.circ(96, 66, 18, "#e85dae", sw=4)
    c.path("M22,72 L138,72 L124,142 L36,142 Z", c.lg("#e2584a", "#b23d30"), sw=5)
    for x in (52, 80, 108):
        c.line(x, 80, x - 2 if x < 80 else x + 2, 136, stroke="#f08a7c", sw=4)
    c.rect(16, 66, 128, 16, "#c4483e", rx=7, sw=5)
    c.save("icon_basket", folder)
    # sổ ngôi sao (Nhiệm vụ / thành tích)
    c = icon_canvas(160)
    c.shadow(80, 148, 52, 10, 0.25)
    c.rect(30, 22, 100, 120, c.lg("#a8683d", "#7a4a2e"), rx=12, sw=5)
    c.rect(40, 30, 84, 104, "#c98a55", rx=8, stroke=None)
    d = ""
    for k in range(10):
        r = 30 if k % 2 == 0 else 13
        a = -math.pi / 2 + k * math.pi / 5
        d += ("M" if k == 0 else "L") + "%s,%s " % (f(84 + math.cos(a) * r), f(80 + math.sin(a) * r))
    c.path(d + "Z", c.rg([(0, "#ffe27a", 1), (1, "#f2862e", 1)]), sw=4)
    c.path("M108,132 L108,154 L116,146 L124,154 L124,132", "#4fa3e0", sw=4)
    c.save("icon_book", folder)
    # mái nhà (khu quán)
    c = icon_canvas(160)
    c.shadow(80, 146, 56, 10, 0.25)
    c.rect(36, 74, 88, 66, c.lg("#f6dcb4", "#e2bd86"), rx=8, sw=5)
    c.path("M66,140 L66,108 Q80,94 94,108 L94,140 Z", "#7a4a2e", sw=4)
    c.path("M14,82 L80,22 L146,82 L132,94 L80,46 L28,94 Z", c.lg("#e0985a", "#b8693a"), sw=5)
    c.path("M44,46 L56,30 L66,44 Z M116,46 L104,30 L94,44 Z", "#c97a44", sw=4)
    c.save("icon_house", folder)
    # đĩa món (bộ đếm món)
    c = icon_canvas(160)
    c.ell(80, 108, 64, 24, "#d9dde2", sw=5)
    c.ell(80, 102, 64, 24, c.lg("#ffffff", "#eef1f4"), sw=5)
    c.path("M38,98 Q40,48 80,44 Q120,48 122,98 Q80,114 38,98 Z", c.rg([(0, "#ffffff", 1), (1, "#f0e6cc", 1)]), sw=4)
    c.path("M52,70 Q80,52 108,72 Q96,84 80,78 Q64,86 52,70 Z", "#f6c95a", sw=3)
    c.save("icon_plate", folder)
    # nút cộng xanh
    c = icon_canvas(96)
    c.circ(48, 50, 40, "#3f8f2a", stroke=None)
    c.circ(48, 46, 40, c.lg("#8ee06a", "#4fb83a"), sw=5)
    c.path("M48,26 L48,66 M28,46 L68,46", "none", stroke="#ffffff", sw=12)
    c.save("plus_green", folder)
    # nhân viên + (thuê thêm)
    c = icon_canvas(160)
    c.circ(74, 74, 44, c.rg([(0, lt(SKIN, 0.35), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.12), 1)], 0.42, 0.38, 0.6), sw=5)
    c.rect(40, 18, 68, 22, "#ffffff", rx=8, sw=5)
    for x, y, r in [(52, 14, 16), (96, 14, 16), (74, 4, 20)]:
        c.circ(x, y + 6, r, "#ffffff", sw=5)
    c.rect(42, 30, 64, 16, "#ffffff", rx=6, stroke=None)
    c.ell(62, 80, 6, 8, "#2b1a12", stroke=None)
    c.ell(88, 80, 6, 8, "#2b1a12", stroke=None)
    c.path("M66,98 q8,8 16,0", "none", stroke="#2b1a12", sw=4)
    c.circ(122, 120, 26, c.lg("#7fd8ff", "#3aa7e0"), sw=5)
    c.path("M122,104 L122,136 M106,120 L138,120", "none", stroke="#ffffff", sw=9)
    c.save("icon_staff", folder)
    # mặt khách (nút giữa)
    c = icon_canvas(180)
    cx, cy = 90, 96
    c.circ(cx, cy, 70, c.rg([(0, lt(SKIN, 0.4), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.12), 1)], 0.42, 0.38, 0.6), sw=6)
    c.path("M22,96 Q14,20 92,22 Q168,22 158,96 Q140,60 110,52 Q84,70 52,58 Q32,72 22,96 Z",
           c.rg([(0, "#8a5a3a", 1), (1, "#4a2e1e", 1)], 0.4, 0.2, 0.8), sw=5)
    for dx in (-26, 26):
        c.ell(cx + dx, cy + 14, 12, 16, "#2b1a12", stroke=None)
        c.circ(cx + dx + 4, cy + 7, 5, "#ffffff", stroke=None)
    c.ell(cx - 46, cy + 36, 12, 7, "#ff8f8f", stroke=None, extra='opacity="0.6"')
    c.ell(cx + 46, cy + 36, 12, 7, "#ff8f8f", stroke=None, extra='opacity="0.6"')
    c.path("M%s,%s q12,12 24,0" % (f(cx - 12), f(cy + 40)), "none", stroke="#2b1a12", sw=5)
    c.save("icon_customers", folder)
    # avatar chủ quán (khung tròn)
    c = icon_canvas(200)
    c.circ(100, 100, 94, c.lg("#8a4e2c", "#5e3420"), sw=6)
    c.circ(100, 100, 80, c.rg([(0, "#ffe9b8", 1), (1, "#f2b875", 1)]), sw=4)
    c.circ(100, 112, 46, c.rg([(0, lt(SKIN, 0.4), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.12), 1)], 0.42, 0.38, 0.6), sw=5)
    c.path("M52,112 Q46,50 100,48 Q154,50 148,112 Q138,84 118,76 Q100,92 76,80 Q60,92 52,112 Z", "#2c2c3a", sw=5)
    c.poly([(30, 92), (172, 92), (100, 30)], c.lg("#f6e3a1", "#d9b968", 0, 0, 1, 0), sw=5)
    for dx in (-17, 17):
        c.ell(100 + dx, 118, 7, 9, "#2b1a12", stroke=None)
        c.circ(102 + dx, 114, 3, "#ffffff", stroke=None)
    c.ell(72, 132, 8, 5, "#ff8f8f", stroke=None, extra='opacity="0.6"')
    c.ell(128, 132, 8, 5, "#ff8f8f", stroke=None, extra='opacity="0.6"')
    c.path("M92,138 q8,8 16,0", "none", stroke="#2b1a12", sw=4)
    c.path("M70,160 Q100,176 130,160 L136,184 Q100,196 64,184 Z", "#e8414f", sw=4)
    c.save("avatar", folder)


def app_icon():
    c = C(256, 256, 128, 128)
    c.rect(8, 8, 240, 240, c.lg("#ffe08a", "#f6a85a"), rx=56, sw=8)
    c.shadow(128, 214, 92, 16, 0.25)
    c.rect(54, 112, 148, 100, c.lg("#fff3d6", "#ecd29b"), rx=10, sw=7)
    c.poly([(32, 120), (128, 44), (224, 120)], c.lg("#e86a5f", "#b8423a"), sw=7)
    c.rect(108, 146, 40, 66, c.lg("#b77744", "#8a5530"), rx=6, sw=6)
    c.rect(66, 132, 30, 30, "#bfe9ff", rx=5, sw=5)
    c.rect(160, 132, 30, 30, "#bfe9ff", rx=5, sw=5)
    c.circ(196, 70, 26, c.rg([(0, "#fff2a8", 1), (0.6, "#ffc93c", 1), (1, "#e89b16", 1)]), sw=6)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">'
           '<defs>%s</defs>%s</svg>') % ("".join(c.defs), "".join(c.els))
    (ROOT / "icon.svg").write_text(svg, encoding="utf-8")


def main():
    floor_wood("floor_wood_a", "#f0c48c", 1)
    floor_wood("floor_wood_b", "#ecbd84", 2)
    floor_wood("floor_out_a", "#d9a46c", 3)
    floor_wood("floor_out_b", "#d39d66", 4)
    carpet_runner("carpet_runner")
    wall_post("wall_post")
    floor_stone("floor_stone_a", "#c9c3b8", 3)
    floor_stone("floor_stone_b", "#bdb6aa", 4)
    floor_tile_vip("floor_vip")
    for k in range(3):
        grass("grass_%d" % k, k)
    dirt("dirt_a", 5)
    dirt("dirt_b", 6)
    floor_edge("edge_wood_l", "l", "#b37a48")
    floor_edge("edge_wood_r", "r", "#b37a48")
    floor_edge("edge_stone_l", "l", "#a39b8e")
    floor_edge("edge_stone_r", "r", "#a39b8e")
    for kind in ("a", "b"):
        for side in ("l", "r"):
            wall("wall_%s_%s" % (kind, side), side, kind)
            wall("wall_%s_%s_window" % (kind, side), side, kind, "window")
            wall("wall_%s_%s_door" % (kind, side), side, kind, "door")
    for t in (1, 2, 3):
        table("table_%d" % t, t)
        chair("chair_%d" % t, t)
    kitchen_counter("kitchen_counter")
    stove("stove")
    pot("pot")
    cashier_counter("cashier_counter")
    shelf("shelf")
    plant_pot("plant_pot")
    lantern("lantern")
    painting("painting_l", "l", 0)
    painting("painting_r", "r", 1)
    rug("rug")
    tree("tree_a", 0)
    tree("tree_b", 1)
    bush("bush_flower")
    fence("fence_x", "x")
    fence("fence_y", "y")
    gate("gate")
    bed("bed")
    signpost("signpost")
    characters()
    story_characters()
    coin()
    diamond_icon()
    coin("coin", UI_DIR)
    diamond_icon("diamond", UI_DIR)
    star_icon("star")
    star_icon("exp", "#7bd35b")
    gear_icon()
    lock_icon()
    hand_icon()
    tab_icons()
    misc_icons()
    bubbles()
    dish_icons()
    more_dish_icons()
    event_icons()
    chapter_thumbs()
    progression_icons()
    nav_buttons()
    chapter_props()
    customer_badges()
    area_thumbs()
    logo()
    ui_icons_v2()
    app_icon()
    # bộ vẽ mới (phiên bản 2): mỗi module ghi đè các sprite cùng tên, giữ nguyên điểm neo
    import importlib
    import sys as _sys
    base = _sys.modules[__name__]
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    for mod in ("art_characters", "art_props", "art_icons"):
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        m.run(base)
    story_portraits()
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    print("sprites:", len(manifest), "ui:", len(list(UI_DIR.glob("*.svg"))))


if __name__ == "__main__":
    main()
