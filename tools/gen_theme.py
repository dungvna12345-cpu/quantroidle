# -*- coding: utf-8 -*-
"""Sinh theme/main_theme.tres (font Baloo 2 đậm, nút nổi khối, thẻ bo góc có bóng)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "theme" / "main_theme.tres"
OUT.parent.mkdir(parents=True, exist_ok=True)

subs = []      # (id, type, props)
props = []     # dòng thuộc tính của Theme


def col(h, a=1.0):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return "Color(%.4g, %.4g, %.4g, %.4g)" % (r, g, b, a)


def sb(bg, radius=20, border=None, bw=(0, 0, 0, 0), margin=(12, 8, 12, 8), shadow=None, alpha=1.0,
       radius_each=None, skew=None):
    sid = "StyleBoxFlat_%d" % (len(subs) + 1)
    p = ["bg_color = %s" % col(bg, alpha)]
    l, t, r, b = margin
    p += ["content_margin_left = %d" % l, "content_margin_top = %d" % t,
          "content_margin_right = %d" % r, "content_margin_bottom = %d" % b]
    if border:
        p += ["border_width_left = %d" % bw[0], "border_width_top = %d" % bw[1],
              "border_width_right = %d" % bw[2], "border_width_bottom = %d" % bw[3],
              "border_color = %s" % col(border)]
    rr = radius_each or (radius, radius, radius, radius)
    p += ["corner_radius_top_left = %d" % rr[0], "corner_radius_top_right = %d" % rr[1],
          "corner_radius_bottom_right = %d" % rr[2], "corner_radius_bottom_left = %d" % rr[3],
          "corner_detail = 10"]
    if shadow:
        p += ["shadow_color = %s" % col("#000000", shadow[0]), "shadow_size = %d" % shadow[1],
              "shadow_offset = Vector2(0, %d)" % shadow[2]]
    subs.append((sid, "StyleBoxFlat", p))
    return 'SubResource("%s")' % sid


def empty():
    sid = "StyleBoxEmpty_%d" % (len(subs) + 1)
    subs.append((sid, "StyleBoxEmpty", []))
    return 'SubResource("%s")' % sid


def button(prefix, bg, edge, text, outline=None):
    """Nút nổi khối: viền dưới dày và đậm hơn, nhấn xuống thì viền dưới mỏng lại."""
    props.append('%s/styles/normal = %s' % (prefix, sb(bg, 22, edge, (3, 3, 3, 9), (16, 8, 16, 12))))
    props.append('%s/styles/hover = %s' % (prefix, sb(lighten(bg), 22, edge, (3, 3, 3, 9), (16, 8, 16, 12))))
    props.append('%s/styles/pressed = %s' % (prefix, sb(darken(bg), 22, edge, (3, 6, 3, 4), (16, 13, 16, 7))))
    props.append('%s/styles/disabled = %s' % (prefix, sb("#e6dfd6", 22, "#c4b9ab", (3, 3, 3, 9), (16, 8, 16, 12))))
    props.append('%s/styles/focus = %s' % (prefix, empty()))
    for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"):
        props.append('%s/colors/%s = %s' % (prefix, k, col(text)))
    props.append('%s/colors/font_disabled_color = %s' % (prefix, col("#8f8577")))
    if outline:
        props.append('%s/colors/font_outline_color = %s' % (prefix, col(outline)))
        props.append('%s/constants/outline_size = 7' % prefix)
    props.append('%s/constants/icon_max_width = 34' % prefix)
    props.append('%s/constants/h_separation = 6' % prefix)


def lighten(h, t=0.15):
    h = h.lstrip("#")
    v = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join("%02x" % int(c + (255 - c) * t) for c in v)


def darken(h, t=0.1):
    h = h.lstrip("#")
    v = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join("%02x" % int(c * (1 - t)) for c in v)


# ---- mặc định
props.append('default_font = SubResource("FontVariation_bold")')
props.append("default_font_size = 26")

button("Button", "#f5a623", "#c77c0c", "#3e2415", "#ffffff")
props.append("Button/font_sizes/font_size = 26")
for name, bg, edge in [("GreenButton", "#43a047", "#2e7d32"), ("BlueButton", "#3498db", "#217dbb"),
                       ("RedButton", "#c0392b", "#962d22")]:
    props.append('%s/base_type = &"Button"' % name)
    button(name, bg, edge, "#ffffff", "#3e2415")
props.append('IconButton/base_type = &"Button"')
props.append('IconButton/styles/normal = %s' % empty())
props.append('IconButton/styles/hover = %s' % empty())
props.append('IconButton/styles/pressed = %s' % empty())
props.append('IconButton/styles/disabled = %s' % empty())
props.append('IconButton/styles/focus = %s' % empty())
props.append('TabButton/base_type = &"Button"')
props.append('TabButton/styles/normal = %s' % empty())
props.append('TabButton/styles/hover = %s' % empty())
props.append('TabButton/styles/pressed = %s' % empty())
props.append('TabButton/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('TabButton/colors/%s = %s' % (k, col("#ffffff")))
props.append('TabButton/colors/font_outline_color = %s' % col("#3e2415"))
props.append('TabButton/constants/outline_size = 6')
props.append('TabButton/font_sizes/font_size = 20')

# ---- khung kiểu game mobile Quán Trọ Đông Dương (Ấm áp, viền gỗ mộc, giấy ngà)
props.append('CounterBar/base_type = &"PanelContainer"')
props.append('CounterBar/styles/panel = %s' % sb("#fffdf8", 26, "#8c5836", (2, 2, 2, 4), (46, 2, 16, 4), (0.16, 6, 2)))
props.append('LevelPill/base_type = &"PanelContainer"')
props.append('LevelPill/styles/panel = %s' % sb("#fffdf8", 22, "#8c5836", (2, 2, 2, 4), (8, 2, 12, 4), (0.16, 6, 2)))
props.append('StatusBanner/base_type = &"PanelContainer"')
props.append('StatusBanner/styles/panel = %s' % sb("#4a7c59", 20, "#2d5238", (2, 2, 2, 4), (16, 4, 16, 6), (0.16, 6, 3)))
props.append('SidePanel/base_type = &"PanelContainer"')
props.append('SidePanel/styles/panel = %s' % empty())
props.append('AreaPill/base_type = &"PanelContainer"')
props.append('AreaPill/styles/panel = %s' % sb("#fffdf8", 26, "#8c5836", (2, 2, 2, 4), (18, 4, 18, 6), (0.16, 6, 3)))

# Cột thẻ nổi bên phải (SideCard)
props.append('SideCard/base_type = &"Button"')
props.append('SideCard/styles/normal = %s' % sb("#fffdf8", 18, "#8c5836", (2, 2, 2, 4), (6, 6, 6, 6), (0.16, 6, 3)))
props.append('SideCard/styles/hover = %s' % sb("#ffffff", 18, "#f5a623", (2, 2, 2, 4), (6, 6, 6, 6), (0.22, 8, 4)))
props.append('SideCard/styles/pressed = %s' % sb("#f4e8d3", 18, "#633c22", (2, 4, 2, 2), (6, 8, 6, 4), (0.10, 4, 2)))
props.append('SideCard/styles/disabled = %s' % sb("#e8e1d7", 18, "#c4b9ab", (2, 2, 2, 4), (6, 6, 6, 6)))
props.append('SideCard/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('SideCard/colors/%s = %s' % (k, col("#3e2415")))
props.append('SideCard/font_sizes/font_size = 15')

props.append('RoundNav/base_type = &"Button"')
for st in ("normal", "hover", "pressed"):
    props.append('RoundNav/styles/%s = %s' % (st, sb("#fffdf8" if st != "pressed" else "#fbe6da", 60, "#c0392b",
                                                    (3, 3, 3, 6), (6, 6, 6, 8), (0.24, 8, 5))))
props.append('RoundNav/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('RoundNav/colors/%s = %s' % (k, col("#c0392b")))
props.append('RoundNav/colors/font_outline_color = %s' % col("#fffaf2"))
props.append('RoundNav/constants/outline_size = 6')
props.append('RoundNav/font_sizes/font_size = 24')
props.append('RoundNav/constants/icon_max_width = 92')

# ---- chữ
props.append('Label/colors/font_color = %s' % col("#3e2415"))
props.append('Label/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('Label/constants/line_spacing = 0')
props.append('TitleLabel/base_type = &"Label"')
props.append('TitleLabel/colors/font_color = %s' % col("#ffffff"))
props.append('TitleLabel/colors/font_outline_color = %s' % col("#3e2415"))
props.append('TitleLabel/constants/outline_size = 10')
props.append('TitleLabel/font_sizes/font_size = 38')
props.append('HeaderLabel/base_type = &"Label"')
props.append('HeaderLabel/colors/font_color = %s' % col("#c0392b"))
props.append('HeaderLabel/font_sizes/font_size = 28')
props.append('SmallLabel/base_type = &"Label"')
props.append('SmallLabel/colors/font_color = %s' % col("#7a523a"))
props.append('SmallLabel/font_sizes/font_size = 20')
props.append('GreenLabel/base_type = &"Label"')
props.append('GreenLabel/colors/font_color = %s' % col("#2e7d32"))
props.append('GreenLabel/font_sizes/font_size = 22')
props.append('WhiteLabel/base_type = &"Label"')
props.append('WhiteLabel/colors/font_color = %s' % col("#ffffff"))
props.append('WhiteLabel/colors/font_outline_color = %s' % col("#3e2415"))
props.append('WhiteLabel/constants/outline_size = 8')

# Chữ cho số tài nguyên & trạng thái
props.append('ResourceLabel/base_type = &"Label"')
props.append('ResourceLabel/colors/font_color = %s' % col("#301a0e"))
props.append('ResourceLabel/font_sizes/font_size = 26')
props.append('StatusLabel/base_type = &"Label"')
props.append('StatusLabel/colors/font_color = %s' % col("#ffffff"))
props.append('StatusLabel/colors/font_outline_color = %s' % col("#1e3b25"))
props.append('StatusLabel/constants/outline_size = 4')
props.append('StatusLabel/font_sizes/font_size = 18')
props.append('SideLabel/base_type = &"Label"')
props.append('SideLabel/colors/font_color = %s' % col("#4a2810"))
props.append('SideLabel/font_sizes/font_size = 15')
props.append('NavLabel/base_type = &"Label"')
props.append('NavLabel/colors/font_color = %s' % col("#4a2810"))
props.append('NavLabel/font_sizes/font_size = 16')

# ---- khung
card = sb("#fdfbf6", 24, "#dfcaa7", (2, 2, 2, 4), (16, 14, 16, 14), (0.14, 8, 4))
props.append('PanelContainer/styles/panel = %s' % card)
props.append('Card/base_type = &"PanelContainer"')
props.append('Card/styles/panel = %s' % sb("#fdfbf6", 24, "#dfcaa7", (2, 2, 2, 4), (16, 14, 16, 14), (0.14, 8, 4)))
props.append('CardDim/base_type = &"PanelContainer"')
props.append('CardDim/styles/panel = %s' % sb("#f4ede2", 24, "#d0beaa", (2, 2, 2, 3), (16, 14, 16, 14), (0.10, 5, 3)))
props.append('Pill/base_type = &"PanelContainer"')
props.append('Pill/styles/panel = %s' % sb("#fffdf8", 36, "#8c5836", (2, 2, 2, 3), (10, 4, 18, 4), (0.16, 5, 3)))
props.append('Sheet/base_type = &"PanelContainer"')
props.append('Sheet/styles/panel = %s' % sb("#fdfbf6", 0, "#8c5836", (0, 4, 0, 0), (16, 14, 16, 12), (0.24, 12, 0),
                                              radius_each=(32, 32, 0, 0)))
props.append('NavBar/base_type = &"PanelContainer"')
props.append('NavBar/styles/panel = %s' % sb("#382013", 0, "#d49a43", (0, 3, 0, 0), (8, 6, 8, 10), (0.26, 12, -2),
                                               radius_each=(26, 26, 0, 0)))
props.append('PopupCard/base_type = &"PanelContainer"')
props.append('PopupCard/styles/panel = %s' % sb("#fdfbf6", 32, "#5d3820", (5, 5, 5, 6), (22, 18, 22, 22), (0.34, 20, 8)))
props.append('PopupHeader/base_type = &"PanelContainer"')
props.append('PopupHeader/styles/panel = %s' % sb("#c0392b", 22, "#e6ad45", (3, 3, 3, 6), (22, 6, 22, 8)))
props.append('Badge/base_type = &"PanelContainer"')
props.append('Badge/styles/panel = %s' % sb("#c0392b", 18, "#ffffff", (2, 2, 2, 2), (8, 0, 8, 2), (0.20, 4, 2)))
props.append('Toast/base_type = &"PanelContainer"')
props.append('Toast/styles/panel = %s' % sb("#3a2012", 28, "#e6ad45", (2, 2, 2, 3), (26, 12, 26, 14), (0.30, 8, 4), alpha=0.95))
props.append('Highlight/base_type = &"PanelContainer"')
props.append('Highlight/styles/panel = %s' % sb("#fff6d6", 22, "#e6a839", (2, 2, 2, 4), (12, 8, 12, 8)))

# ---- thanh tiến độ
props.append('ProgressBar/styles/background = %s' % sb("#7a4b3a", 12, None, margin=(0, 0, 0, 0), alpha=0.25))
props.append('ProgressBar/styles/fill = %s' % sb("#8fd18a", 12, "#5aa86a", (0, 0, 0, 3), (0, 0, 0, 0)))
props.append('ProgressBar/font_sizes/font_size = 18')
props.append('ProgressBar/colors/font_color = %s' % col("#ffffff"))
props.append('ProgressBar/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('ProgressBar/constants/outline_size = 5')
props.append('ExpBar/base_type = &"ProgressBar"')
props.append('ExpBar/styles/background = %s' % sb("#3e2415", 8, "#8c5836", (1, 1, 1, 1), margin=(0, 0, 0, 0), alpha=0.45))
props.append('ExpBar/styles/fill = %s' % sb("#f5a623", 8, "#c77c0c", (0, 0, 0, 2), margin=(0, 0, 0, 0)))

# ---- cuộn
props.append('VScrollBar/styles/scroll = %s' % sb("#000000", 6, None, margin=(4, 0, 4, 0), alpha=0.06))
props.append('VScrollBar/styles/grabber = %s' % sb("#ecc9ad", 6, None, margin=(4, 0, 4, 0)))
props.append('VScrollBar/styles/grabber_highlight = %s' % sb("#e2b494", 6, None, margin=(4, 0, 4, 0)))
props.append('VScrollBar/styles/grabber_pressed = %s' % sb("#d6a07e", 6, None, margin=(4, 0, 4, 0)))

# ---- CheckButton
props.append('CheckButton/colors/font_color = %s' % col("#6f4636"))
props.append('CheckButton/colors/font_hover_color = %s' % col("#6f4636"))
props.append('CheckButton/colors/font_pressed_color = %s' % col("#6f4636"))
props.append('CheckButton/colors/font_hover_pressed_color = %s' % col("#6f4636"))
props.append('CheckButton/colors/font_focus_color = %s' % col("#6f4636"))
props.append('CheckButton/styles/focus = %s' % empty())
props.append('CheckButton/styles/normal = %s' % empty())
props.append('CheckButton/styles/hover = %s' % empty())
props.append('CheckButton/styles/pressed = %s' % empty())

lines = ['[gd_resource type="Theme" load_steps=%d format=3]' % (len(subs) + 3), "",
         '[ext_resource type="FontFile" path="res://assets/fonts/Baloo2.ttf" id="1_font"]', "",
         '[sub_resource type="FontVariation" id="FontVariation_bold"]',
         'base_font = ExtResource("1_font")',
         'variation_opentype = {2003265652: 750}', ""]
for sid, typ, p in subs:
    lines.append('[sub_resource type="%s" id="%s"]' % (typ, sid))
    lines += p
    lines.append("")
lines.append("[resource]")
lines += props
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("theme ok:", len(subs), "styleboxes")
