class_name UIKit
extends RefCounted
## Hàm dựng giao diện dùng chung để các tab, popup có cùng phong cách.

static var main: Node = null   # tham chiếu Main (mở popup, hiệu ứng)


static func label(text: String, variation: String = "", font_size: int = 0) -> Label:
	var l := Label.new()
	l.text = text
	if not variation.is_empty():
		l.theme_type_variation = variation
	if font_size > 0:
		l.add_theme_font_size_override("font_size", font_size)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


static func icon(tex_id: String, px: float, from_ui: bool = true) -> TextureRect:
	var t := TextureRect.new()
	t.texture = Sprites.ui(tex_id) if from_ui else Sprites.tex(tex_id)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.custom_minimum_size = Vector2(px, px)
	t.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return t


static func button(text: String, variation: String = "", icon_id: String = "", min_w: float = 0.0) -> JuicyButton:
	var b := JuicyButton.new()
	b.text = text
	if not variation.is_empty():
		b.theme_type_variation = variation
	if not icon_id.is_empty():
		b.icon = Sprites.ui(icon_id)
		b.expand_icon = false
	b.custom_minimum_size = Vector2(min_w, 64)
	return b


static func panel(variation: String = "Card") -> PanelContainer:
	var p := PanelContainer.new()
	p.theme_type_variation = variation
	return p


static func hbox(sep: int = 10) -> HBoxContainer:
	var b := HBoxContainer.new()
	b.add_theme_constant_override("separation", sep)
	return b


static func vbox(sep: int = 8) -> VBoxContainer:
	var b := VBoxContainer.new()
	b.add_theme_constant_override("separation", sep)
	return b


static func margin(l: int, t: int, r: int, b: int) -> MarginContainer:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", l)
	m.add_theme_constant_override("margin_top", t)
	m.add_theme_constant_override("margin_right", r)
	m.add_theme_constant_override("margin_bottom", b)
	return m


static func spacer() -> Control:
	var c := Control.new()
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


## Danh sách cuộn dọc có lề, trả về VBox để thêm thẻ.
static func scroll_list(parent: Control, sep: int = 14) -> VBoxContainer:
	var sc := ScrollContainer.new()
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	parent.add_child(sc)
	var m := margin(18, 14, 18, 24)
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(m)
	var v := vbox(sep)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	m.add_child(v)
	return v


## Nền tab dạng tấm giấy bo góc trên, có tiêu đề và danh sách cuộn.
static func tab_sheet(parent: Control, title: String, subtitle: String = "") -> VBoxContainer:
	var sheet := panel("Sheet")
	sheet.set_anchors_preset(Control.PRESET_FULL_RECT)
	parent.add_child(sheet)
	var v := vbox(4)
	sheet.add_child(v)
	var t := label(title, "HeaderLabel", 34)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	if not subtitle.is_empty():
		var s := label(subtitle, "SmallLabel", 20)
		s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		s.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(s)
	var holder := Control.new()
	holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	holder.clip_contents = true
	v.add_child(holder)
	var sc := ScrollContainer.new()
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	holder.add_child(sc)
	var m := margin(2, 8, 2, 24)
	m.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(m)
	var list := vbox(14)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	m.add_child(list)
	return list


static func section(text: String) -> Label:
	var l := label(text, "", 28)
	l.add_theme_color_override("font_color", ChapterTheme.accent())
	return l


## Chữ giá kèm biểu tượng (vàng hoặc kim cương) dạng "1.2K".
static func cost_text(v: float) -> String:
	return NumberFormat.fmt(v)
