# -*- coding: utf-8 -*-
"""Bộ icon v2 cho Quán Trọ Idle: món ăn + icon giao diện, phong cách game mobile cao cấp.

Được gọi từ gen_sprites.main() qua run(base). Ghi đè sprite cùng tên, giữ nguyên kích thước / neo / thư mục.
Chỉ dùng path/shape, linear/radial gradient, opacity, transform đơn giản (ThorVG).
"""
import math

O = "#5a341f"          # viền chung
GOLD, GOLD_D = "#ffc93c", "#e89b16"
CREAM, WOOD = "#fbecd2", "#c98a55"
WHITE = "#ffffff"

C = lt = dk = mix = f = None
OUT_DIR = UI_DIR = SKIN = None
icon_canvas = None


# ================================================================ helpers

def lga(c, stops, x1=0, y1=0, x2=0, y2=1):
    """Linear gradient có opacity: stops = [(offset, color, alpha)]."""
    c.n += 1
    gid = "g%d" % c.n
    s = "".join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>' % (f(o), col, f(a)) for o, col, a in stops)
    c.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                  % (gid, f(x1), f(y1), f(x2), f(y2), s))
    return "url(#%s)" % gid


def R(c, col, l=0.45, d=0.3, cx=0.35, cy=0.3, r=0.8):
    """Radial: sáng góc trên-trái, tối dưới-phải."""
    return c.rg([(0, lt(col, l), 1), (0.5, col, 1), (1, dk(col, d), 1)], cx, cy, r)


def LV(c, col, l=0.3, d=0.25):
    return c.lg(lt(col, l), dk(col, d))


def LH(c, col, l=0.3, d=0.3):
    return c.lg(lt(col, l), dk(col, d), 0, 0, 1, 0, mid=col)


def op(a):
    return 'opacity="%s"' % f(a)


def tr(x, y, ang=0, s=1):
    t = "translate(%s %s)" % (f(x), f(y))
    if ang:
        t += " rotate(%s)" % f(ang)
    if s != 1:
        t += " scale(%s)" % f(s)
    return t


def gloss(c, x, y, rx, ry, rot=-30, a=0.55):
    c.ell(x, y, rx, ry, WHITE, stroke=None,
          extra='opacity="%s" transform="rotate(%s %s %s)"' % (f(a), f(rot), f(x), f(y)))


def gl_line(c, d, w=4, a=0.6, col=WHITE):
    c.path(d, "none", stroke=col, sw=w, extra='stroke-opacity="%s"' % f(a))


def spark(c, x, y, r, col=WHITE, a=1.0):
    k = r * 0.2
    p = [(x, y - r), (x + k, y - k), (x + r, y), (x + k, y + k), (x, y + r), (x - k, y + k), (x - r, y), (x - k, y - k)]
    d = "M%s,%s " % (f(p[0][0]), f(p[0][1]))
    for i in range(1, 9):
        q = p[i % 8]
        d += "L%s,%s " % (f(q[0]), f(q[1]))
    c.path(d + "Z", col, stroke=None, extra=op(a))


def steam(c, xs, y, h=30, a=0.85, w=4.5):
    for i, x in enumerate(xs):
        s = 1 if i % 2 == 0 else -1
        hh = h * (1 if i % 2 == 0 else 0.8)
        d = "M%s,%s q%s,%s 0,%s q%s,%s 0,%s" % (f(x), f(y), f(-8 * s), f(-hh * 0.25), f(-hh * 0.5),
                                                  f(8 * s), f(-hh * 0.25), f(-hh * 0.5))
        c.path(d, "none", stroke="#b98a64", sw=w + 3.5, extra='stroke-opacity="%s"' % f(a * 0.28))
        c.path(d, "none", stroke=WHITE, sw=w, extra='stroke-opacity="%s"' % f(a))


def star_d(cx, cy, ro, ri, n=5, rot=-90):
    d = ""
    for k in range(n * 2):
        r = ro if k % 2 == 0 else ri
        a = math.radians(rot) + k * math.pi / n
        d += ("M" if k == 0 else "L") + "%s,%s " % (f(cx + math.cos(a) * r), f(cy + math.sin(a) * r))
    return d + "Z"


def star_pts(cx, cy, ro, ri, n=5, rot=-90):
    out = []
    for k in range(n * 2):
        r = ro if k % 2 == 0 else ri
        a = math.radians(rot) + k * math.pi / n
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return out


def faceted_star(c, cx, cy, ro, ri, col, sw=5, depth=0):
    """Ngôi sao kiểu game: có đế nổi khối, mặt vát sáng/tối, vệt bóng."""
    if depth:
        c.path(star_d(cx, cy + depth, ro, ri), dk(col, 0.4), sw=sw)
    c.path(star_d(cx, cy, ro, ri), R(c, col, 0.5, 0.15, 0.4, 0.35, 0.7), sw=sw)
    p = star_pts(cx, cy, ro * 0.98, ri * 0.98)
    for k in range(10):
        a, b = p[k], p[(k + 1) % 10]
        ang = math.atan2((a[1] + b[1]) / 2 - cy, (a[0] + b[0]) / 2 - cx)
        lit = math.cos(ang - math.radians(-135))  # ánh sáng trên-trái
        col2 = WHITE if lit > 0 else "#7a3a00"
        al = 0.32 * abs(lit) if lit > 0 else 0.22 * abs(lit)
        c.poly([(cx, cy), a, b], col2, stroke=None, extra=op(al))
    c.path(star_d(cx, cy, ro, ri), "none", sw=sw)
    c.circ(cx, cy, ro * 0.1, WHITE, stroke=None, extra=op(0.35))


def chunky_circle(c, x, y, r, col, sw=5, depth=6, l=0.45, d=0.25):
    c.circ(x, y + depth, r, dk(col, 0.38), sw=sw)
    c.circ(x, y, r, R(c, col, l, d, 0.38, 0.3, 0.8), sw=sw)
    c.path("M%s,%s A%s,%s 0 0 1 %s,%s" % (f(x - r * 0.72), f(y - r * 0.2), f(r * 0.76), f(r * 0.76), f(x + r * 0.15),
                                         f(y - r * 0.74)), "none", stroke=WHITE, sw=r * 0.12,
           extra='stroke-opacity="0.55"')


def drop_shadow(c, x, y, rx, ry, a=0.28):
    c.shadow(x, y, rx, ry, a)


def extrude_path(c, d, col, depth=6, sw=5):
    c.group("translate(0 %s)" % f(depth))
    c.path(d, dk(col, 0.4), sw=sw)
    c.end()


# ---------------------------------------------------------------- món: thành phần

def leaf(c, x, y, L, W, ang, col="#5fb84a", sw=2.2, vein=True):
    c.group(tr(x, y, ang))
    c.path("M0,0 Q%s,%s %s,0 Q%s,%s 0,0 Z" % (f(L * 0.4), f(-W), f(L), f(L * 0.6), f(W)),
           c.lg(lt(col, 0.35), dk(col, 0.15)), stroke=dk(col, 0.5), sw=sw)
    if vein:
        c.path("M%s,0 Q%s,%s %s,0" % (f(L * 0.08), f(L * 0.45), f(-W * 0.15), f(L * 0.82)), "none",
               stroke=lt(col, 0.5), sw=1.4)
    c.end()


def herb(c, x, y, s=1.0, col="#4fae3c", ang=0):
    """Nhánh rau mùi: 3 lá tròn."""
    c.group(tr(x, y, ang, s))
    c.path("M0,6 L0,-2", "none", stroke=dk(col, 0.3), sw=1.8)
    for dx, dy, r in [(-5, -4, 5), (5, -4, 5), (0, -9, 5.5)]:
        c.circ(dx, dy, r, R(c, col, 0.35, 0.15), stroke=dk(col, 0.45), sw=1.6)
    c.end()


def scallion(c, x, y, r=3.2):
    c.circ(x, y, r, "#e7f7c8", stroke="#3f9a3a", sw=1.8)


def chili(c, x, y, r=3.4):
    c.circ(x, y, r, "#e8322c", stroke="#9a1c16", sw=1.6)
    c.circ(x, y, r * 0.45, "#ffb08a", stroke=None)


def lime(c, x, y, r=11, ang=0):
    c.group(tr(x, y, ang))
    c.path("M%s,0 A%s,%s 0 0 0 %s,0 Z" % (f(-r), f(r), f(r), f(r)), "#4e9e2e", stroke=O, sw=2.6)
    c.path("M%s,0 A%s,%s 0 0 0 %s,0 Z" % (f(-r + 2.6), f(r - 2.6), f(r - 2.6), f(r - 2.6)),
           c.rg([(0, "#f4ffc8", 1), (1, "#b6e05a", 1)], 0.5, 0, 0.9), stroke=None)
    for k in (1, 2, 3):
        a = math.pi * k / 4
        c.line(0, 0.5, math.cos(a) * (r - 3.5), math.sin(a) * (r - 3.5), stroke="#e9ffb8", sw=1.3)
    c.path("M%s,0 L%s,0" % (f(-r), f(r)), "none", stroke=O, sw=2.6)
    c.end()


def shrimp(c, x, y, s=1.0, ang=0):
    c.group(tr(x, y, ang, s))
    d = "M-11,3 Q-13,-11 1,-11 Q13,-10 12,2 Q11,7 5,6 Q6,-3 0,-3 Q-5,-3 -4,5 Z"
    c.path(d, c.rg([(0, "#ffd2b8", 1), (0.6, "#ff8a5a", 1), (1, "#e0502a", 1)], 0.4, 0.3, 0.8), stroke="#9c3a18",
           sw=2)
    for a in (-60, -20, 20):
        r1, r2 = 4, 10
        ra = math.radians(a - 90)
        c.line(math.cos(ra) * r1 + 0.5, math.sin(ra) * r1 - 2, math.cos(ra) * r2 + 0.5, math.sin(ra) * r2 - 2,
               stroke="#fff1e6", sw=1.5)
    c.path("M-4,5 L-9,10 L-1,9 Z", "#ff7a4a", stroke="#9c3a18", sw=1.6)
    c.end()


def beef(c, x, y, rx=10, ry=5, ang=0, col="#c9705a"):
    c.group(tr(x, y, ang))
    c.ell(0, 0, rx, ry, c.rg([(0, lt(col, 0.3), 1), (0.7, col, 1), (1, dk(col, 0.3), 1)], 0.4, 0.35, 0.7),
          stroke=dk(col, 0.5), sw=1.8)
    c.path("M%s,%s Q0,%s %s,%s" % (f(-rx * 0.6), f(-ry * 0.1), f(ry * 0.4), f(rx * 0.6), f(-ry * 0.2)), "none",
           stroke=lt(col, 0.5), sw=1.4)
    c.end()


def egg_half(c, x, y, r=6):
    c.ell(x, y, r, r * 0.8, "#fffdf4", stroke="#b89a6a", sw=1.6)
    c.circ(x + 0.5, y + 0.3, r * 0.5, c.rg([(0, "#ffe680", 1), (1, "#f0a020", 1)]), stroke=None)


def noodles(c, x0, x1, y, rows=3, col="#fffaf0", amp=4, step=10, gap=4.5, w=3.2):
    for r in range(rows):
        yy = y + r * gap
        d = "M%s,%s" % (f(x0), f(yy))
        x = x0
        k = 0
        while x < x1:
            k += 1
            d += " q%s,%s %s,0" % (f(step / 2), f(-amp if (k + r) % 2 else amp), f(step))
            x += step
        c.path(d, "none", stroke=dk(col, 0.28), sw=w + 1.8)
        c.path(d, "none", stroke=col, sw=w)


def chopsticks(c, x1=118, y1=18, x2=52, y2=56, col="#c98a55"):
    for dx, dy in ((0, 0), (8, 6)):
        c.line(x1 + dx, y1 + dy, x2 + dx, y2 + dy, stroke=O, sw=6.5)
        c.line(x1 + dx, y1 + dy, x2 + dx, y2 + dy, stroke=col, sw=3.6)
        c.line(x1 + dx - 0.8, y1 + dy - 1, x1 + dx - (x1 - x2) * 0.25, y1 + dy - (y1 - y2) * 0.25 - 1,
               stroke=lt(col, 0.5), sw=1.2)


def bowl(c, body="#ffffff", band="#3d7fc4", soup="#f2c27a", cx=64, ty=60, rx=54, ry=17, by=112, sw=4.5,
         inner=None, shadow=True, band2=True):
    """Bát gốm: thân, chân, viền men, nước dùng. Trả về (cx, cy_soup, rx_soup, ry_soup)."""
    if shadow:
        c.shadow(cx, by + 3, rx * 0.82, 6, 0.3)
    fw = rx * 0.42
    c.path("M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Z" % (f(cx - fw), f(by - 8), f(cx - fw * 0.9), f(by + 1.5), f(cx),
           f(by + 4), f(cx + fw * 0.9), f(by + 1.5), f(cx + fw), f(by - 8)), c.lg(dk(body, 0.12), dk(body, 0.3)),
           sw=sw * 0.8)
    d = "M%s,%s C%s,%s %s,%s %s,%s C%s,%s %s,%s %s,%s Z" % (
        f(cx - rx), f(ty), f(cx - rx), f(ty + (by - ty) * 0.62), f(cx - rx * 0.5), f(by - 2), f(cx), f(by - 2),
        f(cx + rx * 0.5), f(by - 2), f(cx + rx), f(ty + (by - ty) * 0.62), f(cx + rx), f(ty))
    c.path(d, c.lg(lt(body, 0.35), dk(body, 0.3), 0, 0, 1, 0, mid=body), sw=sw)
    c.path(d, lga(c, [(0, "#000000", 0), (0.55, "#000000", 0), (1, "#3a1a08", 0.22)]), stroke=None)
    if band:
        h = (by - ty)
        for yy, w in ([(ty + h * 0.2, 4.5)] + ([(ty + h * 0.2 + 7, 1.8)] if band2 else [])):
            k = (yy - ty) / h
            rxb = rx * (1 - 0.18 * k * k * 3.2) if k > 0.1 else rx - 1
            rxb = min(rxb, rx - 2.5 - k * 10)
            c.path("M%s,%s A%s,%s 0 0 0 %s,%s" % (f(cx - rxb), f(yy), f(rxb), f(ry * 0.95), f(cx + rxb), f(yy)),
                   "none", stroke=band, sw=w)
    gl_line(c, "M%s,%s Q%s,%s %s,%s" % (f(cx - rx + 8), f(ty + 14), f(cx - rx + 10), f(ty + (by - ty) * 0.62),
                                        f(cx - rx * 0.45), f(by - 9)), w=5, a=0.5)
    c.ell(cx, ty, rx, ry, c.lg(lt(body, 0.4), body), sw=sw)
    inner = inner or dk(body, 0.14)
    c.ell(cx, ty + 1, rx - 5, ry - 3.6, c.lg(dk(inner, 0.12), inner), stroke=None)
    srx, sry, scy = rx - 7.5, ry - 6, ty + 3
    if soup:
        c.ell(cx, scy, srx, sry, c.rg([(0, lt(soup, 0.35), 1), (0.6, soup, 1), (1, dk(soup, 0.18), 1)],
                                       0.4, 0.4, 0.7), stroke=dk(soup, 0.35), sw=1.6)
    gl_line(c, "M%s,%s A%s,%s 0 0 0 %s,%s" % (f(cx - rx + 5), f(ty + 5), f(rx - 4), f(ry - 2), f(cx - rx * 0.25),
                                              f(ty + ry - 1.5)), w=2.6, a=0.75)
    return cx, scy, srx, sry


def plate(c, cx=64, cy=88, rx=58, ry=22, col="#ffffff", band=None, sw=4.5, depth=5, shadow=True):
    if shadow:
        c.shadow(cx, cy + ry * 0.5 + 4, rx * 0.86, 7, 0.26)
    c.ell(cx, cy + depth, rx, ry, dk(col, 0.25), sw=sw)
    c.ell(cx, cy, rx, ry, c.rg([(0, WHITE, 1), (0.6, col, 1), (1, dk(col, 0.1), 1)], 0.4, 0.3, 0.75), sw=sw)
    c.ell(cx, cy + 1.5, rx * 0.72, ry * 0.68, c.lg(dk(col, 0.12), lt(col, 0.3)), stroke=dk(col, 0.18), sw=1.4)
    if band:
        c.ell(cx, cy, rx * 0.87, ry * 0.85, "none", stroke=band, sw=2.4)
    gl_line(c, "M%s,%s A%s,%s 0 0 1 %s,%s" % (f(cx - rx + 6), f(cy - 2), f(rx - 5), f(ry - 4), f(cx - rx * 0.3),
                                              f(cy - ry + 3.5)), w=2.6, a=0.8)


def dip_bowl(c, x, y, r=13, sauce="#e8a050", band="#3d7fc4"):
    bowl(c, WHITE, band, sauce, cx=x, ty=y, rx=r, ry=r * 0.38, by=y + r * 0.85, sw=3, shadow=False, band2=False)


def rice_mound(c, x, y, rx, ry, col="#fffdf6"):
    d = "M%s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Q%s,%s %s,%s Z" % (
        f(x - rx), f(y), f(x - rx), f(y - ry * 0.8), f(x - rx * 0.5), f(y - ry), f(x), f(y - ry * 1.12),
        f(x + rx * 0.55), f(y - ry), f(x + rx), f(y - ry * 0.75), f(x + rx), f(y), f(x), f(y + ry * 0.4),
        f(x - rx), f(y))
    c.path(d, c.rg([(0, WHITE, 1), (0.65, col, 1), (1, dk(col, 0.14), 1)], 0.4, 0.3, 0.8), sw=3.2)
    for i in range(14):
        a = i * 2.4
        rr = (i % 5) / 5.0
        gx = x + math.cos(a) * rx * 0.75 * rr
        gy = y - ry * 0.45 + math.sin(a) * ry * 0.5 * rr
        c.ell(gx, gy, 2.6, 1.5, WHITE, stroke=dk(col, 0.16), sw=0.9,
              extra='transform="rotate(%d %s %s)"' % ((i * 37) % 180, f(gx), f(gy)))


def glass_body(top, bot, xt, xb, cx=64):
    return "M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s L%s,%s Z" % (
        f(cx - xt), f(top), f(cx - xb), f(bot - 6), f(cx - xb + 1), f(bot), f(cx - xb + 7), f(bot),
        f(cx + xb - 7), f(bot), f(cx + xb - 1), f(bot), f(cx + xb), f(bot - 6), f(cx + xt), f(top))


def gx(y, top, bot, xt, xb, cx=64):
    t = (y - top) / float(bot - top)
    w = xt + (xb - xt) * t
    return cx - w, cx + w


def glass_layer(c, top, bot, xt, xb, y0, y1, fill, inset=2.5):
    a0, b0 = gx(y0, top, bot, xt, xb)
    a1, b1 = gx(min(y1, bot - 3), top, bot, xt, xb)
    if y1 >= bot - 3:
        d = "M%s,%s L%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s Z" % (
            f(a0 + inset), f(y0), f(a1 + inset), f(bot - 7), f(a1 + inset), f(bot - inset), f(a1 + 8), f(bot - inset),
            f(b1 - 8), f(bot - inset), f(b1 - inset), f(bot - inset), f(b1 - inset), f(bot - 7))
        d += " L%s,%s Z" % (f(b0 - inset), f(y0))
        d = d.replace(" Z L", " L", 1)
    else:
        d = "M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(a0 + inset), f(y0), f(a1 + inset), f(y1), f(b1 - inset), f(y1),
                                              f(b0 - inset), f(y0))
    c.path(d, fill, stroke=None)


def ice(c, x, y, s, ang):
    c.group(tr(x, y, ang))
    c.rect(-s / 2, -s / 2, s, s, c.lg("#ffffff", "#cdeefa"), rx=s * 0.22, stroke="#8cc8e0", sw=1.8, extra=op(0.9))
    c.path("M%s,%s L%s,%s" % (f(-s / 2 + 3), f(-s / 2 + 4), f(s / 2 - 4), f(-s / 2 + 3)), "none", stroke=WHITE,
           sw=2)
    c.end()


def straw(c, x1, y1, x2, y2, col="#e8414f", col2=WHITE):
    c.line(x1, y1, x2, y2, stroke=O, sw=8.5)
    c.line(x1, y1, x2, y2, stroke=col2, sw=5)
    n = 5
    for k in range(n):
        t0, t1 = k / float(n), (k + 0.5) / float(n)
        c.line(x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0, x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1, stroke=col, sw=5)


# ================================================================ MÓN ĂN (128x128, neo giữa)

def dishes():
    # ---------------- Trà đá
    c = icon_canvas()
    top, bot, xt, xb = 22, 116, 31, 23
    c.shadow(64, 118, 34, 6, 0.3)
    c.path(glass_body(top, bot, xt, xb), "#ffffff", stroke=None, extra=op(0.35))
    glass_layer(c, top, bot, xt, xb, 38, bot, c.lg("#f9b24a", "#b55a12"))
    glass_layer(c, top, bot, xt, xb, 38, bot, lga(c, [(0, "#ffffff", 0.25), (0.4, "#ffffff", 0), (1, "#5a1a00", 0.3)],
                                                     0, 0, 1, 0))
    c.ell(64, 38, 28, 5, c.lg("#ffd28a", "#f5a640"), stroke="#b56a1a", sw=1.6)
    ice(c, 50, 36, 17, -14)
    ice(c, 73, 32, 16, 18)
    ice(c, 60, 56, 15, 8)
    ice(c, 74, 78, 13, -20)
    c.ell(64, 38, 28, 5, "none", stroke="#ffe7b0", sw=1.2, extra=op(0.7))
    leaf(c, 80, 30, 20, 6, -50, "#5fb84a")
    c.path(glass_body(top, bot, xt, xb), "none", sw=4.5)
    gl_line(c, "M41,32 L47,104", w=5, a=0.65)
    gl_line(c, "M85,30 L83,44", w=3, a=0.5)
    c.ell(64, top, xt, 5.5, "none", sw=4)
    c.ell(64, top + 0.5, xt - 3, 3.2, "none", stroke=WHITE, sw=1.5, extra=op(0.7))
    for x, y, r in [(80, 66, 2.6), (47, 82, 2.2), (78, 96, 2.8), (52, 64, 1.8)]:
        c.ell(x, y, r * 0.8, r, WHITE, stroke=None, extra=op(0.85))
    c.save("dish_tra_da")

    # ---------------- Nước mía
    c = icon_canvas()
    top, bot, xt, xb = 26, 116, 29, 22
    c.shadow(64, 118, 34, 6, 0.3)
    # khúc mía phía sau
    c.group(tr(34, 66, -14))
    c.rect(-7, -60, 14, 92, c.lg("#c7d94a", "#7a9a22", 0, 0, 1, 0, mid="#a8c23a"), rx=5, sw=3.5)
    for yy in (-36, -8, 20):
        c.rect(-8, yy, 16, 5, "#c4a33a", rx=2, stroke=O, sw=2)
    c.path("M-7,-60 L7,-60 L5,-54 L-5,-54 Z", "#f6f0c8", stroke=O, sw=2.5)
    c.end()
    c.path(glass_body(top, bot, xt, xb), "#ffffff", stroke=None, extra=op(0.35))
    glass_layer(c, top, bot, xt, xb, 42, bot, c.lg("#e8f27a", "#9ec22a"))
    glass_layer(c, top, bot, xt, xb, 42, bot, lga(c, [(0, "#ffffff", 0.3), (0.45, "#ffffff", 0), (1, "#2a4a00", 0.25)],
                                                     0, 0, 1, 0))
    glass_layer(c, top, bot, xt, xb, 34, 44, "#fbfadc")
    for x, y, r in [(44, 37, 4), (54, 35, 5), (66, 36, 4.5), (78, 35, 5), (86, 38, 3.5), (60, 40, 3)]:
        c.circ(x, y, r, "#fffff0", stroke="#d8d29a", sw=1.2)
    straw(c, 82, 10, 62, 92, "#3fae5a")
    c.path(glass_body(top, bot, xt, xb), "none", sw=4.5)
    gl_line(c, "M42,36 L48,104", w=5, a=0.65)
    c.ell(64, top, xt, 5.5, "none", sw=4)
    # tắc cắt đôi trên miệng ly
    c.circ(92, 28, 11, "#f08a1a", sw=3)
    c.circ(92, 28, 8, c.rg([(0, "#fff2a0", 1), (1, "#ffb43a", 1)]), stroke=None)
    for k in range(6):
        a = k * math.pi / 3
        c.line(92, 28, 92 + math.cos(a) * 7, 28 + math.sin(a) * 7, stroke="#fff6c8", sw=1.3)
    for x, y, r in [(80, 70, 2.6), (48, 86, 2.2), (77, 98, 2.6)]:
        c.ell(x, y, r * 0.8, r, WHITE, stroke=None, extra=op(0.85))
    c.save("dish_nuoc_mia")

    # ---------------- Bánh mì
    c = icon_canvas()
    c.shadow(64, 104, 54, 10, 0.28)
    c.group("rotate(-16 64 70)")
    c.path("M8,70 Q8,94 38,96 L92,96 Q122,94 120,70 Z", c.lg("#e9a24a", "#a85a1a"), sw=4.5)
    # nhân
    c.path("M10,72 q6,-12 13,-3 q6,-12 13,-3 q6,-12 13,-3 q6,-12 13,-3 q6,-12 13,-3 q6,-12 13,-3 q6,-12 13,-3 "
           "q5,-10 10,0 L118,76 L10,76 Z", c.lg("#9be06a", "#4e9e2e"), stroke="#2f6a1e", sw=2.2)
    for x in (24, 50, 76, 100):
        c.path("M%d,70 Q%d,58 %d,70 Z" % (x - 10, x, x + 10), c.lg("#f2a08a", "#c25a44"), stroke="#8a3424", sw=2)
    for x in (38, 64, 90):
        c.rect(x - 8, 60, 16, 7, "#d9f2a8", rx=3, stroke="#5a9a2e", sw=1.8)
    for x, y in [(30, 62), (70, 60), (106, 64)]:
        chili(c, x, y, 3.4)
    herb(c, 58, 62, 0.8)
    herb(c, 96, 60, 0.75)
    c.path("M6,64 Q6,36 40,34 L90,34 Q124,36 122,62 Q122,70 112,68 Q64,62 16,70 Q6,72 6,64 Z",
           c.rg([(0, "#ffe0a0", 1), (0.5, "#f2ad52", 1), (1, "#c06a1e", 1)], 0.4, 0.2, 0.9), sw=4.5)
    for k in range(4):
        x = 26 + k * 22
        c.path("M%d,52 Q%d,40 %d,40" % (x, x + 6, x + 16), "none", stroke="#c2701e", sw=6)
        c.path("M%d,51 Q%d,40 %d,40" % (x, x + 6, x + 16), "none", stroke="#ffe7b0", sw=3)
    gl_line(c, "M18,52 Q24,40 44,38", w=4, a=0.6)
    c.end()
    spark(c, 106, 30, 6, WHITE, 0.9)
    c.save("dish_banh_mi")

    # ---------------- Gỏi cuốn
    c = icon_canvas()
    plate(c, 64, 86, 58, 24, band="#7cc0e8")
    for k, (x, y) in enumerate([(52, 58), (66, 70), (80, 82)]):
        c.group(tr(x - 8, y, 72))
        c.rect(-13, -30, 26, 60, "#ffffff", rx=13, stroke=None)
        c.rect(-9, -26, 9, 52, "#e9f6dc", rx=4, stroke=None)
        c.path("M-9,-22 q4,6 0,12 q4,6 0,12 q4,6 0,12 q4,6 0,10", "none", stroke="#6cc04a", sw=5)
        shrimp(c, 4, -12, 0.75, 90)
        shrimp(c, 4, 10, 0.75, 90)
        c.rect(-13, -30, 26, 60, lga(c, [(0, "#ffffff", 0.75), (0.5, "#fffaf0", 0.35), (1, "#e8dcc0", 0.7)], 0, 0, 1, 0),
               rx=13, stroke=O, sw=3.2)
        gl_line(c, "M-8,-22 L-8,18", w=3, a=0.7)
        c.end()
    dip_bowl(c, 100, 98, 15, "#8a4a24")
    for x, y in [(96, 98), (103, 97), (100, 101)]:
        c.circ(x, y, 1.8, "#f2c27a", stroke=None)
    chili(c, 106, 99, 2)
    herb(c, 22, 92, 0.9)
    c.save("dish_goi_cuon")

    # ---------------- Xôi
    c = icon_canvas()
    c.shadow(64, 108, 56, 10, 0.26)
    c.path("M6,90 Q30,62 64,64 Q100,62 122,88 Q100,116 62,114 Q24,114 6,90 Z", c.lg("#7fcf5a", "#3f8a2a"), sw=4.5)
    for a in (-40, -15, 15, 40):
        c.path("M64,112 Q%s,%s %s,%s" % (f(64 + a * 0.6), 96, f(64 + a * 1.35), 72), "none", stroke="#a8e07a", sw=1.6)
    c.path("M8,90 Q64,98 120,88", "none", stroke="#2f6a1e", sw=2, extra=op(0.5))
    rice_mound(c, 64, 92, 40, 46, "#fbf6e8")
    c.path("M38,62 Q44,46 64,44 Q84,46 90,62 Q76,72 64,68 Q50,72 38,62 Z", c.rg([(0, "#fff2a0", 1), (1, "#f2c23a", 1)],
                                                                             0.4, 0.3, 0.8), stroke="#c48a1a", sw=2.4)
    for x, y, a in [(46, 58, 20), (56, 52, -30), (68, 50, 40), (80, 56, -10), (62, 60, 60), (72, 62, -40)]:
        c.path("M%d,%d q4,-4 8,0" % (x - 4, y), "none", stroke="#fff6c8", sw=2.2,
               extra='transform="rotate(%d %d %d)"' % (a, x, y))
    for x, y in [(50, 54), (64, 56), (76, 52), (58, 64), (84, 60), (44, 62)]:
        c.ell(x, y, 2.6, 1.6, "#d98a2b", stroke="#9a5214", sw=0.9, extra='transform="rotate(30 %d %d)"' % (x, y))
    for x, y in [(44, 74), (84, 72), (64, 80), (36, 84), (92, 86)]:
        scallion(c, x, y, 2.6)
    gloss(c, 44, 52, 9, 4, -40, 0.5)
    c.save("dish_xoi")

    # ---------------- Chè ba màu
    c = icon_canvas()
    top, bot, xt, xb = 34, 116, 30, 21
    c.shadow(64, 118, 32, 6, 0.3)
    c.path(glass_body(top, bot, xt, xb), "#ffffff", stroke=None, extra=op(0.4))
    glass_layer(c, top, bot, xt, xb, 92, bot, c.lg("#b8303a", "#6a1420"))
    for x, y in [(52, 100), (64, 104), (76, 98), (58, 109), (72, 108), (46, 106), (82, 104)]:
        c.ell(x, y, 3.6, 2.6, "#8a1e28", stroke=None)
        c.ell(x - 1, y - 1, 1.4, 0.9, "#e87070", stroke=None)
    glass_layer(c, top, bot, xt, xb, 70, 92, c.lg("#9be06a", "#3fa33a"))
    for k in range(3):
        y = 76 + k * 6
        c.path("M%d,%d q6,-4 12,0 q6,4 12,0 q6,-4 12,0 q6,4 12,0" % (38 + k * 2, y), "none", stroke="#d8f8a8", sw=2)
    glass_layer(c, top, bot, xt, xb, 50, 70, c.lg("#ffe680", "#f2b632"))
    glass_layer(c, top, bot, xt, xb, 46, 54, "#fff8ec")
    glass_layer(c, top, bot, xt, xb, 46, bot, lga(c, [(0, "#ffffff", 0.3), (0.35, "#ffffff", 0), (1, "#3a0a00", 0.25)],
                                                     0, 0, 1, 0))
    # đá bào + nước cốt dừa
    c.path("M30,40 Q30,14 52,16 Q60,6 74,12 Q98,12 98,40 Z", c.rg([(0, "#ffffff", 1), (1, "#d8eef8", 1)], 0.4, 0.3, 0.8),
           sw=3.5)
    for x, y in [(44, 26), (58, 20), (72, 24), (84, 30), (52, 34), (68, 34)]:
        c.rect(x - 3, y - 3, 6, 6, "#ffffff", rx=1.5, stroke="#a8d8ea", sw=1.2)
    c.path("M34,36 Q44,28 52,34 Q60,40 70,32 Q80,26 94,36", "none", stroke="#fff8e0", sw=4)
    c.path(glass_body(top, bot, xt, xb), "none", sw=4.5)
    gl_line(c, "M40,46 L46,106", w=5, a=0.6)
    c.ell(64, top, xt, 5.5, "none", sw=4)
    # thìa dài
    c.line(96, 10, 80, 40, stroke=O, sw=7)
    c.line(96, 10, 80, 40, stroke="#e8eef4", sw=3.5)
    c.save("dish_che")

    # ---------------- Cơm tấm
    c = icon_canvas()
    plate(c, 64, 84, 58, 26)
    rice_mound(c, 42, 86, 28, 30, "#fffdf6")
    for x, y in [(34, 66), (44, 62), (50, 70), (38, 74)]:
        scallion(c, x, y, 2.4)
    # sườn nướng
    d = "M58,80 Q52,62 70,56 Q92,48 112,62 Q118,76 104,84 Q84,92 66,90 Q58,88 58,80 Z"
    c.path(d, c.rg([(0, "#f0a060", 1), (0.5, "#c0602a", 1), (1, "#6a2a0e", 1)], 0.35, 0.3, 0.8), sw=3.8)
    for k in range(4):
        x = 70 + k * 10
        c.path("M%d,%d l12,%d" % (x - 4, 60 + k * 0, 22 - k * 2), "none", stroke="#4a1a06", sw=3.4, extra=op(0.75))
    c.path("M60,82 Q84,92 108,80", "none", stroke="#ffd8a8", sw=3, extra=op(0.6))
    gloss(c, 74, 62, 9, 3.4, -18, 0.6)
    gloss(c, 96, 60, 5, 2.4, -10, 0.5)
    # trứng ốp la
    c.path("M60,52 Q54,40 66,38 Q74,30 84,36 Q96,36 92,48 Q90,56 76,56 Q64,58 60,52 Z", "#fffdf4", stroke=O, sw=3)
    c.circ(75, 45, 7.5, c.rg([(0, "#fff0a0", 1), (0.6, "#ffb62a", 1), (1, "#e88a10", 1)]), stroke="#c06a10", sw=1.8)
    gloss(c, 72, 42, 2.6, 1.6, -30, 0.9)
    # dưa leo + cà chua
    for x, y in [(30, 102), (44, 106)]:
        c.ell(x, y, 8, 4.5, "#dff5b0", stroke="#3f8a2a", sw=2.2)
        c.ell(x, y, 4, 2, "#f6ffe0", stroke=None)
    c.path("M56,108 A9,6 0 0 0 74,108 Z", "#e8414f", stroke=O, sw=2.4)
    c.save("dish_com_tam")

    # ---------------- Bánh cuốn
    c = icon_canvas()
    plate(c, 64, 86, 58, 24, band="#7cc0e8")
    for k, (x, y) in enumerate([(52, 66), (82, 68), (40, 82), (72, 86)]):
        c.group(tr(x, y, 0))
        c.rect(-20, -10, 40, 20, c.lg("#ffffff", "#ece4d0"), rx=10, sw=3.2)
        c.rect(-14, -3, 28, 8, "#c9906a", rx=4, stroke=None, extra=op(0.35))
        c.path("M-12,-6 Q0,-10 12,-6", "none", stroke="#d4c4a0", sw=1.6)
        c.path("M-14,4 Q0,0 14,4", "none", stroke="#e6dac0", sw=1.4)
        gl_line(c, "M-14,-5 Q-4,-9 6,-8", w=2.4, a=0.85)
        c.end()
    for x, y in [(46, 58), (58, 62), (76, 60), (88, 64), (34, 76), (48, 78), (66, 80), (80, 82), (56, 72)]:
        c.ell(x, y, 2.8, 1.8, "#d98a2b", stroke="#8a4a14", sw=0.9)
    herb(c, 62, 64, 0.8)
    # chả lụa
    for x, y in [(98, 80), (106, 88)]:
        c.ell(x, y, 11, 6, "#f3d8b4", stroke=O, sw=2.6)
        c.ell(x, y, 8, 4, "#fbe8cc", stroke=None)
    dip_bowl(c, 26, 96, 14, "#f2b05a")
    chili(c, 24, 97, 2.2)
    c.ell(30, 98, 2.4, 1.4, "#ff9b3a", stroke=None)
    c.save("dish_banh_cuon")

    # ---------------- Phở
    c = icon_canvas()
    cx, cy, srx, sry = bowl(c, "#ffffff", "#3d7fc4", "#f3c76a", ty=62, by=114)
    noodles(c, 22, 100, 62, 2, "#fffaf0", amp=3, step=12, gap=5)
    beef(c, 46, 60, 12, 5, -8, "#cf7a66")
    beef(c, 70, 58, 12, 5, 10, "#c26a58")
    beef(c, 88, 64, 10, 4.5, -4, "#9a5a44")
    for x, y in [(36, 64), (58, 66), (80, 66)]:
        c.ell(x, y, 5, 2.6, "none", stroke="#f6f0e0", sw=1.6)
    for x, y in [(56, 56), (62, 64), (40, 58), (86, 58), (74, 66)]:
        scallion(c, x, y, 2.6)
    herb(c, 30, 60, 0.8)
    chili(c, 66, 52, 2.6)
    chili(c, 94, 60, 2.6)
    lime(c, 104, 52, 10, -30)
    chopsticks(c, 112, 12, 56, 52)
    steam(c, [44, 60, 76], 40, 30)
    c.save("dish_pho")

    # ---------------- Hủ tiếu
    c = icon_canvas()
    cx, cy, srx, sry = bowl(c, "#fff8ea", "#3fa36a", "#f4e0a6", ty=62, by=114)
    noodles(c, 22, 100, 62, 2, "#fdf6ff", amp=3, step=8, gap=4, w=2.4)
    shrimp(c, 44, 58, 0.85, -10)
    shrimp(c, 82, 60, 0.85, 20)
    egg_half(c, 64, 64, 6)
    for x, y, a in [(56, 56, -6), (96, 66, 8)]:
        c.ell(x, y, 8, 3.6, "#f4d0b4", stroke="#a8684a", sw=1.6, extra='transform="rotate(%d %d %d)"' % (a, x, y))
    for k in range(3):
        c.line(28 + k * 4, 66, 46 + k * 6, 60, stroke="#3f9a3a", sw=2.2)
    for x, y in [(70, 56), (34, 60), (90, 58)]:
        c.circ(x, y, 1.6, "#d98a2b", stroke=None)
    # thìa sứ
    c.path("M88,38 Q104,30 112,40 Q110,50 96,52 Q86,52 88,38 Z", c.lg("#ffffff", "#dfe8ee"), sw=3)
    c.line(96, 46, 118, 16, stroke=O, sw=8)
    c.line(96, 46, 118, 16, stroke="#f4f8fa", sw=4)
    steam(c, [40, 56, 72], 42, 30)
    c.save("dish_hu_tieu")

    # ---------------- Bún chả
    c = icon_canvas()
    c.shadow(64, 112, 56, 8, 0.26)
    c.ell(64, 92, 60, 22, "#a8743a", sw=4.5)
    c.ell(64, 88, 60, 22, c.rg([(0, "#f2d29a", 1), (1, "#c99a5a", 1)], 0.4, 0.35, 0.8), sw=4.5)
    for k in range(5):
        c.ell(64, 88, 52 - k * 9, 18 - k * 3.2, "none", stroke="#b9884a", sw=1.3, extra=op(0.7))
    # rau sống phía sau
    leaf(c, 18, 70, 30, 9, -30, "#6cc04a")
    leaf(c, 30, 62, 28, 8, -60, "#4fae3c")
    leaf(c, 40, 66, 22, 7, -95, "#7fd05a")
    # lá bún
    c.path("M14,88 Q14,72 40,70 Q66,72 66,88 Q40,102 14,88 Z", c.rg([(0, "#ffffff", 1), (1, "#ece4d4", 1)]), sw=3.4)
    for k in range(4):
        y = 76 + k * 5
        c.path("M%d,%d q5,-3 10,0 q5,3 10,0 q5,-3 10,0 q5,3 10,0" % (20 + k, y), "none", stroke="#e0d6c0", sw=1.6)
    # bát nước chấm + chả
    bcx, bcy, brx, bry = bowl(c, "#ffffff", "#3d7fc4", "#f0a85a", cx=88, ty=72, rx=30, ry=10, by=104, sw=4,
                              shadow=False, band2=False)
    for x, y in [(80, 68), (96, 72)]:
        c.ell(x, y, 8.5, 5.5, c.rg([(0, "#c0703a", 1), (1, "#5a2a0e", 1)], 0.4, 0.3, 0.8), stroke=O, sw=2)
        c.path("M%d,%d l6,-4 M%d,%d l6,-4" % (x - 5, y + 1, x - 1, y + 3), "none", stroke="#3a1606", sw=1.4)
        gloss(c, x - 3, y - 2, 2.6, 1.2, -20, 0.7)
    c.path("M86,74 l8,-5 l2,4 Z", "#ffb070", stroke="#c0602a", sw=1.2)
    c.path("M100,66 l8,2 l-3,4 Z", "#ffb070", stroke="#c0602a", sw=1.2)
    chili(c, 104, 74, 2.2)
    steam(c, [80, 96], 56, 22, 0.8, 3.6)
    c.save("dish_bun_cha")

    # ---------------- Nem rán
    c = icon_canvas()
    plate(c, 64, 86, 58, 24)
    leaf(c, 16, 84, 40, 13, -14, "#7fd05a")
    leaf(c, 60, 78, 44, 14, -20, "#6cc04a")

    def nem(x, y, ang, L=52):
        c.group(tr(x, y, ang))
        c.rect(-L / 2, -9, L, 18, c.lg("#ffd88a", "#c0701e"), rx=9, sw=3.2)
        for k in range(7):
            xx = -L / 2 + 6 + k * (L - 12) / 6.0
            c.circ(xx, -3 + (k % 2) * 4, 1.6 + (k % 3) * 0.4, "#ffecb8", stroke=None)
            c.circ(xx + 3, 3 - (k % 2) * 3, 1.2, "#a8501a", stroke=None, extra=op(0.7))
        gl_line(c, "M%s,-5 L%s,-5" % (f(-L / 2 + 6), f(L / 2 - 10)), w=2.6, a=0.6)
        c.end()
    nem(46, 86, -8)
    nem(76, 88, -8)
    nem(58, 72, -10)
    nem(84, 66, -10, 40)
    # đầu cắt lộ nhân
    c.ell(104, 63, 6, 8.5, "#d98a3a", stroke=O, sw=2.6)
    c.ell(104, 63, 4, 6, c.rg([(0, "#e8a070", 1), (1, "#8a4a2a", 1)]), stroke=None)
    dip_bowl(c, 104, 102, 14, "#f6c27a")
    c.ell(100, 103, 2.6, 1.4, "#ff9b3a", stroke=None)
    c.ell(108, 102, 2.2, 1.2, "#fff2c8", stroke=None)
    chili(c, 104, 104, 1.8)
    c.save("dish_nem_ran")

    # ---------------- Bánh bèo
    c = icon_canvas()
    c.shadow(64, 112, 58, 8, 0.26)
    c.ell(64, 90, 60, 24, "#7a4a2e", sw=4.5)
    c.ell(64, 86, 60, 24, c.rg([(0, "#d9a06a", 1), (1, "#a8683d", 1)], 0.4, 0.35, 0.8), sw=4.5)
    c.ell(64, 86, 52, 19, "none", stroke="#8a5530", sw=1.6, extra=op(0.6))
    for x, y in [(34, 72), (64, 66), (94, 72), (40, 96), (88, 96), (64, 88)]:
        c.ell(x, y + 3, 16, 7, "#4a8ac4", sw=2.6)
        c.ell(x, y, 16, 7, c.lg("#ffffff", "#e4eef6"), sw=2.6)
        c.ell(x, y + 0.5, 11.5, 4.6, c.rg([(0, "#ffffff", 1), (1, "#efe8da", 1)]), stroke="#d6cbb4", sw=1.2)
        c.ell(x, y - 0.5, 6, 2.6, c.rg([(0, "#ffb070", 1), (1, "#e8602a", 1)]), stroke=None)
        c.circ(x + 6, y + 1, 1.8, "#fff2c8", stroke="#c9a06a", sw=0.8)
        c.circ(x - 6, y + 1.5, 1.4, "#6cc04a", stroke=None)
        gl_line(c, "M%s,%s q4,-3 9,-3.5" % (f(x - 13), f(y - 1)), w=1.6, a=0.8)
    c.save("dish_banh_beo")

    # ---------------- Bánh xèo
    c = icon_canvas()
    plate(c, 64, 88, 58, 22)
    leaf(c, 8, 74, 34, 12, -40, "#6cc04a")
    leaf(c, 94, 70, 30, 10, -20, "#7fd05a")
    # nhân lộ ra ở mép gấp: giá, tôm, thịt
    for k in range(7):
        x = 24 + k * 13
        c.path("M%d,80 q%d,8 %d,15" % (x, 4 if k % 2 else -4, 2 if k % 2 else -2), "none", stroke="#c9b88a", sw=4.4)
        c.path("M%d,80 q%d,8 %d,15" % (x, 4 if k % 2 else -4, 2 if k % 2 else -2), "none", stroke="#fffbe8", sw=2.6)
    for x in (44, 80):
        c.path("M%d,82 q8,12 18,2" % (x - 8), "none", stroke="#c0401a", sw=7)
        c.path("M%d,82 q8,12 18,2" % (x - 8), "none", stroke="#ff8a5a", sw=4.4)
    c.ell(62, 86, 7, 3.4, "#f2c0a0", stroke="#a8604a", sw=1.4)
    c.path("M12,84 Q12,42 62,36 Q112,38 116,82 Q64,74 12,84 Z",
           c.rg([(0, "#fff3a8", 1), (0.5, "#ffcc2e", 1), (1, "#e08a14", 1)], 0.4, 0.3, 0.85), sw=4.5)
    # mép giòn ren nâu
    c.path("M18,72 Q20,48 60,42 Q104,42 110,70", "none", stroke="#c06a10", sw=3, extra=op(0.45))
    for x, y in [(30, 56), (46, 46), (66, 42), (86, 46), (102, 58), (24, 70), (108, 72)]:
        c.circ(x, y, 3, "#b8601a", stroke=None, extra=op(0.45))
    for x, y in [(44, 64), (70, 60), (88, 66), (58, 72)]:
        c.ell(x, y, 4.5, 2.2, "#7cc96b", stroke="#3f8a2a", sw=1)
    gl_line(c, "M24,66 Q28,48 50,42", w=4, a=0.65)
    gloss(c, 76, 50, 6, 2.4, -5, 0.4)
    herb(c, 64, 46, 0.8)
    c.save("dish_banh_xeo")

    # ---------------- Cơm gà
    c = icon_canvas()
    plate(c, 64, 86, 58, 24, band="#e8a020")
    rice_mound(c, 42, 88, 28, 32, "#ffd25a")
    # thịt gà luộc xé / chặt miếng, da vàng óng
    for k, (x, y, a) in enumerate([(98, 60, 62), (88, 68, 58), (78, 76, 54)]):
        c.group(tr(x, y, a))
        c.path("M-16,-4 Q0,-9 16,-4 L15,5 Q0,9 -15,5 Z", "#fffaf0", stroke=O, sw=2.4)
        c.path("M-16,-4 Q0,-9 16,-4 L16,-1 Q0,-5 -16,-1 Z", c.lg("#ffe680", "#f2b632"), stroke=None)
        c.path("M-12,2 L12,2", "none", stroke="#efe2c8", sw=1.4)
        c.path("M-16,-4 Q0,-9 16,-4 L15,5 Q0,9 -15,5 Z", "none", stroke=O, sw=2.4)
        c.end()
    gloss(c, 90, 58, 5, 1.6, 60, 0.6)
    leaf(c, 58, 56, 18, 5, -70, "#3f9a3a")
    leaf(c, 62, 56, 16, 4.5, -110, "#4fae3c")
    for x, y in [(74, 96), (84, 100), (96, 92)]:
        c.ell(x, y, 5, 2.4, "#f4f0ff", stroke="#c4a8d8", sw=1)
    chili(c, 66, 98, 2.6)
    chili(c, 104, 86, 2.6)
    herb(c, 30, 64, 0.75)
    c.save("dish_com_ga")

    # ---------------- Bún bò Huế
    c = icon_canvas()
    cx, cy, srx, sry = bowl(c, "#ffffff", "#c4353a", "#e8602a", ty=62, by=114)
    noodles(c, 22, 100, 62, 2, "#fff6ea", amp=3, step=12, gap=5, w=3.8)
    for x, y, r in [(34, 62, 3), (50, 68, 2.4), (76, 58, 2.8), (92, 66, 2.2), (60, 56, 2)]:
        c.circ(x, y, r, "#ffb03a", stroke="#c0401a", sw=0.8)
    beef(c, 44, 58, 11, 5, -6, "#8a4a34")
    c.circ(78, 62, 8, "#f6dcc0", stroke=O, sw=2.2)
    c.circ(78, 62, 4, "#e8c09a", stroke="#a8784a", sw=1.2)
    c.rect(56, 62, 9, 7, "#5a1e1e", rx=2, stroke="#2a0e0e", sw=1.2)
    c.rect(94, 56, 8, 6, "#5a1e1e", rx=2, stroke="#2a0e0e", sw=1.2)
    for x, y in [(66, 56), (88, 54), (30, 58)]:
        scallion(c, x, y, 2.4)
    leaf(c, 20, 54, 16, 4, -10, "#4fae3c")
    for x, y in [(104, 50), (110, 56), (98, 46)]:
        chili(c, x, y, 3.2)
    lime(c, 24, 48, 9, 20)
    chopsticks(c, 112, 14, 58, 54)
    steam(c, [44, 60, 76], 40, 30)
    c.save("dish_bun_bo_hue")

    # ---------------- Lẩu
    c = icon_canvas()
    c.shadow(64, 118, 54, 7, 0.3)
    # bếp ga mini
    c.rect(22, 98, 84, 18, c.lg("#5b5f66", "#2e3036"), rx=6, sw=4)
    for x in (36, 50, 64, 78, 92):
        c.path("M%d,100 q-3,-6 0,-10 q3,4 0,10 Z" % x, "#4fc3f7", stroke=None, extra=op(0.85))
    c.rect(86, 104, 12, 6, "#e8414f", rx=2, stroke=None)
    # nồi
    d = "M12,58 L14,86 Q16,100 64,100 Q112,100 114,86 L116,58 Z"
    c.path(d, c.lg("#f2f5f8", "#7c8791", 0, 0, 1, 0, mid="#c8d0d8"), sw=4.5)
    gl_line(c, "M20,64 L22,88", w=5, a=0.7)
    for s in (-1, 1):
        x = 64 + s * 58
        c.path("M%s,64 q%s,0 %s,10" % (f(x), f(s * 10), f(s * 6)), "none", sw=8)
        c.path("M%s,64 q%s,0 %s,10" % (f(x), f(s * 10), f(s * 6)), "none", stroke="#5b5f66", sw=4)
    c.ell(64, 58, 52, 16, c.lg("#ffffff", "#b8c0c8"), sw=4.5)
    c.ell(64, 60, 46, 12, c.rg([(0, "#ff8a4a", 1), (0.6, "#e8402a", 1), (1, "#a8201a", 1)], 0.4, 0.4, 0.7),
          stroke="#8a1a10", sw=1.6)
    # nguyên liệu
    for k in range(5):
        c.line(36 + k * 3, 60, 32 + k * 4, 50, stroke="#f6f0dc", sw=2.4)
        c.circ(32 + k * 4, 50, 2, "#f6f0dc", stroke=None)
    c.path("M48,58 Q54,50 62,56 Z", "#7a4a2e", stroke=O, sw=2)
    shrimp(c, 72, 58, 0.8, 30)
    leaf(c, 84, 62, 18, 6, -20, "#5fb84a")
    c.rect(52, 62, 9, 7, "#fff6dc", rx=2, stroke="#c9a06a", sw=1.3)
    c.path("M92,56 A6,6 0 0 0 102,60 Z", "#ff6b4a", stroke="#a8201a", sw=1.4)
    for x, y in [(44, 66), (60, 54), (90, 64), (80, 54)]:
        c.circ(x, y, 1.8, "#ffd0a0", stroke=None)
    steam(c, [40, 58, 76, 92], 42, 34)
    c.save("dish_lau")

    # ---------------- Mì Quảng
    c = icon_canvas()
    # bánh tráng mè dựng phía sau
    c.circ(92, 40, 26, c.rg([(0, "#fff0c0", 1), (0.7, "#f2c27a", 1), (1, "#d9963a", 1)]), sw=3.6)
    for x, y in [(84, 30), (96, 26), (104, 38), (88, 44), (98, 50), (80, 40), (106, 30)]:
        c.ell(x, y, 1.6, 1, "#3a2410", stroke=None)
    gloss(c, 84, 28, 6, 3, -40, 0.5)
    cx, cy, srx, sry = bowl(c, "#fff6dc", "#e89b16", "#f0a040", ty=62, by=114, inner="#f2dcae")
    for k in range(3):
        y = 58 + k * 5
        c.path("M%d,%d q8,-6 16,0 q8,6 16,0 q8,-6 16,0 q8,6 16,0" % (26 + k * 3, y), "none", stroke="#c98a1a", sw=6)
        c.path("M%d,%d q8,-6 16,0 q8,6 16,0 q8,-6 16,0 q8,6 16,0" % (26 + k * 3, y), "none", stroke="#ffd24a", sw=4)
    shrimp(c, 42, 56, 0.85, -20)
    egg_half(c, 64, 54, 5.5)
    c.ell(84, 60, 9, 4, "#f2b48a", stroke="#a8604a", sw=1.6)
    for x, y in [(52, 64), (56, 60), (74, 64), (96, 62), (70, 58)]:
        c.ell(x, y, 2.4, 1.8, "#e0a860", stroke="#8a5a2a", sw=0.8)
    leaf(c, 24, 58, 16, 4.5, -20, "#4fae3c")
    herb(c, 98, 58, 0.7)
    chili(c, 34, 62, 2.4)
    c.save("dish_mi_quang")

    # ---------------- Bò kho
    c = icon_canvas()
    # bánh mì dựng phía sau
    c.group(tr(100, 56, 24))
    c.rect(-12, -46, 24, 84, c.rg([(0, "#ffe0a0", 1), (0.5, "#f2ad52", 1), (1, "#b8601a", 1)], 0.3, 0.3, 0.9),
           rx=12, sw=4)
    for k in range(3):
        c.path("M-6,%d q6,-6 12,-6" % (-28 + k * 18), "none", stroke="#c2701e", sw=5)
        c.path("M-6,%d q6,-6 12,-6" % (-29 + k * 18), "none", stroke="#ffe7b0", sw=2.4)
    c.end()
    cx, cy, srx, sry = bowl(c, "#a86a42", "#e8c27a", "#d8502a", cx=58, ty=64, rx=50, ry=16, by=114, inner="#7a4a2e")
    for x, y, r in [(32, 64, 2.6), (50, 70, 2.2), (80, 62, 2.6), (66, 70, 1.8)]:
        c.circ(x, y, r, "#ffb03a", stroke=None, extra=op(0.8))
    for x, y, a in [(38, 60, -10), (60, 58, 6), (78, 66, -4)]:
        c.group(tr(x, y, a))
        c.rect(-8, -6, 16, 12, c.rg([(0, "#a8583a", 1), (1, "#4a1a0a", 1)], 0.35, 0.3, 0.8), rx=4, stroke=O, sw=2)
        gloss(c, -3, -3, 3, 1.4, -10, 0.6)
        c.end()
    for x, y in [(50, 66), (70, 62)]:
        c.path("M%d,%d l6,-5 l6,5 l-6,5 Z" % (x - 6, y), c.lg("#ffb060", "#e8701a"), stroke="#a8401a", sw=1.6)
    c.path(star_d(88, 58, 6, 2.6, 8), "#7a3a1a", stroke="#3a1606", sw=1.2)
    leaf(c, 24, 56, 18, 5, -20, "#3f9a3a")
    leaf(c, 46, 52, 14, 4, -60, "#4fae3c")
    steam(c, [40, 56, 72], 44, 30)
    c.save("dish_bo_kho")

    # ---------------- Cá kho tộ
    c = icon_canvas()
    c.shadow(64, 116, 50, 7, 0.32)
    d = "M14,58 Q8,82 24,102 Q36,116 64,116 Q92,116 104,102 Q120,82 114,58 Z"
    c.path(d, c.rg([(0, "#a8583a", 1), (0.6, "#6a2e18", 1), (1, "#3a160a", 1)], 0.3, 0.2, 0.9), sw=4.5)
    c.path("M16,74 Q64,90 112,74", "none", stroke="#c47a4a", sw=2.4, extra=op(0.7))
    gl_line(c, "M22,66 Q20,86 34,102", w=5, a=0.45)
    for s in (-1, 1):
        x = 64 + s * 52
        c.ell(x, 62, 8, 5, "#7a3a1c", sw=3.4)
    c.ell(64, 58, 52, 15, c.lg("#a8583a", "#7a3a1c"), sw=4.5)
    c.ell(64, 60, 45, 11, c.rg([(0, "#d0782a", 1), (0.6, "#8a3a10", 1), (1, "#4a1a06", 1)], 0.4, 0.4, 0.7),
          stroke="#3a1606", sw=1.4)
    for x, y, a in [(48, 56, -8), (78, 58, 6)]:
        c.group(tr(x, y, a))
        c.ell(0, 0, 15, 8.5, c.rg([(0, "#f0a050", 1), (0.6, "#b85a1a", 1), (1, "#6a2a0a", 1)], 0.4, 0.3, 0.8),
              stroke=O, sw=2.4)
        c.ell(0, 0, 9, 5, "none", stroke="#e89a5a", sw=1.4)
        c.circ(0, 0, 2.2, "#fff0d8", stroke="#a8683d", sw=1)
        gloss(c, -6, -4, 4, 1.6, -15, 0.7)
        c.end()
    for x, y in [(36, 64), (62, 66), (92, 62), (56, 52), (70, 50)]:
        c.circ(x, y, 1.3, "#1a0e08", stroke=None)
    for x, y in [(64, 62), (96, 56)]:
        chili(c, x, y, 2.8)
    for x, y in [(30, 60), (90, 66)]:
        scallion(c, x, y, 2.4)
    steam(c, [44, 64, 84], 38, 28)
    c.save("dish_ca_kho")

    # ---------------- Bánh canh cua
    c = icon_canvas()
    cx, cy, srx, sry = bowl(c, "#3d7fc4", "#ffffff", "#f0a050", ty=62, by=114, inner="#d8e8f4")
    for k in range(2):
        y = 60 + k * 6
        c.path("M%d,%d q8,-5 16,0 q8,5 16,0 q8,-5 16,0 q8,5 16,0" % (26 + k * 4, y), "none", stroke="#d8c8a8", sw=7)
        c.path("M%d,%d q8,-5 16,0 q8,5 16,0 q8,-5 16,0 q8,5 16,0" % (26 + k * 4, y), "none", stroke="#fffaf0", sw=5)
    # càng cua
    c.group(tr(66, 50, -20))
    c.path("M-14,8 Q-18,-6 -4,-10 Q4,-12 8,-6 L16,-14 Q20,-4 12,0 Q14,6 6,10 Q-6,16 -14,8 Z",
           c.rg([(0, "#ffb070", 1), (0.6, "#ee5a2a", 1), (1, "#b8301a", 1)], 0.4, 0.3, 0.8), stroke=O, sw=2.6)
    gloss(c, -8, -2, 4, 2, -20, 0.7)
    for x, y in [(-6, 4), (2, 6), (-10, -2)]:
        c.circ(x, y, 1.1, "#fff2e0", stroke=None)
    c.end()
    for x, y in [(40, 58), (46, 62), (90, 60)]:
        c.ell(x, y, 4, 2.4, "#ffe0c0", stroke="#e88a5a", sw=1)
    egg_half(c, 94, 56, 5.5)
    for x, y in [(34, 62), (54, 66), (80, 64), (100, 64)]:
        scallion(c, x, y, 2.4)
    for x, y in [(60, 66), (74, 68), (86, 54), (50, 54)]:
        c.circ(x, y, 1.2, "#3a2410", stroke=None)
    steam(c, [42, 58, 74], 40, 28)
    c.save("dish_banh_canh")

    # ---------------- Vịt quay
    c = icon_canvas()
    plate(c, 64, 90, 60, 22, band="#e8414f")
    # thân vịt quay: da bóng màu gụ
    duck = c.rg([(0, "#ffb060", 1), (0.4, "#d0602a", 1), (0.8, "#8a2a10", 1), (1, "#5a1a08", 1)], 0.38, 0.28, 0.85)
    d = "M14,78 Q10,52 40,42 Q70,32 98,44 Q118,54 112,70 Q104,90 60,94 Q20,96 14,78 Z"
    c.path(d, duck, sw=4.5)
    # đùi trước
    c.path("M60,74 Q62,92 84,92 Q104,90 102,76 Q96,62 78,64 Q62,64 60,74 Z",
           c.rg([(0, "#f09048", 1), (0.6, "#b8481a", 1), (1, "#6a2208", 1)], 0.35, 0.3, 0.8), stroke=O, sw=3)
    c.path("M98,82 L110,90", "none", sw=7)
    c.path("M98,82 L110,90", "none", stroke="#fff4e0", sw=3.6)
    c.circ(112, 89, 3.6, "#fff4e0", stroke=O, sw=2.2)
    c.circ(109, 93, 3.2, "#fff4e0", stroke=O, sw=2.2)
    gloss(c, 74, 70, 6, 2.4, -10, 0.55)
    # cánh
    c.path("M28,62 Q44,48 66,52 Q58,64 40,68 Q30,70 28,62 Z", c.lg("#e08a3a", "#9a3a12"), stroke="#5a1e08", sw=2.2)
    gloss(c, 34, 50, 12, 4.5, -22, 0.6)
    gloss(c, 96, 50, 5, 2, 20, 0.45)
    for x, y in [(30, 70), (60, 82), (84, 74), (50, 46)]:
        c.circ(x, y, 1.4, "#fff2c8", stroke=None, extra=op(0.8))
    # trang trí
    for x, y in [(20, 96), (32, 100)]:
        c.ell(x, y, 7, 3.6, "#dff5b0", stroke="#3f8a2a", sw=2)
    herb(c, 16, 84, 0.8)
    chili(c, 44, 100, 2.6)
    c.path("M80,96 A8,5 0 0 0 96,96 Z", "#e8414f", stroke=O, sw=2.2)
    c.save("dish_vit_quay")

    # ---------------- Chả cá Lã Vọng
    c = icon_canvas()
    c.shadow(60, 108, 52, 8, 0.3)
    # cán chảo
    c.path("M100,70 L118,60", "none", sw=12)
    c.path("M100,70 L118,60", "none", stroke="#3a3430", sw=7)
    c.path("M98,72 L116,63", "none", stroke="#8a7a70", sw=2)
    d = "M6,74 Q8,104 58,106 Q108,104 110,74 Z"
    c.path(d, c.lg("#5c5550", "#2a2420", 0, 0, 1, 0, mid="#3a3430"), sw=4.5)
    c.ell(58, 74, 52, 20, c.lg("#6b6560", "#3a3430"), sw=4.5)
    c.ell(58, 75, 45, 15.5, c.rg([(0, "#8a6a2a", 1), (1, "#3a2a10", 1)], 0.5, 0.4, 0.7), stroke=None)
    gl_line(c, "M12,72 A50,18 0 0 1 40,57", w=2.5, a=0.5)
    for x, y, a in [(36, 72, -8), (58, 66, 6), (80, 74, -4), (50, 82, 10), (72, 84, -6)]:
        c.group(tr(x, y, a))
        c.rect(-10, -6, 20, 12, c.rg([(0, "#fff0a0", 1), (0.55, "#ffc02a", 1), (1, "#d8801a", 1)], 0.4, 0.3, 0.8),
               rx=4, stroke=O, sw=2)
        c.path("M-8,4 L8,4", "none", stroke="#b8601a", sw=2, extra=op(0.6))
        gloss(c, -4, -3, 3.4, 1.4, -10, 0.7)
        c.end()
    # thì là + hành
    for k in range(3):
        x = 40 + k * 18
        c.line(x - 10, 60 + k * 4, x + 14, 52 + k * 6, stroke="#e8f8d0", sw=4)
        c.line(x - 10, 60 + k * 4, x + 14, 52 + k * 6, stroke="#7cc96b", sw=1.8)

    def dill(x, y, ang, s=1.0):
        c.group(tr(x, y, ang, s))
        c.path("M0,0 Q4,-10 2,-22", "none", stroke="#2f6a1e", sw=2.6)
        for k in range(5):
            yy = -4 - k * 4
            w = 6 - k * 0.6
            c.path("M1.5,%s q%s,-2 %s,-5 M1.5,%s q%s,-2 %s,-5" % (f(yy), f(-w * 0.5), f(-w), f(yy), f(w * 0.5), f(w)),
                   "none", stroke="#2f6a1e", sw=3.4)
            c.path("M1.5,%s q%s,-2 %s,-5 M1.5,%s q%s,-2 %s,-5" % (f(yy), f(-w * 0.5), f(-w), f(yy), f(w * 0.5), f(w)),
                   "none", stroke="#7fd05a", sw=1.8)
        c.end()
    for x, y, a in [(48, 64, -25), (64, 60, 8), (80, 68, 35), (34, 72, -45)]:
        dill(x, y, a)
    for x, y in [(26, 80), (92, 82), (60, 92), (42, 90)]:
        c.circ(x, y, 2, "#ffe7a0", stroke=None, extra=op(0.8))
    steam(c, [36, 56, 76], 46, 28)
    c.save("dish_cha_ca")

    # ---------------- Cao lầu
    c = icon_canvas()
    cx, cy, srx, sry = bowl(c, "#2f5d7a", "#9fd0e8", "#8a5a2a", ty=62, by=114, inner="#d8e4ea")
    for k in range(3):
        y = 58 + k * 5
        c.path("M%d,%d q8,-5 16,0 q8,5 16,0 q8,-5 16,0 q8,5 16,0" % (26 + k * 3, y), "none", stroke="#a8702a", sw=7)
        c.path("M%d,%d q8,-5 16,0 q8,5 16,0 q8,-5 16,0 q8,5 16,0" % (26 + k * 3, y), "none", stroke="#e8b866", sw=5)
    for x, y, a in [(44, 54, -10), (66, 52, 8)]:
        c.group(tr(x, y, a))
        c.path("M-12,2 Q-12,-6 0,-6 Q12,-6 12,2 Z", "#f6c0b0", stroke="#a8301a", sw=2)
        c.path("M-12,2 L12,2 L11,6 L-11,6 Z", "#c8402a", stroke="#7a1a0a", sw=1.6)
        c.end()
    for x, y in [(86, 54), (94, 62), (80, 64)]:
        c.rect(x - 5, y - 5, 10, 10, c.lg("#ffe08a", "#d8901a"), rx=2, stroke=O, sw=1.6,
               extra='transform="rotate(15 %d %d)"' % (x, y))
    leaf(c, 18, 56, 22, 7, -10, "#6cc04a")
    leaf(c, 30, 50, 18, 6, -50, "#4fae3c")
    for k in range(3):
        c.path("M%d,64 q4,-2 8,-6" % (52 + k * 6), "none", stroke="#fffbe8", sw=2.2)
    chopsticks(c, 112, 14, 58, 52, "#2a1a10")
    c.save("dish_cao_lau")


# ================================================================ TIỀN TỆ / NGÔI SAO

def coin(name="coin", folder=None):
    c = icon_canvas()
    x, y, r = 64, 60, 50
    c.shadow(64, 117, 42, 6, 0.3)
    c.circ(x, y + 7, r, c.lg("#e89b16", "#a35a08"), sw=5)
    for k in range(9):
        a = math.pi * (0.12 + 0.76 * k / 8.0)
        px = x + math.cos(a) * r
        c.line(px, y + math.sin(a) * r + 1, px, y + math.sin(a) * r + 6, stroke="#8a4a06", sw=1.6, extra=op(0.6))
    c.circ(x, y, r, R(c, GOLD, 0.6, 0.18, 0.35, 0.28, 0.8), sw=5)
    c.circ(x, y, r - 10, c.rg([(0, "#e8a020", 1), (0.6, "#f6b832", 1), (1, "#ffd860", 1)], 0.35, 0.3, 0.8),
           stroke="#c47a10", sw=3)
    for k in range(20):
        a = 2 * math.pi * k / 20
        c.circ(x + math.cos(a) * (r - 5), y + math.sin(a) * (r - 5), 1.5, "#fff3b8", stroke=None, extra=op(0.85))
    # đồng xu lỗ vuông nổi
    c.rect(x - 17, y - 17, 34, 34, R(c, "#ffe27a", 0.5, 0.15), rx=7, stroke="#c47a10", sw=3)
    c.rect(x - 8, y - 8, 16, 16, c.lg("#9a5206", "#d8901a"), rx=3, stroke="#8a4a08", sw=2)
    c.path("M%s,%s L%s,%s" % (f(x - 12), f(y - 13), f(x + 10), f(y - 13)), "none", stroke=WHITE, sw=2,
           extra='stroke-opacity="0.7"')
    c.path("M%s,%s A%s,%s 0 0 1 %s,%s" % (f(x - r + 6), f(y + 4), f(r - 6), f(r - 6), f(x - 6), f(y - r + 6)), "none",
           stroke=WHITE, sw=5, extra='stroke-opacity="0.6"')
    gloss(c, x - 24, y - 26, 8, 4, -40, 0.75)
    spark(c, x + 34, y - 36, 10)
    spark(c, x + 44, y - 20, 4.5)
    c.save(name, folder or OUT_DIR)


def diamond_icon(name="diamond", folder=None):
    c = icon_canvas()
    c.shadow(64, 118, 36, 6, 0.3)
    T1, T2 = (38, 28), (90, 28)
    G = [(10, 52), (37, 52), (64, 52), (91, 52), (118, 52)]
    B = (64, 116)
    out = [G[0], T1, T2, G[4], B]
    c.group("translate(0 5)")
    c.poly(out, "#1d5fa8", sw=5)
    c.end()
    facets = [([G[0], T1, G[1]], "#8fe2ff"), ([T1, G[2], G[1]], "#c8f4ff"), ([T1, T2, G[2]], "#e8fbff"),
              ([T2, G[3], G[2]], "#9fe6ff"), ([T2, G[4], G[3]], "#4fb8f0"),
              ([G[0], G[1], B], "#5fc8f8"), ([G[1], G[2], B], "#8fdcff"), ([G[2], G[3], B], "#3aa2e8"),
              ([G[3], G[4], B], "#2a7fd0")]
    for p, col in facets:
        c.poly(p, col, stroke=None)
    c.poly([T1, T2, G[2]], c.lg("#ffffff", "#bff0ff"), stroke=None)
    for p, col in facets:
        c.poly(p, "none", stroke=WHITE, sw=1.4, extra='stroke-opacity="0.55"')
    c.poly(out, "none", sw=5)
    gl_line(c, "M44,34 L58,34", w=4, a=0.9)
    gl_line(c, "M22,58 L40,82", w=3.5, a=0.55)
    spark(c, 104, 22, 12)
    spark(c, 22, 30, 6)
    spark(c, 84, 76, 5, WHITE, 0.8)
    c.save(name, folder or OUT_DIR)


def stars():
    for name, col in [("star", "#ffc93c"), ("exp", "#6fd14a")]:
        c = icon_canvas()
        c.shadow(64, 118, 40, 6, 0.28)
        faceted_star(c, 64, 64, 57, 27, col, sw=5, depth=6)
        gloss(c, 44, 46, 7, 3.4, -40, 0.7)
        spark(c, 104, 24, 9)
        c.save(name, UI_DIR)
    c = icon_canvas()
    faceted_star(c, 64, 64, 57, 27, "#cfc4b6", sw=5, depth=6)
    c.save("star_empty", UI_DIR)


# ================================================================ ICON GIAO DIỆN NHỎ

def gear_d(cx, cy, ro, ri, n):
    d = ""
    for k in range(n):
        a = 2 * math.pi * k / n
        hw, bw = math.pi / n * 0.42, math.pi / n * 0.66
        for aa, rr in [(a - bw, ri), (a - hw, ro), (a + hw, ro), (a + bw, ri)]:
            d += ("M" if d == "" else "L") + "%s,%s " % (f(cx + math.cos(aa) * rr), f(cy + math.sin(aa) * rr))
    return d + "Z"


def ui_small():
    # bánh răng
    c = icon_canvas()
    c.shadow(64, 118, 40, 6, 0.28)
    g = gear_d(64, 60, 56, 43, 9)
    extrude_path(c, g, "#8f9caa", 4)
    c.path(g, R(c, "#b4c0cc", 0.5, 0.2), sw=5)
    c.circ(64, 60, 32, "none", stroke=WHITE, sw=3, extra='stroke-opacity="0.35"')
    c.circ(64, 60, 18, c.lg("#5b6670", "#c8d2dc"), sw=5)
    c.circ(64, 60, 7, "#4a545e", stroke=None)
    gl_line(c, "M24,46 A42,42 0 0 1 50,20", w=5, a=0.55)
    c.save("gear", UI_DIR)

    # ổ khóa
    c = icon_canvas()
    c.shadow(64, 120, 40, 6, 0.28)
    sh = "M38,62 L38,42 Q38,14 64,14 Q90,14 90,42 L90,62"
    c.path(sh, "none", stroke=O, sw=19)
    c.path(sh, "none", stroke="#aab6c2", sw=11)
    c.path("M41,58 L41,42 Q41,19 64,18", "none", stroke=WHITE, sw=3.5, extra='stroke-opacity="0.7"')
    c.rect(20, 60, 88, 56, dk(GOLD_D, 0.35), rx=16, sw=5)
    c.rect(20, 54, 88, 56, R(c, GOLD, 0.55, 0.2, 0.3, 0.2, 0.9), rx=16, sw=5)
    c.rect(27, 60, 74, 8, WHITE, rx=4, stroke=None, extra=op(0.45))
    c.circ(64, 78, 9, "#5a341f", stroke=None)
    c.path("M60,82 L58,98 L70,98 L68,82 Z", "#5a341f", stroke=None)
    for x, y in [(30, 100), (98, 100), (30, 68), (98, 68)]:
        c.circ(x, y, 3, "#fff2b0", stroke="#c47a10", sw=1.5)
    c.save("lock", UI_DIR)

    # bàn tay chỉ
    c = icon_canvas(160)
    d = ("M70,20 Q70,8 82,8 Q94,8 94,20 L94,70 Q100,62 110,64 Q120,66 120,78 Q128,72 136,78 Q144,84 142,96 "
         "L140,120 Q136,150 106,152 L84,152 Q60,150 50,128 L34,98 Q28,86 38,82 Q48,78 56,90 L70,108 Z")
    c.group("translate(82 8) scale(0.95) translate(-82 -8)")
    c.group("translate(3 5)")
    c.path(d, "#000000", stroke=None, extra=op(0.18))
    c.end()
    c.path(d, c.rg([(0, "#ffffff", 1), (0.6, "#fdf3e8", 1), (1, "#e9d3bc", 1)], 0.35, 0.3, 0.85), sw=6)
    c.path("M94,70 L94,98 M120,78 L120,102", "none", stroke=O, sw=4)
    c.path("M76,14 Q82,10 88,14 L88,22 Q82,25 76,22 Z", "#ffe6dc", stroke="#d8b8a8", sw=1.5)
    gl_line(c, "M76,30 L76,96", w=5, a=0.9)
    c.path("M60,138 Q84,148 120,140", "none", stroke="#d8b89a", sw=3, extra=op(0.7))
    c.end()
    c.save("hand", UI_DIR)

    # mũi tên
    for name, sgn in [("arrow_left", 1), ("arrow_right", -1)]:
        c = icon_canvas()
        p = [(84, 14), (28, 64), (84, 114), (102, 96), (66, 64), (102, 32)]
        if sgn < 0:
            p = [(128 - x, y) for x, y in p]
        c.group("translate(0 6)")
        c.poly(p, "#a8784a", sw=6)
        c.end()
        c.poly(p, c.lg("#ffffff", "#f2dcbc"), sw=6)
        hl = [(84, 22), (38, 64)] if sgn > 0 else [(44, 22), (90, 64)]
        c.line(hl[0][0], hl[0][1], hl[1][0], hl[1][1], stroke=WHITE, sw=4)
        c.save(name, UI_DIR)

    # đóng
    c = icon_canvas()
    chunky_circle(c, 64, 60, 52, "#f2554a")
    c.path("M44,40 L84,80 M84,40 L44,80", "none", stroke="#9a2a22", sw=18, extra='transform="translate(0 3)"')
    c.path("M44,40 L84,80 M84,40 L44,80", "none", stroke=O, sw=19)
    c.path("M44,40 L84,80 M84,40 L44,80", "none", stroke=WHITE, sw=11)
    c.save("close", UI_DIR)

    # tim
    c = icon_canvas()
    hd = "M64,112 C24,86 8,62 16,40 C24,18 52,18 64,38 C76,18 104,18 112,40 C120,62 104,86 64,112 Z"
    c.shadow(64, 118, 34, 5, 0.25)
    extrude_path(c, hd, "#e8414f", 5)
    c.path(hd, R(c, "#f2475a", 0.55, 0.2, 0.32, 0.25, 0.85), sw=5)
    gloss(c, 38, 42, 12, 7, -40, 0.75)
    c.circ(52, 34, 3, WHITE, stroke=None, extra=op(0.8))
    spark(c, 100, 22, 8)
    c.save("heart", UI_DIR)

    # đồng hồ báo thức
    c = icon_canvas()
    c.shadow(64, 120, 40, 5, 0.25)
    for s in (-1, 1):
        c.path("M%s,%s L%s,%s" % (f(64 + s * 30), 108, f(64 + s * 38), 118), "none", stroke=O, sw=8)
        c.circ(64 + s * 34, 22, 14, R(c, GOLD, 0.5, 0.2), sw=4.5)
    c.rect(56, 6, 16, 10, "#c47a10", rx=3, sw=3.5)
    c.circ(64, 66, 48, dk(GOLD_D, 0.3), sw=5, extra='transform="translate(0 4)"')
    c.circ(64, 66, 48, R(c, GOLD, 0.55, 0.2), sw=5)
    c.circ(64, 66, 37, c.rg([(0, "#ffffff", 1), (0.8, "#fdf4e2", 1), (1, "#e9d6b4", 1)], 0.4, 0.35, 0.75),
           stroke="#c47a10", sw=3)
    for k in range(12):
        a = k * math.pi / 6
        r1 = 30 if k % 3 else 27
        c.line(64 + math.cos(a) * r1, 66 + math.sin(a) * r1, 64 + math.cos(a) * 33, 66 + math.sin(a) * 33,
               stroke="#8a5a3a", sw=3 if k % 3 == 0 else 1.8)
    c.path("M64,66 L64,42", "none", stroke=O, sw=6)
    c.path("M64,66 L82,76", "none", stroke="#e8414f", sw=4.5)
    c.circ(64, 66, 5, O, stroke=None)
    gl_line(c, "M30,52 A36,36 0 0 1 52,32", w=4.5, a=0.7)
    c.save("clock", UI_DIR)

    # tia sét
    c = icon_canvas()
    bp = [(76, 6), (26, 72), (58, 72), (48, 122), (104, 50), (70, 50), (88, 6)]
    c.shadow(64, 120, 30, 5, 0.25)
    c.group("translate(0 5)")
    c.poly(bp, "#c4700a", sw=5)
    c.end()
    c.poly(bp, c.lg("#fff3a0", "#ffa81a", 0.2, 0, 0.8, 1), sw=5)
    c.poly([(76, 6), (26, 72), (40, 72), (82, 12)], WHITE, stroke=None, extra=op(0.45))
    c.poly([(58, 72), (48, 122), (66, 74)], "#c4700a", stroke=None, extra=op(0.35))
    c.poly(bp, "none", sw=5)
    spark(c, 106, 22, 8)
    c.save("bolt", UI_DIR)

    # lấp lánh (hạt hiệu ứng, không viền)
    c = icon_canvas()
    c.circ(64, 64, 58, c.rg([(0, "#fff6c0", 0.85), (0.35, "#ffd860", 0.35), (1, "#ffc93c", 0)]), stroke=None)
    c.path("M64,6 Q70,58 122,64 Q70,70 64,122 Q58,70 6,64 Q58,58 64,6 Z",
           c.rg([(0, "#ffffff", 1), (0.5, "#fff6b0", 1), (1, "#ffd24a", 1)]), stroke=None)
    c.path("M64,30 Q67,61 98,64 Q67,67 64,98 Q61,67 30,64 Q61,61 64,30 Z", WHITE, stroke=None, extra=op(0.9))
    c.circ(64, 64, 6, WHITE, stroke=None)
    c.save("sparkle", UI_DIR)

    # khói (hạt hiệu ứng, không viền)
    c = icon_canvas()
    for x, y, r, a in [(64, 74, 40, 0.9), (40, 70, 26, 0.85), (88, 70, 26, 0.85), (54, 48, 26, 0.9), (78, 50, 22, 0.85)]:
        c.circ(x, y, r, c.rg([(0, "#ffffff", a), (0.6, "#ffffff", a * 0.6), (1, "#ffffff", 0)], 0.42, 0.4, 0.55),
               stroke=None)
    c.save("puff", UI_DIR)

    # túi vàng
    c = icon_canvas()
    c.shadow(64, 120, 46, 6, 0.28)
    sack = "M42,44 Q16,66 18,94 Q20,118 64,118 Q108,118 110,94 Q112,66 86,44 Z"
    c.path(sack, c.rg([(0, "#f6c27a", 1), (0.6, "#d08a3a", 1), (1, "#8a5020", 1)], 0.35, 0.3, 0.85), sw=5)
    c.path("M30,104 Q64,114 98,104", "none", stroke="#7a4218", sw=2, extra=op(0.5))
    c.path("M44,44 Q34,28 44,16 L54,24 L62,10 L70,22 L82,14 Q94,26 84,44 Z", c.lg("#f2be76", "#c07a32"), sw=4.5)
    c.rect(36, 38, 56, 12, c.lg("#e8414f", "#a82a2a"), rx=6, sw=4)
    c.circ(64, 80, 21, dk(GOLD_D, 0.3), sw=4, extra='transform="translate(0 3)"')
    c.circ(64, 80, 21, R(c, GOLD, 0.55, 0.15), sw=4)
    c.path(star_d(64, 81, 11, 5), "#fff0a0", stroke="#c47a10", sw=2)
    gloss(c, 34, 66, 7, 12, 20, 0.35)
    for x, y in [(102, 108), (114, 100)]:
        c.ell(x, y + 3, 11, 6, "#a35a08", sw=3)
        c.ell(x, y, 11, 6, R(c, GOLD, 0.5, 0.15), sw=3)
    spark(c, 22, 30, 8)
    c.save("gold_bag", UI_DIR)

    # hộp quà
    c = icon_canvas()
    c.shadow(64, 120, 46, 6, 0.28)
    c.rect(22, 58, 84, 58, c.lg("#f2554a", "#a8282a"), rx=6, sw=5)
    c.rect(22, 58, 84, 12, "#7a1a1a", rx=2, stroke=None, extra=op(0.35))
    c.rect(56, 58, 16, 58, c.lg("#ffe27a", "#e89b16", 0, 0, 1, 0), stroke=O, sw=3.5)
    c.rect(14, 42, 100, 22, c.lg("#ff7a6a", "#d23a34"), rx=6, sw=5)
    c.rect(54, 42, 20, 22, c.lg("#ffe27a", "#e89b16", 0, 0, 1, 0), stroke=O, sw=3.5)
    c.rect(20, 46, 30, 5, WHITE, rx=2.5, stroke=None, extra=op(0.5))
    for s in (-1, 1):
        c.path("M64,42 Q%s,%s %s,%s Q%s,%s 64,42 Z" % (f(64 + s * 22), 10, f(64 + s * 36), 22, f(64 + s * 30),
                                                     40), R(c, GOLD, 0.5, 0.2), sw=4)
        c.path("M64,42 Q%s,%s %s,%s" % (f(64 + s * 18), 22, f(64 + s * 28), 26), "none", stroke="#c47a10", sw=2)
    c.circ(64, 40, 8, R(c, GOLD, 0.5, 0.2), sw=4)
    spark(c, 108, 30, 8)
    spark(c, 18, 26, 5)
    c.save("gift", UI_DIR)

    # thăng cấp quán (nhà vàng)
    c = icon_canvas()
    c.shadow(64, 120, 46, 6, 0.28)
    c.rect(26, 62, 76, 52, dk(GOLD_D, 0.3), rx=4, sw=5, extra='transform="translate(0 4)"')
    c.rect(26, 62, 76, 52, c.lg("#fff0b0", "#f2b632"), rx=4, sw=5)
    c.path("M52,114 L52,90 Q64,76 76,90 L76,114 Z", c.rg([(0, "#fff6c0", 1), (1, "#ffb43a", 1)], 0.5, 0.6, 0.7),
           sw=4)
    for x in (34, 82):
        c.rect(x, 74, 12, 12, "#fff6c0", rx=2, stroke="#c47a10", sw=2.5)
    roof = "M6,64 Q30,58 46,40 L64,20 L82,40 Q98,58 122,64 Q114,72 104,68 L24,68 Q14,72 6,64 Z"
    c.path(roof, R(c, "#ffb02a", 0.45, 0.25, 0.4, 0.2, 0.9), sw=5)
    for k in range(5):
        x = 34 + k * 15
        c.path("M%d,66 L%d,%d" % (x, x + (64 - x) * 0.25, 46 + abs(64 - x) * 0.25), "none", stroke="#c4700a", sw=2,
               extra=op(0.6))
    c.path(star_d(64, 16, 11, 5), R(c, "#fff27a", 0.5, 0.1), sw=3.5)
    gl_line(c, "M14,62 Q32,56 46,44", w=3.5, a=0.7)
    spark(c, 110, 30, 9)
    spark(c, 20, 34, 6)
    c.save("prestige", UI_DIR)

    # nhạc
    c = icon_canvas()
    c.shadow(64, 120, 40, 5, 0.25)
    beam = "M46,32 L104,18 L104,34 L46,48 Z"
    c.rect(42, 34, 9, 64, "#7a5ad8", sw=4.5)
    c.rect(99, 22, 9, 62, "#7a5ad8", sw=4.5)
    c.path(beam, c.lg("#a890ff", "#6a4ac8"), sw=4.5)
    for x, y in [(34, 98), (90, 86)]:
        c.ell(x, y, 18, 13, R(c, "#8a6cf0", 0.5, 0.2), sw=4.5, extra='transform="rotate(-20 %d %d)"' % (x, y))
        gloss(c, x - 6, y - 5, 6, 3, -20, 0.7)
    c.rect(44, 38, 3.5, 54, WHITE, stroke=None, extra=op(0.5))
    c.save("music", UI_DIR)

    # âm thanh
    c = icon_canvas()
    c.shadow(56, 118, 40, 5, 0.25)
    sp = "M14,46 L40,46 L72,20 Q78,18 78,26 L78,102 Q78,110 72,108 L40,82 L14,82 Q10,82 10,78 L10,50 Q10,46 14,46 Z"
    extrude_path(c, sp, "#c8b8a0", 5)
    c.path(sp, c.lg("#ffffff", "#e8d8c0"), sw=5)
    c.rect(14, 50, 24, 28, c.lg("#7fb8e8", "#3a7fc4"), rx=3, stroke=None)
    gl_line(c, "M44,50 L70,28", w=4, a=0.9)
    for r, w in [(16, 1), (30, 1)]:
        d = "M%s,%s A%s,%s 0 0 1 %s,%s" % (f(88), f(64 - r), f(r), f(r), f(88), f(64 + r))
        c.path(d, "none", stroke=O, sw=13, extra='transform="translate(-4 0)"')
        c.path(d, "none", stroke="#4fa3e0", sw=6.5, extra='transform="translate(-4 0)"')
    c.save("sound", UI_DIR)

    # rung
    c = icon_canvas()
    c.shadow(64, 120, 30, 5, 0.25)
    c.rect(38, 16, 52, 98, dk("#4a4e58", 0.3), rx=12, sw=5, extra='transform="translate(0 4)"')
    c.rect(38, 16, 52, 98, c.lg("#6a707c", "#33363e", 0, 0, 1, 0), rx=12, sw=5)
    c.rect(44, 26, 40, 72, c.lg("#9fe0ff", "#3a8fd8"), rx=4, stroke=None)
    c.poly([(44, 26), (66, 26), (44, 60)], WHITE, stroke=None, extra=op(0.35))
    c.circ(64, 106, 3.4, "#9aa0aa", stroke=None)
    for s in (-1, 1):
        x0 = 64 + s * 38
        d = "M%s,40 l%s,8 l%s,8 l%s,8 l%s,8 l%s,8" % (f(x0), f(s * 8), f(-s * 8), f(s * 8), f(-s * 8), f(s * 8))
        c.path(d, "none", stroke=O, sw=10)
        c.path(d, "none", stroke="#ffb43a", sw=5)
    c.save("vibrate", UI_DIR)

    # thùng rác
    c = icon_canvas()
    c.shadow(64, 120, 40, 5, 0.25)
    body = "M28,40 L100,40 L92,110 Q91,116 84,116 L44,116 Q37,116 36,110 Z"
    c.path(body, c.lg("#ff8a7a", "#c4383a", 0, 0, 1, 0, mid="#ef5a50"), sw=5)
    for x in (48, 64, 80):
        c.path("M%d,52 L%s,104" % (x, f(x + (x - 64) * 0.1)), "none", stroke="#a82a2a", sw=6)
        c.path("M%d,52 L%s,104" % (x, f(x + (x - 64) * 0.1)), "none", stroke="#ffb0a8", sw=2.4)
    c.rect(50, 14, 28, 14, "none", rx=6, stroke=O, sw=11)
    c.rect(50, 14, 28, 14, "none", rx=6, stroke="#d8443e", sw=5)
    c.rect(18, 26, 92, 16, c.lg("#ff8a7a", "#d23a34"), rx=7, sw=5)
    gl_line(c, "M24,31 L60,31", w=3.5, a=0.7)
    c.save("trash", UI_DIR)

    # đúng / cộng / thông tin
    c = icon_canvas()
    chunky_circle(c, 64, 60, 52, "#5fc23a")
    c.path("M38,60 L56,78 L92,40", "none", stroke="#2e7a1e", sw=18, extra='transform="translate(0 3)"')
    c.path("M38,60 L56,78 L92,40", "none", stroke=O, sw=19)
    c.path("M38,60 L56,78 L92,40", "none", stroke=WHITE, sw=11)
    c.save("check", UI_DIR)
    c = icon_canvas()
    chunky_circle(c, 64, 60, 50, "#fffaf0", l=0.5, d=0.12)
    c.path("M64,36 L64,84 M40,60 L88,60", "none", stroke=O, sw=19)
    c.path("M64,36 L64,84 M40,60 L88,60", "none", stroke="#5fc23a", sw=11)
    c.save("plus", UI_DIR)
    c = icon_canvas()
    chunky_circle(c, 64, 60, 52, "#4fa3e8")
    c.circ(64, 34, 8, WHITE, sw=4)
    c.rect(56, 50, 16, 42, WHITE, rx=6, sw=4)
    c.save("info", UI_DIR)
    c = icon_canvas(96)
    chunky_circle(c, 48, 44, 38, "#6fd14a", sw=4.5, depth=5)
    c.path("M48,26 L48,62 M30,44 L66,44", "none", stroke=O, sw=16)
    c.path("M48,26 L48,62 M30,44 L66,44", "none", stroke=WHITE, sw=9)
    c.save("plus_green", UI_DIR)


# ================================================================ ICON LỚN (160)

def ui_big():
    # ---- nồi (Thực đơn)
    c = icon_canvas(160)
    c.shadow(80, 146, 62, 9, 0.3)
    body = "M22,76 L24,118 Q26,142 80,142 Q134,142 136,118 L138,76 Z"
    for s in (-1, 1):
        x = 80 + s * 60
        c.path("M%s,86 q%s,0 %s,14" % (f(x), f(s * 14), f(s * 4)), "none", sw=10)
        c.path("M%s,86 q%s,0 %s,14" % (f(x), f(s * 14), f(s * 4)), "none", stroke="#c4383a", sw=5)
    c.path(body, c.lg("#ff8a6a", "#a8242a", 0, 0, 1, 0, mid="#e8443a"), sw=5)
    c.path("M26,104 Q80,120 134,104", "none", stroke="#fff0d8", sw=4, extra=op(0.85))
    gl_line(c, "M32,84 L34,120", w=6, a=0.55)
    c.ell(80, 76, 58, 17, c.lg("#ff9a7a", "#d23a34"), sw=5)
    c.ell(80, 78, 50, 12, c.rg([(0, "#ffd070", 1), (0.6, "#f29a2a", 1), (1, "#c0601a", 1)], 0.4, 0.4, 0.7),
          stroke="#8a3a10", sw=1.8)
    for x, y, col in [(54, 76, "#7cc96b"), (68, 80, "#e8414f"), (90, 74, "#fff2c8"), (104, 80, "#7cc96b")]:
        c.circ(x, y, 5.5, R(c, col, 0.4, 0.2), stroke=dk(col, 0.45), sw=1.6)
    shrimp(c, 80, 76, 0.9, 10)
    # nắp hé mở
    c.group(tr(100, 46, -22))
    c.path("M-44,8 Q-40,-18 0,-20 Q40,-18 44,8 Z", c.lg("#ff8a6a", "#c4383a"), sw=5)
    c.ell(0, 8, 46, 7, c.lg("#e8443a", "#8a1e22"), sw=4.5)
    c.circ(0, -22, 8, R(c, "#ffd34d", 0.4, 0.2), sw=4)
    gl_line(c, "M-32,-2 Q-24,-14 -6,-15", w=4, a=0.6)
    c.end()
    steam(c, [40, 58], 60, 34, 0.9, 5)
    c.save("icon_pot", UI_DIR)

    # ---- chậu cây
    c = icon_canvas(160)
    c.shadow(80, 148, 50, 8, 0.3)
    c.rect(78, 60, 5, 40, "#7a4a2e", stroke=None)
    for x, y, r, col in [(80, 44, 32, "#4fae3c"), (48, 64, 26, "#5fb84a"), (112, 64, 26, "#4fae3c"),
                         (60, 28, 22, "#6cc04a"), (100, 30, 22, "#5fb84a")]:
        c.circ(x, y, r, R(c, col, 0.45, 0.25, 0.38, 0.3, 0.75), sw=4.5)
    for x, y, r in [(70, 40, 6), (54, 58, 5), (100, 52, 5), (90, 24, 4), (114, 66, 4)]:
        c.circ(x - 1, y - 1, r * 0.9, lt("#6cc04a", 0.4), stroke=None, extra=op(0.5))
    for x, y in [(66, 34), (98, 46), (44, 62), (118, 58), (84, 20)]:
        for k in range(5):
            a = k * 2 * math.pi / 5
            c.circ(x + math.cos(a) * 4, y + math.sin(a) * 4, 3.6, "#ff8fb0", stroke="#c44a70", sw=1.2)
        c.circ(x, y, 2.6, "#ffe27a", stroke=None)
    c.path("M44,96 L116,96 L106,144 Q105,148 100,148 L60,148 Q55,148 54,144 Z",
           c.lg("#e88a5a", "#a8522a", 0, 0, 1, 0, mid="#d0703e"), sw=5)
    c.rect(38, 88, 84, 18, c.lg("#f0a070", "#c0643a"), rx=6, sw=5)
    gl_line(c, "M44,93 L80,93", w=3.5, a=0.6)
    gl_line(c, "M56,110 L62,140", w=4, a=0.4)
    c.save("icon_plant", UI_DIR)

    # ---- giỏ quà
    c = icon_canvas(160)
    c.shadow(80, 148, 60, 8, 0.3)
    c.path("M34,76 Q80,0 126,76", "none", stroke=O, sw=15)
    c.path("M34,76 Q80,0 126,76", "none", stroke="#c98a55", sw=8)
    c.path("M38,70 Q80,8 122,70", "none", stroke="#f2c08a", sw=2.4)
    for x, y, r, col in [(54, 68, 18, "#ff9a2a"), (82, 62, 20, "#e8414f"), (108, 68, 16, "#ffd34d")]:
        c.circ(x, y, r, R(c, col, 0.5, 0.25), sw=4)
        gloss(c, x - r * 0.35, y - r * 0.4, r * 0.3, r * 0.18, -30, 0.7)
    leaf(c, 82, 44, 14, 5, -60, "#5fb84a")
    for k, (x, y) in enumerate([(122, 56), (128, 64), (118, 66), (124, 74)]):
        c.circ(x, y, 6, R(c, "#9a5ad8", 0.45, 0.2), stroke="#4a2a7a", sw=2)
    bk = "M18,76 L142,76 L128,140 Q126,146 118,146 L42,146 Q34,146 32,140 Z"
    c.path(bk, c.lg("#e0a060", "#9a5a2a"), sw=5)
    for k in range(4):
        y = 90 + k * 14
        c.path("M%s,%d L%s,%d" % (f(22 + k * 3), y, f(138 - k * 3), y), "none", stroke="#8a5020", sw=2.4, extra=op(0.6))
    for k in range(8):
        x = 30 + k * 14
        c.path("M%d,80 L%s,142" % (x, f(x + (x - 80) * -0.1)), "none", stroke="#f6c890", sw=2, extra=op(0.55))
    c.rect(12, 70, 136, 16, c.lg("#f0b070", "#b8763a"), rx=8, sw=5)
    c.path("M80,96 q-18,-12 -20,4 q0,10 20,0 q18,-12 20,4 q0,10 -20,0 Z", R(c, "#e8414f", 0.4, 0.2), sw=3.5)
    c.circ(80, 98, 5, "#c4283a", sw=3)
    spark(c, 22, 40, 8)
    c.save("icon_basket", UI_DIR)

    # ---- sổ nhiệm vụ
    c = icon_canvas(160)
    c.shadow(80, 150, 54, 8, 0.3)
    c.rect(36, 24, 96, 120, "#fbecd2", rx=8, sw=5)
    for k in range(6):
        c.line(122, 34 + k * 18, 130, 34 + k * 18, stroke="#c9a37a", sw=2)
    c.rect(26, 18, 98, 122, c.rg([(0, "#d08a52", 1), (0.6, "#a8602e", 1), (1, "#6a3a1a", 1)], 0.3, 0.25, 0.9),
           rx=12, sw=5)
    c.rect(26, 18, 16, 122, "#5a2e14", rx=8, stroke=None, extra=op(0.45))
    c.rect(48, 28, 68, 102, "none", rx=8, stroke="#ffd98a", sw=2.4, extra=op(0.7))
    for x, y in [(48, 28), (116, 28), (48, 130), (116, 130)]:
        c.circ(x, y, 5, R(c, GOLD, 0.5, 0.2), stroke="#a35a08", sw=1.8)
    faceted_star(c, 82, 78, 30, 14, GOLD, sw=4)
    c.path("M100,136 L100,156 L108,149 L116,156 L116,136 Z", c.lg("#5fb0f0", "#2a6ab8"), sw=4)
    gl_line(c, "M36,30 L36,128", w=4, a=0.35)
    gl_line(c, "M50,22 L104,22", w=3, a=0.5)
    c.save("icon_book", UI_DIR)

    # ---- nhà (khu quán)
    c = icon_canvas(160)
    c.shadow(80, 148, 62, 8, 0.3)
    c.rect(30, 72, 100, 70, c.lg("#fff3d8", "#e8c890"), rx=4, sw=5)
    for x in (30, 124):
        c.rect(x, 72, 6, 70, "#a8683d", stroke=None)
    c.rect(26, 136, 108, 8, "#a8683d", rx=3, sw=4)
    c.path("M64,138 L64,104 Q80,88 96,104 L96,138 Z", c.lg("#b8763a", "#7a4a2e"), sw=4)
    c.line(80, 98, 80, 138, stroke="#5a341f", sw=2.4)
    for x in (40, 104):
        c.rect(x, 90, 18, 18, c.lg("#fff6c0", "#ffc860"), rx=2, stroke=O, sw=3)
        c.line(x + 9, 90, x + 9, 108, stroke=O, sw=2)
    roof = "M8,80 Q30,74 46,52 L80,18 L114,52 Q130,74 152,80 Q146,90 132,84 L28,84 Q14,90 8,80 Z"
    c.path(roof, c.rg([(0, "#ff9a6a", 1), (0.6, "#d8503a", 1), (1, "#8a2a1a", 1)], 0.4, 0.2, 0.9), sw=5)
    for k in range(7):
        x = 32 + k * 16
        c.path("M%d,82 L%s,%s" % (x, f(x + (80 - x) * 0.42), f(52 - abs(80 - x) * 0.0 + abs(80 - x) * 0.12 - 8)),
               "none", stroke="#a8301e", sw=2.2, extra=op(0.55))
    c.path("M10,80 Q30,74 46,52 L80,18", "none", stroke="#ffc0a0", sw=3, extra=op(0.7))
    c.line(116, 84, 116, 94, stroke=O, sw=2)
    c.ell(116, 102, 8, 10, c.rg([(0, "#fff0a0", 1), (1, "#e8414f", 1)]), sw=3)
    c.circ(80, 16, 6, R(c, GOLD, 0.5, 0.2), sw=3)
    c.save("icon_house", UI_DIR)

    # ---- đĩa món
    c = icon_canvas(160)
    plate(c, 80, 108, 70, 26, band="#4fa3e0")
    rice_mound(c, 60, 108, 34, 40, "#fffdf6")
    c.path("M88,104 Q82,76 104,70 Q128,66 134,88 Q136,106 112,110 Q94,112 88,104 Z",
           c.rg([(0, "#f0a060", 1), (0.5, "#c0602a", 1), (1, "#6a2a0e", 1)], 0.35, 0.3, 0.8), sw=4)
    c.path("M124,74 L140,58", "none", sw=9)
    c.path("M124,74 L140,58", "none", stroke="#fff4e0", sw=4.5)
    c.circ(143, 57, 4.6, "#fff4e0", stroke=O, sw=2.4)
    c.circ(139, 52, 4.4, "#fff4e0", stroke=O, sw=2.4)
    gloss(c, 102, 78, 8, 3, -20, 0.6)
    herb(c, 50, 70, 1.1)
    chili(c, 96, 118, 3)
    for x, y in [(40, 120), (54, 124)]:
        c.ell(x, y, 8, 4, "#dff5b0", stroke="#3f8a2a", sw=2)
    steam(c, [56, 74], 56, 30, 0.85, 4.5)
    c.save("icon_plate", UI_DIR)

    # ---- nhân viên (đầu bếp +)
    c = icon_canvas(160)
    c.shadow(76, 148, 48, 7, 0.25)
    c.path("M30,148 Q30,116 74,114 Q118,116 118,148 Z", c.lg("#ffffff", "#d8e2ec"), sw=5)
    c.path("M64,116 L74,132 L84,116", "#e8414f", sw=3)
    c.circ(74, 80, 38, c.rg([(0, lt(SKIN, 0.45), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.15), 1)], 0.4, 0.35, 0.7), sw=5)
    c.rect(44, 36, 60, 20, "#ffffff", rx=6, sw=5)
    for x, y, r in [(54, 30, 15), (94, 30, 15), (74, 20, 19)]:
        c.circ(x, y, r, c.rg([(0, "#ffffff", 1), (1, "#e2e8ee", 1)], 0.4, 0.3, 0.8), sw=5)
    c.rect(46, 34, 56, 16, "#ffffff", rx=5, stroke=None)
    c.rect(44, 44, 60, 12, c.lg("#ffffff", "#dfe6ee"), rx=5, sw=4)
    for dx in (-13, 13):
        c.ell(74 + dx, 84, 5, 6.5, "#2b1a12", stroke=None)
        c.circ(74 + dx + 2, 81.5, 2, WHITE, stroke=None)
    c.ell(54, 96, 7, 4, "#ff8f8f", stroke=None, extra=op(0.55))
    c.ell(94, 96, 7, 4, "#ff8f8f", stroke=None, extra=op(0.55))
    c.path("M66,98 q8,8 16,0", "none", stroke="#2b1a12", sw=4)
    chunky_circle(c, 124, 118, 24, "#3aa7e8", sw=4.5, depth=4)
    c.path("M124,104 L124,132 M110,118 L138,118", "none", stroke=O, sw=13)
    c.path("M124,104 L124,132 M110,118 L138,118", "none", stroke=WHITE, sw=7)
    c.save("icon_staff", UI_DIR)

    # ---- khách (nút giữa)
    c = icon_canvas(180)
    cx, cy = 90, 98
    c.shadow(90, 170, 56, 7, 0.25)
    c.path("M22,104 Q14,26 92,24 Q166,26 158,104 Q166,140 146,150 L34,150 Q14,140 22,104 Z",
           c.rg([(0, "#8a5a3a", 1), (1, "#4a2a1a", 1)], 0.4, 0.2, 0.8), sw=6)
    for s in (-1, 1):
        c.circ(cx + s * 66, cy + 20, 12, c.rg([(0, lt(SKIN, 0.2), 1), (1, dk(SKIN, 0.1), 1)]), sw=5)
    c.circ(cx, cy + 8, 64, c.rg([(0, lt(SKIN, 0.45), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.15), 1)], 0.42, 0.38, 0.6),
           sw=6)
    c.path("M26,92 Q24,26 92,26 Q156,28 154,92 Q140,62 112,54 Q88,72 56,60 Q36,72 26,92 Z",
           c.rg([(0, "#a8704a", 1), (0.6, "#6a4028", 1), (1, "#3e2416", 1)], 0.4, 0.2, 0.8), sw=5)
    gl_line(c, "M50,46 Q70,34 96,36", w=5, a=0.4)
    for dx in (-24, 24):
        c.ell(cx + dx, cy + 18, 11, 15, "#2b1a12", stroke=None)
        c.circ(cx + dx + 4, cy + 11, 5, WHITE, stroke=None)
        c.circ(cx + dx - 3, cy + 24, 2.2, WHITE, stroke=None, extra=op(0.7))
    c.ell(cx - 44, cy + 40, 12, 7, "#ff8f8f", stroke=None, extra=op(0.55))
    c.ell(cx + 44, cy + 40, 12, 7, "#ff8f8f", stroke=None, extra=op(0.55))
    c.path("M%s,%s q12,14 24,0 Z" % (f(cx - 12), f(cy + 40)), "#c4383a", stroke="#2b1a12", sw=4)
    c.save("icon_customers", UI_DIR)

    # ---- avatar chủ quán
    c = icon_canvas(200)
    c.circ(100, 102, 90, "#4a2a16", sw=6)
    c.circ(100, 99, 90, c.lg("#c98a55", "#7a4a2e"), sw=6)
    c.circ(100, 100, 82, R(c, GOLD, 0.5, 0.25), sw=3.5)
    c.circ(100, 100, 74, c.rg([(0, "#fff3d0", 1), (0.7, "#ffd890", 1), (1, "#f2a85a", 1)], 0.5, 0.4, 0.7),
           stroke="#c47a10", sw=3)
    c.path("M48,168 Q52,140 100,138 Q148,140 152,168 Q126,178 100,178 Q74,178 48,168 Z", c.lg("#e8414f", "#a8242a"),
           sw=5)
    c.path("M88,140 L100,156 L112,140", "#fff3d8", stroke=O, sw=3)
    c.circ(100, 108, 40, c.rg([(0, lt(SKIN, 0.45), 1), (0.7, SKIN, 1), (1, dk(SKIN, 0.15), 1)], 0.42, 0.38, 0.6),
           sw=5)
    c.path("M60,108 Q56,64 100,64 Q144,64 140,108 Q130,86 114,80 Q100,94 80,84 Q66,92 60,108 Z", "#2c2430", sw=4.5)
    # nón lá
    c.path("M22,86 Q100,98 178,86 L104,22 Q100,18 96,22 Z", c.lg("#fff3c0", "#d8b260", 0, 0, 1, 0, mid="#f2d890"),
           sw=5)
    for k in range(4):
        y = 40 + k * 12
        hw = (y - 22) * 1.2
        c.path("M%s,%s Q100,%s %s,%s" % (f(100 - hw), f(y), f(y + 4), f(100 + hw), f(y)), "none", stroke="#c4a050",
               sw=1.8, extra=op(0.8))
    c.path("M22,86 Q100,98 178,86", "none", stroke="#a8803a", sw=3)
    gl_line(c, "M92,30 L52,80", w=4, a=0.6)
    for dx in (-15, 15):
        c.ell(100 + dx, 112, 6, 8, "#2b1a12", stroke=None)
        c.circ(102 + dx, 108, 2.6, WHITE, stroke=None)
    c.ell(74, 126, 8, 5, "#ff8f8f", stroke=None, extra=op(0.6))
    c.ell(126, 126, 8, 5, "#ff8f8f", stroke=None, extra=op(0.6))
    c.path("M90,128 q10,10 20,0", "none", stroke="#2b1a12", sw=4)
    spark(c, 170, 30, 10)
    c.save("avatar", UI_DIR)

    # ---- đơn đặt tiệc (cuộn giấy)
    c = icon_canvas(160)
    c.shadow(80, 150, 56, 8, 0.28)
    c.rect(36, 24, 88, 114, c.lg("#fffaf0", "#f0d8ac"), rx=4, sw=5)
    c.rect(36, 24, 10, 114, "#c9a37a", stroke=None, extra=op(0.25))
    for k in range(4):
        w = 56 if k % 2 == 0 else 40
        c.line(52, 50 + k * 16, 52 + w, 50 + k * 16, stroke="#c9a37a", sw=5)
    for y in (18, 132):
        c.rect(28, y, 104, 16, c.lg("#d89a62", "#8a5530"), rx=8, sw=5)
        for x in (22, 138):
            c.circ(x, y + 8, 8, R(c, "#e8414f", 0.4, 0.2), sw=4)
        gl_line(c, "M36,%d L120,%d" % (y + 5, y + 5), w=2.5, a=0.5)
    c.circ(108, 112, 18, dk("#e8414f", 0.35), sw=4, extra='transform="translate(0 3)"')
    c.circ(108, 112, 18, R(c, "#e8414f", 0.45, 0.2), sw=4)
    c.path(star_d(108, 113, 9, 4), "#ffd0c0", stroke="#a8242a", sw=1.8)
    c.save("icon_order", UI_DIR)

    # ---- sự kiện (pháo hoa)
    c = icon_canvas(160)
    c.circ(80, 80, 72, c.rg([(0, "#fff3b0", 0.8), (0.5, "#ffd34d", 0.25), (1, "#ffc93c", 0)]), stroke=None)
    cols = ["#ffd34d", "#ff6b8b", "#6fd14a", "#4fc3f7", "#b98af0", "#ff9f43"]
    for k in range(12):
        a = k * math.pi / 6 + 0.12
        col = cols[k % 6]
        r1, r2 = 26, 58 if k % 2 == 0 else 48
        x1, y1 = 80 + math.cos(a) * r1, 80 + math.sin(a) * r1
        x2, y2 = 80 + math.cos(a) * r2, 80 + math.sin(a) * r2
        c.line(x1, y1, x2, y2, stroke=O, sw=11)
        c.line(x1, y1, x2, y2, stroke=col, sw=6)
        c.circ(80 + math.cos(a) * (r2 + 10), 80 + math.sin(a) * (r2 + 10), 5, R(c, col, 0.5, 0.15), sw=3)
    c.path(star_d(80, 80, 28, 14, 8, -90), R(c, "#fff3a0", 0.6, 0.1), sw=4.5)
    c.circ(80, 80, 9, WHITE, stroke=None, extra=op(0.85))
    spark(c, 132, 26, 9)
    spark(c, 26, 132, 7)
    c.save("icon_event", UI_DIR)

    # ---- rương
    for name, body, band, trim in [("chest_wood", "#b97a4c", "#6a6f78", "#a8b0ba"),
                                   ("chest_silver", "#a9bccd", "#5a6b80", "#e4ecf4"),
                                   ("chest_gold", "#ffc93c", "#c4700a", "#fff3a0")]:
        c = icon_canvas(160)
        if name == "chest_gold":
            c.circ(80, 84, 76, c.rg([(0, "#fff3b0", 0.85), (0.55, "#ffd34d", 0.3), (1, "#ffc93c", 0)]), stroke=None)
        c.shadow(80, 146, 64, 9, 0.32)
        bx = "M18,78 L142,78 L140,136 Q140,144 132,144 L28,144 Q20,144 20,136 Z"
        c.path(bx, c.lg(body, dk(body, 0.35), 0, 0, 0, 1), sw=5)
        if name == "chest_wood":
            for y in (96, 114, 130):
                c.line(24, y, 136, y, stroke=dk(body, 0.45), sw=2, extra=op(0.6))
        lid = "M18,80 Q16,30 80,28 Q144,30 142,80 Z"
        c.path(lid, c.rg([(0, lt(body, 0.45), 1), (0.6, body, 1), (1, dk(body, 0.25), 1)], 0.35, 0.25, 0.9), sw=5)
        if name == "chest_wood":
            for y in (46, 62):
                c.path("M%d,%d Q80,%d %d,%d" % (22, y + 6, y - 6, 138, y + 6), "none", stroke=dk(body, 0.4), sw=2,
                       extra=op(0.6))
        for x in (40, 120):
            c.rect(x - 7, 47, 14, 96, c.lg(trim, band, 0, 0, 1, 0, mid=lt(band, 0.3)), rx=3, stroke=O, sw=3)
        c.rect(14, 72, 132, 14, c.lg(trim, band), rx=5, sw=4.5)
        for x in (40, 120):
            for y in (79, 110, 134):
                c.circ(x, y, 2.4, lt(trim, 0.4), stroke=dk(band, 0.3), sw=1)
        c.rect(64, 70, 32, 38, dk(GOLD_D, 0.3), rx=7, sw=4.5, extra='transform="translate(0 3)"')
        c.rect(64, 70, 32, 38, R(c, GOLD, 0.55, 0.2), rx=7, sw=4.5)
        c.circ(80, 85, 5, O, stroke=None)
        c.path("M77,87 L75,99 L85,99 L83,87 Z", O, stroke=None)
        gl_line(c, "M30,64 Q32,40 70,34", w=5, a=0.55)
        if name == "chest_gold":
            for x, y, col in [(80, 48, "#e8414f"), (54, 54, "#4fc3f7"), (106, 54, "#6fd14a")]:
                c.path("M%d,%d l7,7 l-7,7 l-7,-7 Z" % (x, y - 7), R(c, col, 0.5, 0.2), sw=2.5)
            spark(c, 140, 30, 11)
            spark(c, 22, 40, 8)
            spark(c, 138, 110, 6)
        elif name == "chest_silver":
            spark(c, 136, 34, 7, WHITE, 0.9)
        c.save(name, UI_DIR)

    # ---- điểm nghiên cứu (128)
    c = icon_canvas(128)
    c.circ(64, 40, 34, c.rg([(0, "#fff6b0", 0.9), (0.6, "#ffd34d", 0.3), (1, "#ffc93c", 0)]), stroke=None)
    c.shadow(64, 118, 50, 6, 0.28)
    c.path("M10,62 Q36,52 64,64 Q92,52 118,62 L118,114 Q92,104 64,116 Q36,104 10,114 Z", c.lg("#3a7fc4", "#24558a"),
           sw=5)
    c.path("M14,56 Q38,46 64,58 L64,108 Q38,98 14,106 Z", c.lg("#fffaf0", "#efdcb8", 0, 0, 1, 0), sw=4)
    c.path("M114,56 Q90,46 64,58 L64,108 Q90,98 114,106 Z", c.lg("#f2e0c0", "#fffaf0", 0, 0, 1, 0), sw=4)
    for k in range(3):
        y = 68 + k * 11
        c.path("M22,%d Q38,%d 56,%d" % (y, y - 5, y + 2), "none", stroke="#c9a37a", sw=2.6)
        c.path("M72,%d Q90,%d 106,%d" % (y + 2, y - 5, y), "none", stroke="#c9a37a", sw=2.6)
    # bóng đèn ý tưởng
    c.rect(57, 44, 14, 12, c.lg("#c8d0d8", "#7c8791", 0, 0, 1, 0), rx=3, sw=3.4)
    c.line(58, 49, 70, 49, stroke="#5b6670", sw=1.6)
    c.path("M56,46 Q44,36 46,24 Q50,8 64,8 Q78,8 82,24 Q84,36 72,46 Z", R(c, "#ffe066", 0.7, 0.15, 0.4, 0.3, 0.8),
           sw=4)
    c.path("M59,40 L59,30 Q64,24 69,30 L69,40", "none", stroke="#e8901a", sw=2.4)
    gloss(c, 56, 20, 5, 3, -30, 0.85)
    spark(c, 96, 18, 7)
    spark(c, 30, 24, 5)
    c.save("icon_rp", UI_DIR)

    # ---- bình nghiên cứu
    c = icon_canvas(160)
    c.shadow(80, 148, 52, 8, 0.28)
    fl = "M62,22 L98,22 L98,62 L134,122 Q142,142 118,142 L42,142 Q18,142 26,122 L62,62 Z"
    c.path(fl, c.lg("#f4fbff", "#c8e4f4", 0, 0, 1, 0), sw=5, extra=op(0.95))
    c.path("M47,96 L113,96 L130,124 Q135,137 118,137 L42,137 Q25,137 30,124 Z",
           c.lg("#c9a0ff", "#6a3fc4"), stroke=None)
    c.ell(80, 96, 33, 5, "#e0c8ff", stroke=None)
    for x, y, r in [(62, 118, 7), (90, 110, 5), (100, 126, 4), (76, 86, 4), (84, 72, 3), (70, 58, 2.6)]:
        c.circ(x, y, r, WHITE, stroke=None, extra=op(0.75))
    c.path(fl, "none", sw=5)
    gl_line(c, "M68,30 L68,64 L40,116", w=5, a=0.8)
    c.rect(56, 10, 48, 16, c.lg("#d89a62", "#8a5530"), rx=5, sw=4.5)
    spark(c, 124, 40, 8)
    spark(c, 30, 56, 5)
    c.save("icon_research", UI_DIR)

    # ---- bộ thẻ
    c = icon_canvas(160)
    c.shadow(80, 150, 60, 8, 0.28)
    for k, (dx, rot, col, gem) in enumerate([(-17, -13, "#5fa8e8", "#4fc3f7"), (17, 13, "#b98af0", "#ff6bb3"),
                                             (0, 0, "#ffc93c", "#e8414f")]):
        c.group("translate(80 128) scale(0.92) rotate(%d) translate(-80 -130)" % rot)
        x0 = 46 + dx
        c.rect(x0, 18, 68, 104, c.lg(lt(col, 0.3), dk(col, 0.2)), rx=10, sw=5)
        c.rect(x0 + 7, 25, 54, 62, c.rg([(0, "#fffaf0", 1), (1, "#f2dcb4", 1)], 0.5, 0.4, 0.7), rx=6,
               stroke=dk(col, 0.3), sw=2)
        c.path("M%d,87 Q%d,64 %d,64 Q%d,64 %d,87 Z" % (x0 + 12, x0 + 14, x0 + 34, x0 + 54, x0 + 56),
               c.lg("#e8414f", "#a8242a"), stroke=None)
        c.circ(x0 + 34, 50, 13, R(c, SKIN, 0.4, 0.15), stroke=O, sw=2.5)
        c.path("M%d,48 Q%d,32 %d,48 Q%d,40 %d,48 Z" % (x0 + 21, x0 + 34, x0 + 47, x0 + 34, x0 + 21), "#3a2a20",
               stroke=None)
        c.rect(x0 + 7, 25, 54, 62, "none", rx=6, stroke=dk(col, 0.3), sw=2)
        c.path("M%d,96 l7,7 l-7,7 l-7,-7 Z" % (x0 + 34), R(c, gem, 0.5, 0.2), stroke=O, sw=2.5)
        gl_line(c, "M%d,24 L%d,110" % (x0 + 4, x0 + 4), w=2.5, a=0.5)
        c.end()
    spark(c, 136, 20, 8)
    c.save("icon_cards", UI_DIR)

    # ---- vòng quay
    c = icon_canvas(160)
    c.shadow(80, 150, 46, 7, 0.28)
    c.path("M64,124 L56,148 L104,148 L96,124 Z", c.lg("#c98a55", "#7a4a2e"), sw=4.5)
    cx, cy, R0 = 80, 78, 66
    c.circ(cx, cy + 5, R0, "#7a3a16", sw=5)
    c.circ(cx, cy, R0, R(c, "#e8a050", 0.4, 0.3), sw=5)
    cols = ["#ff5a5a", "#ffd34d", "#6fd14a", "#4fc3f7", "#b98af0", "#ff9f43", "#ef7fb0", "#5fd1c4"]
    rr = 54
    for k in range(8):
        a0 = k * math.pi / 4 - math.pi / 2 - math.pi / 8
        a1 = a0 + math.pi / 4
        p0 = (cx + math.cos(a0) * rr, cy + math.sin(a0) * rr)
        p1 = (cx + math.cos(a1) * rr, cy + math.sin(a1) * rr)
        c.path("M%d,%d L%s,%s A%d,%d 0 0 1 %s,%s Z" % (cx, cy, f(p0[0]), f(p0[1]), rr, rr, f(p1[0]), f(p1[1])),
               c.rg([(0, lt(cols[k], 0.45), 1), (1, cols[k], 1)], 0.5, 0.5, 0.6), stroke="#fff6e0", sw=2.4)
    c.circ(cx, cy, rr, "none", stroke=O, sw=3)
    for k in range(16):
        a = k * math.pi / 8
        c.circ(cx + math.cos(a) * 60, cy + math.sin(a) * 60, 2.8, "#fff6c0" if k % 2 else "#ffffff",
               stroke="#a35a08", sw=1)
    c.path("M28,52 A56,56 0 0 1 60,26", "none", stroke=WHITE, sw=5, extra='stroke-opacity="0.45"')
    c.circ(cx, cy, 15, R(c, GOLD, 0.55, 0.2), sw=4)
    c.path(star_d(cx, cy + 1, 8, 3.5), "#fff6c0", stroke=None)
    c.path("M68,8 L92,8 Q96,8 94,12 L82,32 Q80,35 78,32 L66,12 Q64,8 68,8 Z", R(c, "#e8414f", 0.45, 0.2), sw=4)
    c.save("icon_wheel", UI_DIR)


# ================================================================ HUY HIỆU KHÁCH (96)

def badges():
    c = icon_canvas(96)
    chunky_circle(c, 48, 45, 38, "#ff8a4a", sw=4.5, depth=5)
    c.path("M26,32 L42,40 M70,32 L54,40", "none", stroke=O, sw=5)
    c.ell(37, 50, 4, 5, O, stroke=None)
    c.ell(59, 50, 4, 5, O, stroke=None)
    c.path("M34,68 Q48,58 62,68", "none", stroke=O, sw=5)
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        c.path("M%d,%d q%d,0 %d,%d" % (76 + dx * 2, 16 + dy * 2, dx * 4, dx * 4, dy * 5), "none", stroke="#e8414f",
               sw=3.2)
    c.save("badge_picky", UI_DIR)

    c = icon_canvas(96)
    c.shadow(48, 88, 36, 5, 0.25)
    c.rect(30, 16, 28, 14, "#3a3c42", rx=4, sw=4)
    c.rect(10, 28, 76, 52, dk("#4a4e58", 0.3), rx=11, sw=4.5, extra='transform="translate(0 4)"')
    c.rect(10, 28, 76, 52, c.lg("#6a707c", "#33363e"), rx=11, sw=4.5)
    c.rect(10, 44, 76, 10, "#c98a55", stroke=None, extra=op(0.85))
    c.circ(48, 54, 18, c.lg("#9aa2ae", "#4a4e58"), sw=4)
    c.circ(48, 54, 11, c.rg([(0, "#bfe8ff", 1), (0.6, "#3a7fc4", 1), (1, "#1a3a6a", 1)], 0.35, 0.3, 0.8), sw=2.5)
    c.circ(44, 50, 3.5, WHITE, stroke=None, extra=op(0.85))
    c.circ(74, 38, 4.5, "#ffd34d", stroke=O, sw=2)
    gl_line(c, "M17,34 L36,34", w=3, a=0.5)
    c.save("badge_tourist", UI_DIR)

    c = icon_canvas(96)
    hd = "M48,84 C18,64 6,46 12,30 C18,14 40,14 48,30 C56,14 78,14 84,30 C90,46 78,64 48,84 Z"
    c.shadow(48, 88, 30, 4, 0.25)
    extrude_path(c, hd, GOLD_D, 4, 4.5)
    c.path(hd, R(c, GOLD, 0.6, 0.2, 0.32, 0.25, 0.85), sw=4.5)
    c.path(star_d(48, 46, 14, 6.5), "#fff6c0", stroke="#c47a10", sw=2)
    gloss(c, 28, 32, 8, 4.5, -40, 0.75)
    spark(c, 80, 14, 7)
    c.save("badge_regular", UI_DIR)


# ================================================================ BONG BÓNG THOẠI (120x120, neo 60,112)

def bubbles():
    bub = "M60,112 L47,94 Q12,92 10,56 Q10,12 60,10 Q110,12 110,56 Q108,92 73,94 Z"

    def bubble():
        c = C(120, 120, 60, 112)
        c.path(bub, "#000000", stroke=None, extra='opacity="0.12" transform="translate(2 4)"')
        c.path(bub, c.rg([(0, "#ffffff", 1), (0.75, "#fbf6ee", 1), (1, "#e8dccb", 1)], 0.4, 0.3, 0.8), sw=5)
        gl_line(c, "M22,44 Q28,22 52,18", w=4, a=0.9)
        return c
    bubble().save("bubble")

    def face(name, col, mouth, brow=None, extra=None):
        c = bubble()
        c.circ(60, 55, 30, dk(col, 0.3), sw=4, extra='transform="translate(0 3)"')
        c.circ(60, 55, 30, R(c, col, 0.55, 0.2), sw=4)
        c.ell(50, 50, 4.2, 6, "#2b1a12", stroke=None)
        c.ell(70, 50, 4.2, 6, "#2b1a12", stroke=None)
        c.circ(51.5, 47.5, 1.6, WHITE, stroke=None)
        c.circ(71.5, 47.5, 1.6, WHITE, stroke=None)
        c.path(mouth, "#a8242a" if "Z" in mouth else "none", stroke="#2b1a12", sw=4)
        if brow:
            c.path(brow, "none", stroke="#2b1a12", sw=4)
        c.ell(42, 63, 5, 3, "#ff7a7a", stroke=None, extra=op(0.5))
        c.ell(78, 63, 5, 3, "#ff7a7a", stroke=None, extra=op(0.5))
        gloss(c, 47, 37, 8, 4, -30, 0.6)
        if extra:
            extra(c)
        c.save(name)
    face("face_happy", "#ffd34d", "M46,62 Q60,80 74,62 Z")
    face("face_neutral", "#ffc56b", "M49,68 L71,68")

    def anger(c):
        c.path("M84,26 l0,8 M80,30 l8,0", "none", stroke="#e8414f", sw=0)
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            c.path("M%d,%d q%d,%d %d,%d" % (88 + dx * 2, 28 + dy * 2, dx * 4, 0, dx * 4, dy * 5), "none",
                   stroke="#e8414f", sw=3.2)
    face("face_angry", "#ff7a4a", "M48,72 Q60,62 72,72", "M40,38 L55,45 M80,38 L65,45", anger)

    c = bubble()
    hd = "M60,88 C32,70 22,54 28,40 C34,26 54,26 60,40 C66,26 86,26 92,40 C98,54 88,70 60,88 Z"
    extrude_path(c, hd, "#e8414f", 3, 4)
    c.path(hd, R(c, "#f2475a", 0.55, 0.2, 0.32, 0.25, 0.85), sw=4)
    gloss(c, 40, 42, 7, 4, -40, 0.75)
    c.path("M92,22 C86,18 86,12 89,10 C92,8 94,11 94,13 C94,11 96,8 99,10 C102,12 102,18 92,22 Z", "#ff8fa0",
           stroke="#c4283a", sw=1.6)
    c.save("face_heart")

    c = bubble()
    zp = [(0, 0), (26, 0), (26, 6), (10, 22), (26, 22), (26, 28), (0, 28), (0, 22), (16, 6), (0, 6)]
    for x, y, s in [(24, 46, 1.0), (56, 33, 0.75), (80, 22, 0.55)]:
        pts_ = [(x + px * s, y + py * s) for px, py in zp]
        c.group("translate(0 2.5)")
        c.poly(pts_, "#24508a", sw=3.4)
        c.end()
        c.poly(pts_, c.lg("#bfe6ff", "#3a7fd8"), sw=3.4)
    c.save("bubble_zzz")


# ================================================================ NÚT TRÒN THANH ĐIỀU HƯỚNG

def nav_buttons():
    for name, rim1, rim2, sel in [("nav_circle", "#f2dcb4", "#c99a64", False),
                                  ("nav_circle_sel", "#fff0a0", "#e89b16", True)]:
        c = C(240, 252, 120, 120)
        c.ell(120, 236, 94, 13, c.rg([(0, "#000000", 0.3), (1, "#000000", 0)]), stroke=None)
        if sel:
            c.circ(120, 120, 118, c.rg([(0.7, "#fff0b0", 0.95), (0.86, "#ffd34d", 0.45), (1, "#ffc93c", 0)]),
                   stroke=None)
        c.circ(120, 130, 104, dk(rim2, 0.3), stroke=O, sw=5)
        c.circ(120, 118, 104, c.lg(rim1, rim2), stroke=O, sw=5)
        c.path("M28,112 A92,92 0 0 1 172,40", "none", stroke=WHITE, sw=6, extra='stroke-opacity="0.55"')
        c.path("M212,128 A92,92 0 0 1 150,206", "none", stroke=dk(rim2, 0.3), sw=5, extra='stroke-opacity="0.35"')
        for k in range(8):
            a = k * math.pi / 4 + math.pi / 8
            x, y = 120 + math.cos(a) * 96, 118 + math.sin(a) * 96
            c.circ(x, y, 3.2, lt(rim1, 0.5), stroke=dk(rim2, 0.3), sw=1.4)
        c.circ(120, 116, 87, dk(rim2, 0.15), stroke=None)
        c.circ(120, 119, 86, c.rg([(0, "#fffdf6", 1), (0.72, "#fbecd2", 1), (1, "#ecd0a4", 1)], 0.5, 0.42, 0.62),
               stroke=dk(rim2, 0.25), sw=3)
        c.path("M56,92 Q120,22 184,92 Q120,54 56,92 Z", WHITE, stroke=None, extra=op(0.5))
        if sel:
            spark(c, 32, 40, 12)
            spark(c, 214, 70, 8)
            spark(c, 206, 196, 10)
        c.save(name, UI_DIR)


# ================================================================ KHU VỰC (200x170) & CHƯƠNG (240x180)

def area_thumbs():
    for name in ("area_hall", "area_garden", "area_vip", "area_lodging"):
        c = C(200, 170, 100, 128)
        s = 0.33

        def p(x, y, z=0):
            return (100 + (x - y) * 128 * s, 108 + (x + y) * 64 * s - z * s)

        def ibox(x0, y0, x1, y1, z0, z1, col, sw=2.6):
            top = [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
            lf = [p(x0, y1, z1), p(x1, y1, z1), p(x1, y1, z0), p(x0, y1, z0)]
            rt = [p(x1, y0, z1), p(x1, y1, z1), p(x1, y1, z0), p(x1, y0, z0)]
            c.poly(lf, dk(col, 0.12), stroke=O, sw=sw)
            c.poly(rt, dk(col, 0.3), stroke=O, sw=sw)
            c.poly(top, c.lg(lt(col, 0.3), col), stroke=O, sw=sw)

        floor_col, wall_l, wall_r, trim = {
            "area_hall": ("#e9b57a", "#fbe3bc", "#f2d2a0", "#a8683d"),
            "area_garden": ("#8fd06a", "#f6e3bd", "#ead2a4", "#7a4a2e"),
            "area_vip": ("#b8303a", "#c4483e", "#a8343a", "#ffc93c"),
            "area_lodging": ("#d8b890", "#cfe0f2", "#b8cde6", "#7a5a3a")}[name]
        c.shadow(100, 158, 90, 10, 0.25)
        # đế sàn dày
        c.poly([p(-1, 1), p(1, 1), p(1, -1), p(1, -1, -22), p(1, 1, -22), p(-1, 1, -22)], dk(floor_col, 0.35), sw=4)
        c.poly([p(-1, 1), p(1, 1), p(1, 1, -22), p(-1, 1, -22)], dk(floor_col, 0.2), stroke=None)
        c.poly([p(-1, -1), p(1, -1), p(1, 1), p(-1, 1)], c.lg(lt(floor_col, 0.2), dk(floor_col, 0.08), 0, 0, 1, 1),
               sw=4)
        if name in ("area_hall", "area_lodging"):
            for k in range(1, 8):
                t = -1 + k * 0.25
                a, b = p(t, -1), p(t, 1)
                c.line(a[0], a[1], b[0], b[1], stroke=dk(floor_col, 0.2), sw=1.4, extra=op(0.7))
        elif name == "area_garden":
            for k, (x, y) in enumerate([(-0.4, 0.6), (0.0, 0.2), (0.4, -0.2), (0.75, -0.55)]):
                q = p(x, y)
                c.ell(q[0], q[1], 13, 6.5, "#d8d0c0", stroke=O, sw=2)
            for x, y in [(0.6, 0.6), (-0.6, -0.3), (0.2, 0.8)]:
                q = p(x, y)
                c.path("M%s,%s l-3,-6 M%s,%s l0,-7 M%s,%s l3,-6" % (f(q[0]), f(q[1]), f(q[0]), f(q[1]), f(q[0]),
                                                                    f(q[1])), "none", stroke="#3f8a2a", sw=2)
        elif name == "area_vip":
            c.poly([p(-0.8, -0.8), p(0.8, -0.8), p(0.8, 0.8), p(-0.8, 0.8)], "none", stroke=GOLD, sw=3)
            c.poly([p(-0.6, -0.6), p(0.6, -0.6), p(0.6, 0.6), p(-0.6, 0.6)], c.lg("#d8404a", "#9a2030"),
                   stroke="#ffd34d", sw=1.6)
        if name == "area_lodging":
            c.poly([p(-0.3, -0.1), p(0.5, -0.1), p(0.5, 0.7), p(-0.3, 0.7)], c.lg("#7fb8e8", "#4a8ac4"), stroke=O,
                   sw=2)
        # tường
        H = 150
        if name == "area_garden":
            H = 60
        c.poly([p(-1, -1), p(-1, 1), p(-1, 1, H), p(-1, -1, H)], c.lg(lt(wall_l, 0.1), dk(wall_l, 0.05)), sw=4)
        c.poly([p(-1, -1), p(1, -1), p(1, -1, H), p(-1, -1, H)], c.lg(wall_r, dk(wall_r, 0.08)), sw=4)
        for side in ("l", "r"):
            if side == "l":
                a0, a1 = p(-1, -1, 10), p(-1, 1, 10)
            else:
                a0, a1 = p(-1, -1, 10), p(1, -1, 10)
            c.line(a0[0], a0[1], a1[0], a1[1], stroke=trim, sw=5)
        tl, tr_ = p(-1, -1, H), p(-1, 1, H)
        c.line(tl[0], tl[1], tr_[0], tr_[1], stroke=lt(wall_l, 0.5), sw=2.5)
        if name == "area_garden":
            for k in range(5):
                for side in (0, 1):
                    t = -1 + k * 0.5
                    q = p(-1, t, H) if side == 0 else p(t, -1, H)
                    c.circ(q[0], q[1] - 4, 9, R(c, "#5fb84a", 0.4, 0.25), stroke=O, sw=2.4)
            # cây
            q = p(0.45, 0.35)
            c.rect(q[0] - 4, q[1] - 30, 8, 30, "#8a5530", rx=2, stroke=O, sw=2.4)
            for dx, dy, r in [(0, -48, 22), (-16, -36, 15), (16, -36, 15)]:
                c.circ(q[0] + dx, q[1] + dy, r, R(c, "#5fb84a", 0.45, 0.25), stroke=O, sw=3)
            for dx, dy in [(-8, -50), (10, -40), (-14, -32)]:
                c.circ(q[0] + dx, q[1] + dy, 3, "#ff8fb0", stroke="#c44a70", sw=1)
            q = p(-0.5, 0.35)
            for dx in (-12, 0, 12):
                c.circ(q[0] + dx, q[1] - 8, 8, R(c, "#6cc04a", 0.4, 0.25), stroke=O, sw=2.2)
                c.circ(q[0] + dx, q[1] - 12, 3, "#ffd34d", stroke="#c47a10", sw=1)
        elif name == "area_hall":
            # cửa sổ tường phải
            a, b = p(-0.2, -1, 110), p(0.4, -1, 60)
            c.poly([p(-0.2, -1, 110), p(0.4, -1, 110), p(0.4, -1, 60), p(-0.2, -1, 60)], c.lg("#e6f8ff", "#9fd8f0"),
                   sw=3)
            # bàn
            for x, y in [(-0.35, 0.35), (0.45, 0.25)]:
                ibox(x - 0.04, y - 0.04, x + 0.04, y + 0.04, 0, 26, "#8a5530", sw=2)
                ibox(x - 0.24, y - 0.24, x + 0.24, y + 0.24, 26, 34, "#c98a55")
                q = p(x, y, 34)
                c.ell(q[0], q[1] - 3, 7, 3.4, "#ffffff", stroke=O, sw=1.8)
                c.ell(q[0], q[1] - 4, 4.6, 1.8, "#f2b05a", stroke=None)
            # đèn lồng
            q = p(-1, 0.2, 135)
            c.line(q[0] + 30, q[1] - 8, q[0] + 30, q[1] + 4, stroke=O, sw=2)
            c.ell(q[0] + 30, q[1] + 14, 9, 11, c.rg([(0, "#fff0a0", 1), (1, "#e8414f", 1)]), stroke=O, sw=2.6)
        elif name == "area_vip":
            for k in range(3):
                a0 = p(-1, -1 + 0.5 * (k + 1), 20)
                a1 = p(-1, -1 + 0.5 * (k + 1), H - 10)
                c.line(a0[0], a0[1], a1[0], a1[1], stroke="#ffd34d", sw=2, extra=op(0.8))
                b0 = p(-1 + 0.5 * (k + 1), -1, 20)
                b1 = p(-1 + 0.5 * (k + 1), -1, H - 10)
                c.line(b0[0], b0[1], b1[0], b1[1], stroke="#ffd34d", sw=2, extra=op(0.8))
            q = p(0.05, 0.05)
            c.ell(q[0], q[1] - 4, 34, 14, "#7a1a22", stroke=O, sw=2.6)
            c.ell(q[0], q[1] - 12, 34, 14, c.lg("#fff0a0", "#e8a020"), stroke=O, sw=3)
            c.ell(q[0], q[1] - 13, 9, 4, WHITE, stroke=O, sw=1.6)
            c.ell(q[0], q[1] - 15, 6, 2, "#e8414f", stroke=None)
            for dx in (-38, 38):
                c.rect(q[0] + dx - 6, q[1] - 26, 12, 20, c.lg("#e8414f", "#8a1a22"), rx=4, stroke=O, sw=2.4)
            q = p(-1, -1, H)
            c.line(q[0], q[1], q[0], q[1] + 18, stroke=O, sw=2)
            c.path("M%s,%s l-14,10 l28,0 Z" % (f(q[0]), f(q[1] + 16)), R(c, GOLD, 0.5, 0.2), stroke=O, sw=2.4)
            for dx in (-10, 0, 10):
                c.circ(q[0] + dx, q[1] + 30, 2.6, "#fff6c0", stroke=None)
            spark(c, 170, 40, 9)
        elif name == "area_lodging":
            c.poly([p(0.0, -1, 120), p(0.5, -1, 120), p(0.5, -1, 70), p(0.0, -1, 70)], c.lg("#e6f8ff", "#9fd8f0"),
                   sw=3)
            ibox(-0.95, -0.25, -0.1, 0.55, 0, 22, "#a8683d")
            ibox(-0.92, -0.22, -0.13, 0.52, 22, 34, "#ffffff")
            ibox(-0.92, -0.22, -0.55, 0.52, 34, 37, "#5fa8e8", sw=2)
            ibox(-0.9, -0.15, -0.25, 0.1, 34, 44, "#fffaf0", sw=2)
            ibox(0.55, -0.95, 0.85, -0.65, 0, 28, "#c98a55")
            q = p(0.7, -0.8, 28)
            c.rect(q[0] - 2, q[1] - 14, 4, 14, O, stroke=None)
            c.path("M%s,%s l-9,0 l5,-12 l8,0 Z" % (f(q[0] + 4), f(q[1] - 12)), c.lg("#fff6c0", "#ffc860"),
                   stroke=O, sw=2)
        c.save(name, UI_DIR)


def chapter_frame(c, sky1, sky2, ground1, ground2, gy=128):
    c.rect(6, 8, 228, 168, "#3a2414", rx=26, stroke=None, extra=op(0.25))
    c.rect(6, 6, 228, 166, c.lg(sky1, sky2), rx=26, stroke=None)
    c.path("M9,%d L231,%d L231,146 Q231,169 208,169 L32,169 Q9,169 9,146 Z" % (gy, gy),
           c.lg(ground1, ground2), stroke=None)


def chapter_close(c):
    c.rect(6, 6, 228, 166, "none", rx=26, stroke=O, sw=6)
    c.rect(11, 11, 218, 156, "none", rx=22, stroke=WHITE, sw=2.5, extra='stroke-opacity="0.45"')


def tube_house(c, x, w, h, wall, roof, gy=130, shutter="#3f8a5a"):
    y = gy - h
    c.rect(x, y, w, h, c.lg(lt(wall, 0.15), dk(wall, 0.1), 0, 0, 1, 0), sw=3.5)
    c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(x - 5), f(y + 2), f(x + 4), f(y - 12), f(x + w - 4), f(y - 12),
                                              f(x + w + 5), f(y + 2)), c.lg(lt(roof, 0.2), dk(roof, 0.15)), sw=3.5)
    for k in range(1, 4):
        xx = x + k * w / 4.0
        c.line(xx - 2, y - 10, xx - 3, y, stroke=dk(roof, 0.35), sw=1.4)
    rows = int((h - 30) / 26)
    for r in range(rows):
        yy = y + 10 + r * 26
        c.rect(x + w / 2 - 9, yy, 18, 16, "#fff2c0", rx=2, stroke=O, sw=2)
        c.rect(x + w / 2 - 15, yy, 6, 16, shutter, rx=1, stroke=O, sw=1.6)
        c.rect(x + w / 2 + 9, yy, 6, 16, shutter, rx=1, stroke=O, sw=1.6)
        c.rect(x + 3, yy + 18, w - 6, 3, dk(wall, 0.35), stroke=None)
    c.rect(x + w / 2 - 8, gy - 22, 16, 22, "#8a5530", rx=2, stroke=O, sw=2.4)


def chapter_thumbs():
    # 1. Hà Nội phố cổ
    c = C(240, 180, 120, 90)
    chapter_frame(c, "#ffe2b0", "#ffb37a", "#d9a46c", "#b8804a")
    c.circ(186, 46, 20, c.rg([(0, "#fff6d0", 1), (1, "#ffd27a", 1)]), stroke=None)
    for x, w, h in [(14, 30, 60), (150, 40, 70), (196, 30, 54)]:
        c.rect(x, 130 - h, w, h, "#e8a888", stroke=None, extra=op(0.6))
    c.rect(26, 92, 7, 38, "#7a4a2e", stroke=O, sw=2.5)
    c.circ(31, 80, 18, R(c, "#5fb84a", 0.4, 0.25), sw=3.5)
    c.circ(24, 98, 11, R(c, "#4fae3c", 0.4, 0.25), sw=3.5)
    for x, w, h, wall, roof in [(46, 36, 78, "#ffe2a0", "#b8442e"), (82, 34, 96, "#f6c890", "#a83a2a"),
                                (116, 38, 70, "#fbe8c8", "#c4583a"), (154, 36, 88, "#f2d070", "#a8442e"),
                                (190, 30, 62, "#f6dcb8", "#b8442e")]:
        tube_house(c, x, w, h, wall, roof)
    for x, y, col in [(60, 60, "#e8414f"), (104, 50, "#e8414f"), (140, 70, "#ffb347")]:
        c.ell(x, y, 5, 6, c.rg([(0, "#fff0a0", 1), (1, col, 1)]), stroke=O, sw=1.8)
    c.rect(14, 136, 212, 4, "#a8743a", stroke=None, extra=op(0.5))
    for k in range(9):
        c.line(18 + k * 25, 140, 14 + k * 25, 166, stroke="#a8743a", sw=1.4, extra=op(0.5))
    # bàn ghế nhựa vỉa hè + gánh hàng
    c.rect(96, 142, 34, 6, c.lg("#7fb8e8", "#3a7fc4"), rx=2, stroke=O, sw=2.2)
    c.rect(100, 148, 4, 10, "#3a7fc4", stroke=O, sw=1.6)
    c.rect(122, 148, 4, 10, "#3a7fc4", stroke=O, sw=1.6)
    c.ell(113, 140, 6, 2.6, WHITE, stroke=O, sw=1.6)
    for x in (80, 140, 154):
        c.path("M%d,148 L%d,148 L%d,160 L%d,160 Z" % (x - 7, x + 7, x + 5, x - 5), c.lg("#ff6a5a", "#c4283a"), stroke=O,
               sw=2)
    c.line(30, 150, 74, 142, stroke="#8a5530", sw=3)
    for x, y in [(32, 150), (72, 142)]:
        c.line(x, y, x, y + 8, stroke=O, sw=1.4)
        c.ell(x, y + 11, 8, 4, c.lg("#e8b06a", "#a8683d"), stroke=O, sw=2)
    chapter_close(c)
    c.save("chapter_1", UI_DIR)

    # 2. Hội An: phố vàng + đèn lồng + sông
    c = C(240, 180, 120, 90)
    chapter_frame(c, "#5a4a9a", "#ff9a8a", "#3a7fa8", "#245a80", gy=136)
    for x, y in [(30, 24), (80, 16), (150, 28), (206, 20)]:
        spark(c, x, y, 4, "#fff6c0", 0.9)
    for x, w, h in [(16, 52, 70), (68, 48, 82), (116, 56, 66), (172, 52, 78)]:
        y = 136 - h
        c.rect(x, y, w, h, c.lg("#ffe070", "#e8a820"), sw=3.5)
        c.path("M%s,%s L%s,%s L%s,%s L%s,%s Z" % (f(x - 4), f(y + 4), f(x + 8), f(y - 16), f(x + w - 8),
                                                  f(y - 16), f(x + w + 4), f(y + 4)), c.lg("#b8704a", "#5a2e1a"),
               sw=3.5)
        for k in range(1, 6):
            xx = x + w * k / 6.0
            c.line(xx + (xx - x - w / 2) * 0.12, y + 2, xx, y - 14, stroke="#4a2410", sw=1.3, extra=op(0.6))
        c.rect(x + w / 2 - 9, 136 - 26, 18, 26, "#2f7a5a", rx=2, stroke=O, sw=2.2)
        c.rect(x + 6, y + 14, 14, 14, "#fff2c0", rx=2, stroke=O, sw=2)
        if w > 50:
            c.rect(x + w - 20, y + 14, 14, 14, "#fff2c0", rx=2, stroke=O, sw=2)
    c.path("M10,40 Q60,64 120,46 Q180,64 230,42", "none", stroke=O, sw=1.6)
    for k, col in enumerate(["#e8414f", "#ffb347", "#ff6bb3", "#e8414f", "#ffd34d", "#ff6bb3", "#e8414f",
                             "#ffb347", "#ff6bb3"]):
        x = 22 + k * 24
        t = (x - 10) / 110.0 if x < 120 else (x - 120) / 110.0
        y = (40 + (46 - 40) * t + 24 * 4 * t * (1 - t) * 0.5) if x < 120 else (46 + (42 - 46) * t + 18 * 4 * t * (1 - t) * 0.5)
        c.circ(x, y + 8, 11, c.rg([(0, "#fff6b0", 0.6), (1, col, 0)]), stroke=None)
        c.ell(x, y + 8, 6, 7.5, c.rg([(0, "#fff0a0", 1), (1, col, 1)]), stroke=O, sw=1.8)
    for k in range(4):
        c.path("M%d,%d q10,-4 20,0" % (24 + k * 54, 146 + (k % 2) * 8), "none", stroke="#9fd8f0", sw=2.4)
    c.path("M126,150 L176,150 Q172,162 152,162 Q132,162 126,150 Z", c.lg("#c98a55", "#7a4a2e"), sw=3)
    c.ell(150, 151, 26, 3, "#a8683d", stroke=None)
    c.path("M144,150 Q150,138 158,150 Z", "#e8a820", stroke=O, sw=2)
    chapter_close(c)
    c.save("chapter_2", UI_DIR)

    # 3. Sài Gòn: đô thị hiện đại
    c = C(240, 180, 120, 90)
    chapter_frame(c, "#ffd2a0", "#ff8a6a", "#8a8a9a", "#5a5a6a", gy=134)
    c.circ(60, 60, 24, c.rg([(0, "#fff6d0", 1), (1, "#ffc06a", 1)]), stroke=None)
    for x, w, h in [(12, 30, 60), (176, 28, 72), (110, 30, 56)]:
        c.rect(x, 134 - h, w, h, "#d8789a", stroke=None, extra=op(0.45))
    # tháp Bitexco
    c.path("M110,134 L114,34 Q122,22 130,34 L134,134 Z", c.lg("#cfe6ff", "#5a8ac4", 0, 0, 1, 0), sw=3.5)
    c.ell(132, 70, 12, 4, "#8ab8e8", stroke=O, sw=2.5)
    c.line(122, 28, 122, 14, stroke=O, sw=2)
    for yy in range(46, 130, 10):
        c.line(116, yy, 128, yy, stroke="#fff6c0", sw=1.6, extra=op(0.8))
    for x, h, col in [(20, 72, "#7fa0c8"), (56, 88, "#9fb5d6"), (148, 96, "#6f90c0"), (186, 66, "#8fb0d6")]:
        w = 34
        c.rect(x, 134 - h, w, h, c.lg(lt(col, 0.15), dk(col, 0.15), 0, 0, 1, 0), sw=3.5)
        for yy in range(134 - h + 8, 126, 12):
            for xx in (x + 6, x + 20):
                c.rect(xx, yy, 8, 7, "#fff2a0" if (xx + yy) % 3 else "#d8ecff", rx=1, stroke=None)
    c.rect(56, 134 - 88 - 6, 34, 8, "#e8414f", rx=3, stroke=O, sw=2.4)
    for x in (24, 98, 204):
        c.rect(x - 2, 112, 4, 22, "#7a4a2e", stroke=None)
        c.circ(x, 108, 11, R(c, "#4fae3c", 0.4, 0.25), stroke=O, sw=2.4)
    c.rect(14, 146, 212, 3, "#fff6e0", stroke=None, extra=op(0.7))
    for x in (40, 90, 140, 190):
        c.rect(x, 154, 18, 3, "#fff6e0", stroke=None, extra=op(0.8))
    chapter_close(c)
    c.save("chapter_3", UI_DIR)

    # 4. Đà Lạt: đồi thông + nhà gỗ
    c = C(240, 180, 120, 90)
    chapter_frame(c, "#bfe6ff", "#e8f6ff", "#7cc96b", "#4e9a3e", gy=132)
    c.path("M9,96 Q50,60 100,88 Q150,58 231,84 L231,140 L9,140 Z", "#9fc8d8", stroke=None, extra=op(0.8))
    c.path("M9,112 Q70,80 130,106 Q180,86 231,104 L231,140 L9,140 Z", "#7cb88a", stroke=None)

    def pine(x, y, h, col="#2f7a52"):
        c.rect(x - 2.5, y - 8, 5, 10, "#6a4028", stroke=None)
        for k in range(3):
            w = h * (0.42 - k * 0.1)
            yy = y - 6 - k * h * 0.26
            c.poly([(x - w, yy), (x + w, yy), (x, yy - h * 0.42)], c.lg(lt(col, 0.2), dk(col, 0.15)), stroke=O, sw=2.4)
    for x, y, h in [(38, 128, 54), (58, 134, 42), (190, 128, 58), (206, 134, 40), (172, 132, 40)]:
        pine(x, y, h)
    c.rect(82, 82, 76, 52, c.lg("#d89a62", "#9a5a2e"), rx=3, sw=3.5)
    for k in range(4):
        c.line(84, 92 + k * 11, 156, 92 + k * 11, stroke="#7a4a2e", sw=1.4, extra=op(0.6))
    c.path("M72,86 L120,48 L168,86 L160,90 L120,58 L80,90 Z", c.lg("#8a5ad8", "#5a3a9a"), sw=3.5)
    c.rect(132, 52, 10, 20, "#a8683d", stroke=O, sw=2.4)
    c.path("M137,46 q-6,-6 0,-12 q6,-6 0,-12", "none", stroke=WHITE, sw=3, extra='stroke-opacity="0.8"')
    c.rect(110, 104, 20, 30, "#6a3a1e", rx=2, stroke=O, sw=2.4)
    for x in (90, 136):
        c.rect(x, 96, 14, 14, "#fff2c0", rx=2, stroke=O, sw=2)
    c.path("M9,70 Q60,62 120,72 Q180,80 231,70", "none", stroke=WHITE, sw=8, extra='stroke-opacity="0.45"')
    for x, col in [(70, "#b07ae0"), (78, "#ff8fb0"), (166, "#b07ae0"), (174, "#ffd34d"), (100, "#ff8fb0"),
                   (150, "#b07ae0")]:
        c.circ(x, 146, 5, col, stroke=O, sw=1.6)
    chapter_close(c)
    c.save("chapter_4", UI_DIR)

    # 5. Huế: Ngọ Môn mái vàng
    c = C(240, 180, 120, 90)
    chapter_frame(c, "#ffe9c0", "#ffb88a", "#5aa8c8", "#2a7aa0", gy=140)
    c.circ(196, 40, 16, c.rg([(0, "#fff6d0", 1), (1, "#ffd27a", 1)]), stroke=None)
    c.rect(26, 92, 188, 48, c.lg("#d8584a", "#8a2a22"), rx=3, sw=3.5)
    for x in (40, 70, 160, 190):
        c.rect(x, 100, 10, 40, "#7a1e1a", rx=2, stroke=None, extra=op(0.5))
    c.path("M104,140 L104,116 Q120,96 136,116 L136,140 Z", "#3a1a10", sw=3)
    for x in (76, 164):
        c.path("M%d,140 L%d,124 Q%d,114 %d,124 L%d,140 Z" % (x - 8, x - 8, x, x + 8, x + 8), "#3a1a10", sw=2.4)

    def roof(x0, x1, y, h):
        cx_ = (x0 + x1) / 2.0
        w_ = (x1 - x0) * 0.32
        c.path("M%s,%s Q%s,%s %s,%s L%s,%s Q%s,%s %s,%s L%s,%s L%s,%s Z" % (
            f(x0 - 8), f(y - 8), f(x0 + 2), f(y), f(x0 + 18), f(y), f(x1 - 18), f(y), f(x1 - 2), f(y), f(x1 + 8),
            f(y - 8), f(cx_ + w_), f(y - h), f(cx_ - w_), f(y - h)),
            c.lg("#ffe27a", "#e08a10"), sw=3.5)
        for k in range(1, 8):
            xb = x0 + 18 + (x1 - x0 - 36) * k / 8.0
            xt = cx_ - w_ + 2 * w_ * k / 8.0
            c.line(xb, y - 2, xt, y - h + 2, stroke="#c4700a", sw=1.3, extra=op(0.6))
        c.path("M%s,%s L%s,%s" % (f(x0 + 18), f(y), f(x1 - 12), f(y)), "none", stroke="#a8580a", sw=2)
        c.path("M%s,%s L%s,%s" % (f(cx_ - (x1 - x0) * 0.3), f(y - h), f(cx_ + (x1 - x0) * 0.3), f(y - h)), "none",
               stroke="#fff6c0", sw=2)
    c.rect(56, 72, 128, 22, c.lg("#e8604a", "#a8342a"), sw=3)
    for x in range(64, 180, 14):
        c.rect(x, 76, 6, 16, "#ffd34d", rx=1, stroke=None, extra=op(0.7))
    roof(30, 210, 94, 16)
    c.rect(80, 50, 80, 22, c.lg("#e8604a", "#a8342a"), sw=3)
    roof(62, 178, 70, 18)
    roof(90, 150, 48, 16)
    c.circ(120, 24, 5, R(c, GOLD, 0.5, 0.2), stroke=O, sw=2)
    for x in (30, 96, 166, 210):
        c.path("M%d,154 q6,-8 12,0" % (x - 6), "none", stroke="#bfe8ff", sw=2.2)
    for x, y in [(40, 160), (190, 158)]:
        c.ell(x, y, 10, 4, "#4fae3c", stroke=O, sw=1.8)
        c.path("M%d,%d q-4,-8 0,-12 q4,4 0,12 Z" % (x, y - 2), "#ff8fb0", stroke="#c44a70", sw=1.4)
    chapter_close(c)
    c.save("chapter_5", UI_DIR)


# ================================================================ MÀN THƯỞNG: TIA SÁNG + RUY BĂNG

def rays_ribbon():
    c = C(512, 512, 256, 256)
    n = 18
    d = ""
    for k in range(n):
        a0 = 2 * math.pi * k / n - math.pi / n / 2
        a1 = a0 + math.pi / n
        r = 252
        d += "M256,256 L%s,%s L%s,%s Z " % (f(256 + math.cos(a0) * r), f(256 + math.sin(a0) * r),
                                            f(256 + math.cos(a1) * r), f(256 + math.sin(a1) * r))
    c.path(d, c.rg([(0, "#fff6c0", 0.85), (0.35, "#ffd860", 0.55), (0.75, "#ffc93c", 0.18), (1, "#ffc93c", 0)],
                   0.5, 0.5, 0.5), stroke=None)
    d2 = ""
    for k in range(n):
        a0 = 2 * math.pi * k / n - math.pi / n * 0.15
        a1 = a0 + math.pi / n * 0.3
        r = 200
        d2 += "M256,256 L%s,%s L%s,%s Z " % (f(256 + math.cos(a0) * r), f(256 + math.sin(a0) * r),
                                             f(256 + math.cos(a1) * r), f(256 + math.sin(a1) * r))
    c.path(d2, c.rg([(0, "#ffffff", 0.7), (0.5, "#fff6c0", 0.25), (1, "#fff6c0", 0)], 0.5, 0.5, 0.5), stroke=None)
    c.circ(256, 256, 150, c.rg([(0, "#fffbe0", 0.95), (0.4, "#ffe680", 0.55), (1, "#ffd34d", 0)]), stroke=None)
    c.save("rays", UI_DIR)

    c = C(600, 150, 300, 75)
    c.ell(300, 140, 250, 8, c.rg([(0, "#000000", 0.25), (1, "#000000", 0)]), stroke=None)
    for s in (-1, 1):
        # đuôi
        x_in, x_out = 300 + s * 196, 300 + s * 290
        tail = "M%s,52 L%s,52 L%s,84 L%s,116 L%s,116 Z" % (f(x_in), f(x_out), f(x_out - s * 26), f(x_out), f(x_in))
        c.path(tail, c.lg("#d8343a", "#8a1a22"), sw=5)
        c.path("M%s,60 L%s,60" % (f(x_in + s * 4), f(x_out - s * 14)), "none", stroke="#ffd34d", sw=3,
               extra=op(0.8))
        c.path("M%s,108 L%s,108" % (f(x_in + s * 4), f(x_out - s * 14)), "none", stroke="#ffd34d", sw=3,
               extra=op(0.8))
        # nếp gấp
        fold = "M%s,94 L%s,116 L%s,98 Z" % (f(300 + s * 230), f(300 + s * 230), f(300 + s * 196))
        c.path(fold, c.lg("#7a1a22", "#4a0a10"), sw=4)
    body = "M70,32 Q300,6 530,32 L530,98 Q300,72 70,98 Z"
    c.path("M70,38 Q300,12 530,38 L530,104 Q300,78 70,104 Z", "#3a0a10", stroke=None, extra=op(0.3))
    c.path(body, c.lg("#ff6a5a", "#c4283a", 0, 0, 0, 1, mid="#e8414f"), sw=5)
    c.path("M76,42 Q300,17 524,42", "none", stroke="#ffd34d", sw=5)
    c.path("M76,42 Q300,17 524,42", "none", stroke="#fff3a0", sw=2)
    c.path("M76,88 Q300,63 524,88", "none", stroke="#ffd34d", sw=5)
    c.path("M76,88 Q300,63 524,88", "none", stroke="#c47a10", sw=1.5, extra=op(0.6))
    c.path("M80,36 Q300,11 520,36 L520,46 Q300,22 80,46 Z", WHITE, stroke=None, extra=op(0.3))
    for x, y in [(98, 64), (502, 64)]:
        c.path(star_d(x, y, 12, 5.5), R(c, GOLD, 0.6, 0.15), stroke=O, sw=2.6)
    c.save("ribbon", UI_DIR)


# ================================================================ RUN

def run(base):
    global C, lt, dk, mix, f, OUT_DIR, UI_DIR, SKIN, icon_canvas
    C, lt, dk, mix, f = base.C, base.lt, base.dk, base.mix, base.f
    OUT_DIR, UI_DIR, SKIN = base.OUT_DIR, base.UI_DIR, base.SKIN
    icon_canvas = base.icon_canvas
    dishes()
    for folder in (OUT_DIR, UI_DIR):
        coin("coin", folder)
        diamond_icon("diamond", folder)
    stars()
    ui_small()
    ui_big()
    badges()
    bubbles()
    nav_buttons()
    area_thumbs()
    chapter_thumbs()
    rays_ribbon()
