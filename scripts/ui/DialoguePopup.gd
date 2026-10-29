extends Control
## Màn hội thoại cốt truyện kiểu truyện tranh: chân dung lớn, bảng tên, chữ chạy từng chữ.
## Chạm để hiện hết câu / sang câu tiếp. Nút "Bỏ qua" để xem nhanh.

signal finished(scene_id: String)

const CHARS_PER_SEC := 45.0

var scene_id: String = ""
var lines: Array = []
var _i: int = -1
var _shown: float = 0.0
var _portrait: TextureRect
var _name_panel: PanelContainer
var _name_label: Label
var _text: Label
var _arrow: Label
var _panel: PanelContainer
var _t: float = 0.0
var _last_who: String = ""
var _done: bool = false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var dim := ColorRect.new()
	dim.color = Color(0.12, 0.06, 0.02, 0.45)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	# chân dung đứng trên khung thoại
	_portrait = TextureRect.new()
	_portrait.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_portrait.offset_left = 10
	_portrait.offset_right = 330
	_portrait.offset_top = -760
	_portrait.offset_bottom = -300
	add_child(_portrait)
	# khung thoại
	_panel = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("fff6e6")
	sb.set_corner_radius_all(30)
	sb.set_border_width_all(5)
	sb.border_color = Color("8a5530")
	sb.shadow_color = Color(0, 0, 0, 0.3)
	sb.shadow_size = 14
	sb.content_margin_left = 28
	sb.content_margin_right = 28
	sb.content_margin_top = 34
	sb.content_margin_bottom = 26
	_panel.add_theme_stylebox_override("panel", sb)
	_panel.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_panel.offset_left = 16
	_panel.offset_right = -16
	_panel.offset_top = -330
	_panel.offset_bottom = -40
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_panel)
	_text = UIKit.label("", "", 28)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_panel.add_child(_text)
	_arrow = UIKit.label("Chạm để tiếp ▼", "SmallLabel", 18)
	_arrow.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_arrow.offset_left = -230
	_arrow.offset_top = -78
	_arrow.offset_right = -40
	_arrow.offset_bottom = -48
	_arrow.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	add_child(_arrow)
	# bảng tên
	_name_panel = PanelContainer.new()
	_name_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_name_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_name_panel.offset_left = 40
	_name_panel.offset_top = -356
	_name_panel.offset_right = 340
	_name_panel.offset_bottom = -306
	add_child(_name_panel)
	_name_label = UIKit.label("", "WhiteLabel", 26)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name_panel.add_child(_name_label)
	var skip := UIKit.button("Bỏ qua", "", "arrow_right", 170)
	skip.custom_minimum_size = Vector2(170, 56)
	skip.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	skip.offset_left = -190
	skip.offset_right = -20
	skip.offset_top = 150
	skip.offset_bottom = 206
	skip.pressed.connect(_finish)
	add_child(skip)
	modulate.a = 0.0
	create_tween().tween_property(self, "modulate:a", 1.0, 0.2)
	_next()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed \
			and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		accept_event()
		if _shown < _text.text.length():
			_shown = _text.text.length()
			_text.visible_characters = -1
		else:
			_next()


func _next() -> void:
	_i += 1
	if _i >= lines.size():
		_finish()
		return
	var ln: Dictionary = lines[_i]
	var who: String = str(ln["who"])
	var ch: Dictionary = Story.character(who)
	_name_label.text = str(ch["name"])
	var nsb := StyleBoxFlat.new()
	nsb.bg_color = Color(str(ch.get("color", "#6b4128")))
	nsb.set_corner_radius_all(18)
	nsb.set_border_width_all(4)
	nsb.border_color = Color("fff6e6")
	nsb.content_margin_top = 4
	nsb.content_margin_bottom = 6
	_name_panel.add_theme_stylebox_override("panel", nsb)
	# Phát (đối thủ) đứng bên phải, mọi người khác bên trái
	var right: bool = who == "phat"
	_portrait.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT if right else Control.PRESET_BOTTOM_LEFT)
	_portrait.offset_left = -330 if right else 10
	_portrait.offset_right = -10 if right else 330
	_portrait.offset_top = -760
	_portrait.offset_bottom = -300
	_portrait.flip_h = right
	_name_panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT if right else Control.PRESET_BOTTOM_LEFT)
	_name_panel.offset_left = -340 if right else 40
	_name_panel.offset_right = -40 if right else 340
	_name_panel.offset_top = -356
	_name_panel.offset_bottom = -306
	var p: String = str(ch.get("portrait", ""))
	_portrait.texture = Sprites.ui(p) if not p.is_empty() else null
	if who != _last_who:
		# nhân vật mới bước vào: trượt lên + nảy
		_portrait.pivot_offset = Vector2(160, 460)
		_portrait.scale = Vector2(0.9, 0.9)
		_portrait.modulate.a = 0.0
		var tw := create_tween().set_parallel(true)
		tw.tween_property(_portrait, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(_portrait, "modulate:a", 1.0, 0.15)
		AudioManager.play("pop", 0.1)
	_last_who = who
	_text.text = str(ln["text"])
	_text.visible_characters = 0
	_shown = 0.0


func _process(delta: float) -> void:
	_t += delta
	if _shown < _text.text.length():
		_shown += delta * CHARS_PER_SEC
		_text.visible_characters = int(_shown)
		_arrow.modulate.a = 0.0
	else:
		_arrow.modulate.a = 0.5 + 0.5 * sin(_t * 5.0)
	# nhân vật nhún nhẹ khi đang nói
	if _shown < _text.text.length():
		_portrait.rotation = sin(_t * 12.0) * 0.012


## Đóng (nút Back Android / kiểm thử): coi như đã xem.
func close() -> void:
	_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	set_process(false)
	finished.emit(scene_id)
	var tw := create_tween()
	tw.tween_property(self, "modulate:a", 0.0, 0.15)
	tw.tween_callback(queue_free)
