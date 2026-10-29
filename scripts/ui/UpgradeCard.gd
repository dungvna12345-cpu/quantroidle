class_name UpgradeCard
extends PanelContainer
## Thẻ nâng cấp bo góc lớn có bóng: ảnh, tên, cấp, 2 dòng chỉ số, tối đa 2 nút.

signal action(idx: int)

var icon_rect: TextureRect
var title_label: Label
var level_label: Label
var line1: Label
var line2: Label
var button_box: VBoxContainer
var buttons: Array[JuicyButton] = []


func _init() -> void:
	theme_type_variation = "Card"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var row := UIKit.hbox(14)
	add_child(row)
	var icon_bg := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("ffe9c2")
	sb.set_corner_radius_all(22)
	sb.border_color = Color("e2c08c")
	sb.set_border_width_all(3)
	sb.set_content_margin_all(6)
	icon_bg.add_theme_stylebox_override("panel", sb)
	icon_bg.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(icon_bg)
	icon_rect = TextureRect.new()
	icon_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon_rect.custom_minimum_size = Vector2(96, 96)
	icon_bg.add_child(icon_rect)
	var info := UIKit.vbox(2)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(info)
	var title_row := UIKit.hbox(8)
	info.add_child(title_row)
	# tiêu đề dài thì rút gọn bằng "…" thay vì đẩy thẻ rộng ra ngoài màn hình
	title_label = UIKit.label("", "", 26)
	title_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_row.add_child(title_label)
	level_label = UIKit.label("", "SmallLabel")
	level_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	level_label.size_flags_horizontal = Control.SIZE_SHRINK_END
	title_row.add_child(level_label)
	line1 = UIKit.label("", "GreenLabel")
	line1.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(line1)
	line2 = UIKit.label("", "SmallLabel")
	line2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.add_child(line2)
	button_box = UIKit.vbox(8)
	button_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(button_box)


func setup(tex: Texture2D, title: String, button_count: int = 1) -> void:
	icon_rect.texture = tex
	title_label.text = title
	for i in button_count:
		var b := UIKit.button("", "", "coin", 190)
		b.clip_text = true
		b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		b.add_theme_font_size_override("font_size", 23)
		var idx := i
		b.pressed.connect(func() -> void: action.emit(idx))
		button_box.add_child(b)
		buttons.append(b)


func set_info(lvl: String, a: String, b: String = "") -> void:
	level_label.text = lvl
	line1.text = a
	line2.text = b
	line2.visible = not b.is_empty()


## Cập nhật nút: chữ, bật/tắt, kiểu, icon giá, nhấp nháy khi đủ tiền.
func set_button(i: int, text: String, enabled: bool, variation: String = "", icon_id: String = "coin",
		pulse: bool = false) -> void:
	if i >= buttons.size():
		return
	var b := buttons[i]
	b.text = text
	b.disabled = not enabled
	b.theme_type_variation = variation
	b.icon = Sprites.ui(icon_id) if not icon_id.is_empty() else null
	b.pulse = pulse and enabled
	b.visible = true


func hide_button(i: int) -> void:
	if i < buttons.size():
		buttons[i].visible = false


func dim(on: bool) -> void:
	theme_type_variation = "CardDim" if on else "Card"
	icon_rect.modulate = Color(0.55, 0.55, 0.55) if on else Color.WHITE
