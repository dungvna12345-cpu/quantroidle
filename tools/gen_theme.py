# -*- coding: utf-8 -*-
"""
Sinh theme/main_theme.tres cho Quán Trọ Idle.
Phong cách: Cổ trấn Đông Dương, mộc ấm, ngà gấm, sơn mài chu sa và vàng kim.
Loại bỏ hoàn toàn các khối trắng bệt (flat white boxes) gây cảm giác chắp vá/web app.
"""
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
    """Nút nổi khối 3D: viền dưới đậm hơn, bấm xuống thì lún nhẹ."""
    props.append('%s/styles/normal = %s' % (prefix, sb(bg, 20, edge, (2, 2, 2, 6), (16, 8, 16, 11), shadow=(0.20, 6, 2))))
    props.append('%s/styles/hover = %s' % (prefix, sb(lighten(bg, 0.12), 20, edge, (2, 2, 2, 6), (16, 8, 16, 11), shadow=(0.28, 8, 3))))
    props.append('%s/styles/pressed = %s' % (prefix, sb(darken(bg, 0.12), 20, edge, (2, 5, 2, 3), (16, 11, 16, 8))))
    props.append('%s/styles/disabled = %s' % (prefix, sb("#d6cbbd", 20, "#b3a593", (2, 2, 2, 5), (16, 8, 16, 11))))
    props.append('%s/styles/focus = %s' % (prefix, empty()))
    for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color", "font_hover_pressed_color"):
        props.append('%s/colors/%s = %s' % (prefix, k, col(text)))
    props.append('%s/colors/font_disabled_color = %s' % (prefix, col("#8a7c6a")))
    if outline:
        props.append('%s/colors/font_outline_color = %s' % (prefix, col(outline)))
        props.append('%s/constants/outline_size = 6' % prefix)
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


# ---- Font mặc định
props.append('default_font = SubResource("FontVariation_bold")')
props.append("default_font_size = 24")

# ---- Nút bấm nổi khối
button("Button", "#d97706", "#92400e", "#fffdf0", "#451a03")
props.append("Button/font_sizes/font_size = 24")

for name, bg, edge, outl in [
    ("GreenButton", "#15803d", "#14532d", "#052e16"),
    ("BlueButton", "#0284c7", "#075985", "#082f49"),
    ("RedButton", "#b91c1c", "#7f1d1d", "#450a0a")
]:
    props.append('%s/base_type = &"Button"' % name)
    button(name, bg, edge, "#fffdf0", outl)

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
    props.append('TabButton/colors/%s = %s' % (k, col("#fffdf0")))
props.append('TabButton/colors/font_outline_color = %s' % col("#2b1307"))
props.append('TabButton/constants/outline_size = 5')
props.append('TabButton/font_sizes/font_size = 18')

# ---- KHUNG GIAO DIỆN (Tránh hoàn toàn màu trắng bệt!)
# 1. Đế điều hướng đáy (NavBar): Gỗ gụ trầm viền chỉ vàng kim
props.append('NavBar/base_type = &"PanelContainer"')
props.append('NavBar/styles/panel = %s' % sb("#1d0d06", 0, "#d97706", (0, 2, 0, 0), (8, 6, 8, 10), (0.35, 14, -3),
                                             radius_each=(22, 22, 0, 0)))

# 2. Ô đếm tiền / kim cương (CounterBar): Vỏ gỗ trầm trong mờ, viền chỉ đồng sang trọng
props.append('CounterBar/base_type = &"PanelContainer"')
props.append('CounterBar/styles/panel = %s' % sb("#221008", 24, "#b45309", (1, 1, 1, 3), (44, 2, 14, 4), (0.22, 6, 2), alpha=0.88))

# 3. Huy hiệu Cấp độ (LevelPill): Gỗ sậm viền đồng
props.append('LevelPill/base_type = &"PanelContainer"')
props.append('LevelPill/styles/panel = %s' % sb("#221008", 20, "#b45309", (1, 1, 1, 3), (8, 2, 10, 4), (0.22, 6, 2), alpha=0.88))

# 4. Biển hiệu Tên Khu Vực (AreaPill): Biển gỗ chạm trổ viền đồng vàng kim
props.append('AreaPill/base_type = &"PanelContainer"')
props.append('AreaPill/styles/panel = %s' % sb("#381a0e", 22, "#d97706", (2, 2, 2, 4), (18, 4, 18, 6), (0.32, 10, 4)))

# 5. Cột thẻ menu nổi (SideCard): Thẻ gỗ treo có viền đồng
props.append('SideCard/base_type = &"Button"')
props.append('SideCard/styles/normal = %s' % sb("#34180c", 18, "#b45309", (1, 1, 1, 3), (6, 6, 6, 6), (0.24, 8, 3)))
props.append('SideCard/styles/hover = %s' % sb("#452010", 18, "#f59e0b", (1, 1, 1, 3), (6, 6, 6, 6), (0.30, 10, 4)))
props.append('SideCard/styles/pressed = %s' % sb("#241008", 18, "#78350f", (1, 3, 1, 1), (6, 8, 6, 4), (0.12, 4, 2)))
props.append('SideCard/styles/disabled = %s' % sb("#2d1810", 18, "#542c17", (1, 1, 1, 3), (6, 6, 6, 6), alpha=0.6))
props.append('SideCard/styles/focus = %s' % empty())
for k in ("font_color", "font_hover_color", "font_pressed_color", "font_focus_color"):
    props.append('SideCard/colors/%s = %s' % (k, col("#fffaf0")))
props.append('SideCard/colors/font_outline_color = %s' % col("#1a0a04"))
props.append('SideCard/constants/outline_size = 4')
props.append('SideCard/font_sizes/font_size = 14')

# 6. Dải trạng thái đặc biệt (StatusBanner)
props.append('StatusBanner/base_type = &"PanelContainer"')
props.append('StatusBanner/styles/panel = %s' % sb("#14532d", 20, "#16a34a", (2, 2, 2, 4), (16, 4, 16, 6), (0.25, 8, 3)))
props.append('SidePanel/base_type = &"PanelContainer"')
props.append('SidePanel/styles/panel = %s' % empty())

# 7. Thẻ nội dung thông thường (Card): Giấy ngà ấm cổ truyền (Parchment), KHÔNG dùng màu trắng bệt
props.append('PanelContainer/styles/panel = %s' % sb("#f7efe0", 22, "#cfbc9e", (2, 2, 2, 4), (16, 14, 16, 14), (0.12, 7, 3)))
props.append('Card/base_type = &"PanelContainer"')
props.append('Card/styles/panel = %s' % sb("#f7efe0", 22, "#cfbc9e", (2, 2, 2, 4), (16, 14, 16, 14), (0.12, 7, 3)))

# 8. Thẻ tối mờ (CardDim)
props.append('CardDim/base_type = &"PanelContainer"')
props.append('CardDim/styles/panel = %s' % sb("#ecdfc8", 22, "#beaa8f", (2, 2, 2, 3), (16, 14, 16, 14), (0.08, 4, 2)))

# 9. Tấm bảng cuộn nội dung Tab (Sheet)
props.append('Sheet/base_type = &"PanelContainer"')
props.append('Sheet/styles/panel = %s' % sb("#f7efe0", 0, "#92400e", (0, 3, 0, 0), (16, 14, 16, 12), (0.26, 12, 0),
                                            radius_each=(28, 28, 0, 0)))

# 10. Khung Popup chính (PopupCard): Cuộn chiếu chỉ hoàng gia / Gỗ gụ viền vàng
props.append('PopupCard/base_type = &"PanelContainer"')
props.append('PopupCard/styles/panel = %s' % sb("#fbf6ea", 28, "#451a03", (4, 4, 4, 7), (20, 16, 20, 20), (0.42, 22, 8)))

# 11. Tiêu đề Popup (PopupHeader): Sơn mài Chu Sa viền vàng
props.append('PopupHeader/base_type = &"PanelContainer"')
props.append('PopupHeader/styles/panel = %s' % sb("#881337", 20, "#f59e0b", (2, 2, 2, 5), (20, 6, 20, 8), (0.25, 8, 3)))

# 12. Huy hiệu đỏ (Badge)
props.append('Badge/base_type = &"PanelContainer"')
props.append('Badge/styles/panel = %s' % sb("#b91c1c", 16, "#fef08a", (1.5, 1.5, 1.5, 2), (8, 0, 8, 2), (0.22, 4, 2)))

# 13. Hộp thông báo nhanh (Toast)
props.append('Toast/base_type = &"PanelContainer"')
props.append('Toast/styles/panel = %s' % sb("#2b1207", 26, "#f59e0b", (2, 2, 2, 3), (24, 10, 24, 12), (0.35, 10, 4), alpha=0.96))

# 14. Vùng nổi bật (Highlight): Lụa vàng hoàng triều
props.append('Highlight/base_type = &"PanelContainer"')
props.append('Highlight/styles/panel = %s' % sb("#fef3c7", 20, "#d97706", (2, 2, 2, 3), (12, 8, 12, 8)))

# 15. Viên tròn kiểu Pill
props.append('Pill/base_type = &"PanelContainer"')
props.append('Pill/styles/panel = %s' % sb("#381a0e", 32, "#b45309", (1.5, 1.5, 1.5, 3), (10, 4, 18, 4), (0.18, 5, 3)))

# ---- PHÔNG CHỮ & MÀU SẮC
props.append('Label/colors/font_color = %s' % col("#381a0e"))
props.append('Label/colors/font_outline_color = %s' % col("#fef3c7"))
props.append('Label/constants/line_spacing = 0')

props.append('TitleLabel/base_type = &"Label"')
props.append('TitleLabel/colors/font_color = %s' % col("#fffdf0"))
props.append('TitleLabel/colors/font_outline_color = %s' % col("#450a0a"))
props.append('TitleLabel/constants/outline_size = 8')
props.append('TitleLabel/font_sizes/font_size = 34')

props.append('HeaderLabel/base_type = &"Label"')
props.append('HeaderLabel/colors/font_color = %s' % col("#991b1b"))
props.append('HeaderLabel/font_sizes/font_size = 26')

props.append('SmallLabel/base_type = &"Label"')
props.append('SmallLabel/colors/font_color = %s' % col("#713f12"))
props.append('SmallLabel/font_sizes/font_size = 18')

props.append('GreenLabel/base_type = &"Label"')
props.append('GreenLabel/colors/font_color = %s' % col("#15803d"))
props.append('GreenLabel/font_sizes/font_size = 22')

props.append('WhiteLabel/base_type = &"Label"')
props.append('WhiteLabel/colors/font_color = %s' % col("#fffdf0"))
props.append('WhiteLabel/colors/font_outline_color = %s' % col("#2b1207"))
props.append('WhiteLabel/constants/outline_size = 6')

# Chữ cho số tiền & tài nguyên (màu vàng kim ấm)
props.append('ResourceLabel/base_type = &"Label"')
props.append('ResourceLabel/colors/font_color = %s' % col("#fef3c7"))
props.append('ResourceLabel/colors/font_outline_color = %s' % col("#1a0802"))
props.append('ResourceLabel/constants/outline_size = 4')
props.append('ResourceLabel/font_sizes/font_size = 24')

props.append('StatusLabel/base_type = &"Label"')
props.append('StatusLabel/colors/font_color = %s' % col("#f0fdf4"))
props.append('StatusLabel/colors/font_outline_color = %s' % col("#052e16"))
props.append('StatusLabel/constants/outline_size = 4')
props.append('StatusLabel/font_sizes/font_size = 16')

props.append('SideLabel/base_type = &"Label"')
props.append('SideLabel/colors/font_color = %s' % col("#fffaf0"))
props.append('SideLabel/colors/font_outline_color = %s' % col("#1d0d06"))
props.append('SideLabel/constants/outline_size = 4')
props.append('SideLabel/font_sizes/font_size = 14')

props.append('NavLabel/base_type = &"Label"')
props.append('NavLabel/colors/font_color = %s' % col("#d4bda4"))
props.append('NavLabel/colors/font_outline_color = %s' % col("#140702"))
props.append('NavLabel/constants/outline_size = 3')
props.append('NavLabel/font_sizes/font_size = 14')

# ---- THANH TIẾN ĐỘ
props.append('ProgressBar/styles/background = %s' % sb("#2b1307", 10, None, margin=(0, 0, 0, 0), alpha=0.35))
props.append('ProgressBar/styles/fill = %s' % sb("#16a34a", 10, "#14532d", (0, 0, 0, 2), (0, 0, 0, 0)))
props.append('ProgressBar/font_sizes/font_size = 16')
props.append('ProgressBar/colors/font_color = %s' % col("#fffdf0"))
props.append('ProgressBar/colors/font_outline_color = %s' % col("#052e16"))
props.append('ProgressBar/constants/outline_size = 4')

props.append('ExpBar/base_type = &"ProgressBar"')
props.append('ExpBar/styles/background = %s' % sb("#1d0b04", 6, "#542813", (1, 1, 1, 1), margin=(0, 0, 0, 0), alpha=0.7))
props.append('ExpBar/styles/fill = %s' % sb("#f59e0b", 6, "#b45309", (0, 0, 0, 1), margin=(0, 0, 0, 0)))

# ---- THANH CUỘN
props.append('VScrollBar/styles/scroll = %s' % sb("#000000", 6, None, margin=(4, 0, 4, 0), alpha=0.08))
props.append('VScrollBar/styles/grabber = %s' % sb("#cfbc9e", 6, None, margin=(4, 0, 4, 0)))
props.append('VScrollBar/styles/grabber_highlight = %s' % sb("#bda380", 6, None, margin=(4, 0, 4, 0)))
props.append('VScrollBar/styles/grabber_pressed = %s' % sb("#9d815d", 6, None, margin=(4, 0, 4, 0)))

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
print("Theme rebuilt successfully:", len(subs), "styleboxes.")
