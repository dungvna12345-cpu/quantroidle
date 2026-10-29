# -*- coding: utf-8 -*-
"""Bộ vẽ nhân vật chibi phiên bản 2 cho Quán Trọ Idle.

Được gen_sprites.main() gọi qua run(base) sau khi các sprite cũ đã được ghi;
mỗi sprite cùng tên sẽ bị ghi đè (cùng canvas 150x220, neo 75,206).

Phong cách: viền nâu #5a341f, ánh sáng từ trên-trái (lớp phủ radial: điểm sáng
trên-trái + vùng tối cứng phía dưới-phải), mắt to bóng, tóc có lọn + vệt sáng,
quần áo có nếp gấp, bàn tay, giày có điểm sáng.
Chỉ dùng path/shape + gradient + opacity (tương thích ThorVG).
"""
import math

OL = "#5a341f"
SK = "#f9d2ad"
SKS = "#e8b48c"
INK = "#3a2216"
BLUSH = "#ff8f8f"
GOLD = "#f3c94f"
MOUTH = "#9b3a35"

_b = None


def F(v):
    return _b.f(v)


def lt(c, t):
    return _b.lt(c, t)


def dk(c, t):
    return _b.dk(c, t)


def mix(a, b, t):
    return _b.mix(a, b, t)


def P(*a):
    """Ghép lệnh path: chuỗi giữ nguyên, số -> định dạng gọn, cặp (x, y) -> 'x,y'."""
    out = []
    for v in a:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, tuple):
            out.append(F(v[0]) + "," + F(v[1]))
        else:
            out.append(F(v))
    return " ".join(out)


def capsule(p0, p1, r0, r1):
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    a = (x0 + nx * r0, y0 + ny * r0)
    b = (x1 + nx * r1, y1 + ny * r1)
    c = (x1 - nx * r1, y1 - ny * r1)
    d = (x0 - nx * r0, y0 - ny * r0)
    return P("M", a, "L", b, "A", r1, r1, "0 0 0", c, "L", d, "A", r0, r0, "0 0 0", a, "Z")


def ell_d(x, y, rx, ry):
    return P("M", (x - rx, y), "A", rx, ry, "0 1 0", (x + rx, y), "A", rx, ry, "0 1 0", (x - rx, y), "Z")


# ====================================================================== Figure

class Fig:
    def __init__(self, sit=False):
        self.c = _b.C(150, 220, 75, 206)
        self.sit = sit
        self.cx, self.by = 75, 206
        self.dy = 26 if sit else 0
        self.T = 120 + self.dy          # vai
        self.B = 168 + self.dy          # eo / gấu áo
        self.hx, self.hy = 77, 84 + self.dy
        # lớp phủ sáng/tối dùng chung (objectBoundingBox -> hợp với mọi hình)
        self.sh = self.c.rg([(0, "#ffffff", 0.42), (0.3, "#ffffff", 0), (0.68, "#3b1d0c", 0),
                             (0.71, "#3b1d0c", 0.13), (1, "#3b1d0c", 0.24)], cx=0.32, cy=0.26, r=0.8)
        self.sh_soft = self.c.rg([(0, "#ffffff", 0.3), (0.35, "#ffffff", 0), (0.75, "#3b1d0c", 0),
                                  (1, "#3b1d0c", 0.16)], cx=0.34, cy=0.3, r=0.8)

    # --- primitives
    def fill(self, d, col, shade=True):
        self.c.path(d, col, stroke=None)
        if shade:
            self.c.path(d, self.sh if shade is True else shade, stroke=None)

    def line(self, d, sw=4.5, col=OL, op=None):
        ex = ('stroke-opacity="%s"' % F(op)) if op is not None else ""
        self.c.path(d, "none", stroke=col, sw=sw, extra=ex)

    def part(self, d, col, sw=4.5, shade=True):
        self.fill(d, col, shade)
        self.line(d, sw)

    def blob(self, d, col, op=1.0):
        self.c.path(d, col, stroke=None, extra=('opacity="%s"' % F(op)) if op < 1 else "")

    def vg(self, col, a=0.14, b=0.1):
        return self.c.lg(lt(col, a), dk(col, b))

    def hg(self, col, a=0.1, b=0.16):
        return self.c.lg(lt(col, a), dk(col, b), 0, 0, 1, 0)

    def dot(self, x, y, r, col, op=1.0):
        self.c.circ(x, y, r, col, stroke=None, extra=('opacity="%s"' % F(op)) if op < 1 else "")

    def oval(self, x, y, rx, ry, col, op=1.0):
        self.c.ell(x, y, rx, ry, col, stroke=None, extra=('opacity="%s"' % F(op)) if op < 1 else "")

    def button(self, x, y, col, r=2.8):
        self.c.circ(x, y, r, col, stroke=dk(col, 0.45), sw=1.2)
        self.dot(x - r * 0.35, y - r * 0.35, r * 0.38, "#ffffff", 0.75)

    def torso_d(self, wt=23, wb=26, bot=None, belly=0):
        cx, T = self.cx, self.T
        Bb = self.B if bot is None else bot
        if belly:
            return P("M", (cx - wt + 5, T), "C", (cx - wt - 2, T + 1), (cx - wt - 4, T + 10), (cx - wt - 4, T + 20),
                     "C", (cx - wt - 4 - belly, T + 32), (cx - wb - belly, Bb - 8), (cx - wb, Bb),
                     "Q", (cx + 1, Bb + 7), (cx + wb + 2, Bb),
                     "C", (cx + wb + 2 + belly, Bb - 8), (cx + wt + 6 + belly, T + 32), (cx + wt + 6, T + 20),
                     "C", (cx + wt + 6, T + 10), (cx + wt + 4, T + 1), (cx + wt - 3, T),
                     "Q", (cx + 1, T - 3), (cx - wt + 5, T), "Z")
        return P("M", (cx - wt + 5, T), "C", (cx - wt - 2, T + 1), (cx - wt - 4, T + 10), (cx - wt - 4, T + 20),
                 "L", (cx - wb, Bb), "Q", (cx + 1, Bb + 5), (cx + wb + 2, Bb),
                 "L", (cx + wt + 6, T + 20), "C", (cx + wt + 6, T + 10), (cx + wt + 4, T + 1), (cx + wt - 3, T),
                 "Q", (cx + 1, T - 3), (cx - wt + 5, T), "Z")

    def neck_u(self, w=11, depth=12):
        cx, T = self.cx, self.T
        d = P("M", (cx + 2 - w, T - 1), "Q", (cx + 2, T + depth), (cx + 2 + w + 1, T - 1), "Z")
        self.blob(d, mix(SK, SKS, 0.6))
        self.line(P("M", (cx + 2 - w, T - 1), "Q", (cx + 2, T + depth), (cx + 3 + w, T - 1)), sw=2.4)

    def fold(self, d, col, op=0.5, sw=2.0):
        self.line(d, sw=sw, col=dk(col, 0.32), op=op)

    def shine(self, d, op=0.55, sw=2.4):
        self.line(d, sw=sw, col="#ffffff", op=op)


# ====================================================================== feet / legs

def shoe(s, x, y, col, kind="leather"):
    d = P("M", (x - 10, y + 4), "C", (x - 12, y - 5), (x - 3, y - 8), (x + 3, y - 7),
          "C", (x + 10, y - 6), (x + 13, y - 1), (x + 12, y + 4), "Q", (x + 1, y + 7), (x - 10, y + 4), "Z")
    if kind == "sneaker":
        s.part(d, s.vg("#fbf8f2", 0.2, 0.08), sw=3.4)
        s.line(P("M", (x - 10, y + 2), "Q", (x + 1, y + 5), (x + 12, y + 2)), sw=2.6, col=col)
        s.line(P("M", (x - 3, y - 6), "L", (x + 1, y - 2), "M", (x + 1, y - 7), "L", (x + 4, y - 3)), sw=1.6, col=dk(col, 0.1))
    else:
        s.part(d, s.vg(col, 0.18, 0.12), sw=3.4)
        s.line(P("M", (x - 10, y + 2.5), "Q", (x + 1, y + 5.5), (x + 12, y + 2.5)), sw=1.6, col=lt(col, 0.3), op=0.7)
    s.oval(x + 3, y - 3.5, 4.2, 1.8, "#ffffff", 0.6)


def legs(s, kind, col, shoe_col, shoe_kind="leather"):
    cx, by, B = s.cx, s.by, s.B
    if s.sit:
        shoe(s, cx - 12, by - 1, shoe_col, shoe_kind)
        shoe(s, cx + 16, by - 1, shoe_col, shoe_kind)
        if kind in ("skirt",):
            for lx in (-12, 13):
                s.part(capsule((cx + lx, B + 2), (cx + lx + 1, B + 10), 6, 6), SK, sw=3.4, shade=s.sh_soft)
        d = P("M", (cx - 25, B - 6), "L", (cx + 27, B - 6), "C", (cx + 31, B), (cx + 32, B + 8), (cx + 28, B + 12),
              "Q", (cx + 16, B + 15), (cx + 4, B + 12), "Q", (cx + 1, B + 10), (cx - 2, B + 12),
              "Q", (cx - 14, B + 15), (cx - 26, B + 12), "C", (cx - 30, B + 8), (cx - 29, B), (cx - 25, B - 6), "Z")
        if kind == "skirt":
            d = P("M", (cx - 25, B - 6), "L", (cx + 27, B - 6), "C", (cx + 31, B), (cx + 33, B + 4), (cx + 30, B + 8),
                  "Q", (cx + 1, B + 12), (cx - 28, B + 8), "C", (cx - 31, B + 4), (cx - 29, B), (cx - 25, B - 6), "Z")
        s.part(d, s.hg(col))
        s.fold(P("M", (cx + 1, B + 2), "L", (cx + 1, B + 9)), col)
        return
    if kind == "skirt":
        for lx in (-12, 13):
            s.part(capsule((cx + lx, B + 4), (cx + lx, by - 9), 5.5, 5), s.hg(SK, 0.05, 0.05), sw=3.4, shade=s.sh_soft)
            s.oval(cx + lx, by - 11, 5, 3, "#ffffff", 0.95)  # tất
        shoe(s, cx - 13, by - 3, shoe_col, shoe_kind)
        shoe(s, cx + 14, by - 3, shoe_col, shoe_kind)
        d = P("M", (cx - 24, B - 8), "L", (cx + 26, B - 8), "L", (cx + 33, B + 15),
              "Q", (cx + 1, B + 22), (cx - 31, B + 15), "Z")
        s.part(d, s.hg(col))
        for k in (-16, -5, 7, 18):
            s.fold(P("M", (cx + k * 0.7, B - 4), "L", (cx + k, B + 16)), col, op=0.45)
        s.shine(P("M", (cx - 20, B - 4), "L", (cx - 25, B + 10)), op=0.3, sw=2.5)
        return
    wide = kind == "wide"
    shoe(s, cx - 13, by - 3, shoe_col, shoe_kind)
    shoe(s, cx + 14, by - 3, shoe_col, shoe_kind)
    o = 3 if wide else 0
    d = P("M", (cx - 24, B - 6), "L", (cx + 26, B - 6), "C", (cx + 28, B + 6), (cx + 26 + o, B + 18), (cx + 25 + o, by - 9),
          "Q", (cx + 15, by - 6), (cx + 4 - o, by - 9), "L", (cx + 2, B + 10), "Q", (cx + 1, B + 7), (cx, B + 10),
          "L", (cx - 2 + o, by - 9), "Q", (cx - 13, by - 6), (cx - 23 - o, by - 9),
          "C", (cx - 24, B + 18), (cx - 26, B + 6), (cx - 24, B - 6), "Z")
    s.part(d, s.hg(col))
    s.fold(P("M", (cx - 13, B + 8), "Q", (cx - 12, B + 16), (cx - 13, by - 12)), col, op=0.4)
    s.fold(P("M", (cx + 15, B + 8), "Q", (cx + 16, B + 16), (cx + 15, by - 12)), col, op=0.4)
    s.shine(P("M", (cx - 20, B + 4), "L", (cx - 20, by - 14)), op=0.22, sw=2.6)


# ====================================================================== arms / hands

def hand(s, x, y, side=1):
    s.c.ell(x + side * 4.5, y - 2.5, 3.2, 4, SK, stroke=OL, sw=2.6)
    s.c.ell(x, y, 6.6, 7.2, s.c.rg([(0, lt(SK, 0.3), 1), (0.7, SK, 1), (1, SKS, 1)], 0.38, 0.32, 0.7), stroke=OL, sw=3.2)
    s.line(P("M", (x - side * 2, y + 3), "L", (x + side * 1, y + 5.5)), sw=1.4, col=SKS)


def arm(s, side, spec):
    cx, T = s.cx, s.T
    sx, sy = cx + 1 + side * 21, T + 9
    wx, wy = cx + 1 + side * 29, T + 37
    col = spec["col"]
    kind = spec.get("kind", "long")
    if kind in ("short", "puff"):
        s.part(capsule((sx, sy + 4), (wx, wy), 5.6, 5.0), s.hg(SK, 0.05, 0.05), sw=3.6, shade=s.sh_soft)
        if kind == "puff":
            s.part(ell_d(cx + 1 + side * 24, T + 13, 10, 9.5), s.vg(col))
            s.fold(P("M", (cx + 1 + side * 19, T + 20), "Q", (cx + 1 + side * 24, T + 17), (cx + 1 + side * 30, T + 19)), col, op=0.5)
        else:
            s.part(capsule((sx, sy), (cx + 1 + side * 26, T + 21), 8.6, 8.2), s.vg(col))
            s.line(P("M", (cx + 1 + side * 19, T + 25), "L", (cx + 1 + side * 33, T + 22)), sw=2, col=dk(col, 0.3), op=0.5)
    else:
        r1 = 8.0 if kind == "wide" else 6.6
        s.part(capsule((sx, sy), (wx, wy), 8.2, r1), s.hg(col, 0.12, 0.12))
        s.fold(P("M", (sx + side * 2, sy + 12), "q", side * 3, 3, side * 5, 1), col, op=0.5)
        s.fold(P("M", (sx + side * 4, sy + 20), "q", side * 3, 2, side * 5, 0), col, op=0.4)
        cuff = spec.get("cuff")
        if cuff:
            s.part(capsule((wx - side * 0.6, wy - 3), (wx, wy + 0.5), r1 + 0.6, r1 + 0.6), s.vg(cuff), sw=3)
    hand(s, wx + side * 0.5, wy + 6, side)


def tray_arm(s, spec):
    cx, T = s.cx, s.T
    col = spec["col"]
    ex, ey = cx + 41, T + 10
    s.part(capsule((ex, ey), (cx + 47, T - 30), 6.8, 6.0), s.hg(col, 0.12, 0.12))
    s.part(capsule((cx + 22, T + 9), (ex, ey), 8.2, 7.0), s.hg(col, 0.12, 0.12))
    cuff = spec.get("cuff")
    if cuff:
        s.part(capsule((cx + 47, T - 28), (cx + 47.5, T - 32), 6.8, 6.8), s.vg(cuff), sw=3)


def tray_top(s):
    x, y = 123, 71 + s.dy
    hand(s, x - 2, y + 14, 1)
    s.c.ell(x, y + 3.5, 25, 7.5, s.c.lg("#b9c2cc", "#7f8a96", 0, 0, 1, 0), stroke=OL, sw=3.6)
    s.c.ell(x, y, 25, 6.8, s.c.lg("#f4f7fa", "#c4ccd5", 0, 0, 1, 1), stroke=OL, sw=3.2)
    s.c.ell(x, y, 19.5, 4.4, "none", stroke="#9aa5b1", sw=1.6, extra='stroke-opacity="0.7"')
    s.c.path(P("M", (x - 18, y - 2.5), "Q", (x - 8, y - 5.5), (x + 4, y - 5.2)), "none", stroke="#ffffff", sw=2.2,
             extra='stroke-opacity="0.9"')


# ====================================================================== head / face

def face_d(hx, hy):
    return P("M", (hx - 40, hy + 2), "C", (hx - 41, hy - 24), (hx - 22, hy - 37), (hx + 1, hy - 37),
             "C", (hx + 24, hy - 37), (hx + 41, hy - 22), (hx + 40, hy + 2),
             "C", (hx + 39, hy + 25), (hx + 24, hy + 37), (hx + 2, hy + 37),
             "C", (hx - 20, hy + 37), (hx - 40, hy + 26), (hx - 40, hy + 2), "Z")


def head(s, forehead_shadow=True):
    c, hx, hy = s.c, s.hx, s.hy
    # tai
    c.ell(hx - 38, hy + 8, 7.5, 9.5, SK, stroke=OL, sw=3.4)
    s.line(P("M", (hx - 39, hy + 3), "Q", (hx - 43, hy + 8), (hx - 38, hy + 13)), sw=2, col=SKS)
    c.ell(hx + 39, hy + 8, 5.5, 8.5, mix(SK, SKS, 0.4), stroke=OL, sw=3.4)
    fg = c.rg([(0, lt(SK, 0.38), 1), (0.55, SK, 1), (0.9, mix(SK, SKS, 0.55), 1), (1, SKS, 1)], 0.4, 0.36, 0.66)
    s.part(face_d(hx, hy), fg, sw=4.6, shade=False)
    # bóng má phía phải + bóng dưới tóc
    s.blob(P("M", (hx + 31, hy - 18), "Q", (hx + 42, hy + 4), (hx + 30, hy + 30), "Q", (hx + 22, hy + 35),
             (hx + 12, hy + 36), "Q", (hx + 34, hy + 22), (hx + 31, hy - 18), "Z"), SKS, 0.45)
    if forehead_shadow:
        s.oval(hx + 2, hy - 14, 34, 11, SKS, 0.55)


def eye(s, x, y, rx, ry, kind="normal", lash=False, iris="#5a3320"):
    c = s.c
    if kind == "happy":
        s.line(P("M", (x - rx, y + 3), "Q", (x, y - ry), (x + rx, y + 3)), sw=3.6, col=INK)
        if lash:
            s.line(P("M", (x + rx - 0.5, y + 2), "l", 3, -2), sw=2.4, col=INK)
        return
    if kind == "smug":
        top = y - 1
        c.path(P("M", (x - rx, top), "A", rx, ry, "0 0 0", (x + rx, top), "Z"), "#ffffff", stroke=OL, sw=1.6)
        c.path(P("M", (x - rx + 2.4, top), "A", rx - 1.8, ry - 1.6, "0 0 0", (x + rx - 0.6, top), "Z"),
               c.lg(dk(iris, 0.45), lt(iris, 0.25)), stroke=None)
        s.oval(x + 1, top + 3, rx * 0.4, ry * 0.3, dk(iris, 0.6))
        s.dot(x - rx * 0.25, top + 2.4, rx * 0.26, "#ffffff")
        s.line(P("M", (x - rx - 1.5, top - 0.5), "L", (x + rx + 1.5, top - 2)), sw=3.6, col=INK)
        s.line(P("M", (x - rx + 1, top - 4.5), "Q", (x, top - 7), (x + rx, top - 5.5)), sw=1.5, col=INK, op=0.5)
        return
    c.ell(x, y, rx, ry, "#ffffff", stroke=OL, sw=1.6)
    c.ell(x + 0.6, y + 1.1, rx - 1.35, ry - 1.25, c.lg(dk(iris, 0.6), lt(iris, 0.12), mid=iris), stroke=None)
    s.oval(x + 0.7, y + 1.8, rx * 0.42, ry * 0.46, dk(iris, 0.65))
    s.oval(x + 0.9, y + ry * 0.5, rx * 0.55, ry * 0.24, "#e9a35a", 0.75)
    s.dot(x - rx * 0.3, y - ry * 0.32, rx * 0.42, "#ffffff")
    s.dot(x + rx * 0.42, y + ry * 0.36, rx * 0.18, "#ffffff")
    s.line(P("M", (x - rx - 1.2, y - ry * 0.2), "Q", (x - rx * 0.15, y - ry - 3.4), (x + rx + 1.2, y - ry * 0.32)),
           sw=3.6, col=INK)
    if lash:
        s.line(P("M", (x + rx + 0.6, y - ry * 0.34), "L", (x + rx + 4, y - ry * 0.8)), sw=2.6, col=INK)
        s.line(P("M", (x + rx - 1.2, y - ry * 0.68), "L", (x + rx + 2, y - ry * 1.15)), sw=2.2, col=INK)
    s.line(P("M", (x - rx * 0.45, y + ry + 1.6), "Q", (x, y + ry + 2.6), (x + rx * 0.45, y + ry + 1.6)), sw=1.4, col=INK,
           op=0.35)


def brow(s, x, y, col, kind="normal", side=1):
    if kind == "up":
        d = P("M", (x - 6, y - 1), "Q", (x, y - 6), (x + 6, y - 3))
    elif kind == "kind":
        d = P("M", (x - 6, y - 1), "Q", (x, y - 4), (x + 6, y))
    elif kind == "thick":
        s.c.path(P("M", (x - 7, y), "Q", (x, y - 6), (x + 7, y - 1), "Q", (x, y - 2), (x - 7, y), "Z"), col,
                 stroke=col, sw=2.2)
        return
    else:
        d = P("M", (x - 6, y - 0.5), "Q", (x, y - 4.5), (x + 6, y - 1.5))
    s.line(d, sw=3.2, col=col)


def mouth(s, kind, mx, my):
    if kind == "smile":
        s.line(P("M", (mx - 6, my - 1), "Q", (mx, my + 5), (mx + 6, my - 1.5)), sw=2.7, col=INK)
    elif kind == "kind":
        s.line(P("M", (mx - 7.5, my - 2), "Q", (mx, my + 5.5), (mx + 7.5, my - 2.5)), sw=2.7, col=INK)
        s.line(P("M", (mx - 2.5, my + 5.5), "Q", (mx, my + 6.6), (mx + 2.5, my + 5.5)), sw=1.6, col=INK, op=0.4)
    elif kind in ("open", "grin"):
        d = P("M", (mx - 7, my - 2), "Q", (mx, my), (mx + 7, my - 2.5), "Q", (mx + 6.5, my + 9), (mx, my + 9.5),
              "Q", (mx - 6.5, my + 9), (mx - 7, my - 2), "Z")
        s.c.path(d, MOUTH, stroke=None)
        s.oval(mx + 0.5, my + 6.6, 4.4, 2.6, "#f27b7b")
        if kind == "grin":
            s.c.path(P("M", (mx - 6.4, my - 1.3), "Q", (mx, my + 0.8), (mx + 6.4, my - 1.8), "L", (mx + 6, my + 1.8),
                       "Q", (mx, my + 3.6), (mx - 6, my + 2), "Z"), "#ffffff", stroke=None)
        s.line(d, sw=2.4, col=INK)
    elif kind == "smug":
        d = P("M", (mx - 8, my - 1), "Q", (mx + 1, my + 3), (mx + 10, my - 5), "Q", (mx + 9, my + 6), (mx + 2, my + 7),
              "Q", (mx - 5, my + 6), (mx - 8, my - 1), "Z")
        s.c.path(d, MOUTH, stroke=None)
        s.c.path(P("M", (mx - 7, my - 0.4), "Q", (mx + 1, my + 3.4), (mx + 9.4, my - 4.2), "L", (mx + 9, my - 1),
                   "Q", (mx + 1, my + 5.6), (mx - 6, my + 2), "Z"), "#ffffff", stroke=None)
        s.line(d, sw=2.4, col=INK)
        s.line(P("M", (mx + 10.5, my - 8), "Q", (mx + 12.5, my - 5), (mx + 10.5, my - 2)), sw=1.8, col=INK, op=0.6)


def face(s, f):
    hx, hy = s.hx, s.hy
    ey = hy + 8
    lash = f.get("lash", False)
    ek = f.get("eyes", "normal")
    iris = f.get("iris", "#7a3f1c")
    eye(s, hx - 10, ey, 7.8, 9.8, ek, lash, iris)
    eye(s, hx + 18, ey, 7.0, 9.4, ek, lash, iris)
    if f.get("wrinkles"):
        for x, sd in ((hx - 21, -1), (hx + 28, 1)):
            s.line(P("M", (x, ey + 1), "l", sd * 3, 1.5), sw=1.4, col=SKS)
            s.line(P("M", (x, ey + 4), "l", sd * 3, 0.5), sw=1.4, col=SKS)
    # má hồng
    s.oval(hx - 22, hy + 21, 7.5, 4.4, BLUSH, 0.45)
    s.oval(hx + 31, hy + 21, 6.0, 4.0, BLUSH, 0.45)
    s.line(P("M", (hx - 25, hy + 20), "l", 1.6, -2.4, "M", (hx - 21, hy + 20), "l", 1.6, -2.4), sw=1.2, col="#ffffff", op=0.7)
    # mũi
    s.line(P("M", (hx + 5, hy + 15.5), "Q", (hx + 7.5, hy + 17.5), (hx + 4.5, hy + 19)), sw=2.0, col=dk(SKS, 0.18))
    mx, my = hx + 5, hy + 26
    m = f.get("mustache")
    if m:
        mouth(s, f.get("mouth", "smile"), mx + 1, my + 6)
    else:
        mouth(s, f.get("mouth", "smile"), mx, my)


def face_top(s, f, hair_col):
    """Lông mày, kính, ria — vẽ sau tóc."""
    hx, hy = s.hx, s.hy
    bcol = f.get("brow_col", dk(hair_col, 0.25))
    bk = f.get("brow", "normal")
    brow(s, hx - 10, hy - 5, bcol, bk if bk != "smug" else "normal", -1)
    brow(s, hx + 18, hy - 5, bcol, bk if bk != "smug" else "up", 1)
    g = f.get("glasses")
    if g:
        ey = hy + 8
        for x, r in ((hx - 10, 11.5), (hx + 18, 10.5)):
            s.c.circ(x, ey, r, "#ffffff", stroke=None, extra='opacity="0.16"')
            s.line(P("M", (x - r * 0.5, ey - r * 0.1), "L", (x - r * 0.05, ey - r * 0.55)), sw=1.8, col="#ffffff", op=0.8)
            s.c.circ(x, ey, r, "none", stroke=g, sw=2.8)
        s.line(P("M", (hx + 1.5, ey - 1), "Q", (hx + 4, ey - 4), (hx + 7.5, ey - 1)), sw=2.6, col=g)
        s.line(P("M", (hx - 21.5, ey - 1), "L", (hx - 37, ey - 2)), sw=2.6, col=g)
    m = f.get("mustache")
    if m:
        mx, my = hx + 5, hy + 26
        col = f.get("mcol", "#2c2c3a")
        if m == "curl":
            d = P("M", (mx, my - 5), "Q", (mx - 9, my - 10), (mx - 17, my - 3), "Q", (mx - 8, my - 2), (mx, my - 2),
                  "Q", (mx + 8, my - 2), (mx + 18, my - 3), "Q", (mx + 9, my - 10), (mx, my - 5), "Z")
            s.part(d, s.vg(col, 0.25, 0.0), sw=2.2, shade=False)
            for sd in (-1, 1):
                ex = mx + sd * 17 + (1 if sd > 0 else 0)
                s.line(P("M", (ex, my - 3), "Q", (ex + sd * 6, my - 2), (ex + sd * 5.5, my - 7), "Q", (ex + sd * 4, my - 10),
                         (ex + sd * 2, my - 8)), sw=4.6, col=OL)
                s.line(P("M", (ex, my - 3), "Q", (ex + sd * 6, my - 2), (ex + sd * 5.5, my - 7), "Q", (ex + sd * 4, my - 10),
                         (ex + sd * 2, my - 8)), sw=2.2, col=col)
            s.shine(P("M", (mx - 12, my - 5.5), "Q", (mx - 6, my - 8), (mx - 1, my - 6)), op=0.45, sw=1.6)
        else:
            d = P("M", (mx, my - 5), "C", (mx - 5, my - 10), (mx - 15, my - 9), (mx - 17, my - 1),
                  "C", (mx - 12, my - 3), (mx - 6, my - 1), (mx, my - 3),
                  "C", (mx + 6, my - 1), (mx + 13, my - 3), (mx + 18, my - 1),
                  "C", (mx + 16, my - 9), (mx + 5, my - 10), (mx, my - 5), "Z")
            s.part(d, s.vg(col, 0.25, 0.0), sw=2.4, shade=False)
            s.shine(P("M", (mx - 12, my - 5), "Q", (mx - 7, my - 8), (mx - 2, my - 6)), op=0.4, sw=1.6)


# ====================================================================== hair

def hair_fill(s, d, col, sw=4.4):
    s.part(d, s.c.lg(lt(col, 0.2), dk(col, 0.12)), sw=sw)


def strands(s, col, ds, op=0.5):
    for d in ds:
        s.line(d, sw=2.0, col=dk(col, 0.4), op=op)


def hair_shine(s, d, col, op=0.6, sw=4.0):
    s.line(d, sw=sw, col=lt(col, 0.65), op=op)


def hair_back(s, style, col, opts):
    hx, hy = s.hx, s.hy
    if style == "long":
        bot = min(hy + 86, 212)
        d = P("M", (hx - 44, hy - 10), "C", (hx - 48, hy - 50), (hx + 50, hy - 50), (hx + 46, hy - 10),
              "C", (hx + 52, hy + 30), (hx + 54, hy + 64), (hx + 48, bot - 2), "Q", (hx + 34, bot + 4), (hx + 22, bot - 4),
              "L", (hx - 20, bot - 4), "Q", (hx - 34, bot + 4), (hx - 48, bot - 2),
              "C", (hx - 54, hy + 64), (hx - 52, hy + 30), (hx - 44, hy - 10), "Z")
        s.part(d, s.c.lg(dk(col, 0.05), dk(col, 0.28)))
        strands(s, col, [P("M", (hx - 40, hy + 30), "Q", (hx - 44, hy + 60), (hx - 40, bot - 6)),
                         P("M", (hx + 42, hy + 30), "Q", (hx + 46, hy + 60), (hx + 40, bot - 6))], 0.45)
    elif style == "pony":
        d = P("M", (hx - 24, hy - 46), "C", (hx - 64, hy - 52), (hx - 74, hy - 6), (hx - 60, hy + 34),
              "Q", (hx - 57, hy + 46), (hx - 46, hy + 54), "Q", (hx - 54, hy + 30), (hx - 46, hy + 12),
              "Q", (hx - 40, hy - 10), (hx - 22, hy - 30), "Z")
        s.part(d, s.c.lg(lt(col, 0.12), dk(col, 0.15), 0, 0, 1, 1))
        strands(s, col, [P("M", (hx - 34, hy - 42), "Q", (hx - 62, hy - 30), (hx - 56, hy + 30)),
                         P("M", (hx - 32, hy - 36), "Q", (hx - 50, hy - 10), (hx - 50, hy + 30))], 0.5)
        hair_shine(s, P("M", (hx - 46, hy - 40), "Q", (hx - 62, hy - 30), (hx - 64, hy - 6)), col, 0.55, 3.5)
    elif style == "bun":
        bx, by_ = hx - 2, hy - 50
        s.part(ell_d(bx, by_, 16, 14), s.c.rg([(0, lt(col, 0.3), 1), (1, dk(col, 0.1), 1)], 0.35, 0.3, 0.75))
        strands(s, col, [P("M", (bx - 10, by_ - 4), "Q", (bx, by_ - 13), (bx + 10, by_ - 5)),
                         P("M", (bx - 12, by_ + 3), "Q", (bx + 1, by_ - 6), (bx + 13, by_ + 2))], 0.5)
        hair_shine(s, P("M", (bx - 10, by_ - 6), "Q", (bx - 5, by_ - 11), (bx + 2, by_ - 11)), col, 0.6, 3)
        if opts.get("pin"):
            pc = opts["pin"]
            s.line(P("M", (bx - 20, by_ + 3), "L", (bx + 17, by_ - 9)), sw=5.5, col=OL)
            s.line(P("M", (bx - 20, by_ + 3), "L", (bx + 17, by_ - 9)), sw=2.8, col=pc)
            s.c.circ(bx + 18, by_ - 9.5, 3.4, "#e8414f", stroke=OL, sw=2)


def hair_front(s, style, col, opts):
    hx, hy = s.hx, s.hy
    if style in ("short", "cap"):
        d = P("M", (hx - 42, hy + 10), "C", (hx - 47, hy - 22), (hx - 34, hy - 50), (hx, hy - 50),
              "C", (hx + 34, hy - 50), (hx + 50, hy - 28), (hx + 43, hy + 4),
              "Q", (hx + 40, hy - 8), (hx + 35, hy - 12), "Q", (hx + 31, hy - 7), (hx + 26, hy - 9),
              "Q", (hx + 22, hy - 19), (hx + 14, hy - 20), "Q", (hx + 10, hy - 11), (hx + 4, hy - 9),
              "Q", (hx - 1, hy - 19), (hx - 8, hy - 20), "Q", (hx - 13, hy - 11), (hx - 19, hy - 9),
              "Q", (hx - 24, hy - 19), (hx - 31, hy - 17), "Q", (hx - 35, hy - 7), (hx - 36, hy + 2),
              "Q", (hx - 38, hy + 8), (hx - 42, hy + 10), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx + 2, hy - 46), "Q", (hx + 16, hy - 36), (hx + 24, hy - 14)),
                         P("M", (hx - 10, hy - 44), "Q", (hx - 2, hy - 30), (hx + 2, hy - 14)),
                         P("M", (hx - 26, hy - 38), "Q", (hx - 22, hy - 26), (hx - 19, hy - 13)),
                         P("M", (hx + 26, hy - 40), "Q", (hx + 38, hy - 28), (hx + 38, hy - 12))])
        hair_shine(s, P("M", (hx - 33, hy - 24), "Q", (hx - 25, hy - 41), (hx - 6, hy - 44)), col)
        hair_shine(s, P("M", (hx + 4, hy - 44), "L", (hx + 10, hy - 44)), col, 0.5, 3)
    elif style == "spiky":
        cx0, cy0 = hx, hy - 8
        d = P("M", (hx - 42, hy + 8))
        n = 8
        for k in range(n + 1):
            a = math.radians(196 + k * (148.0 / n))
            if k > 0:
                am = math.radians(196 + (k - 0.5) * (148.0 / n) + 5)
                d += " " + P("L", (cx0 + math.cos(am) * 60, cy0 + math.sin(am) * 54))
            d += " " + P("L", (cx0 + math.cos(a) * 43, cy0 + math.sin(a) * 41))
        d += " " + P("L", (hx + 43, hy + 2), "L", (hx + 36, hy - 10), "L", (hx + 30, hy - 4), "L", (hx + 25, hy - 18),
                     "L", (hx + 14, hy - 8), "L", (hx + 8, hy - 21), "L", (hx - 3, hy - 9), "L", (hx - 8, hy - 21),
                     "L", (hx - 19, hy - 9), "L", (hx - 24, hy - 20), "L", (hx - 33, hy - 6), "L", (hx - 36, hy + 4), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx - 6, hy - 40), "L", (hx + 4, hy - 20)), P("M", (hx + 14, hy - 40), "L", (hx + 18, hy - 22)),
                         P("M", (hx - 24, hy - 34), "L", (hx - 18, hy - 18))], 0.45)
        hair_shine(s, P("M", (hx - 34, hy - 26), "Q", (hx - 26, hy - 40), (hx - 10, hy - 44)), col, 0.7)
        hair_shine(s, P("M", (hx + 2, hy - 46), "L", (hx + 9, hy - 46)), col, 0.7, 3)
    elif style == "bob":
        d = P("M", (hx - 46, hy + 30), "C", (hx - 52, hy - 14), (hx - 40, hy - 52), (hx, hy - 52),
              "C", (hx + 40, hy - 52), (hx + 54, hy - 14), (hx + 46, hy + 30),
              "Q", (hx + 41, hy + 36), (hx + 35, hy + 30), "C", (hx + 37, hy + 12), (hx + 37, hy - 2), (hx + 32, hy - 12),
              "Q", (hx + 26, hy - 6), (hx + 20, hy - 9), "Q", (hx + 14, hy - 19), (hx + 6, hy - 21),
              "Q", (hx, hy - 9), (hx - 8, hy - 10), "Q", (hx - 16, hy - 21), (hx - 26, hy - 19),
              "C", (hx - 34, hy - 10), (hx - 36, hy + 10), (hx - 36, hy + 30),
              "Q", (hx - 41, hy + 37), (hx - 46, hy + 30), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx - 42, hy - 2), "Q", (hx - 42, hy + 16), (hx - 41, hy + 30)),
                         P("M", (hx + 42, hy - 2), "Q", (hx + 43, hy + 16), (hx + 41, hy + 30)),
                         P("M", (hx + 4, hy - 46), "Q", (hx + 12, hy - 30), (hx + 18, hy - 12)),
                         P("M", (hx - 12, hy - 44), "Q", (hx - 6, hy - 30), (hx - 2, hy - 12)),
                         P("M", (hx + 24, hy - 42), "Q", (hx + 36, hy - 30), (hx + 36, hy - 12))])
        hair_shine(s, P("M", (hx - 36, hy - 26), "Q", (hx - 26, hy - 44), (hx - 6, hy - 46)), col)
        hair_shine(s, P("M", (hx - 46, hy + 2), "L", (hx - 46, hy + 14)), col, 0.4, 3)
    elif style == "pony":
        d = P("M", (hx - 44, hy + 14), "C", (hx - 50, hy - 18), (hx - 38, hy - 52), (hx, hy - 52),
              "C", (hx + 38, hy - 52), (hx + 52, hy - 20), (hx + 45, hy + 12),
              "Q", (hx + 41, hy + 16), (hx + 37, hy + 10), "C", (hx + 38, hy + 2), (hx + 36, hy - 6), (hx + 32, hy - 12),
              "Q", (hx + 26, hy - 6), (hx + 20, hy - 9), "Q", (hx + 14, hy - 19), (hx + 6, hy - 21),
              "Q", (hx, hy - 9), (hx - 8, hy - 10), "Q", (hx - 16, hy - 21), (hx - 26, hy - 19),
              "C", (hx - 34, hy - 10), (hx - 36, hy + 2), (hx - 37, hy + 12),
              "Q", (hx - 40, hy + 18), (hx - 44, hy + 14), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx + 4, hy - 46), "Q", (hx + 12, hy - 30), (hx + 18, hy - 12)),
                         P("M", (hx - 12, hy - 44), "Q", (hx - 6, hy - 30), (hx - 2, hy - 12)),
                         P("M", (hx + 24, hy - 42), "Q", (hx + 36, hy - 30), (hx + 36, hy - 12)),
                         P("M", (hx - 20, hy - 46), "Q", (hx - 30, hy - 44), (hx - 34, hy - 40))])
        hair_shine(s, P("M", (hx - 36, hy - 24), "Q", (hx - 26, hy - 44), (hx - 6, hy - 46)), col)
        # dây buộc / scrunchie
        sc = opts.get("tie", "#e8414f")
        tx, ty = hx - 36, hy - 40
        for a in range(0, 360, 60):
            r = math.radians(a)
            s.c.circ(tx + math.cos(r) * 6, ty + math.sin(r) * 5, 5.2, sc, stroke=OL, sw=2.4)
        s.c.circ(tx, ty, 6.5, s.c.rg([(0, lt(sc, 0.35), 1), (1, sc, 1)], 0.35, 0.3, 0.7), stroke=None)
        s.dot(tx - 3, ty - 3, 2, "#ffffff", 0.7)
    elif style == "long":
        d = P("M", (hx - 46, hy + 52), "C", (hx - 54, hy + 6), (hx - 50, hy - 50), (hx, hy - 50),
              "C", (hx + 50, hy - 50), (hx + 54, hy + 6), (hx + 46, hy + 52),
              "Q", (hx + 41, hy + 57), (hx + 36, hy + 50), "C", (hx + 39, hy + 22), (hx + 39, hy + 2), (hx + 31, hy - 12),
              "Q", (hx + 18, hy - 16), (hx + 6, hy - 30), "Q", (hx - 4, hy - 12), (hx - 30, hy - 10),
              "C", (hx - 37, hy + 4), (hx - 37, hy + 24), (hx - 36, hy + 50),
              "Q", (hx - 41, hy + 57), (hx - 46, hy + 52), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx - 42, hy + 4), "Q", (hx - 44, hy + 28), (hx - 41, hy + 50)),
                         P("M", (hx + 43, hy + 4), "Q", (hx + 45, hy + 28), (hx + 41, hy + 50)),
                         P("M", (hx + 6, hy - 44), "Q", (hx + 6, hy - 38), (hx + 6, hy - 30)),
                         P("M", (hx - 6, hy - 26), "Q", (hx - 18, hy - 16), (hx - 30, hy - 12)),
                         P("M", (hx + 14, hy - 24), "Q", (hx + 24, hy - 16), (hx + 31, hy - 10))])
        hair_shine(s, P("M", (hx - 38, hy - 22), "Q", (hx - 28, hy - 42), (hx - 8, hy - 45)), col)
        hair_shine(s, P("M", (hx - 47, hy + 14), "L", (hx - 47, hy + 32)), col, 0.4, 3)
    elif style == "bun":
        d = P("M", (hx - 42, hy + 10), "C", (hx - 48, hy - 26), (hx - 32, hy - 48), (hx, hy - 48),
              "C", (hx + 32, hy - 48), (hx + 48, hy - 26), (hx + 42, hy + 6),
              "Q", (hx + 40, hy - 8), (hx + 30, hy - 16), "Q", (hx + 16, hy - 26), (hx + 2, hy - 24),
              "Q", (hx - 18, hy - 22), (hx - 32, hy - 12), "Q", (hx - 38, hy - 2), (hx - 42, hy + 10), "Z")
        hair_fill(s, d, col)
        strands(s, col, [P("M", (hx + 2, hy - 24), "Q", (hx - 6, hy - 38), (hx - 4, hy - 46)),
                         P("M", (hx + 16, hy - 24), "Q", (hx + 12, hy - 38), (hx + 8, hy - 46)),
                         P("M", (hx - 14, hy - 22), "Q", (hx - 20, hy - 34), (hx - 18, hy - 44)),
                         P("M", (hx + 30, hy - 16), "Q", (hx + 30, hy - 32), (hx + 22, hy - 42))], 0.45)
        hair_shine(s, P("M", (hx - 36, hy - 18), "Q", (hx - 30, hy - 38), (hx - 10, hy - 44)), col, 0.65)
    elif style == "bald":
        for sd, x0, w in ((-1, hx - 38, 1.0), (1, hx + 38, 0.75)):
            d = P("M", (x0 + sd * 1, hy + 10), "Q", (x0 + sd * 9 * w, hy + 4), (x0 + sd * 8 * w, hy - 8),
                  "Q", (x0 + sd * 8 * w, hy - 18), (x0 - sd * 2, hy - 22), "Q", (x0 + sd * 1, hy - 14), (x0 - sd * 2, hy - 10),
                  "Q", (x0 - sd * 1, hy - 2), (x0 - sd * 2, hy + 2), "Z")
            hair_fill(s, d, col, sw=3.4)
            hair_shine(s, P("M", (x0 + sd * 4 * w, hy - 14), "L", (x0 + sd * 5 * w, hy - 4)), col, 0.5, 2.2)
        s.line(P("M", (hx - 12, hy - 33), "Q", (hx + 2, hy - 40), (hx + 18, hy - 32)), sw=1.8, col=col, op=0.9)
        s.line(P("M", (hx - 6, hy - 31), "Q", (hx + 6, hy - 36), (hx + 20, hy - 29)), sw=1.6, col=col, op=0.8)
        s.c.ell(hx - 14, hy - 25, 11, 5, "#ffffff", stroke=None, extra='opacity="0.55" transform="rotate(-25 %s %s)"'
                % (F(hx - 14), F(hy - 25)))
        s.dot(hx + 2, hy - 31, 2.2, "#ffffff", 0.6)
    elif style == "slick":
        d = P("M", (hx - 42, hy + 8), "C", (hx - 48, hy - 30), (hx - 26, hy - 54), (hx + 4, hy - 54),
              "C", (hx + 36, hy - 56), (hx + 54, hy - 40), (hx + 46, hy - 14),
              "Q", (hx + 44, hy - 4), (hx + 41, hy - 2), "Q", (hx + 38, hy - 16), (hx + 30, hy - 20),
              "Q", (hx + 12, hy - 27), (hx - 6, hy - 21), "Q", (hx - 26, hy - 15), (hx - 36, hy - 2),
              "Q", (hx - 39, hy + 4), (hx - 42, hy + 8), "Z")
        hair_fill(s, d, col)
        for k, op in ((0, 0.55), (8, 0.35)):
            s.line(P("M", (hx - 34 + k, hy - 22 + k * 0.2), "Q", (hx - 10, hy - 50 + k), (hx + 30, hy - 42 + k)), sw=2.2,
                   col="#8d8aa6", op=op)
        hair_shine(s, P("M", (hx - 30, hy - 30), "Q", (hx - 16, hy - 48), (hx + 6, hy - 49)), "#9e9ab8", 0.7, 3.4)


# ====================================================================== hats

def hat(s, kind, opts):
    c, hx, hy = s.c, s.hx, s.hy
    if kind == "chef":
        d = P("M", (hx - 34, hy - 40), "A", 16, 16, "0 0 1", (hx - 30, hy - 61), "A", 19, 19, "0 0 1", (hx - 6, hy - 72),
              "A", 19, 19, "0 0 1", (hx + 20, hy - 68), "A", 16, 16, "0 0 1", (hx + 36, hy - 40), "Z")
        s.part(d, s.c.lg("#ffffff", "#dde2ea"), sw=4.4)
        for x0, x1 in ((-20, -22), (-2, -6), (16, 14)):
            s.line(P("M", (hx + x0, hy - 40), "Q", (hx + x1 - 3, hy - 54), (hx + x1, hy - 62)), sw=2, col="#b9c1cd", op=0.8)
        s.shine(P("M", (hx - 30, hy - 56), "Q", (hx - 24, hy - 66), (hx - 12, hy - 68)), op=0.9, sw=3)
        band = P("M", (hx - 37, hy - 44), "Q", (hx + 1, hy - 50), (hx + 39, hy - 44), "L", (hx + 38, hy - 26),
                 "Q", (hx + 1, hy - 18), (hx - 36, hy - 26), "Z")
        s.part(band, s.c.lg("#ffffff", "#d9dee7"), sw=4.2)
        s.line(P("M", (hx - 33, hy - 36), "Q", (hx + 1, hy - 40), (hx + 35, hy - 36)), sw=1.6, col="#b9c1cd", op=0.8)
    elif kind == "cap":
        col = opts.get("hat_col", "#f2a541")
        d = P("M", (hx - 43, hy - 12), "C", (hx - 46, hy - 50), (hx - 20, hy - 58), (hx + 2, hy - 58),
              "C", (hx + 28, hy - 58), (hx + 47, hy - 46), (hx + 44, hy - 14), "Q", (hx, hy - 6), (hx - 43, hy - 12), "Z")
        s.part(d, s.vg(col, 0.15, 0.08))
        s.line(P("M", (hx + 2, hy - 57), "Q", (hx - 14, hy - 40), (hx - 18, hy - 11)), sw=2, col=dk(col, 0.3), op=0.6)
        s.line(P("M", (hx + 2, hy - 57), "Q", (hx + 22, hy - 40), (hx + 26, hy - 12)), sw=2, col=dk(col, 0.3), op=0.6)
        c.circ(hx + 6, hy - 32, 8.5, "#fffaf0", stroke=OL, sw=2.4)
        c.path(P("M", (hx + 6, hy - 38), "l", 1.8, 3.8, 4, 0.4, -3, 2.8, 0.9, 4.1, -3.7, -2.2, -3.7, 2.2, 0.9, -4.1, -3, -2.8,
                 4, -0.4, "Z"), "#e8574f", stroke=None)
        s.shine(P("M", (hx - 34, hy - 30), "Q", (hx - 28, hy - 48), (hx - 10, hy - 54)), op=0.5, sw=3)
        brim = P("M", (hx - 4, hy - 13), "Q", (hx + 30, hy - 22), (hx + 62, hy - 14), "Q", (hx + 68, hy - 8), (hx + 58, hy - 5),
                 "Q", (hx + 30, hy - 7), (hx + 2, hy - 6), "Q", (hx - 10, hy - 7), (hx - 4, hy - 13), "Z")
        s.part(brim, s.vg(dk(col, 0.06), 0.1, 0.18))
        s.line(P("M", (hx + 2, hy - 9), "Q", (hx + 30, hy - 11), (hx + 60, hy - 8)), sw=1.6, col=dk(col, 0.4), op=0.6)
        c.ell(hx + 2, hy - 57, 4.5, 2.6, dk(col, 0.1), stroke=OL, sw=2)
    elif kind == "non_la":
        apex = (hx + 2, hy - 76)
        L, R, Bm = (hx - 66, hy - 18), (hx + 68, hy - 20), (hx + 2, hy + 1)
        d = P("M", L, "Q", (hx - 36, hy - 52), apex, "Q", (hx + 40, hy - 52), R, "Q", Bm, L, "Z")
        s.part(d, s.c.lg("#fbe8a8", "#d3aa58", 0, 0, 1, 0.3), sw=4.4)

        def lerp(p, q, t):
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        for t in (0.32, 0.56, 0.8):
            a, b, m = lerp(apex, L, t), lerp(apex, R, t), lerp(apex, Bm, t)
            s.line(P("M", a, "Q", m, b), sw=1.8, col="#b88a3c", op=0.65)
        for u in (-0.55, -0.25, 0.08, 0.4, 0.7):
            x = hx + 2 + u * 64
            yb = hy - 12 + abs(u) * -6
            s.line(P("M", (apex[0] + u * 4, apex[1] + 8), "L", (x, yb)), sw=1.3, col="#b88a3c", op=0.35)
        s.blob(P("M", (apex[0] + 2, apex[1] + 4), "Q", (hx + 38, hy - 50), (R[0] - 4, R[1] - 1), "Q", (hx + 40, hy - 14),
                 (hx + 26, hy - 12), "Q", (hx + 22, hy - 44), (apex[0] + 2, apex[1] + 4), "Z"), "#8a5a20", 0.16)
        s.shine(P("M", (apex[0] - 4, apex[1] + 8), "Q", (hx - 26, hy - 44), (hx - 52, hy - 20)), op=0.6, sw=3)
        s.line(P("M", L, "Q", Bm, R), sw=2, col="#fff3c8", op=0.8)
    elif kind == "khan_dong":
        col = opts.get("hat_col", "#7b2fa8")
        d = P("M", (hx - 43, hy - 12), "C", (hx - 47, hy - 36), (hx - 42, hy - 50), (hx - 30, hy - 54),
              "Q", (hx, hy - 60), (hx + 30, hy - 54), "C", (hx + 42, hy - 50), (hx + 47, hy - 36), (hx + 44, hy - 14),
              "Q", (hx, hy - 2), (hx - 43, hy - 12), "Z")
        s.part(d, s.vg(col, 0.12, 0.12))
        c.ell(hx, hy - 53, 28, 4.5, dk(col, 0.25), stroke=None, extra='opacity="0.6"')
        for k in range(4):
            y = hy - 46 + k * 8
            s.line(P("M", (hx - 40, y + 6), "Q", (hx - 18, y + 4), (hx + 4, y - 4), "Q", (hx + 24, y + 4), (hx + 42, y + 5)),
                   sw=2.2, col=dk(col, 0.35), op=0.7)
            s.line(P("M", (hx - 38, y + 3.5), "Q", (hx - 18, y + 1.5), (hx + 4, y - 6.5), "Q", (hx + 24, y + 1.5), (hx + 40, y + 2.5)),
                   sw=1.6, col=lt(col, 0.35), op=0.6)
        s.line(P("M", (hx - 42, hy - 15), "Q", (hx, hy - 5), (hx + 43, hy - 17)), sw=7.5, col=OL)
        s.line(P("M", (hx - 42, hy - 15), "Q", (hx, hy - 5), (hx + 43, hy - 17)), sw=4.5, col=GOLD)
        s.line(P("M", (hx - 38, hy - 16), "Q", (hx, hy - 7.5), (hx + 30, hy - 15.5)), sw=1.4, col="#fff4c0", op=0.9)
        c.circ(hx + 6, hy - 11, 5.4, s.c.rg([(0, "#fff2a8", 1), (1, GOLD, 1)], 0.35, 0.3, 0.7), stroke=OL, sw=2.2)
        c.circ(hx + 6, hy - 11, 2.4, "#e8414f", stroke=None)
        s.shine(P("M", (hx - 36, hy - 30), "Q", (hx - 32, hy - 46), (hx - 16, hy - 52)), op=0.45, sw=3)


def non_la_strap(s):
    hx, hy = s.hx, s.hy
    col = "#ef6f9f"
    s.line(P("M", (hx - 32, hy - 10), "Q", (hx - 38, hy + 30), (hx + 2, hy + 40)), sw=2, col=col, op=0.75)
    s.line(P("M", (hx + 36, hy - 12), "Q", (hx + 42, hy + 28), (hx + 6, hy + 40)), sw=2, col=col, op=0.75)


# ====================================================================== outfits

def o_tee(s, col, deco=None):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d()
    s.fill(d, s.vg(col))
    s.neck_u()
    s.line(P("M", (cx - 12, T + 1), "Q", (cx + 2, T + 16), (cx + 17, T + 1)), sw=3, col=lt(col, 0.35), op=0.8)
    s.fold(P("M", (cx - 19, B - 14), "Q", (cx - 12, B - 6), (cx - 3, B - 5)), col)
    s.fold(P("M", (cx + 16, T + 30), "Q", (cx + 20, T + 38), (cx + 17, B - 7)), col, 0.4)
    s.fold(P("M", (cx - 24, B - 4), "Q", (cx + 1, B + 1), (cx + 26, B - 4)), col, 0.55)
    if deco == "star":
        x, y = cx + 4, T + 27
        pts = []
        for k in range(10):
            r = 8 if k % 2 == 0 else 3.6
            a = math.radians(-90 + k * 36)
            pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
        s.c.poly(pts, s.vg("#ffd34d", 0.3, 0.05), stroke=OL, sw=2.2)
    elif deco == "pocket":
        s.c.path(P("M", (cx - 16, T + 18), "L", (cx - 4, T + 18), "L", (cx - 4, T + 30), "Q", (cx - 10, T + 33), (cx - 16, T + 30), "Z"),
                 lt(col, 0.12), stroke=dk(col, 0.35), sw=2)
        s.line(P("M", (cx - 16, T + 21), "L", (cx - 4, T + 21)), sw=1.6, col=dk(col, 0.35), op=0.7)
    s.line(d)
    return {"col": col, "kind": "short"}


def o_polo(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d()
    s.fill(d, s.vg(col))
    s.neck_u(9, 10)
    s.line(P("M", (cx + 2, T + 9), "L", (cx + 2, T + 24)), sw=2, col=dk(col, 0.3), op=0.6)
    s.button(cx + 4.5, T + 14, "#fffaf0", 2.2)
    s.button(cx + 4.5, T + 21, "#fffaf0", 2.2)
    for sd in (-1, 1):
        x0 = cx + 2 + sd * 9
        s.part(P("M", (x0, T - 2), "L", (x0 + sd * 7, T + 1), "L", (x0 + sd * 5, T + 10), "L", (x0 - sd * 6, T + 8), "Z"),
               lt(col, 0.25), sw=2.4, shade=False)
    s.fold(P("M", (cx - 19, B - 14), "Q", (cx - 12, B - 6), (cx - 3, B - 5)), col)
    s.fold(P("M", (cx + 16, T + 30), "Q", (cx + 20, T + 38), (cx + 17, B - 7)), col, 0.4)
    s.line(d)
    return {"col": col, "kind": "short"}


def o_blouse(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(23, 22)
    s.fill(d, s.vg(col))
    s.neck_u(9, 9)
    s.fold(P("M", (cx - 14, B - 10), "Q", (cx - 10, B - 4), (cx - 4, B - 3)), col)
    s.fold(P("M", (cx + 12, B - 12), "Q", (cx + 14, B - 5), (cx + 20, B - 3)), col)
    s.button(cx + 2, T + 20, "#ffffff", 2.3)
    s.button(cx + 2, T + 30, "#ffffff", 2.3)
    for sd in (-1, 1):
        x0 = cx + 2
        s.part(P("M", (x0, T + 2), "Q", (x0 + sd * 4, T + 14), (x0 + sd * 15, T + 9), "Q", (x0 + sd * 17, T + 1), (x0 + sd * 11, T - 2), "Z"),
               "#fffaf2", sw=2.6, shade=s.sh_soft)
    bx, by_ = cx + 2, T + 4
    s.c.path(P("M", (bx, by_), "l", -7, -4, 0, 8, "Z", "M", (bx, by_), "l", 7, -4, 0, 8, "Z"), "#e8414f", stroke=OL, sw=1.8)
    s.c.circ(bx, by_, 2.2, "#c9303e", stroke=OL, sw=1.4)
    s.line(d)
    return {"col": col, "kind": "puff"}


def o_stripe(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d()
    s.fill(d, s.vg(col))
    for y in (T + 24, T + 34):
        s.line(P("M", (cx - 27, y), "Q", (cx + 1, y + 3), (cx + 29, y)), sw=4.2, col="#fff3dc")
    s.neck_u(10, 10)
    s.line(P("M", (cx - 11, T + 1), "Q", (cx + 2, T + 15), (cx + 16, T + 1)), sw=3.2, col=dk(col, 0.12))
    s.fold(P("M", (cx - 24, B - 5), "Q", (cx + 1, B), (cx + 26, B - 5)), col, 0.55)
    s.fold(P("M", (cx - 18, B - 14), "Q", (cx - 12, B - 8), (cx - 4, B - 7)), col)
    s.line(d)
    return {"col": col, "kind": "long", "cuff": dk(col, 0.08)}


def o_hoodie(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(24, 27)
    s.fill(d, s.vg(col))
    pk = P("M", (cx - 15, B - 22), "L", (cx + 19, B - 22), "L", (cx + 23, B - 6), "L", (cx - 19, B - 6), "Z")
    s.part(pk, dk(col, 0.08), sw=2.4, shade=False)
    s.fold(P("M", (cx - 12, B - 20), "L", (cx - 15, B - 7)), col, 0.4)
    s.line(P("M", (cx - 25, B - 5), "Q", (cx + 1, B + 1), (cx + 27, B - 5)), sw=2.2, col=dk(col, 0.3), op=0.7)
    hood = P("M", (cx - 20, T), "Q", (cx - 16, T + 17), (cx + 2, T + 19), "Q", (cx + 20, T + 17), (cx + 25, T),
             "Q", (cx + 2, T + 7), (cx - 20, T), "Z")
    s.part(hood, s.vg(lt(col, 0.06), 0.1, 0.15), sw=3)
    for x0, x1 in ((-5, -7), (9, 11)):
        s.line(P("M", (cx + x0, T + 14), "Q", (cx + x0 - 1, T + 24), (cx + x1, T + 32)), sw=2.2, col="#fffaf0")
        s.c.rect(cx + x1 - 1.6, T + 31, 3.2, 5, "#d0d4dc", rx=1.2, stroke=OL, sw=1.2)
    s.line(d)
    return {"col": col, "kind": "long", "cuff": dk(col, 0.12)}


def o_ao(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(23, 28, B + 6)
    s.fill(d, s.vg(col))
    s.c.path(P("M", (cx - 9, T - 2), "L", (cx + 14, T - 2), "L", (cx + 14, T + 5), "Q", (cx + 2, T + 8), (cx - 9, T + 5), "Z"),
             lt(col, 0.2), stroke=OL, sw=2.4)
    s.line(P("M", (cx + 4, T + 6), "Q", (cx + 14, T + 8), (cx + 22, T + 18)), sw=2.4, col=dk(col, 0.35), op=0.8)
    for x, y in ((cx + 9, T + 7), (cx + 16, T + 11), (cx + 21, T + 17)):
        s.button(x, y, "#fff3dc", 2)
    for x, y in ((cx - 12, T + 30), (cx + 10, T + 40), (cx - 6, B - 4), (cx + 18, T + 24)):
        for a in range(0, 360, 72):
            r = math.radians(a)
            s.dot(x + math.cos(r) * 2.6, y + math.sin(r) * 2.6, 1.8, "#ffffff", 0.9)
        s.dot(x, y, 1.4, "#ffd34d")
    s.fold(P("M", (cx - 20, B - 6), "Q", (cx - 14, B + 2), (cx - 6, B + 3)), col)
    s.line(P("M", (cx - 26, B), "L", (cx - 24, B + 8)), sw=2, col=dk(col, 0.35), op=0.6)
    s.line(P("M", (cx + 28, B), "L", (cx + 27, B + 8)), sw=2, col=dk(col, 0.35), op=0.6)
    s.line(d)
    return {"col": col, "kind": "long", "cuff": lt(col, 0.2)}


def o_robe(s, col, trim):
    cx, T, B, by = s.cx, s.T, s.B, s.by
    R = by - 12 if not s.sit else B + 10
    d = P("M", (cx - 18, T), "C", (cx - 25, T + 1), (cx - 27, T + 10), (cx - 27, T + 20), "L", (cx - 31, R),
          "Q", (cx + 1, R + 6), (cx + 33, R), "L", (cx + 29, T + 20), "C", (cx + 29, T + 10), (cx + 27, T + 1), (cx + 20, T),
          "Q", (cx + 1, T - 3), (cx - 18, T), "Z")
    s.fill(d, s.vg(col, 0.12, 0.14))
    # hoa văn thọ
    for x, y in ((cx - 12, T + 34), (cx + 14, T + 46), (cx - 16, T + 58), (cx + 6, T + 64), (cx + 20, T + 22)):
        if y < R - 6:
            s.c.circ(x, y, 4.6, "none", stroke=trim, sw=1.8, extra='stroke-opacity="0.85"')
            s.dot(x, y, 1.6, trim, 0.85)
    for k in (-14, 4, 20):
        s.fold(P("M", (cx + k, T + 40), "Q", (cx + k + 2, (T + R) / 2 + 20), (cx + k + 1, R - 2)), col, 0.4)
    s.line(P("M", (cx - 30, R - 3), "Q", (cx + 1, R + 3), (cx + 32, R - 3)), sw=7, col=OL)
    s.line(P("M", (cx - 30, R - 3), "Q", (cx + 1, R + 3), (cx + 32, R - 3)), sw=4.2, col=trim)
    # cổ đứng + vạt chéo
    s.c.path(P("M", (cx - 9, T - 3), "L", (cx + 14, T - 3), "L", (cx + 14, T + 5), "Q", (cx + 2, T + 9), (cx - 9, T + 5), "Z"),
             trim, stroke=OL, sw=2.4)
    s.line(P("M", (cx + 3, T + 7), "Q", (cx + 16, T + 9), (cx + 26, T + 22)), sw=7, col=OL)
    s.line(P("M", (cx + 3, T + 7), "Q", (cx + 16, T + 9), (cx + 26, T + 22)), sw=4.2, col=trim)
    s.line(P("M", (cx + 4, T + 6), "Q", (cx + 16, T + 8), (cx + 24, T + 18)), sw=1.2, col="#fff4c0", op=0.9)
    s.line(d)
    return {"col": col, "kind": "wide", "cuff": trim}


def o_chef(s, col="#f7f8fb"):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(23, 27, B + 2)
    s.fill(d, s.c.lg("#ffffff", "#d9dee8"))
    s.line(P("M", (cx + 9, T + 8), "L", (cx + 9, B + 4)), sw=2, col="#a9b2c0", op=0.8)
    for y in (T + 18, T + 30, T + 42):
        s.button(cx - 5, y, "#4a4a5a", 2.6)
        s.button(cx + 18, y, "#4a4a5a", 2.6)
    s.c.path(P("M", (cx - 21, T + 16), "L", (cx - 11, T + 16), "L", (cx - 11, T + 22), "L", (cx - 21, T + 22), "Z"),
             "none", stroke="#a9b2c0", sw=1.6)
    s.line(P("M", (cx - 18, T + 17), "L", (cx - 18, T + 10)), sw=2.2, col="#4f86d9")
    s.fold(P("M", (cx - 20, B - 10), "Q", (cx - 12, B - 2), (cx - 2, B - 1)), "#c0c8d6", 0.6)
    s.fold(P("M", (cx + 20, T + 30), "Q", (cx + 24, T + 40), (cx + 22, B - 4)), "#c0c8d6", 0.5)
    # cổ áo + khăn quàng
    s.c.path(P("M", (cx - 13, T - 3), "Q", (cx + 2, T + 3), (cx + 17, T - 3), "L", (cx + 17, T + 3), "Q", (cx + 2, T + 9),
               (cx - 13, T + 3), "Z"), "#f2f4f8", stroke=OL, sw=2.6)
    nc = "#e8414f"
    s.part(P("M", (cx - 7, T + 3), "L", (cx + 12, T + 3), "L", (cx + 3, T + 17), "Z"), s.vg(nc, 0.15, 0.1), sw=2.6, shade=False)
    s.c.circ(cx + 2.5, T + 4, 4, s.vg(nc, 0.2, 0.1), stroke=OL, sw=2.2)
    s.line(P("M", (cx + 1, T + 6), "L", (cx + 3, T + 13)), sw=1.4, col=dk(nc, 0.3), op=0.6)
    s.line(d)
    return {"col": "#f7f8fb", "kind": "long", "cuff": "#e6eaf1"}


def o_waiter(s):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d()
    s.fill(d, s.c.lg("#ffffff", "#dfe3ea"))
    vc = "#2f2f3a"
    vest = P("M", (cx - 15, T), "C", (cx - 22, T + 1), (cx - 27, T + 10), (cx - 27, T + 20), "L", (cx - 26, B),
             "Q", (cx + 1, B + 5), (cx + 28, B), "L", (cx + 29, T + 20), "C", (cx + 29, T + 10), (cx + 24, T + 1), (cx + 19, T),
             "L", (cx + 6, T + 30), "L", (cx + 2, T + 33), "L", (cx - 2, T + 30), "Z")
    s.fill(vest, s.c.lg(lt(vc, 0.15), dk(vc, 0.1), 0, 0, 1, 0.4))
    s.line(P("M", (cx - 15, T), "L", (cx - 2, T + 30), "L", (cx + 2, T + 33), "L", (cx + 6, T + 30), "L", (cx + 19, T)), sw=2.6)
    s.line(P("M", (cx + 2, T + 33), "L", (cx + 2, B + 3)), sw=1.8, col="#000000", op=0.5)
    s.button(cx + 5, T + 39, "#c9ced6", 2.2)
    s.button(cx + 5, T + 47, "#c9ced6", 2.2)
    s.line(P("M", (cx - 20, T + 34), "L", (cx - 10, T + 34)), sw=2, col="#55556a")
    s.shine(P("M", (cx - 23, T + 14), "Q", (cx - 24, T + 26), (cx - 22, T + 40)), op=0.25, sw=2.4)
    for sd in (-1, 1):
        x0 = cx + 2 + sd * 4
        s.part(P("M", (x0, T + 1), "L", (x0 + sd * 8, T - 1), "L", (x0 + sd * 5, T + 7), "Z"), "#ffffff", sw=2, shade=False)
    bx, bw = cx + 2, T + 6
    bc = "#e8414f"
    s.c.path(P("M", (bx, bw), "l", -10, -6, 0, 12, "Z", "M", (bx, bw), "l", 10, -6, 0, 12, "Z"), s.vg(bc, 0.2, 0.1), stroke=OL, sw=2.2)
    s.c.circ(bx, bw, 3, dk(bc, 0.1), stroke=OL, sw=1.8)
    s.line(d)
    return {"col": "#ffffff", "kind": "long", "cuff": "#eef1f5"}


def o_cashier(s, col, apron):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d()
    s.fill(d, s.vg(col))
    s.neck_u(8, 8)
    for sd in (-1, 1):
        x0 = cx + 2 + sd * 5
        s.part(P("M", (x0, T - 1), "L", (x0 + sd * 9, T - 1), "L", (x0 + sd * 8, T + 8), "L", (x0 - sd * 3, T + 6), "Z"), "#fffaf0",
               sw=2.2, shade=False)
    s.line(P("M", (cx - 9, T + 13), "L", (cx - 16, T + 1)), sw=4.5, col=OL)
    s.line(P("M", (cx - 9, T + 13), "L", (cx - 16, T + 1)), sw=2.2, col=apron)
    s.line(P("M", (cx + 13, T + 13), "L", (cx + 20, T + 1)), sw=4.5, col=OL)
    s.line(P("M", (cx + 13, T + 13), "L", (cx + 20, T + 1)), sw=2.2, col=apron)
    ap = P("M", (cx - 11, T + 13), "L", (cx + 15, T + 13), "L", (cx + 16, T + 30), "L", (cx + 25, T + 31), "L", (cx + 28, B + 12),
           "Q", (cx + 1, B + 17), (cx - 26, B + 12), "L", (cx - 22, T + 31), "L", (cx - 12, T + 30), "Z")
    s.part(ap, s.vg(apron, 0.15, 0.1), sw=3.2)
    s.line(P("M", (cx - 22, T + 31), "Q", (cx + 1, T + 34), (cx + 25, T + 31)), sw=2.4, col=dk(apron, 0.3), op=0.7)
    s.c.path(P("M", (cx - 6, B - 6), "L", (cx + 12, B - 6), "L", (cx + 12, B + 3), "Q", (cx + 3, B + 6), (cx - 6, B + 3), "Z"),
             lt(apron, 0.15), stroke=dk(apron, 0.4), sw=1.8)
    s.line(P("M", (cx + 8, B - 5), "L", (cx + 10, B - 13)), sw=2.4, col="#e8414f")
    s.fold(P("M", (cx - 14, B - 4), "Q", (cx - 12, B + 4), (cx - 14, B + 10)), apron, 0.45)
    s.fold(P("M", (cx + 20, B - 2), "Q", (cx + 22, B + 6), (cx + 21, B + 11)), apron, 0.45)
    s.c.circ(cx + 1, T + 18, 3.2, "#ffd34d", stroke=OL, sw=1.6)
    s.line(d)
    return {"col": col, "kind": "short"}


def o_aodai(s, col, trim):
    cx, T, B, by = s.cx, s.T, s.B, s.by
    Pb = by - 16 if not s.sit else B + 12
    panel = P("M", (cx - 19, B - 10), "L", (cx + 22, B - 10), "C", (cx + 23, B + 8), (cx + 21, Pb - 8), (cx + 18, Pb),
              "Q", (cx + 1, Pb + 6), (cx - 16, Pb), "C", (cx - 18, Pb - 8), (cx - 20, B + 8), (cx - 19, B - 10), "Z")
    s.part(panel, s.hg(col, 0.12, 0.18))
    s.fold(P("M", (cx - 6, B + 4), "Q", (cx - 7, (B + Pb) / 2), (cx - 5, Pb - 2)), col, 0.4)
    s.fold(P("M", (cx + 12, B + 4), "Q", (cx + 13, (B + Pb) / 2), (cx + 11, Pb - 2)), col, 0.4)
    fx, fy = cx + 2, min(B + 16, Pb - 10)
    for a in range(0, 360, 72):
        r = math.radians(a - 90)
        s.c.ell(fx + math.cos(r) * 4, fy + math.sin(r) * 4, 3.4, 3.4, GOLD, stroke=OL, sw=1.2)
    s.dot(fx, fy, 2.2, "#ffffff")
    s.line(P("M", (cx - 15, Pb - 4), "Q", (cx + 1, Pb + 2), (cx + 17, Pb - 4)), sw=2.4, col=trim, op=0.9)
    d = s.torso_d(22, 20)
    s.fill(d, s.vg(col))
    s.c.path(P("M", (cx - 9, T - 3), "L", (cx + 14, T - 3), "L", (cx + 14, T + 5), "Q", (cx + 2, T + 9), (cx - 9, T + 5), "Z"),
             trim, stroke=OL, sw=2.4)
    s.line(P("M", (cx + 3, T + 7), "Q", (cx + 15, T + 9), (cx + 24, T + 20)), sw=6.5, col=OL)
    s.line(P("M", (cx + 3, T + 7), "Q", (cx + 15, T + 9), (cx + 24, T + 20)), sw=3.8, col=trim)
    s.fold(P("M", (cx - 12, B - 14), "Q", (cx - 6, B - 8), (cx + 2, B - 8)), col)
    s.shine(P("M", (cx - 19, T + 14), "Q", (cx - 21, T + 26), (cx - 18, T + 38)), op=0.35, sw=2.4)
    s.line(d)
    return {"col": col, "kind": "long", "cuff": trim}


def o_suit(s, col, bow, buttons, belly=0, square=None):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(23, 26 if not belly else 27, None, belly)
    s.fill(d, s.vg(col, 0.12, 0.12))
    shirt = P("M", (cx - 9, T - 1), "Q", (cx + 2, T + 1), (cx + 13, T - 1), "L", (cx + 6, T + 30), "L", (cx + 2, T + 33),
              "L", (cx - 2, T + 30), "Z")
    s.part(shirt, s.c.lg("#ffffff", "#e1e5ec"), sw=2.4, shade=False)
    lc = dk(col, 0.16)
    s.part(P("M", (cx - 9, T - 1), "L", (cx - 15, T + 10), "L", (cx - 8, T + 13), "L", (cx + 1, T + 32), "Z"), lc, sw=2.4, shade=False)
    s.part(P("M", (cx + 13, T - 1), "L", (cx + 19, T + 10), "L", (cx + 12, T + 13), "L", (cx + 3, T + 32), "Z"), lc, sw=2.4, shade=False)
    s.shine(P("M", (cx - 12, T + 8), "L", (cx - 2, T + 28)), op=0.3, sw=1.6)
    s.line(P("M", (cx + 2, T + 33), "L", (cx + 2, B + 3)), sw=1.8, col=dk(col, 0.4), op=0.7)
    if belly:
        for y in (T + 38, T + 47):
            s.button(cx - 4, y, buttons, 2.8)
            s.button(cx + 9, y, buttons, 2.8)
        s.line(P("M", (cx - 20, B - 16), "Q", (cx - 12, B - 8), (cx - 4, B - 14)), sw=2.2, col=buttons)
        s.c.circ(cx - 21, B - 16, 3, buttons, stroke=OL, sw=1.4)
    else:
        s.button(cx + 4, T + 38, buttons, 2.6)
        s.button(cx + 4, T + 46, buttons, 2.6)
    s.line(P("M", (cx - 21, T + 22), "L", (cx - 10, T + 22)), sw=2, col=dk(col, 0.35))
    if square:
        s.c.path(P("M", (cx - 20, T + 22), "l", 2, -6, 2.5, 4, 2.5, -5, 2.5, 4, 2, -3, 0, 6, "Z"), square, stroke=OL, sw=1.4)
    s.fold(P("M", (cx - 20, B - 6), "Q", (cx - 12, B - 2), (cx - 6, B - 2)), col, 0.5)
    s.fold(P("M", (cx + 22, T + 30), "Q", (cx + 25, T + 38), (cx + 23, B - 4)), col, 0.4)
    bx, bw = cx + 2, T + 6
    big = 12 if belly else 10
    s.c.path(P("M", (bx, bw), "l", -big, -6.5, 0, 13, "Z", "M", (bx, bw), "l", big, -6.5, 0, 13, "Z"), s.vg(bow, 0.25, 0.1),
             stroke=OL, sw=2.2)
    s.c.circ(bx, bw, 3.2, dk(bow, 0.08), stroke=OL, sw=1.8)
    s.line(d)
    return {"col": col, "kind": "long", "cuff": "#ffffff"}


def o_aobaba(s, col):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(24, 29, B + 6)
    s.fill(d, s.vg(col))
    s.neck_u(10, 11)
    s.line(P("M", (cx - 11, T + 1), "Q", (cx + 2, T + 14), (cx + 16, T + 1)), sw=2.4, col=dk(col, 0.3), op=0.7)
    s.line(P("M", (cx + 3, T + 10), "L", (cx + 3, B + 8)), sw=2, col=dk(col, 0.35), op=0.7)
    for k in range(4):
        s.button(cx + 3, T + 15 + k * 10, "#f6e3bd", 2.6)
    for x in (cx - 20, cx + 10):
        s.c.path(P("M", (x, B - 12), "L", (x + 12, B - 12), "L", (x + 12, B - 2), "Q", (x + 6, B + 1), (x, B - 2), "Z"),
                 lt(col, 0.08), stroke=dk(col, 0.4), sw=1.8)
    s.fold(P("M", (cx - 22, T + 28), "Q", (cx - 16, T + 34), (cx - 10, T + 34)), col, 0.45)
    s.fold(P("M", (cx + 22, T + 26), "Q", (cx + 18, T + 34), (cx + 14, T + 36)), col, 0.45)
    s.line(P("M", (cx - 27, B - 1), "L", (cx - 26, B + 7)), sw=2, col=dk(col, 0.35), op=0.6)
    s.line(P("M", (cx + 30, B - 1), "L", (cx + 29, B + 7)), sw=2, col=dk(col, 0.35), op=0.6)
    s.line(d)
    return {"col": col, "kind": "wide"}


def o_lan(s, col, apron="#ffffff"):
    cx, T, B = s.cx, s.T, s.B
    d = s.torso_d(23, 22)
    s.fill(d, s.vg(col))
    s.neck_u(9, 10)
    s.line(P("M", (cx - 10, T + 1), "Q", (cx + 2, T + 14), (cx + 15, T + 1)), sw=3, col=lt(col, 0.4), op=0.8)
    for sd, x0 in ((-1, cx - 9), (1, cx + 13)):
        s.line(P("M", (x0, T + 14), "L", (x0 + sd * 7, T + 1)), sw=4.4, col=OL)
        s.line(P("M", (x0, T + 14), "L", (x0 + sd * 7, T + 1)), sw=2.2, col=apron)
    sb = B + 14
    ap = P("M", (cx - 11, T + 14), "L", (cx + 15, T + 14), "L", (cx + 16, T + 31), "L", (cx + 24, T + 32), "L", (cx + 27, sb))
    xs = [cx + 27 - k * 9 for k in range(7)]
    for k in range(6):
        ap += " " + P("Q", ((xs[k] + xs[k + 1]) / 2, sb + 6), (xs[k + 1], sb))
    ap += " " + P("L", (cx - 21, T + 32), "L", (cx - 12, T + 31), "Z")
    s.part(ap, s.c.lg("#ffffff", "#e6e1dc"), sw=3)
    s.line(P("M", (cx - 21, T + 32), "Q", (cx + 1, T + 35), (cx + 24, T + 32)), sw=2.6, col="#d9d2cb")
    s.line(P("M", (cx - 23, sb - 5), "Q", (cx + 1, sb - 1), (cx + 25, sb - 5)), sw=1.6, col="#cfc6be", op=0.8)
    hx_, hy_ = cx + 4, B - 2
    s.c.path(P("M", (hx_, hy_ + 5), "C", (hx_ - 8, hy_), (hx_ - 6, hy_ - 6), (hx_, hy_ - 3), "C", (hx_ + 6, hy_ - 6), (hx_ + 8, hy_),
               (hx_, hy_ + 5), "Z"), "#ff9cb4", stroke=OL, sw=1.6)
    s.fold(P("M", (cx - 12, B - 2), "Q", (cx - 10, B + 6), (cx - 12, sb - 2)), "#d9d2cb", 0.6)
    s.fold(P("M", (cx + 18, B), "Q", (cx + 20, B + 8), (cx + 19, sb - 2)), "#d9d2cb", 0.6)
    s.line(d)
    return {"col": col, "kind": "puff"}


# ====================================================================== person

def person(name, spec, sit=False, tray=False):
    s = Fig(sit)
    cx, by = s.cx, s.by
    s.c.shadow(cx, by, 38, 11, 0.32)
    hs, hcol = spec["hair"], spec["hcol"]
    opts = spec.get("opts", {})
    hair_back(s, hs, hcol, opts)
    lk, lcol, scol = spec["legs"]
    legs(s, lk, lcol, scol, spec.get("shoe_kind", "leather"))
    fn, args = spec["top"][0], spec["top"][1:]
    armspec = fn(s, *args)
    arm(s, -1, armspec)
    if tray:
        tray_arm(s, armspec)
    else:
        arm(s, 1, armspec)
    head(s, forehead_shadow=hs != "bald")
    fc = spec.get("face", {})
    face(s, fc)
    hair_front(s, hs, hcol, opts)
    if spec.get("hat") == "non_la":
        non_la_strap(s)
    face_top(s, fc, hcol)
    if spec.get("hat"):
        hat(s, spec["hat"], opts)
    if tray:
        tray_top(s)
    s.c.save(name)


def specs():
    return {
        "cust_1": dict(hair="short", hcol="#5b3520", top=(o_tee, "#e8574f", "star"), legs=("pants", "#3f6596", "#e8574f"),
                       shoe_kind="sneaker", face=dict(mouth="open")),
        "cust_2": dict(hair="bob", hcol="#7a4a2a", top=(o_blouse, "#4fa3e0"), legs=("skirt", "#4b3a5a", "#9b3b4a"),
                       face=dict(mouth="smile", lash=True)),
        "cust_3": dict(hair="cap", hcol="#2e2a3a", hat="cap", opts={"hat_col": "#f2a541"}, top=(o_tee, "#6cc25b", "pocket"),
                       legs=("pants", "#7a5a40", "#3f6596"), shoe_kind="sneaker", face=dict(mouth="grin")),
        "cust_4": dict(hair="pony", hcol="#2a2633", opts={"tie": "#ffd34d"}, top=(o_stripe, "#f39a3a"),
                       legs=("pants", "#4b3a5a", "#6b4a3a"), face=dict(mouth="open", lash=True)),
        "cust_5": dict(hair="spiky", hcol="#f2c45a", top=(o_hoodie, "#a066df"), legs=("pants", "#3d3d4a", "#a066df"),
                       shoe_kind="sneaker", face=dict(mouth="grin", brow_col="#b9862c")),
        "cust_6": dict(hair="long", hcol="#a8482a", hat="non_la", top=(o_ao, "#ef7fb0"), legs=("wide", "#5a4a6a", "#7a3b4a"),
                       face=dict(mouth="smile", lash=True)),
        "cust_vip": dict(hair="cap", hcol="#2c2c3a", hat="khan_dong", opts={"hat_col": "#7b2fa8"}, top=(o_robe, "#7b2fa8", GOLD),
                         legs=("pants", "#3d1f52", "#2a2026"),
                         face=dict(mouth="smile", mustache="full", mcol="#2c2c3a", brow="thick")),
        "chef": dict(hair="short", hcol="#4a2c1a", hat="chef", top=(o_chef,), legs=("pants", "#3d3d4a", "#2a2026"),
                     face=dict(mouth="open")),
        "waiter": dict(hair="short", hcol="#6b4226", top=(o_waiter,), legs=("pants", "#2f2f3a", "#2a2026"),
                       face=dict(mouth="smile")),
        "cashier": dict(hair="bun", hcol="#4a2c1a", top=(o_cashier, "#fff1d6", "#5fb84a"), legs=("pants", "#4b3a5a", "#6b4a3a"),
                        face=dict(mouth="smile", lash=True, glasses="#3a2a2a")),
        "receptionist": dict(hair="long", hcol="#24212c", top=(o_aodai, "#e8414f", GOLD), legs=("wide", "#fbf6ee", "#c9303e"),
                             face=dict(mouth="smile", lash=True)),
        "manager": dict(hair="bald", hcol="#7a6656", top=(o_suit, "#3d5a80", "#f2a541", "#d7dde4", 0, "#f2a541"),
                        legs=("pants", "#2a3550", "#2a2026"),
                        face=dict(mouth="smile", mustache="full", mcol="#6a5848", brow="thick", brow_col="#5a4a3a")),
        "guest": dict(hair="bob", hcol="#24212c", top=(o_polo, "#4fb8a8"), legs=("pants", "#4b3a5a", "#6b4a3a"),
                      face=dict(mouth="open", lash=True)),
        "ba_tu": dict(hair="bun", hcol="#d5d0c8", opts={"pin": "#a0703c"}, top=(o_aobaba, "#8a5a3a"),
                      legs=("wide", "#2f2f3a", "#4a3a30"),
                      face=dict(mouth="kind", eyes="happy", glasses="#8a5a32", wrinkles=True, brow="kind",
                                brow_col="#a59d92")),
        "lan": dict(hair="pony", hcol="#24212c", opts={"tie": "#e8414f"}, top=(o_lan, "#e8414f"),
                    legs=("skirt", "#2f2f3a", "#9b3b4a"), face=dict(mouth="open", lash=True)),
        "phat": dict(hair="slick", hcol="#17151c", top=(o_suit, "#6b3fa0", "#ffd34d", "#ffd34d", 4, "#ffd34d"),
                     legs=("pants", "#2a1f3a", "#17151c"),
                     face=dict(mouth="smug", eyes="smug", mustache="curl", mcol="#17151c", brow="smug")),
    }


def run(base):
    global _b
    _b = base
    sp = specs()
    for n in ("cust_1", "cust_2", "cust_3", "cust_4", "cust_5", "cust_6", "cust_vip"):
        person(n, sp[n])
        person(n + "_sit", sp[n], sit=True)
    for n in ("chef", "waiter", "cashier", "receptionist", "manager", "guest", "ba_tu", "lan", "phat"):
        person(n, sp[n])
    person("waiter_tray", sp["waiter"], tray=True)
