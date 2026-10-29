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

button("Button", "#ffcf6b", "#e0a23a", "#6f4636")
props.append("Button/font_sizes/font_size = 26")
for name, bg, edge in [("GreenButton", "#82c99b", "#4e9a6e"), ("BlueButton", "#7cc0e6", "#4c8fb8"),
                       ("RedButton", "#f58274", "#c2503f")]:
    props.append('%s/base_type = &"Button"' % name)
    button(name, bg, edge, "#ffffff", "#7a4b3a")
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
props.append('TabButton/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('TabButton/constants/outline_size = 6')
props.append('TabButton/font_sizes/font_size = 20')

# ---- khung kiểu game mobile (theo ảnh mẫu)
# ---- khung kiểu game mobile (theo Concept A - Ấm A)
props.append('CounterBar/base_type = &"PanelContainer"')
props.append('CounterBar/styles/panel = %s' % sb("#fffbf2", 28, "#dfcaa7", (3, 3, 3, 4), (46, 2, 16, 4), (0.12, 6, 2)))
props.append('LevelPill/base_type = &"PanelContainer"')
props.append('LevelPill/styles/panel = %s' % sb("#fffbf2", 22, "#dfcaa7", (3, 3, 3, 4), (8, 2, 12, 4), (0.12, 6, 2)))
props.append('StatusBanner/base_type = &"PanelContainer"')
props.append('StatusBanner/styles/panel = %s' % sb("#6f9d6c", 20, "#4e774c", (2, 2, 2, 4), (18, 4, 18, 6), (0.16, 6, 3)))
props.append('SidePanel/base_type = &"PanelContainer"')
props.append('SidePanel/styles/panel = %s' % empty())
props.append('AreaPill/base_type = &"PanelContainer"')
props.append('AreaPill/styles/panel = %s' % sb("#fffaf0", 30, "#dfcaa7", (3, 3, 3, 5), (20, 2, 20, 4), (0.12, 6, 3)))

# Cột thẻ nổi bên phải (SideCard)
props.append('SideCard/base_type = &"Button"')
props.append('SideCard/styles/normal = %s' % sb("#fffcf5", 18, "#dfcaa7", (3, 3, 3, 5), (6, 6, 6, 6), (0.15, 6, 3)))
props.append('SideCard/styles/hover = %s' % sb("#ffffff", 18, "#f08a76", (3, 3, 3, 5), (6, 6, 6, 6), (0.20, 8, 4)))
props.append('SideCard/styles/pressed = %s' % sb("#f7efe4", 18, "#cbb494", (3, 5, 3, 3), (6, 8, 6, 4), (0.10, 4, 2)))
props.append('SideCard/styles/disabled = %s' % sb("#e8e1d7", 18, "#c4b9ab", (3, 3, 3, 5), (6, 6, 6, 6)))
props.append('SideCard/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('SideCard/colors/%s = %s' % (k, col("#553524")))
props.append('SideCard/font_sizes/font_size = 15')

props.append('RoundNav/base_type = &"Button"')
for st in ("normal", "hover", "pressed"):
    props.append('RoundNav/styles/%s = %s' % (st, sb("#fffaf2" if st != "pressed" else "#fbe6da", 60, "#f4b8a4",
                                                    (4, 4, 4, 7), (6, 6, 6, 8), (0.22, 8, 5))))
props.append('RoundNav/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('RoundNav/colors/%s = %s' % (k, col("#b0573f")))
props.append('RoundNav/colors/font_outline_color = %s' % col("#fffaf2"))
props.append('RoundNav/constants/outline_size = 6')
props.append('RoundNav/font_sizes/font_size = 24')
props.append('RoundNav/constants/icon_max_width = 92')

# ---- chữ
props.append('Label/colors/font_color = %s' % col("#6f4636"))
props.append('Label/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('Label/constants/line_spacing = 0')
props.append('TitleLabel/base_type = &"Label"')
props.append('TitleLabel/colors/font_color = %s' % col("#ffffff"))
props.append('TitleLabel/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('TitleLabel/constants/outline_size = 12')
props.append('TitleLabel/font_sizes/font_size = 40')
props.append('HeaderLabel/base_type = &"Label"')
props.append('HeaderLabel/colors/font_color = %s' % col("#d06a52"))
props.append('HeaderLabel/font_sizes/font_size = 30')
props.append('SmallLabel/base_type = &"Label"')
props.append('SmallLabel/colors/font_color = %s' % col("#9a8070"))
props.append('SmallLabel/font_sizes/font_size = 21')
props.append('GreenLabel/base_type = &"Label"')
props.append('GreenLabel/colors/font_color = %s' % col("#4a8a63"))
props.append('GreenLabel/font_sizes/font_size = 22')
props.append('WhiteLabel/base_type = &"Label"')
props.append('WhiteLabel/colors/font_color = %s' % col("#ffffff"))
props.append('WhiteLabel/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('WhiteLabel/constants/outline_size = 8')

# Chữ cho số tài nguyên & trạng thái theo Concept A
props.append('ResourceLabel/base_type = &"Label"')
props.append('ResourceLabel/colors/font_color = %s' % col("#432616"))
props.append('ResourceLabel/font_sizes/font_size = 27')
props.append('StatusLabel/base_type = &"Label"')
props.append('StatusLabel/colors/font_color = %s' % col("#ffffff"))
props.append('StatusLabel/colors/font_outline_color = %s' % col("#3a5f38"))
props.append('StatusLabel/constants/outline_size = 4')
props.append('StatusLabel/font_sizes/font_size = 19')
props.append('SideLabel/base_type = &"Label"')
props.append('SideLabel/colors/font_color = %s' % col("#553524"))
props.append('SideLabel/font_sizes/font_size = 15')
props.append('NavLabel/base_type = &"Label"')
props.append('NavLabel/colors/font_color = %s' % col("#4a2c1d"))
props.append('NavLabel/font_sizes/font_size = 16')

# ---- khung
card = sb("#fffaf1", 26, "#f0d6b8", (3, 3, 3, 3), (18, 16, 18, 16), (0.14, 10, 5))
props.append('PanelContainer/styles/panel = %s' % card)
props.append('Card/base_type = &"PanelContainer"')
props.append('Card/styles/panel = %s' % sb("#fffaf1", 28, "#f0d6b8", (3, 3, 3, 3), (16, 14, 16, 14), (0.14, 10, 6)))
props.append('CardDim/base_type = &"PanelContainer"')
props.append('CardDim/styles/panel = %s' % sb("#f4ede2", 28, "#e2d3bc", (3, 3, 3, 3), (16, 14, 16, 14), (0.12, 6, 4)))
props.append('Pill/base_type = &"PanelContainer"')
props.append('Pill/styles/panel = %s' % sb("#ffffff", 40, "#e8b49a", (3, 3, 3, 3), (10, 4, 18, 4), (0.16, 5, 3)))
props.append('Sheet/base_type = &"PanelContainer"')
props.append('Sheet/styles/panel = %s' % sb("#fff4e6", 0, "#e9b99a", (0, 5, 0, 0), (16, 16, 16, 12), (0.25, 14, 0),
                                              radius_each=(38, 38, 0, 0)))
props.append('NavBar/base_type = &"PanelContainer"')
props.append('NavBar/styles/panel = %s' % sb("#d9a574", 0, "#b07c4f", (0, 4, 0, 0), (8, 6, 8, 10), (0.22, 12, -2),
                                               radius_each=(30, 30, 0, 0)))
props.append('PopupCard/base_type = &"PanelContainer"')
props.append('PopupCard/styles/panel = %s' % sb("#fffaf0", 36, "#d9a574", (6, 6, 6, 6), (24, 20, 24, 24), (0.28, 22, 8)))
props.append('PopupHeader/base_type = &"PanelContainer"')
props.append('PopupHeader/styles/panel = %s' % sb("#f08a76", 26, "#c95f4c", (4, 4, 4, 8), (24, 6, 24, 10)))
props.append('Badge/base_type = &"PanelContainer"')
props.append('Badge/styles/panel = %s' % sb("#ff6b6b", 20, "#ffffff", (3, 3, 3, 3), (8, 0, 8, 2)))
props.append('Toast/base_type = &"PanelContainer"')
props.append('Toast/styles/panel = %s' % sb("#6e4535", 30, None, (0, 0, 0, 0), (26, 12, 26, 14), (0.24, 8, 4), alpha=0.9))
props.append('Highlight/base_type = &"PanelContainer"')
props.append('Highlight/styles/panel = %s' % sb("#fff1b8", 22, "#f2a541", (3, 3, 3, 3), (12, 8, 12, 8)))

# ---- thanh tiến độ
props.append('ProgressBar/styles/background = %s' % sb("#7a4b3a", 12, None, margin=(0, 0, 0, 0), alpha=0.25))
props.append('ProgressBar/styles/fill = %s' % sb("#8fd18a", 12, "#5aa86a", (0, 0, 0, 3), (0, 0, 0, 0)))
props.append('ProgressBar/font_sizes/font_size = 18')
props.append('ProgressBar/colors/font_color = %s' % col("#ffffff"))
props.append('ProgressBar/colors/font_outline_color = %s' % col("#7a4b3a"))
props.append('ProgressBar/constants/outline_size = 5')
props.append('ExpBar/base_type = &"ProgressBar"')
props.append('ExpBar/styles/background = %s' % sb("#7a4b3a", 10, None, margin=(0, 0, 0, 0), alpha=0.3))
props.append('ExpBar/styles/fill = %s' % sb("#ffd166", 10, "#e0a23a", (0, 0, 0, 3), (0, 0, 0, 0)))

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
