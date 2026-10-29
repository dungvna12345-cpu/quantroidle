# -*- coding: utf-8 -*-
"""Bộ vẽ đồ vật / cảnh (phiên bản 2) cho Quán Trọ Idle.

Được gen_sprites.main() gọi qua run(base). Mỗi sprite ghi đè file SVG cùng tên và giữ nguyên
kích thước canvas + điểm neo của bản cũ (riêng edge_* cao thêm để không bị cắt mép dưới).

Kỹ thuật chính: vẽ chi tiết trong "mặt phẳng cục bộ" rồi đưa lên màn hình isometric bằng
transform matrix (affine) -> hình tròn thành elip đúng phối cảnh, vân gỗ/viên gạch thẳng hàng.
  - mặt sàn:      matrix(1,0.5,-1,0.5,ox,oy)   (X theo trục x, Y theo trục y, 128 đơn vị / ô)
  - mặt dọc theo x: matrix(1,0.5,0,1,ox,oy)    (X theo trục x, Y = -z)
  - mặt dọc theo -y: matrix(1,-0.5,0,1,ox,oy)  (X theo trục -y, Y = -z)
Chỉ dùng path/shape, gradient, opacity, transform (ThorVG).
"""
import math
import random

OUT = "#5a341f"
SWO = 4.5     # viền ngoài
SWI = 2.5     # viền trong

B = None
C = lt = dk = mix = f = None
HW = HH = 0.0
WALL_H = 360.0


# ================================================================ tiện ích

def op(a):
    return 'opacity="%s"' % f(a)


def G(c, stops, x1=0, y1=0, x2=0, y2=1):
    """linearGradient nhiều điểm dừng: stops = [(offset, màu[, alpha]), ...]"""
    c.n += 1
    gid = "pg%d" % c.n
    s = ""
    for st in stops:
        a = st[2] if len(st) > 2 else 1
        s += '<stop offset="%s" stop-color="%s"%s/>' % (f(st[0]), st[1], "" if a == 1 else ' stop-opacity="%s"' % f(a))
    c.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                  % (gid, f(x1), f(y1), f(x2), f(y2), s))
    return "url(#%s)" % gid


def R(c, stops, cx=0.5, cy=0.5, r=0.5):
    st = [(s[0], s[1], s[2] if len(s) > 2 else 1) for s in stops]
    return c.rg(st, cx, cy, r)


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def P(*pts):
    """điểm -> path d (đa giác kín)"""
    return "M" + " L".join("%s,%s" % (f(x), f(y)) for x, y in pts) + " Z"


def tf_floor(c, x=0.0, y=0.0, z=0.0):
    o = c.iso(x, y, z)
    return "matrix(1,0.5,-1,0.5,%s,%s)" % (f(o[0]), f(o[1]))


def tf_px(c, x, y, z=0.0):
    """mặt phẳng đứng chạy theo +x (mặt nhìn về trái-xuống)."""
    o = c.iso(x, y, z)
    return "matrix(1,0.5,0,1,%s,%s)" % (f(o[0]), f(o[1]))


def tf_ny(c, x, y, z=0.0):
    """mặt phẳng đứng chạy theo -y (mặt nhìn về phải-xuống)."""
    o = c.iso(x, y, z)
    return "matrix(1,-0.5,0,1,%s,%s)" % (f(o[0]), f(o[1]))


def wobble(c, a, b, amp, col, sw, opa, rnd):
    m = lerp(a, b, rnd.uniform(0.35, 0.65))
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    k = rnd.uniform(-amp, amp)
    c.path("M%s,%s Q%s,%s %s,%s" % (f(a[0]), f(a[1]), f(m[0] + nx * k), f(m[1] + ny * k), f(b[0]), f(b[1])),
           "none", stroke=col, sw=sw, extra=op(opa))


def grain_quad(c, q, n, col, opa=0.28, sw=1.3, seed=1, amp=2.5, full=False):
    """vân gỗ chạy song song cạnh q0->q1 của tứ giác q (q0,q1,q2,q3)."""
    rnd = random.Random(seed)
    for k in range(n):
        t = (k + 0.5 + rnd.uniform(-0.3, 0.3)) / n
        a = lerp(q[0], q[3], t)
        b = lerp(q[1], q[2], t)
        if not full:
            s0, s1 = rnd.uniform(0.0, 0.3), rnd.uniform(0.65, 1.0)
            a, b = lerp(a, b, s0), lerp(a, b, s1)
        wobble(c, a, b, amp, col, sw, opa, rnd)


def bx(c, x0, y0, x1, y1, z0, z1, col, top=None, sw=SWO, out=True, ao=True, bevel=True, lfc=None, rtc=None,
       grain=0, seed=1, hide_rt=False):
    """Khối hộp: mặt trên sáng nhất, mặt trái vừa, mặt phải tối; cạnh vát sáng, AO chân."""
    i = c.iso
    top = top or lt(col, 0.14)
    lfc = lfc or dk(col, 0.04)
    rtc = rtc or dk(col, 0.26)
    tp = [i(x0, y0, z1), i(x1, y0, z1), i(x1, y1, z1), i(x0, y1, z1)]
    lf = [i(x0, y1, z1), i(x1, y1, z1), i(x1, y1, z0), i(x0, y1, z0)]
    rt = [i(x1, y1, z1), i(x1, y0, z1), i(x1, y0, z0), i(x1, y1, z0)]
    h = z1 - z0
    c.poly(lf, G(c, [(0, lt(lfc, 0.05)), (1, dk(lfc, 0.1))]), stroke=None)
    if not hide_rt:
        c.poly(rt, G(c, [(0, rtc), (1, dk(rtc, 0.14))]), stroke=None)
    c.poly(tp, G(c, [(0, lt(top, 0.16)), (1, top)], 0, 0, 1, 1), stroke=None)
    if grain and h > 10:
        grain_quad(c, lf, grain, dk(lfc, 0.35), seed=seed)
        if not hide_rt:
            grain_quad(c, rt, max(1, grain - 1), dk(rtc, 0.3), seed=seed + 7)
    if grain:
        tq = [i(x0, y0, z1), i(x1, y0, z1), i(x1, y1, z1), i(x0, y1, z1)]
        grain_quad(c, [tq[0], tq[1], tq[2], tq[3]], grain + 1, dk(top, 0.25), opa=0.3, seed=seed + 3)
    if ao and h > 12:
        e = min(12.0, h * 0.35)
        c.poly([i(x0, y1, z0 + e), i(x1, y1, z0 + e), i(x1, y1, z0), i(x0, y1, z0)],
               G(c, [(0, "#2a160a", 0), (1, "#2a160a", 0.28)]), stroke=None)
        if not hide_rt:
            c.poly([i(x1, y1, z0 + e), i(x1, y0, z0 + e), i(x1, y0, z0), i(x1, y1, z0)],
                   G(c, [(0, "#2a160a", 0), (1, "#2a160a", 0.3)]), stroke=None)
    if bevel:
        ex = min(0.02, (x1 - x0) * 0.12)
        ey = min(0.02, (y1 - y0) * 0.12)
        c.pl([i(x0 + ex, y1 - ey, z1), i(x1 - ex, y1 - ey, z1), i(x1 - ex, y0 + ey, z1)], stroke=lt(top, 0.65),
             sw=max(1.4, sw * 0.42), extra=op(0.9))
        if h > 6:
            zz = z1 - min(2.6, h * 0.25)
            c.pl([i(x0, y1, zz), i(x1, y1, zz)], stroke=lt(lfc, 0.35), sw=1.5, extra=op(0.55))
    if out:
        if not hide_rt:
            c.line(*i(x1, y1, z1), *i(x1, y1, z0), stroke=OUT, sw=max(1.5, sw * 0.42), extra=op(0.5))
        sil = [i(x0, y0, z1), i(x1, y0, z1), i(x1, y0, z0), i(x1, y1, z0), i(x0, y1, z0), i(x0, y1, z1)]
        c.poly(sil, "none", sw=sw)


def cyl(c, cx, cy, rx, ry, h, col, top=None, sw=SWO, hl=True, top_draw=True):
    """Trụ đứng, (cx,cy) = tâm đáy trên màn hình."""
    top = top or lt(col, 0.18)
    side = G(c, [(0, dk(col, 0.05)), (0.22, lt(col, 0.28)), (0.5, col), (1, dk(col, 0.38))], 0, 0, 1, 0)
    d = "M%s,%s L%s,%s A%s,%s 0 0 0 %s,%s L%s,%s A%s,%s 0 0 0 %s,%s Z" % (
        f(cx - rx), f(cy - h), f(cx - rx), f(cy), f(rx), f(ry), f(cx + rx), f(cy), f(cx + rx), f(cy - h),
        f(rx), f(ry), f(cx - rx), f(cy - h))
    c.path(d, side, sw=sw)
    if top_draw:
        c.ell(cx, cy - h, rx, ry, G(c, [(0, lt(top, 0.25)), (1, top)], 0, 0, 0.6, 1), sw=sw)
        if hl:
            c.path("M%s,%s A%s,%s 0 0 0 %s,%s" % (f(cx - rx * 0.82), f(cy - h + ry * 0.2), f(rx * 0.85), f(ry * 0.8),
                                                 f(cx + rx * 0.3), f(cy - h + ry * 0.78)),
                   "none", stroke=lt(top, 0.6), sw=max(1.2, sw * 0.4), extra=op(0.7))


def soft_shadow(c, x, y, rx, ry, a=0.3):
    c.ell(x, y, rx, ry, R(c, [(0, "#3a1f0e", a), (0.6, "#3a1f0e", a * 0.55), (1, "#3a1f0e", 0)]), stroke=None)


def leaf(c, x, y, ang, L, W, col, sw=2.4, vein=True, dark=None):
    c.group("translate(%s %s) rotate(%s)" % (f(x), f(y), f(ang)))
    d = "M0,0 C%s,%s %s,%s 0,%s C%s,%s %s,%s 0,0 Z" % (f(W * 0.8), f(-L * 0.12), f(W * 0.7), f(-L * 0.7), f(-L),
                                                     f(-W * 0.7), f(-L * 0.7), f(-W * 0.8), f(-L * 0.12))
    c.path(d, G(c, [(0, lt(col, 0.22)), (1, dark or dk(col, 0.22))], 0, 0, 1, 0), sw=sw)
    if vein:
        c.path("M0,%s Q%s,%s 0,%s" % (f(-L * 0.06), f(W * 0.12), f(-L * 0.5), f(-L * 0.86)), "none",
               stroke=dk(col, 0.35), sw=1.4, extra=op(0.55))
    c.end()


def blob_canopy(c, blobs, light, mid, dark, sw=SWO, hl=True):
    """Tán lá dạng cụm: viền -> nền tối -> cụm sáng -> điểm sáng."""
    for x, y, r in blobs:
        c.circ(x, y, r + sw * 0.9, OUT, stroke=None)
    for x, y, r in blobs:
        c.circ(x, y, r, dark, stroke=None)
    for x, y, r in blobs:
        c.circ(x - r * 0.12, y - r * 0.14, r * 0.86, R(c, [(0, light), (0.55, mid), (1, mid)], 0.38, 0.32, 0.7),
               stroke=None)
    if hl:
        for x, y, r in blobs:
            c.path("M%s,%s Q%s,%s %s,%s" % (f(x - r * 0.55), f(y - r * 0.2), f(x - r * 0.45), f(y - r * 0.62),
                                            f(x - r * 0.05), f(y - r * 0.66)), "none",
                   stroke=lt(light, 0.45), sw=3, extra=op(0.6))


def flower5(c, x, y, r, col, center="#ffd34d", sw=1.4):
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        c.circ(x + math.cos(a) * r, y + math.sin(a) * r * 0.9, r * 0.75, col, stroke=dk(col, 0.35), sw=sw)
    c.circ(x, y, r * 0.55, center, stroke=None)


# ================================================================ NỀN

def tile_canvas():
    return C(260, 132, 130, 66)


def diamond(c, inflate=2.0):
    return [(c.ax, c.ay - HH - inflate), (c.ax + HW + inflate * 2, c.ay), (c.ax, c.ay + HH + inflate),
            (c.ax - HW - inflate * 2, c.ay)]


# màu gốc của 4 hàng ván (giống nhau giữa _a và _b để ván chạy liền qua các ô)
def _plank_rows(base):
    return [base, lt(base, 0.07), dk(base, 0.05), lt(base, 0.03)]


def floor_wood(name, base, seed, outdoor=False):
    rnd = random.Random(seed * 31 + 7)
    c = tile_canvas()
    rows = _plank_rows(base)
    c.poly(diamond(c), rows[0], stroke=None)
    c.group(tf_floor(c))
    n = 4
    pw = 128.0 / n
    groove = dk(base, 0.32 if not outdoor else 0.42)
    for k in range(n):
        y0 = -64 + k * pw
        y1 = y0 + pw
        rc = rows[k]
        # đoạn ván: hai đầu dùng màu hàng (khớp ô bên), đoạn giữa đổi sắc
        joints = []
        if rnd.random() < 0.8:
            j1 = rnd.uniform(-44, 0)
            j2 = j1 + rnd.uniform(34, 70)
            joints = [j1, min(j2, 48)]
        xs = [-67] + joints + [67]
        for s in range(len(xs) - 1):
            sc = rc if s % 2 == 0 else mix(rc, rnd.choice([lt(base, 0.14), dk(base, 0.1), lt(base, 0.05)]), 0.85)
            c.rect(xs[s], y0, xs[s + 1] - xs[s], pw, G(c, [(0, lt(sc, 0.08)), (0.5, sc), (1, dk(sc, 0.06))]),
                   stroke=None)
        # vân gỗ
        for g in range(3):
            yy = y0 + pw * (0.22 + g * 0.28) + rnd.uniform(-2, 2)
            xa = rnd.uniform(-60, -10)
            xb = xa + rnd.uniform(40, 80)
            c.path("M%s,%s Q%s,%s %s,%s" % (f(xa), f(yy), f((xa + xb) / 2), f(yy + rnd.uniform(-3, 3)), f(xb),
                                            f(yy + rnd.uniform(-1.5, 1.5))),
                   "none", stroke=dk(base, 0.3), sw=1.1, extra=op(0.3))
        if rnd.random() < 0.35:
            kx, ky = rnd.uniform(-40, 40), y0 + pw * rnd.uniform(0.35, 0.65)
            c.ell(kx, ky, 5, 2.6, dk(base, 0.18), stroke=dk(base, 0.35), sw=0.9, extra=op(0.6))
            c.ell(kx, ky, 8.5, 4.2, "none", stroke=dk(base, 0.3), sw=0.9, extra=op(0.35))
        # mối nối đầu ván + đinh
        for j in joints:
            c.line(j, y0 + 0.5, j, y1 - 0.5, stroke=groove, sw=1.8, extra=op(0.75))
            c.line(j + 1.6, y0 + 1, j + 1.6, y1 - 1, stroke=lt(base, 0.35), sw=0.9, extra=op(0.5))
            for yy in (y0 + 6, y1 - 6):
                c.circ(j - 3.5, yy, 1.3, dk(base, 0.45), stroke=None, extra=op(0.7))
                c.circ(j + 3.5, yy, 1.3, dk(base, 0.45), stroke=None, extra=op(0.7))
        # khe ván (cạnh trên của ván) + viền sáng
        c.line(-67, y0 + 0.6, 67, y0 + 0.6, stroke=groove, sw=2.2 if not outdoor else 3.0, extra=op(0.8))
        c.line(-67, y0 + 2.6, 67, y0 + 2.6, stroke=lt(base, 0.4), sw=1.0, extra=op(0.55))
        c.line(-67, y1 - 1.6, 67, y1 - 1.6, stroke=dk(base, 0.14), sw=1.2, extra=op(0.45))
    c.end()
    c.save(name)


def carpet_runner(name):
    c = tile_canvas()
    base = "#d9a46c"
    rows = _plank_rows(base)
    c.poly(diamond(c), rows[0], stroke=None)
    c.group(tf_floor(c))
    for k in range(4):
        y0 = -64 + k * 32
        c.rect(-67, y0, 134, 32, G(c, [(0, lt(rows[k], 0.08)), (1, dk(rows[k], 0.06))]), stroke=None)
        c.line(-67, y0 + 0.6, 67, y0 + 0.6, stroke=dk(base, 0.42), sw=3, extra=op(0.8))
        c.line(-67, y0 + 2.8, 67, y0 + 2.8, stroke=lt(base, 0.4), sw=1, extra=op(0.5))
    # bóng dưới mép thảm
    c.rect(-67, 44, 134, 6, "#3a1f0e", stroke=None, extra=op(0.22))
    red, dred, gold, cream = "#d24a3c", "#9e2a2a", "#f2c14e", "#fbe3b8"
    c.rect(-67, -46, 134, 90, dred, stroke=None)
    c.rect(-67, -42, 134, 82, G(c, [(0, "#e05a48"), (0.5, red), (1, "#b83a33")]), stroke=None)
    for yy in (-36, 34):
        c.rect(-67, yy, 134, 3.5, gold, stroke=None)
    for yy in (-30, 28):
        c.rect(-67, yy, 134, 2, cream, stroke=None, extra=op(0.85))
    # hoạ tiết lặp: hình thoi + chấm
    c.path(P((-30, -2), (0, -22), (30, -2), (0, 18)), "#b93730", stroke=gold, sw=2.2)
    c.path(P((-16, -2), (0, -12), (16, -2), (0, 8)), gold, stroke=None)
    c.circ(0, -2, 3, dred, stroke=None)
    for xx in (-52, 52):
        c.circ(xx, -2, 4, gold, stroke=None)
        c.circ(xx, -2, 1.8, dred, stroke=None)
    for xx in range(-60, 61, 12):
        c.circ(xx, -33.5, 1.2, "#7a1f1f", stroke=None, extra=op(0.7))
        c.circ(xx + 6, 31.5, 1.2, "#7a1f1f", stroke=None, extra=op(0.7))
    # sợi vải mờ
    c.line(-67, -16, 67, -16, stroke="#ffffff", sw=1, extra=op(0.1))
    c.line(-67, 14, 67, 14, stroke="#5a1010", sw=1, extra=op(0.15))
    c.end()
    c.save(name)


def floor_stone(name, base, seed):
    rnd = random.Random(seed * 13 + 1)
    c = tile_canvas()
    grout = dk(base, 0.3)
    c.poly(diamond(c), grout, stroke=None)
    c.group(tf_floor(c))
    for gx in range(2):
        for gy in range(2):
            x0, y0 = -64 + gx * 64 + 3, -64 + gy * 64 + 3
            w = 58
            col = mix(base, rnd.choice([lt(base, 0.18), dk(base, 0.06), lt(base, 0.08), mix(base, "#d8b48a", 0.4)]),
                      rnd.uniform(0.3, 0.9))
            c.rect(x0 + 1.5, y0 + 1.5, w, w, dk(col, 0.25), rx=7, stroke=None)
            c.rect(x0, y0, w, w, G(c, [(0, lt(col, 0.2)), (0.6, col), (1, dk(col, 0.08))], 0, 0, 1, 1), rx=7,
                   stroke=None)
            # vát: sáng mép trên-trái, tối mép dưới-phải
            c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s" % (f(x0 + 3), f(y0 + w - 8), f(x0 + 3), f(y0 + 8), f(x0 + 3),
                                                       f(y0 + 3), f(x0 + 8), f(y0 + 3), f(x0 + w - 8), f(y0 + 3)),
                   "none", stroke=lt(col, 0.55), sw=2.2, extra=op(0.8))
            c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s" % (f(x0 + w - 2), f(y0 + 9), f(x0 + w - 2), f(y0 + w - 8),
                                                       f(x0 + w - 2), f(y0 + w - 2), f(x0 + w - 8), f(y0 + w - 2),
                                                       f(x0 + 9), f(y0 + w - 2)),
                   "none", stroke=dk(col, 0.3), sw=2, extra=op(0.6))
            for _ in range(6):
                px, py = x0 + rnd.uniform(8, w - 8), y0 + rnd.uniform(8, w - 8)
                c.circ(px, py, rnd.uniform(0.8, 1.8), rnd.choice([dk(col, 0.25), lt(col, 0.4)]), stroke=None,
                       extra=op(0.6))
            if rnd.random() < 0.4:
                px, py = x0 + rnd.uniform(14, 40), y0 + rnd.uniform(14, 40)
                c.path("M%s,%s l6,4 l3,9 l7,3" % (f(px), f(py)), "none", stroke=dk(col, 0.3), sw=1, extra=op(0.5))
            if rnd.random() < 0.5:
                c.ell(x0 + w * 0.6, y0 + w * 0.55, 12, 8, dk(col, 0.06), stroke=None, extra=op(0.35))
    c.end()
    c.save(name)


def floor_tile_vip(name):
    c = tile_canvas()
    red, dred, gold, lgold = "#9a2c3a", "#6e1a28", "#d8a845", "#f6d886"
    c.poly(diamond(c), red, stroke=None)
    c.group(tf_floor(c))
    c.rect(-66, -66, 132, 132, G(c, [(0, "#a8343f"), (1, "#8a2433")], 0, 0, 1, 1), stroke=None)
    # khung chìm
    c.rect(-52, -52, 104, 104, "none", rx=6, stroke=dred, sw=4, extra=op(0.7))
    c.rect(-50, -50, 100, 100, "none", rx=5, stroke=gold, sw=1.6, extra=op(0.85))
    c.rect(-47, -47, 94, 94, G(c, [(0, "#b23a45", 0.5), (1, "#7d1f2e", 0.4)], 0, 0, 1, 1), rx=4, stroke=None)
    # góc: 1/4 hoa vàng ghép với ô bên
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        cx, cy = sx * 64, sy * 64
        r = 18
        ax_, ay_ = cx - sx * r, cy
        bx_, by_ = cx, cy - sy * r
        sweep = 1 if sx * sy > 0 else 0
        c.path("M%s,%s L%s,%s A%s,%s 0 0 %d %s,%s Z" % (f(cx), f(cy), f(ax_), f(ay_), f(r), f(r), sweep, f(bx_),
                                                        f(by_)), gold, stroke=None)
        r2 = 10
        c.path("M%s,%s L%s,%s A%s,%s 0 0 %d %s,%s Z" % (f(cx), f(cy), f(cx - sx * r2), f(cy), f(r2), f(r2), sweep,
                                                        f(cx), f(cy - sy * r2)), dred, stroke=None)
    # hoa trung tâm
    for k in range(8):
        a = k * math.pi / 4
        px, py = math.cos(a) * 17, math.sin(a) * 17
        c.ell(px, py, 10, 5.5, gold, stroke="#8a5a1a", sw=1.2,
              extra='transform="rotate(%s %s %s)"' % (f(math.degrees(a)), f(px), f(py)))
    c.circ(0, 0, 12, lgold, stroke="#8a5a1a", sw=1.4)
    c.circ(0, 0, 6, red, stroke=None)
    c.circ(-3, -3, 2.2, "#ffffff", stroke=None, extra=op(0.5))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.circ(math.cos(a) * 36, math.sin(a) * 36, 2.6, lgold, stroke=None)
    # bóng sáng sơn mài
    c.path("M-60,-40 L-40,-60 L-20,-60 L-60,-20 Z", "#ffffff", stroke=None, extra=op(0.08))
    c.end()
    c.save(name)


GRASS = "#94cf62"


def grass(name, seed):
    rnd = random.Random(seed * 17 + 3)
    c = tile_canvas()
    c.poly(diamond(c), GRASS, stroke=None)
    c.group(tf_floor(c))
    for _ in range(5):
        x, y = rnd.uniform(-44, 44), rnd.uniform(-44, 44)
        c.ell(x, y, rnd.uniform(9, 16), rnd.uniform(6, 11), rnd.choice(["#a6da72", "#86c255", "#9ed66b"]),
              stroke=None, extra=op(0.7))
    c.end()
    for _ in range(14):
        x, y = rnd.uniform(-0.42, 0.42), rnd.uniform(-0.42, 0.42)
        p = c.iso(x, y)
        col = rnd.choice(["#6fae43", "#78b94a", "#5e9f3b"])
        hi = "#c4ea8e"
        s = rnd.uniform(0.8, 1.2)
        d = "M%s,%s q-2,-%s -7,-%s M%s,%s q0,-%s 1,-%s M%s,%s q3,-%s 7,-%s" % (
            f(p[0] - 2), f(p[1]), f(7 * s), f(10 * s), f(p[0]), f(p[1]), f(9 * s), f(13 * s),
            f(p[0] + 2), f(p[1]), f(7 * s), f(10 * s))
        c.path(d, "none", stroke=col, sw=2.4)
        c.path("M%s,%s q0,-%s 1,-%s" % (f(p[0] + 0.5), f(p[1] - 2), f(6 * s), f(10 * s)), "none", stroke=hi, sw=1,
               extra=op(0.7))
    if seed != 1:
        for _ in range(2 if seed == 0 else 3):
            p = c.iso(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3))
            col = rnd.choice(["#fff6c8", "#ffb3c9", "#ffe066"])
            for k in range(5):
                a = k * 2 * math.pi / 5
                c.ell(p[0] + math.cos(a) * 3.2, p[1] - 4 + math.sin(a) * 2, 2.6, 2, col, stroke=None)
            c.circ(p[0], p[1] - 4, 1.6, "#f5a623", stroke=None)
    else:
        p = c.iso(rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25))
        c.ell(p[0], p[1], 8, 4, "#3a1f0e", stroke=None, extra=op(0.18))
        c.ell(p[0], p[1] - 3, 7, 4.5, G(c, [(0, "#e2ddd2"), (1, "#b8afa0")]), stroke=dk("#b8afa0", 0.3), sw=1.4)
        c.ell(p[0] - 2, p[1] - 5, 3, 1.4, "#ffffff", stroke=None, extra=op(0.6))
    c.save(name)


def dirt(name, seed):
    rnd = random.Random(seed * 23 + 5)
    c = tile_canvas()
    base = "#e2bf86"
    c.poly(diamond(c), base, stroke=None)
    c.group(tf_floor(c))
    for _ in range(4):
        c.ell(rnd.uniform(-38, 38), rnd.uniform(-38, 38), rnd.uniform(12, 20), rnd.uniform(7, 12),
              rnd.choice(["#d6b077", "#ebcf9c", "#dab47c"]), stroke=None, extra=op(0.75))
    # vệt bánh xe chạy dọc trục x (liền giữa các ô)
    for yy in (-26, 24):
        c.rect(-67, yy, 134, 7, "#c9a066", stroke=None, extra=op(0.55))
        c.rect(-67, yy + 5.5, 134, 1.6, "#f2dcae", stroke=None, extra=op(0.6))
    c.end()
    for _ in range(9):
        p = c.iso(rnd.uniform(-0.38, 0.38), rnd.uniform(-0.38, 0.38))
        r = rnd.uniform(2.2, 4.6)
        col = rnd.choice(["#c4a27a", "#d8c3a2", "#b9936a"])
        c.ell(p[0], p[1] + 1, r * 1.4, r * 0.7, "#5a3a1a", stroke=None, extra=op(0.2))
        c.ell(p[0], p[1], r * 1.3, r * 0.8, col, stroke=dk(col, 0.3), sw=1)
        c.ell(p[0] - r * 0.3, p[1] - r * 0.3, r * 0.5, r * 0.25, "#ffffff", stroke=None, extra=op(0.45))
    for _ in range(10):
        p = c.iso(rnd.uniform(-0.45, 0.45), rnd.uniform(-0.45, 0.45))
        c.circ(p[0], p[1], 1, "#a07a4a", stroke=None, extra=op(0.6))
    c.save(name)


def floor_edge(name, side, kind):
    """Bờ sàn dày ở cạnh trước. Canvas cao 132 (bản cũ 110 bị cắt mép dưới); neo giữ nguyên."""
    c = C(262, 132, 131, 40)
    t = 22
    if kind == "wood":
        col = "#b37a48"
    else:
        col = "#a39b8e"
    if side == "l":
        tf = tf_px(c, -0.5, 0.5, 0)       # chạy theo +x tại y=0.5
        shade = 0.0
    else:
        tf = tf_ny(c, 0.5, 0.5, 0)        # chạy theo -y tại x=0.5
        shade = 0.2
    fc = dk(col, 0.08 + shade)
    c.group(tf)
    c.rect(-1, 0, 130, t, G(c, [(0, lt(fc, 0.08)), (1, dk(fc, 0.2))]), stroke=None)
    if kind == "wood":
        # dầm gỗ: hai tấm ván + vân + đinh
        c.line(-1, 11, 129, 11, stroke=dk(fc, 0.35), sw=1.6, extra=op(0.7))
        rnd = random.Random(len(name))
        for yy in (4.5, 16):
            c.path("M%s,%s Q%s,%s %s,%s" % (f(rnd.uniform(4, 30)), f(yy), f(64), f(yy + rnd.uniform(-2, 2)),
                                            f(rnd.uniform(90, 124)), f(yy)), "none", stroke=dk(fc, 0.3), sw=1,
                   extra=op(0.4))
        for xx in (10, 118):
            c.circ(xx, 5.5, 1.6, dk(fc, 0.5), stroke=None)
            c.circ(xx, 16.5, 1.6, dk(fc, 0.5), stroke=None)
    else:
        for r_ in range(2):
            yy = r_ * 11
            off = 0 if r_ == 0 else 32
            c.line(-1, yy + 11, 129, yy + 11, stroke=dk(fc, 0.35), sw=1.6, extra=op(0.7))
            for xx in range(off, 129, 64):
                c.line(xx, yy + 0.5, xx, yy + 11, stroke=dk(fc, 0.35), sw=1.6, extra=op(0.7))
                c.line(xx + 2, yy + 2, xx + 2, yy + 9, stroke=lt(fc, 0.3), sw=0.9, extra=op(0.5))
    c.rect(-1, 0, 130, 2.6, lt(col, 0.35), stroke=None, extra=op(0.85))
    c.line(-1, t, 129, t, stroke=OUT, sw=3.4)
    c.end()
    c.save(name)


# ================================================================ TƯỜNG

class Wall:
    """Mặt tường cục bộ: X 0..128 từ đầu trái màn hình sang phải, Y = -z."""

    def __init__(self, side):
        self.side = side
        if side == "l":
            self.c = C(160, 460, 144, 450)
            self.o = (16, 450)
            self.m = "matrix(1,-0.5,0,1,16,450)"
            self.sx = 1          # hướng lồi ra phía trước (k, k) / (-k, k)
        else:
            self.c = C(160, 460, 16, 450)
            self.o = (16, 386)
            self.m = "matrix(1,0.5,0,1,16,386)"
            self.sx = -1
        self.back = (-15.4 * self.sx, -15.4)   # độ dày tường (lùi vào)

    def k(self, k):
        return (self.sx * k, k)

    def ledge(self, X0, X1, Y0, Y1, k, col, top=None, end=True, sw=None):
        """Gờ nhô ra (phào, nẹp, bậu cửa): mặt trước + mặt trên + đầu nhìn thấy."""
        c = self.c
        kx, ky = self.k(k)
        top = top or lt(col, 0.25)
        c.path(P((X0, Y0), (X1, Y0), (X1 + kx, Y0 + ky), (X0 + kx, Y0 + ky)), top, stroke=None)
        if end:
            ex = X0 if self.sx > 0 else X1
            c.path(P((ex, Y0), (ex + kx, Y0 + ky), (ex + kx, Y1 + ky), (ex, Y1)), dk(col, 0.25), stroke=None)
        c.rect(min(X0 + kx, X1 + kx), Y0 + ky, X1 - X0, Y1 - Y0, G(c, [(0, lt(col, 0.1)), (1, dk(col, 0.12))]),
               stroke=None)
        c.line(X0 + kx, Y0 + ky + 1, X1 + kx, Y0 + ky + 1, stroke=lt(col, 0.5), sw=1.4, extra=op(0.8))
        c.rect(X0 + kx, Y1 + ky, X1 - X0, 2.4, "#2a160a", stroke=None, extra=op(0.25))
        if sw:
            c.path(P((X0, Y0), (X1, Y0), (X1 + kx, Y0 + ky), (X1 + kx, Y1 + ky), (X0 + kx, Y1 + ky),
                     (X0 + kx, Y0 + ky)), "none", sw=sw)

    def floor_strip(self, X0, X1, k0, k1, fill, extra=""):
        a0, b0 = self.k(k0)
        a1, b1 = self.k(k1)
        self.c.path(P((X0 + a0, b0), (X1 + a0, b0), (X1 + a1, b1), (X0 + a1, b1)), fill, stroke=None, extra=extra)


WALLS = {
    "a": dict(upper="#fbe8c8", lower="#c98a55", trim="#a8683d", rail="#d9a066", base="#8a5530", cap="#9b6438",
              curtain="#e98b6d", curtain2="#f6c6a6", frame="#a8683d"),
    "b": dict(upper="#b9553f", lower="#6e3b2e", trim="#4f2a20", rail="#7e4430", base="#3f2219", cap="#5a2e22",
              curtain="#f0c25a", curtain2="#fbe3a0", frame="#5a2a22", gold="#e8b84a"),
}


def wall(name, side, kind, feature=None):
    w = Wall(side)
    c = w.c
    pal = WALLS[kind]
    sh = 0.0 if side == "l" else 0.1

    def S(col, extra=0.0):
        return dk(col, sh + extra)

    rnd = random.Random("%s%s%s" % (side, kind, feature))
    c.group(w.m)
    # bóng AO trên sàn sát chân tường
    for k0, k1, a in ((0, 26, 0.06), (0, 16, 0.08), (0, 8, 0.12)):
        w.floor_strip(0, 128, k0, k1, "#2a160a", extra=op(a))
    # đầu tường (thấy ở ô cuối dãy; ô kế bên vẽ đè lên)
    bxv, byv = w.back
    ex = 0 if side == "l" else 128
    c.path(P((ex, 0), (ex, -WALL_H), (ex + bxv, -WALL_H + byv), (ex + bxv, byv)), S(pal["upper"], 0.22),
           sw=3)
    # thân tường
    up = S(pal["upper"])
    c.rect(0, -WALL_H, 128, WALL_H, G(c, [(0, dk(up, 0.06)), (0.18, lt(up, 0.05)), (0.7, up), (1, dk(up, 0.06))]),
           stroke=None)
    if kind == "a":
        # vết vữa loang nhẹ
        for _ in range(7):
            c.ell(rnd.uniform(14, 114), rnd.uniform(-310, -130), rnd.uniform(10, 20), rnd.uniform(5, 10),
                  rnd.choice([lt(up, 0.4), dk(up, 0.05)]), stroke=None, extra=op(0.35))
        for _ in range(14):
            c.circ(rnd.uniform(6, 122), rnd.uniform(-330, -112), rnd.uniform(0.7, 1.4), dk(up, 0.15), stroke=None,
                   extra=op(0.4))
    else:
        # gạch xây so le, viên chia đôi ở mép ô có màu cố định để ghép liền
        mortar = S("#e3b48e")
        c.rect(0, -WALL_H + 20, 128, WALL_H - 120, mortar, stroke=None)
        bricks = [S("#b9553f"), S("#a84a37"), S("#c4623f"), S("#9e4434"), S("#bf5a45")]
        rows = 13
        rh = (WALL_H - 20 - 104) / rows
        for r_ in range(rows):
            yb = -104 - r_ * rh
            off = 0 if r_ % 2 == 0 else 16
            xs = []
            x = -16 + off if off else 0
            while x < 128:
                xs.append(x)
                x += 32
            for xa in xs:
                xb = xa + 32
                a_, b_ = max(xa, 0) + 1.5, min(xb, 128) - 1.5
                if xa < 0 or xb > 128:
                    col = bricks[r_ % len(bricks)]
                    a_ = 0 if xa < 0 else a_
                    b_ = 128 if xb > 128 else b_
                else:
                    col = rnd.choice(bricks)
                y0, y1 = yb - rh + 1.5, yb - 1.5
                c.rect(a_, y0, b_ - a_, y1 - y0, G(c, [(0, lt(col, 0.1)), (1, dk(col, 0.1))]), stroke=None)
                c.line(a_ + 1, y0 + 1, b_ - 1, y0 + 1, stroke=lt(col, 0.35), sw=1.2, extra=op(0.7))
                c.line(a_ + 1, y1 - 0.5, b_ - 1, y1 - 0.5, stroke=dk(col, 0.35), sw=1.2, extra=op(0.6))
                if rnd.random() < 0.3 and b_ - a_ > 12:
                    c.circ(rnd.uniform(a_ + 4, b_ - 4), rnd.uniform(y0 + 3, y1 - 3), 1.2, dk(col, 0.3), stroke=None,
                           extra=op(0.6))
    # bóng dưới phào trần
    c.rect(0, -WALL_H + 22, 128, 26, G(c, [(0, "#2a160a", 0.28), (1, "#2a160a", 0)]), stroke=None)

    door = feature == "door"
    segs = [(0, 20), (108, 128)] if door else [(0, 128)]
    # ốp gỗ chân tường
    lw = S(pal["lower"])
    for X0, X1 in segs:
        c.rect(X0, -100, X1 - X0, 100, G(c, [(0, lt(lw, 0.06)), (1, dk(lw, 0.1))]), stroke=None)
    if not door:
        for px in (7, 71):
            x0, x1, y0, y1 = px, px + 50, -86, -22
            c.rect(x0, y0, x1 - x0, y1 - y0, dk(lw, 0.25), stroke=None)
            c.rect(x0 + 2, y0 + 2, x1 - x0 - 2, y1 - y0 - 2, lt(lw, 0.12), stroke=None)
            c.rect(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 12, G(c, [(0, lt(lw, 0.1)), (1, dk(lw, 0.04))]),
                   stroke=None)
            # vát panel
            c.path(P((x0 + 2, y0 + 2), (x1, y0 + 2), (x1 - 6, y0 + 6), (x0 + 6, y0 + 6)), lt(lw, 0.3), stroke=None)
            c.path(P((x0 + 2, y0 + 2), (x0 + 6, y0 + 6), (x0 + 6, y1 - 6), (x0 + 2, y1)), lt(lw, 0.18), stroke=None)
            c.path(P((x0 + 2, y1), (x0 + 6, y1 - 6), (x1 - 6, y1 - 6), (x1, y1)), dk(lw, 0.22), stroke=None)
            c.path(P((x1, y0 + 2), (x1, y1), (x1 - 6, y1 - 6), (x1 - 6, y0 + 6)), dk(lw, 0.14), stroke=None)
            for g in range(3):
                gx = x0 + 14 + g * 11 + rnd.uniform(-2, 2)
                c.path("M%s,%s Q%s,%s %s,%s" % (f(gx), f(y0 + 9), f(gx + rnd.uniform(-3, 3)), f((y0 + y1) / 2),
                                                f(gx + rnd.uniform(-1, 1)), f(y1 - 9)), "none",
                       stroke=dk(lw, 0.3), sw=1, extra=op(0.4))
            if kind == "b":
                cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
                c.path(P((cx_, cy_ - 10), (cx_ + 8, cy_), (cx_, cy_ + 10), (cx_ - 8, cy_)), "none",
                       stroke=pal["gold"], sw=1.6, extra=op(0.8))
    else:
        for X0, X1 in segs:
            c.rect(X0 + 4, -86, X1 - X0 - 8, 64, "none", stroke=dk(lw, 0.25), sw=1.6, extra=op(0.7))
    # bóng dưới nẹp
    for X0, X1 in segs:
        c.rect(X0, -96, X1 - X0, 10, G(c, [(0, "#2a160a", 0.3), (1, "#2a160a", 0)]), stroke=None)
    # nẹp ngang + len chân tường
    for X0, X1 in segs:
        w.ledge(X0, X1, -106, -98, 5, S(pal["rail"]), end=(X0 == 0 if side == "l" else X1 == 128))
        w.ledge(X0, X1, -16, 0, 4, S(pal["base"]), end=(X0 == 0 if side == "l" else X1 == 128))
    if kind == "b":
        for X0, X1 in segs:
            kx, ky = w.k(5)
            c.line(X0 + kx, -102 + ky, X1 + kx, -102 + ky, stroke=pal["gold"], sw=1.6, extra=op(0.9))

    # chi tiết cửa sổ / cửa đi
    if feature == "window":
        window(w, pal, S, kind)
    elif door:
        door_feat(w, pal, S, kind)

    # phào trần 2 tầng
    w.ledge(0, 128, -338, -330, 4, S(pal["trim"], -0.08))
    w.ledge(0, 128, -WALL_H, -338, 9, S(pal["trim"]))
    kx, ky = w.k(9)
    c.line(kx, -WALL_H + ky + 8, 128 + kx, -WALL_H + ky + 8, stroke=dk(S(pal["trim"]), 0.3), sw=1.4, extra=op(0.6))
    if kind == "b":
        c.line(kx, -WALL_H + ky + 13, 128 + kx, -WALL_H + ky + 13, stroke=pal["gold"], sw=2, extra=op(0.9))
    # mặt trên tường (độ dày)
    capc = S(pal["cap"])
    c.path(P((0, -WALL_H), (128, -WALL_H), (128 + bxv, -WALL_H + byv), (bxv, -WALL_H + byv)),
           G(c, [(0, lt(capc, 0.15)), (1, capc)]), stroke=None)
    c.path(P((0, -WALL_H), (128, -WALL_H), (128 + kx, -WALL_H + ky), (kx, -WALL_H + ky)), lt(S(pal["trim"]), 0.22),
           stroke=None)
    c.line(0 + kx, -WALL_H + ky, 128 + kx, -WALL_H + ky, stroke=lt(S(pal["trim"]), 0.5), sw=1.6, extra=op(0.8))
    c.line(bxv - 1, -WALL_H + byv, 128 + bxv + 1, -WALL_H + byv, stroke=OUT, sw=SWO)
    c.end()
    c.save(name)


def window(w, pal, S, kind):
    c = w.c
    l = w.side == "l"
    up = S(pal["upper"])
    fr = S(pal["frame"])
    # khung ngoài
    w.ledge(22, 106, -262, -142, 3, fr, end=True)
    kx, ky = w.k(3)
    # lỗ cửa + mặt dày tường (reveal)
    ox0, ox1, oy0, oy1 = 30 + kx, 98 + kx, -254 + ky, -150 + ky
    c.rect(ox0, oy0, ox1 - ox0, oy1 - oy0, dk(up, 0.22), stroke=OUT, sw=2.2)
    rs = 6
    gx0, gx1 = (ox0, ox1 - rs) if l else (ox0 + rs, ox1)
    gy0, gy1 = oy0, oy1 - rs
    # mặt reveal dưới (sáng) + cạnh bên
    c.path(P((ox0, oy1), (ox1, oy1), (gx1, gy1), (gx0, gy1)), lt(up, 0.1), stroke=None)
    # bầu trời + cảnh xa
    c.rect(gx0, gy0, gx1 - gx0, gy1 - gy0, G(c, [(0, "#8fd3f2"), (0.6, "#c9ecf8"), (1, "#fff1d0")]), stroke=None)
    c.circ(gx0 + (gx1 - gx0) * (0.7 if l else 0.3), gy0 + 22, 9, "#fff7d6", stroke=None, extra=op(0.9))
    c.ell(gx0 + 18, gy0 + 26, 12, 5, "#ffffff", stroke=None, extra=op(0.85))
    c.ell(gx0 + 28, gy0 + 23, 9, 5, "#ffffff", stroke=None, extra=op(0.85))
    hb = gy1
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s L%s,%s Z" % (
        f(gx0), f(hb), f(gx0), f(hb - 26), f(gx0 + 14), f(hb - 40), f(gx0 + 26), f(hb - 28),
        f(gx0 + 40), f(hb - 48), f(gx0 + 52), f(hb - 30), f(gx1 - 4), f(hb - 40), f(gx1), f(hb - 24), f(gx1), f(hb)),
        "#9ccf84", stroke=None)
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s L%s,%s Z" % (
        f(gx0), f(hb), f(gx0), f(hb - 14), f(gx0 + 22), f(hb - 26), f(gx0 + 38), f(hb - 14),
        f(gx1 - 10), f(hb - 24), f(gx1), f(hb - 12), f(gx1), f(hb)), "#6fb35a", stroke=None)
    # phản chiếu kính
    c.path(P((gx0 + 6, gy1), (gx0 + 22, gy0), (gx0 + 32, gy0), (gx0 + 16, gy1)), "#ffffff", stroke=None,
           extra=op(0.32))
    c.path(P((gx0 + 24, gy1), (gx0 + 40, gy0), (gx0 + 44, gy0), (gx0 + 28, gy1)), "#ffffff", stroke=None,
           extra=op(0.22))
    # khung cánh + song cửa
    mx = (gx0 + gx1) / 2
    my = gy0 + (gy1 - gy0) * 0.42
    c.rect(gx0, gy0, gx1 - gx0, gy1 - gy0, "none", stroke=lt(fr, 0.1), sw=5)
    c.line(mx, gy0, mx, gy1, stroke=lt(fr, 0.1), sw=4.5)
    c.line(gx0, my, gx1, my, stroke=lt(fr, 0.1), sw=4)
    c.line(mx - 1.2, gy0 + 2, mx - 1.2, gy1 - 2, stroke=lt(fr, 0.45), sw=1.2, extra=op(0.7))
    c.rect(gx0, gy0, gx1 - gx0, gy1 - gy0, "none", stroke=OUT, sw=1.6, extra=op(0.6))
    # bậu cửa + chậu cây nhỏ
    w.ledge(18, 110, -148, -140, 10, lt(fr, 0.15), sw=2.2)
    sk = w.k(5)
    px, py = 64 + sk[0], -148 + sk[1]
    c.path(P((px - 9, py - 14), (px + 9, py - 14), (px + 7, py), (px - 7, py)), G(c, [(0, "#e8865a"), (1, "#b45434")],
                                                                                  0, 0, 1, 0), sw=2)
    c.rect(px - 10.5, py - 17, 21, 4.5, "#ec9468", rx=1.5, sw=1.8)
    for ang, col in ((-38, "#6cbf55"), (35, "#5aa94a"), (-8, "#7fd064"), (14, "#6cbf55")):
        leaf(c, px, py - 16, ang, 18, 6, col, sw=1.6, vein=False)
    c.circ(px - 4, py - 30, 3.2, "#ff7b8f", stroke=OUT, sw=1.2)
    c.circ(px + 6, py - 27, 2.8, "#ffd34d", stroke=OUT, sw=1.2)
    # rèm cửa
    cur, cur2 = pal["curtain"], pal["curtain2"]
    cur, cur2 = S(cur), S(cur2)
    for s in (0, 1):
        def X(x):
            return x if s == 0 else 128 - x
        d = "M%s,-270 L%s,-270 Q%s,-232 %s,-200 Q%s,-170 %s,-136 L%s,-136 Q%s,-168 %s,-200 Q%s,-236 %s,-270 Z" % (
            f(X(12)), f(X(44)), f(X(40)), f(X(30)), f(X(40)), f(X(42)), f(X(8)), f(X(13)), f(X(19)), f(X(11)),
            f(X(12)))
        c.path(d, G(c, [(0, lt(cur, 0.18)), (0.5, cur), (1, dk(cur, 0.2))], 0, 0, 1, 0) if s == 0 else
               G(c, [(0, dk(cur, 0.2)), (0.5, cur), (1, lt(cur, 0.18))], 0, 0, 1, 0), sw=2.6)
        for fx0, fx1, fx2 in ((22, 24, 18), (32, 28, 32)):
            c.path("M%s,-266 Q%s,-232 %s,-204 M%s,-196 Q%s,-166 %s,-140" % (
                f(X(fx0)), f(X(fx1)), f(X(26 if fx0 == 22 else 29)), f(X(26 if fx0 == 22 else 29)),
                f(X(fx2 + (2 if fx0 == 22 else 6))), f(X(fx2 - (4 if fx0 == 22 else -6)))),
                "none", stroke=dk(cur, 0.3), sw=1.4, extra=op(0.55))
        c.path("M%s,-264 Q%s,-236 %s,-206" % (f(X(16)), f(X(20)), f(X(24))), "none", stroke=lt(cur2, 0.3), sw=1.6,
               extra=op(0.7))
        # dây buộc rèm
        c.path("M%s,-204 Q%s,-198 %s,-196 Q%s,-199 %s,-204 Z" % (f(X(18)), f(X(26)), f(X(36)), f(X(26)), f(X(18))),
               cur2, sw=1.6)
        c.circ(X(18), -200, 2.6, "#f2c14e" if kind == "a" else "#fff0b0", stroke=OUT, sw=1.2)
    # thanh treo + diềm rèm
    c.line(8, -272, 120, -272, stroke=OUT, sw=5.5)
    c.line(8, -272, 120, -272, stroke="#d9a845", sw=3)
    for x in (8, 120):
        c.circ(x, -272, 4.2, "#e8b84a", stroke=OUT, sw=1.8)
    d = "M12,-276 L116,-276 L116,-262"
    n = 6
    for k in range(n):
        xa = 116 - k * (104 / n)
        xb = xa - 104 / n
        d += " Q%s,-252 %s,-262" % (f((xa + xb) / 2), f(xb))
    d += " Z"
    c.path(d, G(c, [(0, lt(cur, 0.12)), (1, dk(cur, 0.12))]), sw=2.4)
    c.line(14, -271, 114, -271, stroke=cur2, sw=1.6, extra=op(0.8))


def door_feat(w, pal, S, kind):
    c = w.c
    l = w.side == "l"
    fr = S(pal["frame"])
    up = S(pal["upper"])
    # thảm chùi chân trên sàn
    a0, b0 = w.k(6)
    a1, b1 = w.k(30)
    c.path(P((34 + a0, b0), (94 + a0, b0), (94 + a1, b1), (34 + a1, b1)), "#b8553a", sw=2.4)
    for t in (0.33, 0.66):
        kk = 6 + 24 * t
        aa, bb = w.k(kk)
        c.line(37 + aa, bb, 91 + aa, bb, stroke="#f2c14e", sw=1.8, extra=op(0.85))
    # khung cửa vòm
    c.path("M18,0 L18,-158 Q18,-206 64,-206 Q110,-206 110,-158 L110,0 Z", G(c, [(0, lt(fr, 0.12)), (1, dk(fr, 0.1))]),
           sw=3)
    c.path("M22,-2 L22,-158 Q22,-202 64,-202 Q106,-202 106,-158 L106,-2", "none", stroke=lt(fr, 0.4), sw=1.4,
           extra=op(0.7))
    # lỗ cửa + reveal
    c.path("M28,0 L28,-156 Q28,-194 64,-194 Q100,-194 100,-156 L100,0 Z", dk(up, 0.35), stroke=OUT, sw=2)
    sx = -5 if l else 5
    x0, x1 = 28 + max(0, sx) + 0.5, 100 + min(0, sx) - 0.5
    mid = (x0 + x1) / 2
    door_c = "#b0703e" if kind == "a" else "#8e2f2f"
    d = "M%s,0 L%s,-151 Q%s,-189 %s,-189 Q%s,-189 %s,-151 L%s,0 Z" % (f(x0), f(x0), f(x0), f(mid), f(x1), f(x1), f(x1))
    c.path(d, G(c, [(0, lt(door_c, 0.12)), (1, dk(door_c, 0.14))], 0, 0, 1, 0), stroke=None)
    # ván dọc
    for k in range(1, 6):
        xx = x0 + (x1 - x0) * k / 6
        top_y = -151 - 38 * math.sqrt(max(0, 1 - ((xx - mid) / ((x1 - x0) / 2)) ** 2)) + 3
        c.line(xx, -3, xx, top_y, stroke=dk(door_c, 0.35), sw=1.6, extra=op(0.75))
        c.line(xx + 1.6, -3, xx + 1.6, top_y + 2, stroke=lt(door_c, 0.3), sw=0.8, extra=op(0.5))
    c.line(mid, -2, mid, -189, stroke=OUT, sw=2.2, extra=op(0.8))
    # bản lề sắt + đinh tán
    iron = "#4a3a34" if kind == "a" else "#c99a3a"
    for yy in (-40, -132):
        c.rect(x0 + 1, yy - 4, x1 - x0 - 2, 8, iron, rx=2, stroke=OUT, sw=1.4)
        for xx in (x0 + 6, mid - 6, mid + 6, x1 - 6):
            c.circ(xx, yy, 1.6, lt(iron, 0.45), stroke=None)
    # ô kính nhỏ trên vòm
    c.path("M%s,-158 Q%s,-180 %s,-182 Q%s,-180 %s,-158 Z" % (f(mid - 20), f(mid - 18), f(mid), f(mid + 18),
                                                             f(mid + 20)),
           G(c, [(0, "#fff2c0"), (1, "#f6c46a")]), stroke=OUT, sw=1.8)
    for a_ in (-14, 0, 14):
        c.line(mid, -160, mid + a_, -178 if a_ == 0 else -174, stroke=OUT, sw=1.2, extra=op(0.7))
    # tay nắm vòng
    for xx in (mid - 9, mid + 9):
        c.circ(xx, -92, 6, "none", stroke=OUT, sw=4)
        c.circ(xx, -92, 6, "none", stroke="#f2c14e", sw=2.2)
        c.circ(xx, -98, 2.4, "#f2c14e", stroke=OUT, sw=1.2)
    # bậc cửa đá
    w.ledge(20, 108, -6, 0, 9, S("#c9bfae"), sw=2.2)
    # biển gỗ treo trên cửa
    w.ledge(46, 82, -238, -214, 3, "#e8b06a" if kind == "a" else pal["gold"], sw=2.4)
    kx, ky = w.k(3)
    c.circ(64 + kx, -226 + ky, 5, "#c4423e", stroke=OUT, sw=1.4)
    for k in range(4):
        a = k * math.pi / 2
        c.circ(64 + kx + math.cos(a) * 8, -226 + ky + math.sin(a) * 5, 1.8, "#c4423e", stroke=None)
    c.line(52 + kx, -238 + ky, 60, -246, stroke=OUT, sw=1.4)
    c.line(76 + kx, -238 + ky, 68, -246, stroke=OUT, sw=1.4)
    c.circ(64, -247, 2, "#e8b84a", stroke=OUT, sw=1)


def wall_post(name):
    c = C(70, 470, 35, 448)
    h = 372
    e = 0.075
    col = "#a8683d"
    bx(c, -e, -e, e, e, 0, h, col, top=lt(col, 0.2), sw=4, grain=3, seed=5, ao=False)
    i = c.iso
    # chân cột + mũ cột
    bx(c, -e - 0.025, -e - 0.025, e + 0.025, e + 0.025, 0, 22, dk(col, 0.15), sw=3.5, ao=False)
    bx(c, -e - 0.03, -e - 0.03, e + 0.03, e + 0.03, h - 10, h + 2, dk(col, 0.1), top=lt(col, 0.15), sw=3.5, ao=False)
    bx(c, -e - 0.015, -e - 0.015, e + 0.015, e + 0.015, 100, 110, dk(col, 0.05), sw=3, ao=False)
    # đường sáng dọc cạnh
    a, b = i(e - 0.012, e, h - 14), i(e - 0.012, e, 26)
    c.line(a[0] - 3, a[1], b[0] - 3, b[1], stroke=lt(col, 0.45), sw=2, extra=op(0.6))
    c.save(name)


# ================================================================ ĐỒ VẬT

def obj_canvas(w, h, ay=None):
    return C(w, h, w / 2, ay if ay is not None else h - 40)


def table(name, tier):
    c = obj_canvas(240, 210, 150)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 104, 48, 0.3)
    if tier == 1:
        top, leg = "#e3a96c", "#8a5530"
        hgt = 74
        for lx, ly in [(-0.28, -0.28)]:
            bx(c, lx - 0.035, ly - 0.035, lx + 0.035, ly + 0.035, 0, hgt - 12, leg, sw=3, ao=False, bevel=False)
        # khung chân (tạp dề bàn)
        bx(c, -0.3, -0.3, 0.3, 0.3, hgt - 26, hgt - 12, dk(top, 0.2), sw=3.5, bevel=False, ao=False)
        for lx, ly in [(-0.28, 0.28), (0.28, -0.28), (0.28, 0.28)]:
            bx(c, lx - 0.038, ly - 0.038, lx + 0.038, ly + 0.038, 0, hgt - 12, leg, sw=3.5, ao=False, bevel=False)
            # chân bọc đồng nhỏ
            bx(c, lx - 0.042, ly - 0.042, lx + 0.042, ly + 0.042, 0, 6, "#5a3a22", sw=2.5, ao=False, bevel=False)
        # mặt bàn ván ghép
        bx(c, -0.37, -0.37, 0.37, 0.37, hgt - 12, hgt, top, top=lt(top, 0.12), sw=SWO, ao=False)
        c.group(tf_floor(c, 0, 0, hgt))
        for yy in (-15.8, 15.8):
            c.line(-46, yy, 46, yy, stroke=dk(top, 0.3), sw=1.8, extra=op(0.8))
            c.line(-46, yy + 1.8, 46, yy + 1.8, stroke=lt(top, 0.45), sw=1, extra=op(0.7))
        rnd = random.Random(3)
        for yy in (-36, -26, -6, 6, 26, 36):
            xa = rnd.uniform(-40, -10)
            c.path("M%s,%s Q%s,%s %s,%s" % (f(xa), f(yy), f(xa + 25), f(yy + rnd.uniform(-2, 2)), f(xa + 55), f(yy)),
                   "none", stroke=dk(top, 0.28), sw=1, extra=op(0.35))
        c.ell(22, -26, 4, 2, dk(top, 0.25), stroke=None, extra=op(0.5))
        c.end()
        # ống đũa + lọ nước tương ở góc phải
        u = i(0.24, -0.2, hgt)
        cyl(c, u[0], u[1], 7, 3.5, 18, "#7fae6a", sw=2.2)
        for dx, hh in ((-3, 30), (0, 33), (3, 29)):
            c.line(u[0] + dx, u[1] - 16, u[0] + dx * 1.6, u[1] - hh, stroke="#f6e1b0", sw=2)
        c.ell(u[0], u[1] - 18, 7, 3.5, "none", stroke=OUT, sw=1.6)
        v = i(0.12, -0.27, hgt)
        cyl(c, v[0], v[1], 5, 2.5, 14, "#5a2e1e", sw=2)
        c.rect(v[0] - 2.5, v[1] - 22, 5, 8, "#5a2e1e", rx=1.5, sw=1.6)
        c.rect(v[0] - 3, v[1] - 24, 6, 3, "#e8414f", rx=1, stroke=None)
    elif tier == 2:
        hgt = 76
        cx, cy = c.ax, c.ay
        # chân đế chữ thập
        for dx, dy in ((-34, 0), (34, 0), (0, -17), (0, 17)):
            c.line(cx, cy - 6, cx + dx, cy - 2 + dy, stroke=OUT, sw=10)
            c.line(cx, cy - 6, cx + dx, cy - 2 + dy, stroke="#7a4a2a", sw=6)
        cyl(c, cx, cy - 4, 12, 6, 40, "#7a4a2a", sw=3)
        # khăn trải bàn rủ
        ty = cy - hgt
        rx, ry = 92, 46
        cloth = "#fff6e6"
        hem_y = ty + 40
        n = 10
        pts_ = []
        for k in range(n + 1):
            a = math.pi - k * math.pi / n
            pts_.append((cx + math.cos(a) * (rx + 4), hem_y + math.sin(a) * (ry + 2)))
        d = "M%s,%s L%s,%s" % (f(cx - rx), f(ty), f(pts_[0][0]), f(pts_[0][1]))
        for k in range(n):
            p0, p1 = pts_[k], pts_[k + 1]
            m = lerp(p0, p1, 0.5)
            d += " Q%s,%s %s,%s" % (f(m[0]), f(m[1] + 9), f(p1[0]), f(p1[1]))
        d += " L%s,%s A%s,%s 0 0 1 %s,%s Z" % (f(cx + rx), f(ty), f(rx), f(ry), f(cx - rx), f(ty))
        c.path(d, G(c, [(0, "#f6e6cc"), (0.3, cloth), (0.75, "#ead6b8"), (1, "#d4bb96")], 0, 0, 1, 0), sw=SWO)
        # nếp gấp
        for k in range(1, n):
            p = pts_[k]
            a = math.pi - k * math.pi / n
            tx_ = cx + math.cos(a) * rx * 0.96
            tyy = ty + math.sin(a) * ry * 0.96
            c.path("M%s,%s Q%s,%s %s,%s" % (f(tx_), f(tyy + 4), f((tx_ + p[0]) / 2 + 2), f((tyy + p[1]) / 2),
                                            f(p[0]), f(p[1] + 6)), "none", stroke="#c9ad86", sw=1.6, extra=op(0.6))
        # viền thêu ở mép
        d2 = ""
        for k in range(n + 1):
            a = math.pi - k * math.pi / n
            p = (cx + math.cos(a) * (rx + 3), hem_y - 6 + math.sin(a) * (ry + 2))
            d2 += ("M" if k == 0 else " L") + "%s,%s" % (f(p[0]), f(p[1]))
        c.path(d2, "none", stroke="#e0644a", sw=3, extra='stroke-dasharray="6 5"')
        # mặt khăn
        c.ell(cx, ty, rx, ry, G(c, [(0, "#ffffff"), (1, "#f4e4c8")], 0, 0, 1, 1), sw=SWO)
        c.group(tf_floor(c, 0, 0, hgt))
        c.circ(0, 0, 50, "none", stroke="#e0644a", sw=2.4, extra='stroke-dasharray="7 5"')
        c.circ(0, 0, 44, "none", stroke="#f2c14e", sw=1.4, extra=op(0.8))
        for k in range(12):
            a = k * math.pi / 6
            c.circ(math.cos(a) * 58, math.sin(a) * 58, 2.4, "#e0644a", stroke=None, extra=op(0.7))
        c.end()
        c.ell(cx - 34, ty - 12, 26, 8, "#ffffff", stroke=None, extra=op(0.55))
        # lọ hoa nhỏ phía sau
        u = i(0.22, -0.24, hgt)
        cyl(c, u[0], u[1], 7, 3.5, 20, "#7cc0d8", sw=2.2)
        c.line(u[0], u[1] - 20, u[0] - 4, u[1] - 34, stroke="#5aa94a", sw=2)
        c.line(u[0], u[1] - 20, u[0] + 5, u[1] - 30, stroke="#5aa94a", sw=2)
        flower5(c, u[0] - 4, u[1] - 37, 4, "#ff8fa8")
        flower5(c, u[0] + 6, u[1] - 31, 3.4, "#ffd34d", center="#f08a3c")
    else:
        hgt = 78
        cx, cy = c.ax, c.ay
        red, gold = "#c42a3c", "#e8b84a"
        # đế
        c.ell(cx, cy - 2, 46, 21, G(c, [(0, lt(gold, 0.2)), (1, dk(gold, 0.25))]), sw=3.5)
        cyl(c, cx, cy - 6, 40, 18, 8, "#7d1a28", sw=3)
        cyl(c, cx, cy - 12, 14, 7, hgt - 30, "#8e2030", sw=3)
        for zz in (22, 40):
            c.ell(cx, cy - zz, 15, 6, "none", stroke=gold, sw=3)
        # mặt bàn sơn mài
        th = 18
        cyl(c, cx, cy - hgt + th, 96, 48, th, red, top="#d83a50", sw=SWO, top_draw=False)
        c.path("M%s,%s A96,48 0 0 0 %s,%s" % (f(cx - 96), f(cy - hgt + th * 0.5), f(cx + 96), f(cy - hgt + th * 0.5)),
               "none", stroke=gold, sw=3)
        for k in range(1, 12):
            a = math.pi - k * math.pi / 12
            p = (cx + math.cos(a) * 96, cy - hgt + th * 0.5 + math.sin(a) * 48)
            c.circ(p[0], p[1] + 1, 2.4, lt(gold, 0.3), stroke=None)
        c.ell(cx, cy - hgt, 96, 48, G(c, [(0, "#e04a5c"), (1, "#b52335")], 0, 0, 1, 1), sw=SWO)
        c.group(tf_floor(c, 0, 0, hgt))
        c.circ(0, 0, 66, "none", stroke=gold, sw=3)
        c.circ(0, 0, 60, "none", stroke=gold, sw=1.2, extra=op(0.8))
        for k in range(16):
            a = k * math.pi / 8
            c.path(P((math.cos(a) * 63, math.sin(a) * 63), (math.cos(a + 0.1) * 70, math.sin(a + 0.1) * 70),
                     (math.cos(a + 0.2) * 63, math.sin(a + 0.2) * 63)), gold, stroke=None, extra=op(0.85))
        # mâm xoay
        c.circ(0, 0, 42, G(c, [(0, "#fff3d6"), (1, "#f0d9a8")], 0, 0, 1, 1), stroke=dk(gold, 0.3), sw=2.4)
        c.circ(0, 0, 36, "none", stroke=gold, sw=1.6)
        c.end()
        c.ell(cx - 40, cy - hgt - 14, 30, 9, "#ffffff", stroke=None, extra=op(0.3))
        # bình sứ hoa lan
        u = i(0.27, -0.28, hgt)
        c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
            f(u[0] - 5), f(u[1] - 24), f(u[0] - 12), f(u[1] - 10), f(u[0] - 6), f(u[1]), f(u[0] + 6), f(u[1]),
            f(u[0] + 12), f(u[1] - 10), f(u[0] + 5), f(u[1] - 24)), G(c, [(0, "#ffffff"), (1, "#c8d6e6")], 0, 0, 1, 0),
            sw=2.2)
        c.path("M%s,%s q4,-4 8,0" % (f(u[0] - 4), f(u[1] - 12)), "none", stroke="#3a6fb5", sw=1.6)
        c.path("M%s,%s q-6,-14 -2,-28 M%s,%s q8,-10 10,-22" % (f(u[0]), f(u[1] - 24), f(u[0]), f(u[1] - 24)), "none",
               stroke="#5a8a3a", sw=2)
        for px, py in ((-2, -52), (10, -46), (4, -38)):
            flower5(c, u[0] + px, u[1] + py, 3.6, "#f6a8d8", center="#ffe14f", sw=1.1)
    c.save(name)


def chair(name, tier):
    c = obj_canvas(130, 200, 160)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 2, 50, 23, 0.3)
    if tier == 1:
        col, leg = "#d19458", "#8a5530"
    elif tier == 2:
        col, leg = "#a8683d", "#7a4a2a"
    else:
        col, leg = "#c42a3c", "#e8b84a"
    seat_z = 46
    # chân sau
    for lx, ly in [(-0.17, -0.17)]:
        bx(c, lx - 0.025, ly - 0.025, lx + 0.025, ly + 0.025, 0, seat_z, leg, sw=2.6, ao=False, bevel=False)
    # thanh giằng
    for (xa, ya), (xb, yb) in (((-0.17, 0.17), (0.17, 0.17)), ((0.17, -0.17), (0.17, 0.17))):
        a, b = i(xa, ya, 16), i(xb, yb, 16)
        c.line(*a, *b, stroke=OUT, sw=6)
        c.line(*a, *b, stroke=dk(leg, 0.05) if tier < 3 else "#8e2030", sw=3)
    for lx, ly in [(-0.17, 0.17), (0.17, -0.17), (0.17, 0.17)]:
        bx(c, lx - 0.027, ly - 0.027, lx + 0.027, ly + 0.027, 0, seat_z, leg, sw=2.8, ao=False, bevel=False)
    # mặt ghế
    seat = col if tier != 3 else "#8e2030"
    bx(c, -0.21, -0.21, 0.21, 0.21, seat_z - 8, seat_z, seat, sw=3.8, ao=False, grain=1 if tier == 1 else 0, seed=4)
    if tier == 2:
        # đệm vải xanh lá
        cu = "#9cc38f"
        bx(c, -0.18, -0.18, 0.18, 0.18, seat_z, seat_z + 7, cu, top=lt(cu, 0.15), sw=3, bevel=False, ao=False)
        u = i(0, 0, seat_z + 7)
        c.circ(u[0], u[1], 2.4, dk(cu, 0.35), stroke=None)
        c.path("M%s,%s q10,4 20,0" % (f(u[0] - 10), f(u[1] - 6)), "none", stroke=lt(cu, 0.5), sw=1.4, extra=op(0.7))
    if tier == 3:
        cu = "#d83a50"
        c.group(tf_floor(c, 0, 0, seat_z + 5))
        c.rect(-24, -24, 48, 48, G(c, [(0, lt(cu, 0.2)), (1, dk(cu, 0.15))], 0, 0, 1, 1), rx=12, sw=3)
        c.rect(-19, -19, 38, 38, "none", rx=9, stroke="#f3d27a", sw=1.6, extra=op(0.9))
        c.circ(0, 0, 2.6, "#f3d27a", stroke=None)
        c.end()
    # lưng ghế (phía sau, mặt y = -0.2)
    if tier == 1:
        for lx in (-0.17, 0.17):
            bx(c, lx - 0.025, -0.2, lx + 0.025, -0.15, seat_z, 122, leg, sw=3, ao=False, bevel=False)
        for zz in (78, 96):
            bx(c, -0.15, -0.19, 0.15, -0.16, zz, zz + 5, dk(col, 0.05), sw=2.6, ao=False, bevel=False)
        bx(c, -0.2, -0.205, 0.2, -0.145, 108, 124, col, sw=3.6, ao=False, grain=1, seed=8)
    elif tier == 2:
        for lx in (-0.17, 0.17):
            bx(c, lx - 0.027, -0.2, lx + 0.027, -0.15, seat_z, 124, leg, sw=3, ao=False, bevel=False)
        # tấm tựa lưng cong
        c.group(tf_px(c, -0.17, -0.175, 0))
        d = "M3,-60 L3,-112 Q22,-132 43.5,-130 Q65,-132 84,-112 L84,-60 Q43.5,-70 3,-60 Z"
        c.path(d, G(c, [(0, lt(col, 0.2)), (1, dk(col, 0.15))], 0, 0, 1, 0), sw=3.4)
        c.path("M43.5,-112 Q52,-100 43.5,-82 Q35,-100 43.5,-112 Z", "#e2b07a", stroke=OUT, sw=1.6)
        c.path("M8,-110 Q24,-126 43.5,-124", "none", stroke=lt(col, 0.45), sw=1.6, extra=op(0.8))
        c.end()
    else:
        for lx in (-0.17, 0.17):
            bx(c, lx - 0.028, -0.2, lx + 0.028, -0.15, seat_z, 128, "#8e2030", sw=3, ao=False, bevel=False)
        c.group(tf_px(c, -0.2, -0.175, 0))
        d = "M2,-58 L2,-110 Q4,-136 25,-138 Q51,-152 77,-138 Q98,-136 100,-110 L100,-58 Z"
        c.path(d, G(c, [(0, "#e04a5c"), (1, "#9e1f30")], 0, 0, 1, 0), sw=3.6)
        c.path("M8,-62 L8,-108 Q10,-130 27,-131 Q51,-144 75,-131 Q92,-130 94,-108 L94,-62", "none",
               stroke="#f3d27a", sw=2.4)
        c.circ(51, -100, 12, G(c, [(0, "#fff0b0"), (1, "#d6a032")]), stroke=OUT, sw=2)
        c.circ(51, -100, 6, "#c42a3c", stroke=None)
        c.path("M12,-112 Q14,-128 30,-128", "none", stroke="#ffffff", sw=2, extra=op(0.4))
        c.end()
        u = i(0, -0.175, 140)
        c.circ(u[0], u[1] + 4, 5, "#f3d27a", stroke=OUT, sw=2)
    c.save(name)


def tiles_splash(c, x0, x1, y, z0, z1, n, pal):
    """Gạch ốp tường bếp (mặt đứng dọc trục x tại y)."""
    c.group(tf_px(c, x0, y, 0))
    W = (x1 - x0) * 128
    c.rect(0, -z1, W, z1 - z0, pal[0], sw=3)
    tw = W / n
    for r_ in range(2):
        for k in range(n):
            xx, yy = k * tw, -z1 + r_ * (z1 - z0) / 2
            hh = (z1 - z0) / 2
            c.rect(xx + 1.5, yy + 1.5, tw - 3, hh - 3, G(c, [(0, "#ffffff"), (1, pal[0])], 0, 0, 1, 1), rx=2,
                   stroke=None)
            c.path(P((xx + tw / 2, yy + 4), (xx + tw - 5, yy + hh / 2), (xx + tw / 2, yy + hh - 4),
                     (xx + 5, yy + hh / 2)), "none", stroke=pal[1], sw=1.4, extra=op(0.8))
            c.circ(xx + tw / 2, yy + hh / 2, 2, pal[2], stroke=None)
    c.rect(0, -z1 - 3, W, 4, "#c98a55", stroke=OUT, sw=1.8)
    c.end()


SPLASH = ("#eef3ea", "#5aa3a0", "#e07a4f")


def kitchen_counter(name):
    c = obj_canvas(270, 230, 170)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 124, 52, 0.26)
    tiles_splash(c, -0.5, 0.5, -0.38, 84, 120, 4, SPLASH)
    wood = "#d39a62"
    # chân tủ lùi vào
    bx(c, -0.5, -0.36, 0.5, 0.34, 0, 10, "#5a3a22", sw=3, bevel=False, ao=False)
    bx(c, -0.5, -0.38, 0.5, 0.38, 10, 74, wood, sw=SWO, bevel=False, grain=0)
    # cửa tủ + ngăn kéo mặt trước (mặt y=0.38)
    c.group(tf_px(c, -0.5, 0.38, 0))
    for k in range(2):
        x0 = 6 + k * 64
        c.rect(x0, -50, 52, 34, dk(wood, 0.2), rx=3, stroke=None)
        c.rect(x0 + 2, -48, 48, 30, G(c, [(0, lt(wood, 0.16)), (1, dk(wood, 0.08))]), rx=3, stroke=dk(wood, 0.4),
               sw=1.6)
        c.rect(x0 + 7, -43, 38, 20, "none", rx=2, stroke=lt(wood, 0.35), sw=1.4, extra=op(0.8))
        c.rect(x0 + 2, -70, 48, 16, G(c, [(0, lt(wood, 0.14)), (1, dk(wood, 0.06))]), rx=3, stroke=dk(wood, 0.4),
               sw=1.6)
        c.rect(x0 + 18, -64, 16, 4, "#e8c27a", rx=2, stroke=OUT, sw=1.2)
        c.circ(x0 + 42 if k == 0 else x0 + 10, -34, 2.8, "#e8c27a", stroke=OUT, sw=1.2)
    c.end()
    # mặt đá
    bx(c, -0.5, -0.4, 0.5, 0.42, 74, 84, "#efe2c8", top="#f7eedc", sw=SWO)
    c.group(tf_floor(c, 0, 0, 84))
    rnd = random.Random(11)
    for _ in range(5):
        x, y = rnd.uniform(-56, 56), rnd.uniform(-44, 44)
        c.path("M%s,%s q8,3 14,-2 t12,4" % (f(x), f(y)), "none", stroke="#c9b48e", sw=1, extra=op(0.5))
    c.end()
    # thớt + rau củ (góc trước trái)
    u = i(-0.3, 0.16, 84)
    c.group(tf_floor(c, -0.3, 0.16, 84))
    c.rect(-22, -15, 44, 30, "#3a1f0e", rx=6, stroke=None, extra=op(0.2) + ' transform="translate(2 3)"')
    c.rect(-22, -15, 44, 30, G(c, [(0, "#f0c890"), (1, "#c98a55")], 0, 0, 1, 1), rx=6, sw=2.6)
    c.end()
    c.path("M%s,%s q10,-6 20,-2 l-2,4 q-9,-2 -17,2 Z" % (f(u[0] - 14), f(u[1] - 4)), "#f28c28", stroke=OUT, sw=1.6)
    c.path("M%s,%s l-5,-5 M%s,%s l-2,-7" % (f(u[0] - 13), f(u[1] - 4), f(u[0] - 13), f(u[1] - 4)), "none",
           stroke="#4ea83a", sw=2)
    for dx in (4, 8, 12):
        c.ell(u[0] + dx, u[1] + 4, 2.4, 1.4, "#7cc96b", stroke=OUT, sw=0.8)
    # dao
    c.line(u[0] + 2, u[1] - 8, u[0] + 20, u[1] - 14, stroke="#c0c6cf", sw=4)
    c.line(u[0] + 20, u[1] - 14, u[0] + 30, u[1] - 17, stroke="#5a3a22", sw=4.5)
    # chậu rau thơm góc sau phải
    v = i(0.36, -0.24, 84)
    cyl(c, v[0], v[1], 11, 5, 14, "#e07a4f", sw=2.4)
    for ang in (-50, -20, 10, 40):
        leaf(c, v[0], v[1] - 14, ang, 18, 5.5, "#6cbf55", sw=1.4, vein=False)
    # lọ gia vị
    for dx, col in ((0.16, "#f2c14e"), (0.24, "#e8414f")):
        w_ = i(dx, -0.3, 84)
        cyl(c, w_[0], w_[1], 5, 2.5, 13, "#f6f1e3", sw=2)
        c.ell(w_[0], w_[1] - 13, 5, 2.5, col, stroke=OUT, sw=1.4)
    c.save(name)


def stove(name):
    c = obj_canvas(270, 250, 190)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 124, 52, 0.26)
    tiles_splash(c, -0.5, 0.5, -0.38, 80, 120, 4, SPLASH)
    brick = "#c0603f"
    bx(c, -0.5, -0.38, 0.5, 0.38, 0, 74, brick, lfc="#c0603f", rtc="#94442e", sw=SWO, bevel=False)
    # gạch trên hai mặt
    for face in ("f", "s"):
        if face == "f":
            c.group(tf_px(c, -0.5, 0.38, 0))
            W = 128
        else:
            c.group(tf_ny(c, 0.5, 0.38, 0))
            W = 0.76 * 128
        rows = 5
        for r_ in range(rows):
            yy = -6 - r_ * 13.6
            c.line(0, yy, W, yy, stroke="#7a3624", sw=1.6, extra=op(0.65))
            c.line(0, yy - 1.6, W, yy - 1.6, stroke="#e8946a", sw=0.9, extra=op(0.45))
            off = 0 if r_ % 2 == 0 else 16
            x = off
            while x < W:
                if x > 0:
                    c.line(x, yy, x, yy - 13.6, stroke="#7a3624", sw=1.6, extra=op(0.65))
                x += 32
        c.end()
    # cửa lò vòm có lửa
    c.group(tf_px(c, -0.5, 0.38, 0))
    c.path("M30,-4 L30,-40 Q30,-62 64,-62 Q98,-62 98,-40 L98,-4 Z", "#8a3a26", sw=3)
    c.path("M36,-4 L36,-38 Q36,-56 64,-56 Q92,-56 92,-38 L92,-4 Z", R(c, [(0, "#ffe27a"), (0.45, "#ff9a3a"),
                                                                            (1, "#5a1a0e")], 0.5, 0.85, 0.75),
           stroke=OUT, sw=2)
    c.path("M42,-6 L86,-14 M44,-14 L84,-6", "none", stroke="#5a2e1a", sw=6)
    c.path("M42,-6 L86,-14 M44,-14 L84,-6", "none", stroke="#8a5530", sw=3.5)
    for dx, h, col in ((-16, 26, "#ff7b3a"), (0, 36, "#ffb347"), (14, 24, "#ff7b3a"), (-4, 20, "#fff1a0"),
                       (6, 16, "#fff1a0")):
        c.path("M%s,-12 q-8,-%s 0,-%s q8,%s 0,%s Z" % (f(64 + dx), f(h * 0.5), f(h), f(h * 0.5), f(h)), col,
               stroke=None)
    c.path("M30,-40 Q30,-62 64,-62 Q98,-62 98,-40", "none", stroke="#e8946a", sw=1.4, extra=op(0.7))
    c.end()
    # mặt gang
    bx(c, -0.5, -0.38, 0.5, 0.4, 74, 80, "#4a4d55", top="#3d3f46", sw=SWO, ao=False)
    for bxx in (-0.22, 0.22):
        u = i(bxx, 0, 80)
        c.ell(u[0], u[1], 36, 18, "#26272c", stroke=OUT, sw=3)
        c.ell(u[0], u[1], 27, 13.5, "none", stroke="#ff7b3a", sw=3.5, extra=op(0.95))
        c.ell(u[0], u[1], 27, 13.5, "none", stroke="#ffd27a", sw=1.2)
        c.ell(u[0], u[1], 14, 7, "#3a3c42", stroke="#6b6f78", sw=2)
        if bxx > 0:
            for k in range(8):
                a = math.pi + k * math.pi / 7
                p = (u[0] + math.cos(a) * 27, u[1] + math.sin(a) * 13.5)
                c.path("M%s,%s q-3,-5 0,-10 q3,5 0,10 Z" % (f(p[0]), f(p[1])), "#ffb347", stroke=None, extra=op(0.9))
        c.path("M%s,%s A36,18 0 0 1 %s,%s" % (f(u[0] - 30), f(u[1] - 10), f(u[0] + 10), f(u[1] - 17.5)), "none",
               stroke="#8d929c", sw=1.4, extra=op(0.7))
    # thanh vịn inox phía trước
    a, b = i(-0.44, 0.42, 70), i(0.44, 0.42, 70)
    c.line(*a, *b, stroke=OUT, sw=6.5)
    c.line(*a, *b, stroke="#c9ced6", sw=3.5)
    c.line(a[0], a[1] - 1, b[0], b[1] - 1, stroke="#ffffff", sw=1, extra=op(0.7))
    # khăn vắt
    m = i(0.2, 0.42, 70)
    c.path("M%s,%s l14,7 l-2,22 l-12,-6 Z" % (f(m[0] - 2), f(m[1])), "#f6f1e3", stroke=OUT, sw=2)
    c.line(m[0] + 1, m[1] + 12, m[0] + 12, m[1] + 18, stroke="#e8414f", sw=2)
    c.save(name)


def pot(name):
    c = obj_canvas(130, 130, 100)
    cx, cy = c.ax, c.ay
    steel = "#a3adb8"
    # quai
    for s in (-1, 1):
        c.path("M%s,%s q%s,-2 %s,10" % (f(cx + s * 40), f(cy - 38), f(s * 12), f(s * 6)), "none", stroke=OUT, sw=7)
        c.path("M%s,%s q%s,-2 %s,10" % (f(cx + s * 40), f(cy - 38), f(s * 12), f(s * 6)), "none", stroke="#5b5f66",
               sw=3.5)
    cyl(c, cx, cy, 42, 20, 46, steel, top="#d6dde4", sw=SWO, top_draw=False)
    # đai
    c.path("M%s,%s A42,20 0 0 0 %s,%s" % (f(cx - 42), f(cy - 14), f(cx + 42), f(cy - 14)), "none", stroke="#7d8793",
           sw=2.4)
    c.line(cx - 22, cy - 40, cx - 22, cy - 2, stroke="#ffffff", sw=4, extra=op(0.45))
    c.line(cx - 30, cy - 38, cx - 30, cy - 6, stroke="#ffffff", sw=1.6, extra=op(0.35))
    # miệng nồi + nước dùng
    c.ell(cx, cy - 46, 42, 20, G(c, [(0, "#eef2f5"), (1, "#9aa5b1")]), sw=SWO)
    c.ell(cx, cy - 45, 35, 15.5, G(c, [(0, "#f7b955"), (1, "#d9822b")]), stroke=dk(steel, 0.3), sw=2)
    for x, y, r in ((-14, -47, 3), (8, -43, 2.4), (18, -48, 1.8), (-4, -41, 1.6)):
        c.circ(cx + x, cy + y, r, "#ffd98a", stroke="#e08a2a", sw=0.8)
    for x, y in ((-20, -42), (12, -49), (2, -46), (-8, -50), (22, -44)):
        c.ell(cx + x, cy + y, 3.4, 1.6, "#5fb84a", stroke=None)
    c.ell(cx - 12, cy - 51, 10, 2.8, "#fff1c4", stroke=None, extra=op(0.7))
    # muôi gỗ
    c.line(cx + 12, cy - 46, cx + 36, cy - 92, stroke=OUT, sw=7)
    c.line(cx + 12, cy - 46, cx + 36, cy - 92, stroke="#c98a55", sw=3.6)
    c.line(cx + 13, cy - 49, cx + 34, cy - 90, stroke="#f0c890", sw=1.2, extra=op(0.8))
    c.save(name)


def cashier_counter(name):
    c = obj_canvas(270, 260, 200)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 124, 52, 0.26)
    wood = "#b66f43"
    bx(c, -0.5, -0.38, 0.5, 0.38, 0, 10, "#5a3a22", sw=3, bevel=False, ao=False)
    bx(c, -0.48, -0.4, 0.48, 0.4, 8, 78, wood, sw=SWO, bevel=False, grain=2, seed=21)
    # mặt trước chạm khắc
    c.group(tf_px(c, -0.48, 0.4, 0))
    W = 0.96 * 128
    c.rect(6, -70, W - 12, 56, dk(wood, 0.35), rx=4, stroke=None)
    c.rect(8, -68, W - 16, 52, G(c, [(0, "#8a5530"), (1, "#6b3f22")]), rx=4, stroke=dk(wood, 0.5), sw=1.6)
    for x0 in (14, W - 44):
        c.rect(x0, -62, 30, 40, "none", rx=3, stroke="#c98a55", sw=1.8, extra=op(0.85))
        c.path("M%s,-42 q7,-12 15,0 q-8,12 -15,0 Z" % f(x0 + 7.5), "#d9a845", stroke=None, extra=op(0.85))
    # đồng tiền may mắn
    cx_ = W / 2
    c.circ(cx_, -42, 17, G(c, [(0, "#ffe27a"), (1, "#d6912a")]), stroke=OUT, sw=2.6)
    c.circ(cx_, -42, 12.5, "none", stroke="#a8641a", sw=1.4)
    c.rect(cx_ - 5, -47, 10, 10, "#8a3a1e", rx=1, stroke=None)
    c.path("M%s,-54 q-6,4 -6,10" % f(cx_ - 4), "none", stroke="#ffffff", sw=2, extra=op(0.6))
    # dây tua đỏ
    c.path("M%s,-25 l0,10 M%s,-25 l-4,12 M%s,-25 l4,12" % (f(cx_), f(cx_), f(cx_)), "none", stroke="#d6313f", sw=2.2)
    c.end()
    # mặt quầy
    bx(c, -0.52, -0.42, 0.52, 0.44, 78, 88, "#e3b47c", top="#eec08a", sw=SWO, grain=1, seed=12)
    # sổ sách + bàn tính (trái)
    bx(c, -0.4, -0.2, -0.14, 0.12, 88, 93, "#f6f1e3", top="#fffaf0", sw=2.6, ao=False)
    bx(c, -0.4, -0.2, -0.14, -0.15, 88, 94, "#c4423e", sw=2, ao=False, bevel=False)
    a, b = i(-0.38, 0.0, 93), i(-0.16, 0.0, 93)
    c.line(*a, *b, stroke="#c9b48e", sw=1.2)
    a, b = i(-0.38, 0.06, 93), i(-0.16, 0.06, 93)
    c.line(*a, *b, stroke="#c9b48e", sw=1.2)
    # máy tính tiền cổ (bằng đồng)
    bx(c, 0.0, -0.3, 0.34, 0.06, 88, 112, "#c9963e", top="#e8c26a", sw=3.6, grain=0)
    bx(c, 0.03, -0.27, 0.31, 0.03, 112, 116, "#a8782a", sw=2.4, ao=False, bevel=False)
    # bàn phím nghiêng
    kp = [i(0.04, 0.03, 112), i(0.3, 0.03, 112), i(0.3, -0.12, 126), i(0.04, -0.12, 126)]
    c.poly(kp, "#3d2a20", sw=2.4)
    for r_ in range(3):
        for k in range(4):
            t0, t1 = 0.1 + r_ * 0.28, 0.1 + k * 0.22
            p = lerp(lerp(kp[0], kp[3], t0 + 0.1), lerp(kp[1], kp[2], t0 + 0.1), t1 + 0.08)
            c.ell(p[0], p[1], 3.4, 2.2, "#f6f1e3" if (r_ + k) % 3 else "#f2c14e", stroke=OUT, sw=0.9)
    # màn hiển thị
    bx(c, 0.06, -0.3, 0.28, -0.24, 116, 146, "#c9963e", top="#e8c26a", sw=3, ao=False)
    c.group(tf_px(c, 0.06, -0.24, 0))
    c.rect(4, -142, 20, 20, "#2a3a2a", rx=2, stroke=OUT, sw=1.4)
    c.rect(6, -140, 16, 7, "#9df0a0", rx=1, stroke=None, extra=op(0.85))
    c.end()
    # mèo thần tài
    u = i(0.36, 0.28, 88)
    cx, cy = u
    c.ell(cx, cy, 14, 6, "#3a1f0e", stroke=None, extra=op(0.2))
    c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (f(cx - 12), f(cy), f(cx - 14), f(cy - 24), f(cx), f(cy - 24),
                                                f(cx + 14), f(cy - 24), f(cx + 12), f(cy)),
           G(c, [(0, "#ffffff"), (1, "#e6dccb")], 0, 0, 1, 0), sw=2.6)
    c.circ(cx, cy - 30, 11, "#ffffff", sw=2.6)
    for s in (-1, 1):
        c.path("M%s,%s l%s,-10 l%s,7 Z" % (f(cx + s * 9), f(cy - 34), f(s * 1), f(-s * 7)), "#ffffff", stroke=OUT,
               sw=1.8)
        c.path("M%s,%s l%s,-6 l%s,4 Z" % (f(cx + s * 8.5), f(cy - 35), f(s * 0.6), f(-s * 4)), "#ffb3c0",
               stroke=None)
    c.circ(cx - 4, cy - 31, 1.5, OUT, stroke=None)
    c.circ(cx + 4, cy - 31, 1.5, OUT, stroke=None)
    c.path("M%s,%s q2,2 4,0" % (f(cx - 2), f(cy - 27)), "none", stroke=OUT, sw=1)
    c.circ(cx - 6.5, cy - 27.5, 2, "#ffb3c0", stroke=None, extra=op(0.8))
    c.circ(cx + 6.5, cy - 27.5, 2, "#ffb3c0", stroke=None, extra=op(0.8))
    # tay vẫy
    c.path("M%s,%s q2,-10 -2,-16 q6,-2 8,4 q2,8 -2,12 Z" % (f(cx + 9), f(cy - 30)), "#ffffff", stroke=OUT, sw=1.8)
    c.path("M%s,%s q%s,4 %s,0" % (f(cx - 9), f(cy - 20), f(9), f(18)), "none", stroke="#d6313f", sw=3)
    c.circ(cx, cy - 18, 3, "#ffd34d", stroke=OUT, sw=1.2)
    c.ell(cx - 4, cy - 9, 5, 3.5, "#ffd34d", stroke=OUT, sw=1.2)
    c.save(name)


def shelf(name):
    c = obj_canvas(200, 300, 250)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 2, 86, 36, 0.26)
    col = "#a96a3c"
    x0, x1, y0, y1 = -0.42, 0.42, -0.18, 0.18
    zt = 196
    # khối tủ (mặt trước là khoang mở)
    bx(c, x0, y0, x1, y1, 0, zt, col, top=lt(col, 0.2), sw=SWO, grain=0, bevel=False)
    c.group(tf_px(c, x0, y1, 0))
    W = (x1 - x0) * 128
    inner = dk(col, 0.45)
    c.rect(8, -zt + 10, W - 16, zt - 22, G(c, [(0, dk(inner, 0.1)), (1, inner)]), stroke=OUT, sw=2)
    c.rect(8, -zt + 10, W - 16, 10, "#1a0e08", stroke=None, extra=op(0.3))
    c.end()
    jars = ["#ff8f5a", "#7cc96b", "#ffd34d", "#4fa3e0", "#ef7fb0", "#a56be0", "#e8414f"]
    rnd = random.Random(7)
    levels = (12, 72, 132)
    for r_, z in enumerate(levels):
        # tấm kệ (thấy mặt trên)
        a, b = i(x0 + 0.06, y1, z), i(x1 - 0.06, y1, z)
        a2, b2 = i(x0 + 0.06, y0 + 0.04, z), i(x1 - 0.06, y0 + 0.04, z)
        c.poly([a2, b2, b, a], lt(col, 0.1), stroke=None)
        c.poly([a, b, (b[0], b[1] + 7), (a[0], a[1] + 7)], G(c, [(0, lt(col, 0.2)), (1, dk(col, 0.1))]), sw=2.2)
        # đồ trên kệ
        if r_ == 0:
            # hũ sành lớn
            for k, xx in enumerate((-0.2, 0.12)):
                u = i(xx, 0.0, z)
                jc = ["#8a5a3a", "#5a7a8a"][k]
                c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
                    f(u[0] - 12), f(u[1] - 40), f(u[0] - 26), f(u[1] - 22), f(u[0] - 14), f(u[1]), f(u[0] + 14),
                    f(u[1]), f(u[0] + 26), f(u[1] - 22), f(u[0] + 12), f(u[1] - 40)),
                    G(c, [(0, lt(jc, 0.25)), (0.4, jc), (1, dk(jc, 0.35))], 0, 0, 1, 0), sw=2.6)
                c.ell(u[0], u[1] - 40, 12, 4.5, dk(jc, 0.3), stroke=OUT, sw=2)
                c.rect(u[0] - 9, u[1] - 30, 18, 12, "#f6e3bd", rx=2, stroke=OUT, sw=1.4)
                c.circ(u[0], u[1] - 24, 3, "#c4423e", stroke=None)
                c.line(u[0] - 14, u[1] - 34, u[0] - 16, u[1] - 12, stroke="#ffffff", sw=2, extra=op(0.4))
        elif r_ == 1:
            for k in range(4):
                u = i(-0.27 + k * 0.18, 0.0, z)
                jc = jars[(k + 2) % len(jars)]
                h = 30 if k % 2 == 0 else 24
                cyl(c, u[0], u[1], 10, 4.5, h, "#f2f6f8", top="#f8fbfc", sw=2.2, hl=False, top_draw=False)
                c.path("M%s,%s L%s,%s A10,4.5 0 0 0 %s,%s L%s,%s Z" % (
                    f(u[0] - 8.5), f(u[1] - h * 0.7), f(u[0] - 8.5), f(u[1] - 2), f(u[0] + 8.5), f(u[1] - 2),
                    f(u[0] + 8.5), f(u[1] - h * 0.7)), jc, stroke=None, extra=op(0.85))
                c.ell(u[0], u[1] - h, 10, 4.5, "#e9d2a8", stroke=OUT, sw=2)
                c.ell(u[0], u[1] - h - 3, 7, 3, "#c98a55", stroke=OUT, sw=1.6)
                c.line(u[0] - 5, u[1] - h + 4, u[0] - 5, u[1] - 6, stroke="#ffffff", sw=1.6, extra=op(0.7))
        else:
            # bát đĩa xếp + ấm trà + chậu cây
            u = i(-0.24, 0.0, z)
            for k in range(3):
                c.ell(u[0], u[1] - 4 - k * 6, 18, 6, "#ffffff", stroke=OUT, sw=1.8)
                c.path("M%s,%s A18,6 0 0 0 %s,%s" % (f(u[0] - 18), f(u[1] - 4 - k * 6), f(u[0] + 18),
                                                    f(u[1] - 4 - k * 6)), "none", stroke="#4f8fd0", sw=1.4)
            v = i(0.04, 0.0, z)
            c.ell(v[0], v[1] - 13, 15, 13, G(c, [(0, "#f6f1e3"), (1, "#c9bfa8")], 0, 0, 1, 1), sw=2.2)
            c.path("M%s,%s q12,-2 14,-12" % (f(v[0] + 13), f(v[1] - 14)), "none", stroke=OUT, sw=2.2)
            c.rect(v[0] - 6, v[1] - 29, 12, 5, "#c98a55", rx=2, sw=1.6)
            w_ = i(0.26, 0.0, z)
            cyl(c, w_[0], w_[1], 9, 4, 14, "#e07a4f", sw=2)
            for ang in (-60, -25, 15, 50):
                leaf(c, w_[0], w_[1] - 14, ang, 22, 6, "#6cbf55", sw=1.4, vein=False)
    # đỉnh tủ: phào + giỏ mây
    bx(c, x0 - 0.03, y0 - 0.03, x1 + 0.03, y1 + 0.03, zt, zt + 10, dk(col, 0.1), top=lt(col, 0.18), sw=SWO,
       ao=False, grain=1, seed=2)
    u = i(-0.1, 0.0, zt + 10)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(u[0] - 22), f(u[1] - 18), f(u[0] + 22), f(u[1] - 18), f(u[0] + 18),
                                               f(u[1]), f(u[0] - 18), f(u[1])),
           G(c, [(0, "#e8c27a"), (1, "#b8873e")], 0, 0, 1, 0), sw=2.4)
    for yy in (-12, -6):
        c.line(u[0] - 20, u[1] + yy, u[0] + 20, u[1] + yy, stroke="#8a5a2a", sw=1.2, extra=op(0.7))
    c.path("M%s,%s Q%s,%s %s,%s" % (f(u[0] - 14), f(u[1] - 18), f(u[0]), f(u[1] - 38), f(u[0] + 14), f(u[1] - 18)),
           "none", stroke=OUT, sw=2.4)
    # chân tủ
    for lx in (x0 + 0.03, x1 - 0.03):
        p = i(lx, y1, 0)
        c.rect(p[0] - 5, p[1] - 2, 10, 6, "#5a3a22", rx=2, sw=1.6)
    c.save(name)


def plant_pot(name):
    c = obj_canvas(130, 200, 170)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 46, 18, 0.3)
    # lá phía sau
    back = [(-62, 50, 22), (62, 50, 22), (-30, 58, 24), (30, 58, 24), (0, 62, 24)]
    for ang, L, W in back:
        leaf(c, cx, cy - 56, ang, L, W, "#4f9a3e", dark="#2f6e2a")
    # chậu đất nung
    pot_c = "#d9724a"
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
        f(cx - 32), f(cy - 52), f(cx + 32), f(cy - 52), f(cx + 30), f(cy - 20), f(cx + 22), f(cy - 2), f(cx - 22),
        f(cy - 2), f(cx - 30), f(cy - 20), f(cx - 32), f(cy - 52)),
        G(c, [(0, lt(pot_c, 0.12)), (0.25, lt(pot_c, 0.3)), (0.6, pot_c), (1, dk(pot_c, 0.35))], 0, 0, 1, 0), sw=SWO)
    c.path("M%s,%s Q%s,%s %s,%s" % (f(cx - 29), f(cy - 30), f(cx), f(cy - 22), f(cx + 29), f(cy - 30)), "none",
           stroke=dk(pot_c, 0.3), sw=2, extra=op(0.6))
    for k in range(5):
        px = cx - 18 + k * 9
        c.path("M%s,%s l4,-6 l4,6" % (f(px - 4), f(cy - 34)), "none", stroke="#f6d6a0", sw=1.6, extra=op(0.85))
    c.line(cx - 20, cy - 46, cx - 18, cy - 10, stroke="#ffffff", sw=3, extra=op(0.3))
    c.rect(cx - 36, cy - 62, 72, 14, G(c, [(0, lt(pot_c, 0.25)), (1, dk(pot_c, 0.15))]), rx=6, sw=SWO)
    c.ell(cx, cy - 61, 31, 4, "#5a3a22", stroke=None)
    # lá phía trước
    front = [(-48, 46, 21, "#6cbf55"), (44, 48, 21, "#62b44c"), (-18, 56, 22, "#7cc95e"), (16, 56, 22, "#6cbf55"),
             (-78, 36, 18, "#5aa94a"), (78, 36, 18, "#5aa94a"), (0, 62, 20, "#86d066")]
    for ang, L, W, col in front:
        leaf(c, cx, cy - 58, ang, L, W, col)
    # chồi non
    leaf(c, cx + 2, cy - 100, 8, 26, 7, "#a6e27f", sw=2)
    c.save(name)


def lantern(name):
    c = obj_canvas(110, 260, 230)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 30, 12, 0.3)
    pc = "#6b4123"
    # chân đế
    c.ell(cx, cy - 2, 24, 10, G(c, [(0, "#8a5530"), (1, "#4a2a16")]), sw=3)
    c.ell(cx, cy - 8, 16, 7, "#7a4a2a", sw=2.6)
    c.rect(cx - 5, cy - 186, 10, 180, G(c, [(0, lt(pc, 0.25)), (0.4, pc), (1, dk(pc, 0.35))], 0, 0, 1, 0), rx=4,
           sw=3)
    c.ell(cx, cy - 186, 7, 3.5, "#e8b84a", stroke=OUT, sw=2)
    # cần treo cong
    c.path("M%s,%s Q%s,%s %s,%s" % (f(cx), f(cy - 180), f(cx + 18), f(cy - 196), f(cx + 26), f(cy - 176)), "none",
           stroke=OUT, sw=5)
    c.path("M%s,%s Q%s,%s %s,%s" % (f(cx), f(cy - 180), f(cx + 18), f(cy - 196), f(cx + 26), f(cy - 176)), "none",
           stroke="#8a5530", sw=2.4)
    lx, ly = cx + 26, cy - 128
    # quầng sáng
    c.circ(lx, ly, 34, R(c, [(0, "#ffd27a", 0.45), (1, "#ffb347", 0)]), stroke=None)
    c.line(lx, cy - 176, lx, ly - 34, stroke=OUT, sw=2)
    # thân đèn lụa
    rx, ry = 24, 30
    c.ell(lx, ly, rx, ry, R(c, [(0, "#fff0a0"), (0.35, "#ff9a4a"), (0.8, "#d6313f"), (1, "#a8202e")], 0.42, 0.42, 0.62),
          sw=SWO)
    for k in (-0.6, -0.25, 0.25, 0.6):
        c.path("M%s,%s Q%s,%s %s,%s" % (f(lx + k * rx * 0.4), f(ly - ry + 2), f(lx + k * rx * 1.25), f(ly),
                                        f(lx + k * rx * 0.4), f(ly + ry - 2)), "none", stroke="#8a1a24", sw=1.4,
               extra=op(0.55))
    c.path("M%s,%s Q%s,%s %s,%s" % (f(lx - rx * 0.55), f(ly - ry * 0.6), f(lx - rx * 0.85), f(ly - 4),
                                    f(lx - rx * 0.6), f(ly + ry * 0.4)), "none", stroke="#fff6c8", sw=2.2,
           extra=op(0.6))
    for yy, w_ in ((ly - ry - 5, 22), (ly + ry - 3, 22)):
        c.rect(lx - w_ / 2, yy, w_, 8, G(c, [(0, "#ffe27a"), (1, "#c9902a")]), rx=3, sw=2.2)
    # tua rua
    c.line(lx, ly + ry + 5, lx, ly + ry + 10, stroke=OUT, sw=2)
    c.circ(lx, ly + ry + 11, 3, "#f2c14e", stroke=OUT, sw=1.4)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(lx - 3), f(ly + ry + 13), f(lx + 3), f(ly + ry + 13), f(lx + 5),
                                               f(ly + ry + 32), f(lx - 5), f(ly + ry + 32)), "#d6313f", stroke=OUT,
           sw=1.8)
    c.line(lx, ly + ry + 15, lx, ly + ry + 30, stroke="#ff7b7b", sw=1, extra=op(0.7))
    c.save(name)


def painting(name, side, motif):
    c = C(240, 380, 120, 352)
    if side == "l":
        tf = tf_ny(c, -0.5, 0.32, 0)
        sx = 1
    else:
        tf = tf_px(c, -0.32, -0.5, 0)
        sx = -1
    W = 0.64 * 128
    z0, z1 = 148, 244
    k = 5
    kx, ky = sx * k, k
    c.group(tf)
    # bóng đổ lên tường
    c.rect(4 + kx * 0.8, -z1 + 6 + ky, W, z1 - z0, "#2a160a", rx=3, stroke=None, extra=op(0.22))
    # dây treo
    c.path("M%s,%s L%s,%s L%s,%s" % (f(W * 0.2 + kx), f(-z1 + ky), f(W / 2), f(-z1 - 22), f(W * 0.8 + kx),
                                     f(-z1 + ky)), "none", stroke=OUT, sw=1.6)
    c.circ(W / 2, -z1 - 22, 2.4, "#e8b84a", stroke=OUT, sw=1)
    # độ dày khung
    gold = "#d9a845"
    if sx > 0:
        c.path(P((0, -z1), (kx, -z1 + ky), (kx, -z0 + ky), (0, -z0)), dk(gold, 0.35), stroke=None)
    else:
        c.path(P((W, -z1), (W + kx, -z1 + ky), (W + kx, -z0 + ky), (W, -z0)), dk(gold, 0.35), stroke=None)
    c.path(P((0, -z1), (W, -z1), (W + kx, -z1 + ky), (kx, -z1 + ky)), lt(gold, 0.3), stroke=None)
    c.group("translate(%s %s)" % (f(kx), f(ky)))
    c.rect(0, -z1, W, z1 - z0, G(c, [(0, "#f6d27a"), (0.5, gold), (1, "#a8742a")], 0, 0, 1, 1), rx=2, sw=3.5)
    c.rect(4, -z1 + 4, W - 8, z1 - z0 - 8, "none", stroke="#fff0b0", sw=1.2, extra=op(0.7))
    c.rect(8, -z1 + 8, W - 16, z1 - z0 - 16, "#fbf1dc", stroke=dk(gold, 0.4), sw=1.6)
    px0, py0, px1, py1 = 12, -z1 + 12, W - 12, -z0 - 12
    pw, ph = px1 - px0, py1 - py0
    if motif == 0:
        # Vịnh Hạ Long: núi đá vôi, sông, thuyền buồm, mặt trời
        c.rect(px0, py0, pw, ph, G(c, [(0, "#9fd8f0"), (0.6, "#f9e2b8"), (1, "#f6c98a")]), stroke=None)
        c.circ(px0 + pw * 0.7, py0 + ph * 0.32, 7, "#ff9f43", stroke=None)
        c.circ(px0 + pw * 0.7, py0 + ph * 0.32, 11, "#ffd27a", stroke=None, extra=op(0.4))
        by = py0 + ph * 0.68
        c.path("M%s,%s L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s L%s,%s Z" % (
            f(px0), f(by), f(px0 + 4), f(by - 22), f(px0 + 10), f(by - 36), f(px0 + 16), f(by - 20),
            f(px0 + 20), f(by - 8), f(px0 + 24), f(by), f(px0), f(by)), "#5f9e7a", stroke=None)
        c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(px0 + 20), f(by), f(px0 + 28), f(by - 50), f(px0 + 38), f(by - 30), f(px0 + 44), f(by - 12),
            f(px0 + 46), f(by)), "#4d8a68", stroke=None)
        c.path("M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(px1 - 22), f(by), f(px1 - 14), f(by - 34), f(px1 - 6), f(by - 24), f(px1), f(by - 10), f(px1), f(by)),
            "#6aa884", stroke=None)
        c.rect(px0, by, pw, py1 - by, G(c, [(0, "#7cc4d8"), (1, "#4f9ab8")]), stroke=None)
        for yy in (by + 5, by + 11):
            c.line(px0 + 6, yy, px0 + 20, yy, stroke="#ffffff", sw=1, extra=op(0.6))
            c.line(px1 - 26, yy + 2, px1 - 10, yy + 2, stroke="#ffffff", sw=1, extra=op(0.6))
        bx_, by_ = px0 + pw * 0.55, by + 7
        c.path("M%s,%s l14,0 l-3,4 l-9,0 Z" % (f(bx_ - 7), f(by_)), "#8a5530", stroke=None)
        c.path("M%s,%s l0,-16 q8,6 9,14 Z" % (f(bx_), f(by_)), "#e8414f", stroke=None)
        c.path("M%s,%s l0,-12 q-6,4 -6,10 Z" % (f(bx_ - 1), f(by_ - 1)), "#f26a5a", stroke=None)
    else:
        # sen hồng
        c.rect(px0, py0, pw, ph, G(c, [(0, "#fff1d6"), (1, "#f5d6a6")]), stroke=None)
        c.ell(px0 + pw * 0.3, py1 - 12, 16, 6, "#5fae6a", stroke=dk("#5fae6a", 0.3), sw=1)
        c.ell(px0 + pw * 0.72, py1 - 8, 13, 5, "#6cbf75", stroke=dk("#5fae6a", 0.3), sw=1)
        c.path("M%s,%s Q%s,%s %s,%s" % (f(px0 + pw * 0.5), f(py1), f(px0 + pw * 0.44), f(py0 + ph * 0.6),
                                        f(px0 + pw * 0.5), f(py0 + ph * 0.42)), "none", stroke="#4e9a52", sw=2.4)
        fx, fy = px0 + pw * 0.5, py0 + ph * 0.38
        for ang, L in ((-50, 20), (50, 20), (-22, 24), (22, 24), (0, 26)):
            c.group("translate(%s %s) rotate(%s)" % (f(fx), f(fy + 8), f(ang)))
            c.path("M0,0 Q%s,%s 0,%s Q%s,%s 0,0 Z" % (f(8), f(-L * 0.5), f(-L), f(-8), f(-L * 0.5)),
                   G(c, [(0, "#ffd0e0"), (1, "#f07aa0")]), stroke="#c04a74", sw=1.2)
            c.end()
        c.circ(fx, fy + 6, 3.4, "#ffd34d", stroke=None)
        c.path("M%s,%s q4,-8 10,-6" % (f(px0 + pw * 0.2), f(py0 + 12)), "none", stroke="#8a5530", sw=1.2,
               extra=op(0.6))
        c.circ(px1 - 10, py0 + 10, 4, "#d6313f", stroke=None, extra=op(0.8))
    # kính phản chiếu
    c.path(P((px0, py0 + ph * 0.5), (px0 + pw * 0.4, py0), (px0 + pw * 0.55, py0), (px0, py0 + ph * 0.75)), "#ffffff",
           stroke=None, extra=op(0.18))
    c.end()
    c.end()
    c.save(name)


def rug(name):
    c = C(520, 270, 260, 135)
    red, dred, gold, cream, navy = "#c8443a", "#8e2a2a", "#f2c14e", "#fbe3b8", "#3d4f7a"
    # độ dày + bóng
    c.group(tf_floor(c, 0, 0, -3))
    c.rect(-118, -118, 236, 236, "#3a1f0e", rx=6, stroke=None, extra=op(0.25))
    c.end()
    c.group(tf_floor(c))
    # tua rua hai đầu
    for k in range(-112, 113, 8):
        c.line(-118, k, -128, k, stroke=cream, sw=2.2)
        c.line(118, k, 128, k, stroke=cream, sw=2.2)
    c.rect(-118, -118, 236, 236, dred, rx=6, sw=3.5)
    c.rect(-110, -110, 220, 220, G(c, [(0, "#d65a48"), (1, "#b23a33")], 0, 0, 1, 1), rx=4, stroke=None)
    c.rect(-104, -104, 208, 208, "none", rx=3, stroke=gold, sw=4)
    c.rect(-96, -96, 192, 192, "none", rx=3, stroke=cream, sw=6)
    for k in range(-88, 89, 16):
        for s in (-96, 96):
            c.circ(k, s, 2.4, dred, stroke=None)
            c.circ(s, k, 2.4, dred, stroke=None)
    c.rect(-86, -86, 172, 172, G(c, [(0, "#c8443a"), (1, "#a83630")], 0, 0, 1, 1), rx=3, stroke=gold, sw=1.6)
    # huy chương giữa
    c.path(P((-62, 0), (0, -62), (62, 0), (0, 62)), navy, stroke=gold, sw=3)
    c.path(P((-46, 0), (0, -46), (46, 0), (0, 46)), red, stroke=cream, sw=2)
    for k in range(8):
        a = k * math.pi / 4
        px, py = math.cos(a) * 22, math.sin(a) * 22
        c.ell(px, py, 12, 6, gold, stroke=dk(gold, 0.4), sw=1.2,
              extra='transform="rotate(%s %s %s)"' % (f(math.degrees(a)), f(px), f(py)))
    c.circ(0, 0, 11, cream, stroke=dk(gold, 0.4), sw=1.4)
    c.circ(0, 0, 5, red, stroke=None)
    # hoạ tiết góc
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = sx * 66, sy * 66
        c.path(P((x - 12, y), (x, y - 12), (x + 12, y), (x, y + 12)), gold, stroke=None)
        c.circ(x, y, 4, navy, stroke=None)
    # sợi len nổi
    rnd = random.Random(9)
    for _ in range(30):
        x, y = rnd.uniform(-80, 80), rnd.uniform(-80, 80)
        c.line(x, y, x + 4, y, stroke="#ffffff", sw=0.8, extra=op(0.12))
    c.end()
    c.save(name)


def tree(name, variant):
    c = obj_canvas(240, 330, 300)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 4, 84, 32, 0.3)
    bark = "#8a5a34"
    if variant == 0:
        # thân + rễ
        c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
            f(cx - 22), f(cy + 2), f(cx - 10), f(cy - 10), f(cx - 11), f(cy - 60), f(cx - 8), f(cy - 128),
            f(cx + 10), f(cy - 128), f(cx + 10), f(cy - 60), f(cx + 12), f(cy - 10), f(cx + 24), f(cy + 2), f(cx),
            f(cy - 4), f(cx - 22), f(cy + 2)), G(c, [(0, lt(bark, 0.15)), (0.4, bark), (1, dk(bark, 0.35))], 0, 0, 1, 0),
            sw=SWO)
        c.path("M%s,%s q4,-30 0,-60 M%s,%s q-3,-20 2,-40" % (f(cx - 3), f(cy - 14), f(cx + 5), f(cy - 30)), "none",
               stroke=dk(bark, 0.35), sw=1.6, extra=op(0.7))
        c.path("M%s,%s q-14,-14 -30,-18 M%s,%s q16,-10 28,-26" % (f(cx - 6), f(cy - 110), f(cx + 6), f(cy - 104)),
               "none", stroke=OUT, sw=7)
        c.path("M%s,%s q-14,-14 -30,-18 M%s,%s q16,-10 28,-26" % (f(cx - 6), f(cy - 110), f(cx + 6), f(cy - 104)),
               "none", stroke=bark, sw=3.5)
        blobs = [(-58, -150, 40), (56, -152, 42), (-30, -196, 50), (32, -200, 50), (0, -150, 44), (-4, -244, 42),
                 (-56, -210, 30), (60, -212, 30)]
        blob_canopy(c, [(cx + x, cy + y, r) for x, y, r in blobs], "#a8e27a", "#6cbf4f", "#3f8a34")
        # quả cam
        for x, y in [(-40, -164), (24, -222), (48, -158), (-14, -206), (8, -170), (-60, -200)]:
            c.circ(cx + x, cy + y, 7, R(c, [(0, "#ffd27a"), (1, "#f07a2a")], 0.35, 0.35, 0.7), stroke=OUT, sw=2)
            c.line(cx + x, cy + y - 7, cx + x + 2, cy + y - 10, stroke="#3f8a34", sw=1.6)
    else:
        # thông Đà Lạt: thân + 4 tầng tán
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 12), f(cy + 2), f(cx - 7), f(cy - 120), f(cx + 7),
                                                   f(cy - 120), f(cx + 12), f(cy + 2)),
               G(c, [(0, lt(bark, 0.15)), (1, dk(bark, 0.35))], 0, 0, 1, 0), sw=SWO)
        tiers = [(-60, 92, 40), (-118, 78, 40), (-170, 62, 38), (-216, 44, 36), (-252, 26, 30)]
        for k, (y, hw, h) in enumerate(tiers):
            yy = cy + y
            d = "M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
                f(cx - hw), f(yy), f(cx - hw * 0.5), f(yy - h * 0.4), f(cx), f(yy - h - 12),
                f(cx + hw * 0.5), f(yy - h * 0.4), f(cx + hw), f(yy),
                f(cx + hw * 0.5), f(yy + 10), f(cx), f(yy + 4),
                f(cx - hw * 0.5), f(yy + 10), f(cx - hw), f(yy))
            c.path(d, G(c, [(0, "#7cc88a"), (0.45, "#3f9a5e"), (1, "#24683e")], 0, 0, 1, 0.3), sw=SWO)
            c.path("M%s,%s Q%s,%s %s,%s" % (f(cx - hw * 0.7), f(yy - 2), f(cx - hw * 0.4), f(yy - h * 0.45),
                                            f(cx - 6), f(yy - h - 4)), "none", stroke="#b6eab0", sw=2.4, extra=op(0.55))
            for s in (-1, 1):
                c.path("M%s,%s q%s,4 %s,0" % (f(cx + s * hw * 0.3), f(yy + 2), f(s * 6), f(s * 12)), "none",
                       stroke="#1e5a34", sw=1.6, extra=op(0.6))
        c.circ(cx - 34, cy - 82, 4.5, "#c98a55", stroke=OUT, sw=1.6)
        c.circ(cx + 26, cy - 140, 4, "#c98a55", stroke=OUT, sw=1.6)
    c.save(name)


def bush(name):
    c = obj_canvas(170, 150, 120)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 66, 24, 0.3)
    blobs = [(-38, -24, 26), (36, -24, 27), (-14, -44, 30), (18, -46, 30), (0, -22, 30)]
    blob_canopy(c, [(cx + x, cy + y, r) for x, y, r in blobs], "#b0e683", "#6cbf4f", "#3f8a34")
    for x, y, col in [(-30, -40, "#ff8fb1"), (12, -64, "#ffd34d"), (40, -32, "#ff8fb1"), (-6, -26, "#ffffff"),
                      (-48, -18, "#ffd34d"), (24, -20, "#ff6b8b"), (-16, -60, "#ffffff"), (44, -50, "#ffffff")]:
        flower5(c, cx + x, cy + y, 4.4, col, center="#f5a623", sw=1.2)
    for x, y in ((-24, -8), (20, -6)):
        leaf(c, cx + x, cy + y, -40 if x < 0 else 40, 14, 5, "#5aa94a", sw=1.6, vein=False)
    c.save(name)


def fence(name, axis):
    c = C(280, 190, 140, 140)
    col = "#e6c08a"
    soft_shadow(c, c.ax, c.ay + 4, 96, 28, 0.18)
    if axis == "x":
        tf = tf_px(c, -0.5, 0, 0)
        back = (3.5, -3.5)
        shade = 0.0
    else:
        tf = tf_ny(c, 0, 0.5, 0)
        back = (-3.5, -3.5)
        shade = 0.12
    cc = dk(col, shade)
    c.group(tf)
    # thanh ngang
    for yy in (-34, -70):
        c.rect(-2, yy - 5, 132, 10, G(c, [(0, lt(cc, 0.2)), (1, dk(cc, 0.2))]), sw=3)
        c.line(-2, yy - 3.5, 130, yy - 3.5, stroke=lt(cc, 0.5), sw=1, extra=op(0.7))
    # cọc rào
    for k in range(4):
        x = 16 + k * 32
        d = "M%s,0 L%s,-90 L%s,-102 L%s,-90 L%s,0 Z" % (f(x - 10), f(x - 10), f(x), f(x + 10), f(x + 10))
        c.group("translate(%s %s)" % (f(back[0]), f(back[1])))
        c.path(d, dk(cc, 0.35), sw=3)
        c.end()
        c.path(d, G(c, [(0, lt(cc, 0.22)), (0.5, cc), (1, dk(cc, 0.16))], 0, 0, 1, 0), sw=3.2)
        c.line(x - 5, -86, x - 5, -6, stroke=lt(cc, 0.5), sw=1.4, extra=op(0.7))
        c.path("M%s,-60 q2,10 0,22" % f(x + 3), "none", stroke=dk(cc, 0.3), sw=1, extra=op(0.6))
        c.circ(x, -34, 1.6, dk(cc, 0.5), stroke=None)
        c.circ(x, -70, 1.6, dk(cc, 0.5), stroke=None)
    # cọc góc
    for x in (0, 128):
        c.rect(x - 6, -110, 12, 110, G(c, [(0, lt("#c98a55", 0.15)), (1, dk("#c98a55", 0.25))], 0, 0, 1, 0), rx=2,
               sw=3)
        c.rect(x - 8, -116, 16, 8, "#a8683d", rx=2, sw=2.6)
    c.end()
    c.save(name)


def gate(name):
    c = C(320, 380, 160, 330)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 124, 38, 0.22)
    wood = "#a96a3c"
    # chân cột đá + cột gỗ
    for x in (-0.5, 0.5):
        bx(c, x - 0.09, -0.09, x + 0.09, 0.09, 0, 24, "#b8afa0", top="#d8d0c2", sw=3.5)
        bx(c, x - 0.06, -0.06, x + 0.06, 0.06, 24, 214, wood, sw=4, grain=2, seed=int(x * 10 + 9), ao=False)
    # câu đối đỏ trên cột
    for x in (-0.5, 0.5):
        c.group(tf_px(c, x - 0.045, 0.06, 0))
        c.rect(0, -190, 11.5, 120, "#c42a3c", rx=1, stroke=OUT, sw=1.8)
        for k in range(4):
            c.rect(3.5, -180 + k * 28, 4.5, 14, "#f2c14e", rx=1, stroke=None, extra=op(0.85))
        c.end()
    # xà ngang + xà phụ
    bx(c, -0.64, -0.08, 0.64, 0.08, 196, 218, "#8a5530", sw=4, grain=2, seed=3)
    bx(c, -0.5, -0.05, 0.5, 0.05, 168, 178, "#8a5530", sw=3.4)
    # biển gỗ treo
    for x in (-0.22, 0.22):
        a, b = i(x, 0, 178), i(x, 0, 160)
        c.line(*a, *b, stroke=OUT, sw=2.2)
    c.group(tf_px(c, -0.3, 0.02, 0))
    c.rect(0, -162, 76.8, 34, G(c, [(0, "#e04a4a"), (1, "#a8282f")]), rx=4, sw=3.4)
    c.rect(4, -158, 68.8, 26, "none", rx=3, stroke="#f2c14e", sw=1.8)
    for k in range(3):
        c.circ(20 + k * 18, -145, 4.4, "#f2c14e", stroke=None)
    c.end()
    # mái ngói âm dương
    x0, x1, zb, zt = -0.74, 0.74, 212, 256
    tile = "#c4523e"
    c.poly([i(x0, -0.28, zb), i(x1, -0.28, zb), i(x1, 0, zt), i(x0, 0, zt)], G(c, [(0, "#a8322f"), (1, "#8e2a28")]),
           sw=4)
    front = [i(x0, 0.28, zb), i(x1, 0.28, zb), i(x1, 0, zt), i(x0, 0, zt)]
    c.poly(front, G(c, [(0, lt(tile, 0.12)), (1, dk(tile, 0.1))]), sw=4)
    for k in range(1, 12):
        t = x0 + (x1 - x0) * k / 12.0
        u, v = i(t, 0.28, zb), i(t, 0.01, zt - 1)
        c.line(*u, *v, stroke=dk(tile, 0.35), sw=3)
        c.line(u[0] - 2, u[1] - 1, v[0] - 2, v[1] - 1, stroke=lt(tile, 0.35), sw=1.2, extra=op(0.7))
    for k in range(1, 4):
        t = k / 4.0
        a, b = lerp(front[0], front[3], t), lerp(front[1], front[2], t)
        c.line(*a, *b, stroke=dk(tile, 0.25), sw=1.4, extra=op(0.6))
    # đầu hồi
    c.poly([i(x1, -0.28, zb), i(x1, 0.28, zb), i(x1, 0, zt)], "#8e2a28", sw=4)
    # mép ngói + bờ nóc cong
    a, b = i(x0, 0.28, zb), i(x1, 0.28, zb)
    c.line(*a, *b, stroke=OUT, sw=7)
    c.line(*a, *b, stroke="#f2d6a0", sw=3)
    r0, r1 = i(x0 - 0.04, 0, zt + 2), i(x1 + 0.04, 0, zt + 2)
    c.line(*r0, *r1, stroke=OUT, sw=11)
    c.line(*r0, *r1, stroke="#d9c7a8", sw=6.5)
    for p, s in ((r0, -1), (r1, 1)):
        c.path("M%s,%s q%s,-4 %s,-18 q%s,6 %s,10" % (f(p[0]), f(p[1]), f(s * 12), f(s * 10), f(-s * 4),
                                                    f(-s * 12)), "#d9c7a8", stroke=OUT, sw=3)
    m = i(0, 0, zt + 8)
    c.circ(m[0], m[1] - 2, 8, R(c, [(0, "#fff0a0"), (1, "#e8a52a")]), stroke=OUT, sw=2.4)
    # đèn lồng hai bên
    for x in (-0.44, 0.44):
        a = i(x, 0.08, 196)
        c.line(a[0], a[1], a[0], a[1] + 12, stroke=OUT, sw=2)
        lx, ly = a[0], a[1] + 28
        c.ell(lx, ly, 13, 16, R(c, [(0, "#fff0a0"), (0.4, "#ff9a4a"), (1, "#c4283e")], 0.42, 0.4, 0.62), sw=3)
        c.rect(lx - 7, ly - 19, 14, 5, "#f2c14e", rx=2, sw=1.6)
        c.rect(lx - 7, ly + 14, 14, 5, "#f2c14e", rx=2, sw=1.6)
        c.line(lx, ly + 19, lx, ly + 32, stroke="#d6313f", sw=2.4)
    c.save(name)


def bed(name):
    c = obj_canvas(270, 230, 180)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 4, 120, 50, 0.26)
    wood = "#a96a3c"
    # đầu giường chạm (phía sau, x âm)
    bx(c, -0.5, -0.34, -0.42, 0.34, 0, 104, wood, sw=SWO, grain=2, seed=9)
    c.group(tf_ny(c, -0.42, 0.34, 0))
    W = 0.68 * 128
    c.path("M-1,-104 Q%s,-136 %s,-104 Z" % (f(W / 2), f(W + 1)), G(c, [(0, lt(wood, 0.15)), (1, dk(wood, 0.2))]),
           sw=3.6)
    c.circ(W / 2, -112, 6, "#f2c14e", stroke=OUT, sw=1.8)
    c.rect(10, -94, W - 20, 34, "none", rx=4, stroke=dk(wood, 0.45), sw=1.6, extra=op(0.8))
    c.rect(13, -91, W - 26, 28, "none", rx=3, stroke=lt(wood, 0.35), sw=1.2, extra=op(0.7))
    c.end()
    # khung giường + chân
    for lx, ly in ((0.44, 0.3), (0.44, -0.3)):
        bx(c, lx - 0.03, ly - 0.03, lx + 0.03, ly + 0.03, 0, 16, dk(wood, 0.2), sw=2.6, ao=False, bevel=False)
    bx(c, -0.42, -0.32, 0.46, 0.32, 12, 38, wood, sw=SWO, grain=2, seed=6)
    # đệm
    bx(c, -0.4, -0.29, 0.43, 0.29, 38, 54, "#f8f4ea", top="#ffffff", sw=3.4, ao=False)
    # gối
    c.group(tf_floor(c, -0.25, 0, 56))
    c.rect(-14, -30, 28, 60, G(c, [(0, "#ffffff"), (1, "#e6eef5")], 0, 0, 1, 1), rx=13, sw=3)
    c.rect(-8, -24, 16, 48, "none", rx=8, stroke="#a8c8e8", sw=1.4, extra=op(0.8))
    c.end()
    u = i(-0.25, 0, 62)
    c.ell(u[0] - 6, u[1] - 2, 10, 4, "#ffffff", stroke=None, extra=op(0.7))
    # chăn bông kẻ ô
    q = "#e8735a"
    bx(c, -0.1, -0.31, 0.45, 0.31, 40, 62, q, top=lt(q, 0.1), sw=3.6, ao=False)
    c.group(tf_floor(c, 0, 0, 62))
    for k in range(-2, 3):
        c.line(-10, k * 14, 55, k * 14, stroke="#fbe3b8", sw=2.4, extra=op(0.8))
    for k in range(0, 5):
        xx = 0 + k * 13
        c.line(xx, -37, xx, 37, stroke="#fbe3b8", sw=2.4, extra=op(0.8))
    for k in range(-2, 2):
        for j in range(4):
            c.circ(6.5 + j * 13, k * 14 + 7, 2, "#c4423e", stroke=None)
    c.rect(-12, -39, 8, 78, "#fbe3b8", stroke=None, extra=op(0.85))
    c.end()
    # chân giường thấp phía trước
    bx(c, 0.44, -0.34, 0.5, 0.34, 0, 50, wood, sw=SWO, grain=1, seed=10)
    c.save(name)


def signpost(name):
    c = C(220, 260, 110, 230)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 70, 16, 0.28)
    pc = "#8a5a34"
    for s in (-1, 1):
        x = cx + s * 72
        c.ell(x, cy - 2, 12, 5, "#3a1f0e", stroke=None, extra=op(0.2))
        c.rect(x - 6, cy - 214, 12, 212, G(c, [(0, lt(pc, 0.2)), (0.4, pc), (1, dk(pc, 0.35))], 0, 0, 1, 0), rx=3,
               sw=3.4)
    # mái nhỏ
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 100), f(cy - 210), f(cx - 84), f(cy - 228), f(cx + 84),
                                               f(cy - 228), f(cx + 100), f(cy - 210)),
           G(c, [(0, "#d65a48"), (1, "#a8322f")]), sw=3.6)
    for k in range(1, 12):
        x = cx - 92 + k * 15.3
        c.line(x, cy - 226, x + (x - cx) * 0.08, cy - 212, stroke="#7a2020", sw=1.6, extra=op(0.7))
    c.line(cx - 100, cy - 210, cx + 100, cy - 210, stroke="#f2d6a0", sw=2.4)
    # bảng ván (giữ vùng chữ trống)
    board = "#a8683d"
    c.rect(cx - 90, cy - 206, 180, 70, G(c, [(0, lt(board, 0.12)), (1, dk(board, 0.12))]), rx=10, sw=SWO)
    for yy in (-183, -160):
        c.line(cx - 86, cy + yy, cx + 86, cy + yy, stroke=dk(board, 0.35), sw=1.6, extra=op(0.6))
    rnd = random.Random(4)
    for yy in (-196, -172, -148):
        xa = cx + rnd.uniform(-80, -40)
        c.path("M%s,%s Q%s,%s %s,%s" % (f(xa), f(cy + yy), f(xa + 40), f(cy + yy + 2), f(xa + 90), f(cy + yy)), "none",
               stroke=dk(board, 0.3), sw=1, extra=op(0.4))
    c.rect(cx - 82, cy - 198, 164, 54, "none", rx=7, stroke=lt(board, 0.35), sw=2, extra=op(0.7))
    for x, y in ((-80, -196), (80, -196), (-80, -146), (80, -146)):
        c.circ(cx + x, cy + y, 2.6, "#e8c27a", stroke=OUT, sw=1)
    # bụi hoa dưới chân
    for s in (-1, 1):
        x = cx + s * 72
        for k, (dx, dy) in enumerate(((-10, -8), (8, -10), (0, -16))):
            leaf(c, x + dx, cy, (dx * 3), 18, 6, "#6cbf55", sw=1.6, vein=False)
        flower5(c, x + 6, cy - 18, 3.4, "#ffd34d", center="#f08a3c", sw=1)
        flower5(c, x - 8, cy - 14, 3.2, "#ff8fb1", sw=1)
    c.save(name)


# ================================================================ ĐỒ ĐẶC TRƯNG CHƯƠNG

def chapter_props():
    # --- Hà Nội: lồng chim tre trên giá gỗ
    c = C(140, 280, 70, 250)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 36, 13, 0.3)
    pc = "#7a4a2a"
    c.ell(cx, cy - 2, 26, 10, G(c, [(0, "#8a5530"), (1, "#4a2a16")]), sw=3)
    c.rect(cx - 5, cy - 168, 10, 166, G(c, [(0, lt(pc, 0.25)), (1, dk(pc, 0.35))], 0, 0, 1, 0), rx=4, sw=3)
    c.path("M%s,%s q24,-14 36,6" % (f(cx), f(cy - 166)), "none", stroke=OUT, sw=5)
    c.path("M%s,%s q24,-14 36,6" % (f(cx), f(cy - 166)), "none", stroke="#a8683d", sw=2.4)
    bx_, by_ = cx + 22, cy - 92
    c.line(bx_ + 14, cy - 160, bx_ + 14, by_ - 62, stroke=OUT, sw=2)
    bxc = bx_ + 14
    # đáy + bóng trong lồng
    c.ell(bxc, by_, 30, 9, "#8a5530", sw=3)
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Z" % (f(bxc - 28), f(by_), f(bxc), f(by_ - 76), f(bxc + 28), f(by_),
                                            f(bxc - 28), f(by_)), "#fff3d6", stroke=None, extra=op(0.35))
    # chim vàng
    c.ell(bxc - 2, by_ - 24, 11, 8.5, G(c, [(0, "#ffe27a"), (1, "#f0a830")]), stroke=OUT, sw=2)
    c.circ(bxc + 7, by_ - 31, 6, "#ffe27a", stroke=OUT, sw=2)
    c.path("M%s,%s l5,1 l-5,2 Z" % (f(bxc + 12), f(by_ - 32)), "#f08a3c", stroke=OUT, sw=1)
    c.circ(bxc + 8.5, by_ - 32.5, 1.4, OUT, stroke=None)
    c.path("M%s,%s q-6,-2 -10,4" % (f(bxc - 6), f(by_ - 26)), "none", stroke="#d08a20", sw=1.6)
    c.line(bxc - 14, by_ - 20, bxc + 14, by_ - 18, stroke="#8a5530", sw=2.4)
    # nan lồng
    for k in range(-3, 4):
        c.path("M%s,%s Q%s,%s %s,%s" % (f(bxc + k * 9), f(by_), f(bxc + k * 5), f(by_ - 56), f(bxc), f(by_ - 70)),
               "none", stroke="#c98a55", sw=2)
    c.path("M%s,%s Q%s,%s %s,%s" % (f(bxc - 28), f(by_), f(bxc), f(by_ - 76), f(bxc + 28), f(by_)), "none", stroke=OUT,
           sw=2.6)
    c.ell(bxc, by_ - 34, 22, 6, "none", stroke="#a8683d", sw=2)
    c.ell(bxc, by_, 30, 9, "none", stroke="#c98a55", sw=2)
    c.circ(bxc, by_ - 71, 4, "#e8b84a", stroke=OUT, sw=1.6)
    # khăn phủ đỏ một bên
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (f(bxc - 4), f(by_ - 70), f(bxc + 22), f(by_ - 56),
                                                        f(bxc + 30), f(by_ - 8), f(bxc + 22), f(by_ - 4), f(bxc + 16),
                                                        f(by_ - 50), f(bxc - 4), f(by_ - 70)), "#c4423e", stroke=OUT,
           sw=2)
    c.save("prop_bird_cage")

    # --- Hà Nội: bàn trà thấp + ấm chén
    c = obj_canvas(200, 160, 120)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 2, 84, 32, 0.3)
    for lx, ly in ((-0.26, 0.26), (0.26, -0.26), (0.26, 0.26)):
        bx(c, lx - 0.04, ly - 0.04, lx + 0.04, ly + 0.04, 0, 26, "#5a3a22", sw=3, ao=False, bevel=False)
    bx(c, -0.33, -0.33, 0.33, 0.33, 24, 36, "#8a5530", top="#a8683d", sw=SWO, grain=2, seed=5)
    # khay tre
    c.group(tf_floor(c, 0, 0, 36))
    c.rect(-30, -30, 60, 60, G(c, [(0, "#e8c27a"), (1, "#c9963e")], 0, 0, 1, 1), rx=6, sw=2.6)
    for k in range(-20, 21, 8):
        c.line(-26, k, 26, k, stroke="#a8742a", sw=1, extra=op(0.6))
    c.end()
    t = i(-0.06, 0.0, 36)
    c.ell(t[0], t[1] - 13, 16, 13, G(c, [(0, "#ffffff"), (1, "#c8d6e6")], 0, 0, 1, 1), sw=2.6)
    c.path("M%s,%s q4,-6 10,0" % (f(t[0] - 7), f(t[1] - 12)), "none", stroke="#3a6fb5", sw=1.6)
    c.path("M%s,%s q12,-2 16,-12" % (f(t[0] + 14), f(t[1] - 14)), "none", stroke=OUT, sw=3)
    c.path("M%s,%s q-12,-4 -12,6 q2,8 8,6" % (f(t[0] - 14), f(t[1] - 18)), "none", stroke=OUT, sw=2.4)
    c.ell(t[0], t[1] - 26, 8, 3, "#e6eef5", stroke=OUT, sw=1.8)
    c.circ(t[0], t[1] - 29, 2.6, "#3a6fb5", stroke=OUT, sw=1)
    for dx, dy in ((0.16, -0.12), (0.18, 0.08), (-0.02, 0.18)):
        u = i(dx, dy, 36)
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(u[0] - 6), f(u[1] - 9), f(u[0] + 6), f(u[1] - 9), f(u[0] + 4.5),
                                                   f(u[1]), f(u[0] - 4.5), f(u[1])), "#ffffff", stroke=OUT, sw=1.8)
        c.ell(u[0], u[1] - 9, 6, 2.2, "#c98a3a", stroke=OUT, sw=1.2)
        c.line(u[0] - 3, u[1] - 5, u[0] + 3, u[1] - 5, stroke="#3a6fb5", sw=1)
    c.save("prop_tea_table")

    # --- Hội An: cây đèn lồng nhiều màu
    c = obj_canvas(170, 300, 270)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 42, 15, 0.3)
    pc = "#6b4123"
    c.ell(cx, cy - 2, 28, 11, G(c, [(0, "#8a5530"), (1, "#4a2a16")]), sw=3)
    c.rect(cx - 5, cy - 224, 10, 222, G(c, [(0, lt(pc, 0.25)), (1, dk(pc, 0.35))], 0, 0, 1, 0), rx=4, sw=3)
    for y, hw in ((-210, 62), (-140, 52)):
        c.path("M%s,%s Q%s,%s %s,%s" % (f(cx - hw), f(cy + y + 6), f(cx), f(cy + y - 8), f(cx + hw), f(cy + y + 6)),
               "none", stroke=OUT, sw=5)
        c.path("M%s,%s Q%s,%s %s,%s" % (f(cx - hw), f(cy + y + 6), f(cx), f(cy + y - 8), f(cx + hw), f(cy + y + 6)),
               "none", stroke="#a8683d", sw=2.4)
    c.circ(cx, cy - 226, 5, "#e8b84a", stroke=OUT, sw=1.8)
    lan = [(-48, -168, "#e8414f", 0), (0, -184, "#ffb347", 1), (48, -168, "#ff6bb3", 0),
           (-38, -98, "#7bd35b", 1), (38, -98, "#4fc3f7", 0)]
    for x, y, col, shape in lan:
        lx, ly = cx + x, cy + y
        top_y = cy + (-206 if y < -150 else -136)
        c.line(lx, top_y, lx, ly - 22, stroke=OUT, sw=1.8)
        c.circ(lx, ly, 26, R(c, [(0, "#fff0a0", 0.4), (1, col, 0)]), stroke=None)
        if shape == 0:
            d = "M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (f(lx - 8), f(ly - 18), f(lx - 26), f(ly), f(lx - 8),
                                                     f(ly + 18), f(lx + 8), f(ly + 18), f(lx + 26), f(ly))
            d = "M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (f(lx - 8), f(ly - 18), f(lx - 26), f(ly), f(lx - 8),
                                                            f(ly + 18), f(lx + 8), f(ly + 18), f(lx + 26), f(ly),
                                                            f(lx + 8), f(ly - 18))
        else:
            d = "M%s,%s L%s,%s L%s,%s L%s,%s L%s,%s L%s,%s Z" % (
                f(lx - 8), f(ly - 18), f(lx + 8), f(ly - 18), f(lx + 18), f(ly), f(lx + 8), f(ly + 18), f(lx - 8),
                f(ly + 18), f(lx - 18), f(ly))
        c.path(d, R(c, [(0, "#fff6c0"), (0.45, lt(col, 0.2)), (1, dk(col, 0.25))], 0.42, 0.42, 0.65), sw=2.8)
        c.path("M%s,%s Q%s,%s %s,%s M%s,%s Q%s,%s %s,%s" % (
            f(lx - 3), f(ly - 17), f(lx - 10), f(ly), f(lx - 3), f(ly + 17), f(lx + 3), f(ly - 17), f(lx + 10), f(ly),
            f(lx + 3), f(ly + 17)), "none", stroke=dk(col, 0.35), sw=1.2, extra=op(0.6))
        c.rect(lx - 9, ly - 22, 18, 5, "#f3c84b", rx=2, sw=1.6)
        c.rect(lx - 9, ly + 17, 18, 5, "#f3c84b", rx=2, sw=1.6)
        c.line(lx, ly + 22, lx, ly + 34, stroke=col, sw=2.4)
    c.save("prop_lantern_tree")

    # --- Sài Gòn: xe Vespa cổ
    c = obj_canvas(240, 200, 160)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 100, 22, 0.3)
    body, cream = "#5fb8b0", "#fbecd2"
    for wx in (-60, 62):
        c.circ(cx + wx, cy - 24, 24, "#2e2f34", sw=4)
        c.circ(cx + wx, cy - 24, 13, G(c, [(0, "#f0f2f4"), (1, "#9aa1aa")]), sw=2.4)
        c.circ(cx + wx, cy - 24, 4, "#5b5f66", stroke=None)
        c.path("M%s,%s a20,20 0 0 1 14,-10" % (f(cx + wx - 18), f(cy - 30)), "none", stroke="#6b6f78", sw=2)
    # thân xe bầu
    d = "M-92,-34 Q-96,-76 -52,-84 Q-20,-86 -2,-62 L10,-44 Q30,-44 34,-34 L-30,-30 Q-60,-30 -92,-34 Z"
    c.group("translate(%s %s)" % (f(cx), f(cy)))
    c.path(d, G(c, [(0, lt(body, 0.3)), (0.5, body), (1, dk(body, 0.25))], 0, 0, 0.3, 1), sw=SWO)
    c.end()
    # chắn bùn + cổ trước
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (f(cx + 36), f(cy - 30), f(cx + 44), f(cy - 54), f(cx + 70),
                                                        f(cy - 54), f(cx + 86), f(cy - 34), f(cx + 62), f(cy - 44),
                                                        f(cx + 36), f(cy - 30)),
           G(c, [(0, lt(body, 0.25)), (1, dk(body, 0.2))]), sw=3.6)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx + 32), f(cy - 40), f(cx + 46), f(cy - 120), f(cx + 58),
                                               f(cy - 118), f(cx + 50), f(cy - 44)),
           G(c, [(0, lt(body, 0.2)), (1, dk(body, 0.2))], 0, 0, 1, 0), sw=3.6)
    # sàn để chân
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx - 4), f(cy - 44), f(cx + 34), f(cy - 44), f(cx + 34),
                                               f(cy - 36), f(cx - 2), f(cy - 36)), "#3a3c42", sw=2.4)
    # yên
    c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (f(cx - 70), f(cy - 86), f(cx - 52), f(cy - 102), f(cx - 8),
                                                        f(cy - 98), f(cx - 8), f(cy - 88), f(cx - 40), f(cy - 84),
                                                        f(cx - 70), f(cy - 86)), "#6b3f22", sw=3)
    c.path("M%s,%s q20,-8 50,-6" % (f(cx - 62), f(cy - 94)), "none", stroke="#a8683d", sw=1.6, extra=op(0.8))
    # tay lái + đèn + gương
    c.path("M%s,%s L%s,%s" % (f(cx + 30), f(cy - 124), f(cx + 72), f(cy - 128)), "none", stroke=OUT, sw=6)
    c.path("M%s,%s L%s,%s" % (f(cx + 30), f(cy - 124), f(cx + 72), f(cy - 128)), "none", stroke="#c9ced6", sw=3)
    c.circ(cx + 52, cy - 124, 9, G(c, [(0, "#fffbe0"), (1, "#f2d27a")]), sw=2.6)
    c.circ(cx + 50, cy - 126, 3, "#ffffff", stroke=None)
    c.line(cx + 36, cy - 126, cx + 32, cy - 146, stroke=OUT, sw=2.2)
    c.ell(cx + 31, cy - 150, 7, 5, "#c9ced6", stroke=OUT, sw=2)
    # sọc kem + logo tròn + giỏ trước
    c.path("M%s,%s Q%s,%s %s,%s" % (f(cx - 88), f(cy - 50), f(cx - 50), f(cy - 58), f(cx - 8), f(cy - 54)), "none",
           stroke=cream, sw=3)
    c.circ(cx - 50, cy - 66, 5, cream, stroke=OUT, sw=1.6)
    c.path("M%s,%s q-18,-8 -22,-30" % (f(cx - 80), f(cy - 76)), "none", stroke="#ffffff", sw=2.4, extra=op(0.4))
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(cx + 52), f(cy - 112), f(cx + 82), f(cy - 112), f(cx + 78),
                                               f(cy - 94), f(cx + 56), f(cy - 94)), "#e8c27a", sw=2.4)
    for k in range(1, 4):
        c.line(cx + 52 + k * 7.5, cy - 112, cx + 55 + k * 6, cy - 94, stroke="#a8742a", sw=1)
    c.circ(cx + 60, cy - 116, 5, "#ff6b8b", stroke=OUT, sw=1.4)
    c.circ(cx + 70, cy - 117, 4.5, "#ffd34d", stroke=OUT, sw=1.4)
    c.circ(cx + 78, cy - 114, 4, "#ffffff", stroke=OUT, sw=1.4)
    c.save("prop_scooter")

    # --- Sài Gòn: biển neon cà phê
    c = obj_canvas(170, 260, 230)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 36, 13, 0.3)
    c.ell(cx, cy - 2, 22, 9, "#3a3c42", sw=3)
    c.rect(cx - 5, cy - 122, 10, 120, G(c, [(0, "#9aa1aa"), (1, "#4a4d55")], 0, 0, 1, 0), rx=3, sw=3)
    c.rect(cx - 16, cy - 124, 32, 8, "#5b5f66", rx=2, sw=2.4)
    # quầng sáng neon
    c.rect(cx - 82, cy - 226, 164, 118, R(c, [(0, "#ff4fb3", 0.28), (1, "#ff4fb3", 0)]), rx=40, stroke=None)
    c.rect(cx - 70, cy - 214, 140, 96, G(c, [(0, "#3a3060"), (1, "#1e1a34")]), rx=16, sw=SWO)
    c.rect(cx - 66, cy - 210, 132, 8, "#ffffff", rx=4, stroke=None, extra=op(0.08))
    c.rect(cx - 60, cy - 204, 120, 76, "none", rx=12, stroke="#ff4fb3", sw=9, extra=op(0.3))
    c.rect(cx - 60, cy - 204, 120, 76, "none", rx=12, stroke="#ff7ccc", sw=4)
    c.rect(cx - 60, cy - 204, 120, 76, "none", rx=12, stroke="#ffe0f2", sw=1.4)
    # ly cà phê neon
    mx, my = cx - 8, cy - 150
    cup = "M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
        f(mx - 22), f(my - 22), f(mx + 22), f(my - 22), f(mx + 22), f(my + 8), f(mx), f(my + 8), f(mx), f(my + 8),
        f(mx - 22), f(my + 8), f(mx - 22), f(my - 22))
    handle = "M%s,%s q16,0 14,12 q-2,8 -14,6" % (f(mx + 22), f(my - 16))
    steam = "M%s,%s q-6,-8 0,-14 q6,-6 0,-12 M%s,%s q-6,-8 0,-14 q6,-6 0,-12" % (
        f(mx - 8), f(my - 28), f(mx + 8), f(my - 28))
    for col, sw_, a in (("#4ff0ff", 9, 0.3), ("#4ff0ff", 4, 1), ("#e0ffff", 1.4, 1)):
        c.path(cup, "none", stroke=col, sw=sw_, extra=op(a))
        c.path(handle, "none", stroke=col, sw=sw_, extra=op(a))
    for col, sw_, a in (("#ffe14f", 8, 0.3), ("#ffe14f", 3.5, 1), ("#fffbe0", 1.2, 1)):
        c.path(steam, "none", stroke=col, sw=sw_, extra=op(a))
    c.line(mx - 26, my + 14, mx + 26, my + 14, stroke="#4ff0ff", sw=3.5)
    # ngôi sao nhỏ
    for sx_, sy_ in ((cx + 44, cy - 190), (cx + 48, cy - 150), (cx - 48, cy - 190)):
        c.circ(sx_, sy_, 6, "#ffe14f", stroke=None, extra=op(0.3))
        c.circ(sx_, sy_, 3, "#fffbe0", stroke=None)
    for x in (-50, 50):
        c.circ(cx + x, cy - 206, 2.6, "#9aa1aa", stroke=OUT, sw=1)
    c.save("prop_neon")

    # --- Đà Lạt: lò sưởi gạch
    c = obj_canvas(220, 260, 200)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 2, 94, 32, 0.3)
    brick = "#b8604a"
    bx(c, -0.42, -0.2, 0.42, 0.2, 0, 128, brick, sw=SWO, bevel=False)
    c.group(tf_px(c, -0.42, 0.2, 0))
    W = 0.84 * 128
    for r_ in range(9):
        yy = -4 - r_ * 13.4
        c.line(0, yy, W, yy, stroke="#6e2e22", sw=1.5, extra=op(0.6))
        c.line(0, yy - 1.6, W, yy - 1.6, stroke="#e2907a", sw=0.9, extra=op(0.4))
        off = 0 if r_ % 2 == 0 else 13
        x = off + 26
        while x < W:
            c.line(x, yy, x, yy - 13.4, stroke="#6e2e22", sw=1.5, extra=op(0.6))
            x += 26
    # cửa lò vòm
    m = W / 2
    c.path("M%s,-6 L%s,-70 Q%s,-110 %s,-110 Q%s,-110 %s,-70 L%s,-6 Z" % (f(m - 42), f(m - 42), f(m - 42), f(m),
                                                                        f(m + 42), f(m + 42), f(m + 42)),
           "#d8c3a2", sw=3)
    c.path("M%s,-6 L%s,-68 Q%s,-100 %s,-100 Q%s,-100 %s,-68 L%s,-6 Z" % (f(m - 33), f(m - 33), f(m - 33), f(m),
                                                                        f(m + 33), f(m + 33), f(m + 33)),
           R(c, [(0, "#ffd27a"), (0.4, "#e8642a"), (1, "#2a1210")], 0.5, 0.9, 0.8), stroke=OUT, sw=2.4)
    c.path("M%s,-10 L%s,-20 M%s,-20 L%s,-10" % (f(m - 26), f(m + 24), f(m - 24), f(m + 26)), "none", stroke="#3a1f0e",
           sw=7)
    c.path("M%s,-10 L%s,-20 M%s,-20 L%s,-10" % (f(m - 26), f(m + 24), f(m - 24), f(m + 26)), "none", stroke="#8a5530",
           sw=4)
    for dx, h, col in ((-14, 46, "#ff7b3a"), (6, 62, "#ffb347"), (20, 38, "#ff7b3a"), (-2, 32, "#fff1a0"),
                       (12, 24, "#fff1a0")):
        c.path("M%s,-16 q-12,-%s 0,-%s q12,%s 0,%s Z" % (f(m + dx), f(h * 0.5), f(h), f(h * 0.5), f(h)), col,
               stroke=None)
    for k in range(7):
        a = math.pi + k * math.pi / 6
        c.circ(m + math.cos(a) * 40, -70 + math.sin(a) * 37, 2.6, "#a84a3a", stroke=None)
    c.end()
    # bệ gỗ trên lò
    bx(c, -0.5, -0.25, 0.5, 0.26, 128, 142, "#7a4a2e", top="#a8683d", sw=SWO, grain=2, seed=4)
    for x, col in ((-0.3, "#fff6e0"), (-0.22, "#fff6e0")):
        u = i(x, 0.02, 142)
        h = 26 if x < -0.25 else 18
        cyl(c, u[0], u[1], 4.5, 2, h, col, sw=2)
        c.path("M%s,%s q-3,-5 0,-10 q3,5 0,10 Z" % (f(u[0]), f(u[1] - h - 1)), "#ffb347", stroke=OUT, sw=1)
    u = i(0.22, 0.0, 142)
    cyl(c, u[0], u[1], 9, 4, 12, "#6fa8dc", sw=2.2)
    for ang in (-50, -20, 20, 50):
        leaf(c, u[0], u[1] - 12, ang, 18, 5, "#6cbf55", sw=1.4, vein=False)
    # bó củi bên cạnh
    for k in range(3):
        u = i(0.36 - k * 0.0, 0.32, 0)
        c.ell(u[0] - 8 + k * 9, u[1] - 6 - (k % 2) * 7, 6, 6, "#c98a55", stroke=OUT, sw=1.8)
        c.circ(u[0] - 8 + k * 9, u[1] - 6 - (k % 2) * 7, 2.6, "none", stroke="#8a5530", sw=1)
    c.save("prop_fireplace")

    # --- Đà Lạt: chậu dã quỳ vàng
    c = obj_canvas(140, 200, 170)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 48, 18, 0.3)
    pc = "#8a6a9e"
    heads = [(-30, -84), (26, -88), (0, -114), (-14, -140), (20, -128), (-40, -116)]
    for x, y in heads:
        c.path("M%s,%s Q%s,%s %s,%s" % (f(cx), f(cy - 50), f(cx + x * 0.3), f(cy + y * 0.6), f(cx + x),
                                        f(cy + y + 10)), "none", stroke=OUT, sw=5)
        c.path("M%s,%s Q%s,%s %s,%s" % (f(cx), f(cy - 50), f(cx + x * 0.3), f(cy + y * 0.6), f(cx + x),
                                        f(cy + y + 10)), "none", stroke="#4ea83a", sw=2.6)
    for ang, L, x0 in ((-60, 34, -6), (55, 34, 6), (-25, 40, -2), (25, 38, 2)):
        leaf(c, cx + x0, cy - 54, ang, L, 11, "#5aa94a")
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
        f(cx - 32), f(cy - 50), f(cx + 32), f(cy - 50), f(cx + 28), f(cy - 18), f(cx + 22), f(cy - 2), f(cx - 22),
        f(cy - 2), f(cx - 28), f(cy - 18), f(cx - 32), f(cy - 50)),
        G(c, [(0, lt(pc, 0.15)), (0.3, lt(pc, 0.3)), (0.6, pc), (1, dk(pc, 0.35))], 0, 0, 1, 0), sw=SWO)
    c.rect(cx - 35, cy - 58, 70, 12, G(c, [(0, lt(pc, 0.25)), (1, dk(pc, 0.15))]), rx=5, sw=SWO)
    c.path("M%s,%s q10,-6 20,0 q10,6 20,0" % (f(cx - 20), f(cy - 30)), "none", stroke="#f6e3bd", sw=2)
    c.line(cx - 22, cy - 44, cx - 20, cy - 10, stroke="#ffffff", sw=3, extra=op(0.3))
    for x, y in heads:
        px, py = cx + x, cy + y
        for k in range(10):
            a = k * math.pi / 5
            ex, ey = px + math.cos(a) * 9, py + math.sin(a) * 7.5
            c.ell(ex, ey, 6.5, 3.4, "#ffd34d" if k % 2 else "#ffc22a", stroke=dk("#e8a520", 0.2), sw=1.1,
                  extra='transform="rotate(%s %s %s)"' % (f(math.degrees(a)), f(ex), f(ey)))
        c.circ(px, py, 5.5, R(c, [(0, "#f0a030"), (1, "#a8601a")]), stroke=OUT, sw=1.6)
    c.save("prop_daquy")

    # --- Huế: cột son vẽ rồng
    c = obj_canvas(110, 380, 350)
    cx, cy = c.ax, c.ay
    soft_shadow(c, cx, cy + 2, 36, 13, 0.3)
    c.ell(cx, cy - 4, 32, 12, G(c, [(0, "#a39b8e"), (1, "#6e675e")]), sw=3.4)
    cyl(c, cx, cy - 8, 30, 11, 14, "#8e867a", sw=3.4)
    cyl(c, cx, cy - 22, 22, 8, 298, "#c42a3c", top="#d83a50", sw=SWO, top_draw=False)
    # rồng vàng uốn quanh cột
    d = "M%s,%s" % (f(cx - 18), f(cy - 40))
    for k in range(5):
        y0 = cy - 40 - k * 52
        d += " Q%s,%s %s,%s Q%s,%s %s,%s" % (f(cx + 26), f(y0 - 13), f(cx + 4), f(y0 - 26), f(cx - 26), f(y0 - 39),
                                              f(cx - 18), f(y0 - 52))
    c.path(d, "none", stroke=OUT, sw=10)
    c.path(d, "none", stroke="#f2c14e", sw=6)
    c.path(d, "none", stroke="#fff0b0", sw=1.6, extra=op(0.8))
    for k in range(10):
        y = cy - 52 - k * 26
        c.circ(cx + (8 if k % 2 else -8), y, 2, "#c9902a", stroke=None)
    # đầu rồng + ngọc
    hx, hy = cx - 4, cy - 300
    c.ell(hx, hy, 12, 9, "#f2c14e", stroke=OUT, sw=2.4)
    c.path("M%s,%s l-6,-10 l6,4 l4,-8 l2,8 Z" % (f(hx - 2), f(hy - 6)), "#f2c14e", stroke=OUT, sw=1.6)
    c.circ(hx + 4, hy - 2, 1.8, OUT, stroke=None)
    c.circ(hx + 18, hy + 6, 5, R(c, [(0, "#ffffff"), (1, "#ff8a3a")]), stroke=OUT, sw=1.6)
    # đầu cột
    cyl(c, cx, cy - 318, 28, 10, 14, "#e8b84a", top="#ffd970", sw=3.6)
    c.ell(cx, cy - 324, 20, 4, "none", stroke="#c9902a", sw=1.6)
    c.save("prop_red_pillar")

    # --- Huế: bình phong sơn son thếp vàng (4 tấm gấp khúc)
    c = obj_canvas(260, 240, 200)
    i = c.iso
    soft_shadow(c, c.ax, c.ay + 2, 116, 28, 0.28)
    gold = "#e8b84a"
    xs = [-0.62, -0.31, 0.0, 0.31, 0.62]
    ys = [0.0, 0.07, 0.0, 0.07, 0.0]
    for k in range(4):
        a0, a1 = (xs[k], ys[k]), (xs[k + 1], ys[k + 1])
        p = [i(a0[0], a0[1], 160), i(a1[0], a1[1], 160), i(a1[0], a1[1], 8), i(a0[0], a0[1], 8)]
        base_ = "#b8283a" if k % 2 == 0 else "#9a1f30"
        c.poly(p, G(c, [(0, lt(base_, 0.12)), (1, dk(base_, 0.12))]), sw=3.6)
        # khung vàng trong
        q = [lerp(lerp(p[0], p[1], 0.1), lerp(p[3], p[2], 0.1), 0.06), lerp(lerp(p[0], p[1], 0.9), lerp(p[3], p[2], 0.9), 0.06),
             lerp(lerp(p[0], p[1], 0.9), lerp(p[3], p[2], 0.9), 0.94), lerp(lerp(p[0], p[1], 0.1), lerp(p[3], p[2], 0.1), 0.94)]
        c.poly(q, "none", stroke=gold, sw=2.4)
        # mây + hoa văn
        cxp = lerp(lerp(p[0], p[1], 0.5), lerp(p[3], p[2], 0.5), 0.38)
        c.circ(cxp[0], cxp[1], 12, "none", stroke=gold, sw=2.4)
        c.circ(cxp[0], cxp[1], 5, gold, stroke=None)
        for s in (-1, 1):
            c.path("M%s,%s q%s,-8 %s,0 q%s,8 %s,0" % (f(cxp[0] - 9), f(cxp[1] + 40 + s * 18), f(4.5), f(9), f(4.5),
                                                     f(9)), "none", stroke=gold, sw=2)
        bl = lerp(lerp(p[0], p[1], 0.5), lerp(p[3], p[2], 0.5), 0.8)
        c.path("M%s,%s q8,-12 16,0 q-8,12 -16,0 Z" % (f(bl[0] - 8), f(bl[1])), gold, stroke=OUT, sw=1.4)
        c.line(*lerp(p[0], p[1], 0.04), *lerp(p[3], p[2], 0.04), stroke=lt(base_, 0.35), sw=1.4, extra=op(0.7))
    # mép trên vàng + chân
    for k in range(4):
        a0, a1 = (xs[k], ys[k]), (xs[k + 1], ys[k + 1])
        c.line(*i(a0[0], a0[1], 162), *i(a1[0], a1[1], 162), stroke=OUT, sw=7)
        c.line(*i(a0[0], a0[1], 162), *i(a1[0], a1[1], 162), stroke=gold, sw=3.6)
    for k in range(5):
        p = i(xs[k], ys[k], 0)
        c.rect(p[0] - 5, p[1] - 12, 10, 14, gold, rx=2, sw=2)
        t = i(xs[k], ys[k], 166)
        c.circ(t[0], t[1], 5, gold, stroke=OUT, sw=2)
    c.save("prop_royal_screen")


# ================================================================ chạy

def run(base):
    global B, C, lt, dk, mix, f, HW, HH, WALL_H
    B = base
    C, lt, dk, mix, f = base.C, base.lt, base.dk, base.mix, base.f
    HW, HH = base.HW, base.HH
    WALL_H = float(getattr(base, "WALL_H", 360.0))

    floor_wood("floor_wood_a", "#efbf86", 1)
    floor_wood("floor_wood_b", "#efbf86", 2)
    floor_wood("floor_out_a", "#d9a46c", 3, outdoor=True)
    floor_wood("floor_out_b", "#d9a46c", 4, outdoor=True)
    carpet_runner("carpet_runner")
    floor_stone("floor_stone_a", "#cdc5b6", 3)
    floor_stone("floor_stone_b", "#cdc5b6", 4)
    floor_tile_vip("floor_vip")
    for k in range(3):
        grass("grass_%d" % k, k)
    dirt("dirt_a", 5)
    dirt("dirt_b", 6)
    floor_edge("edge_wood_l", "l", "wood")
    floor_edge("edge_wood_r", "r", "wood")
    floor_edge("edge_stone_l", "l", "stone")
    floor_edge("edge_stone_r", "r", "stone")
    for kind in ("a", "b"):
        for side in ("l", "r"):
            wall("wall_%s_%s" % (kind, side), side, kind)
            wall("wall_%s_%s_window" % (kind, side), side, kind, "window")
            wall("wall_%s_%s_door" % (kind, side), side, kind, "door")
    wall_post("wall_post")
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
    chapter_props()
