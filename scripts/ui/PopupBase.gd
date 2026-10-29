class_name PopupBase
extends Control
## Khung popup chung: nền tối, bảng bo góc có tiêu đề + nút đóng, hiệu ứng phóng to khi mở.
## Lớp con ghi đè _build(body) để thêm nội dung.

signal closed

var title_text: String = ""
var closable: bool = true
var panel_width: float = 620.0
var panel: PanelContainer
var body: VBoxContainer
var title_label: Label
var _closing: bool = false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0.36, 0.2, 0.16, 0.55)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.gui_input.connect(_on_dim_input)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	panel = PanelContainer.new()
	panel.theme_type_variation = "PopupCard"
	panel.custom_minimum_size = Vector2(panel_width, 0)
	center.add_child(panel)
	var v := UIKit.vbox(16)
	panel.add_child(v)
	var header := PanelContainer.new()
	header.theme_type_variation = "PopupHeader"
	v.add_child(header)
	var hrow := UIKit.hbox(8)
	header.add_child(hrow)
	if closable:
		var pad := Control.new()
		pad.custom_minimum_size = Vector2(52, 0)
		hrow.add_child(pad)
	title_label = UIKit.label(title_text, "TitleLabel", 36)
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hrow.add_child(title_label)
	if closable:
		var x := UIKit.button("", "IconButton", "close")
		x.custom_minimum_size = Vector2(52, 52)
		x.add_theme_constant_override("icon_max_width", 50)
		x.pressed.connect(close)
		hrow.add_child(x)
	body = UIKit.vbox(14)
	v.add_child(body)
	_build(body)
	_add_lanterns()
	# hiệu ứng mở
	panel.resized.connect(_center_pivot)
	panel.scale = Vector2(0.7, 0.7)
	modulate.a = 0.0
	var t := create_tween().set_parallel(true)
	t.tween_property(self, "modulate:a", 1.0, 0.15)
	t.tween_property(panel, "scale", Vector2.ONE, 0.28).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	AudioManager.play("pop")


func _center_pivot() -> void:
	panel.pivot_offset = panel.size * 0.5
	_place_lanterns()


## Hai chiếc đèn lồng treo ở hai góc trên của khung, đung đưa nhẹ.
var _lanterns: Array[HangLantern] = []


func _add_lanterns() -> void:
	for i in 2:
		var l := HangLantern.new()
		l.z_index = 5
		l.scale = Vector2(0.78, 0.78)
		panel.add_child(l)
		_lanterns.append(l)
		var t := l.create_tween().set_loops()
		var amp: float = 0.08 if i == 0 else -0.08
		var dur: float = 1.3 + 0.25 * float(i)
		t.tween_property(l, "rotation", amp, dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
		t.tween_property(l, "rotation", -amp, dur).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_place_lanterns()


func _place_lanterns() -> void:
	if _lanterns.size() < 2 or panel == null:
		return
	_lanterns[0].position = Vector2(12, -64)
	_lanterns[1].position = Vector2(panel.size.x - 12, -64)



func _build(_b: VBoxContainer) -> void:
	pass


func _on_dim_input(event: InputEvent) -> void:
	if closable and event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		close()


func close() -> void:
	if _closing:
		return
	_closing = true
	var t := create_tween().set_parallel(true)
	t.tween_property(self, "modulate:a", 0.0, 0.14)
	t.tween_property(panel, "scale", Vector2(0.85, 0.85), 0.14)
	t.chain().tween_callback(_finish)


func _finish() -> void:
	# đổi tên trước khi báo đóng: popup kế tiếp mở trong handler `closed` sẽ giữ được đúng tên
	# (Main._has_popup tìm popup theo tên) thay vì bị Godot đặt tên tự sinh vì trùng tên
	name = "Closed_%d" % get_instance_id()
	closed.emit()
	queue_free()


## Hàng chữ căn giữa tiện dụng.
func centered_label(text: String, variation: String = "", font_size: int = 0) -> Label:
	var l := UIKit.label(text, variation, font_size)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
