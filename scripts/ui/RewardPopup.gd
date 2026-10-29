extends PopupBase
## Màn nhận thưởng: tia sáng xoay phía sau, tiêu đề trên ruy băng, mỗi phần thưởng là một ô thẻ
## (icon to + số lượng nổi bật) nảy ra lần lượt. Rương thì rung lắc, bật nắp rồi mới lộ thưởng.

var rewards: Array = []
var _rays: TextureRect
var _rays2: TextureRect
var _chest: TextureRect
var _tiles: Array[Control] = []
var _ok: JuicyButton
var _t: float = 0.0
var _wait: float = 0.3
var _shown: int = 0


func _init() -> void:
	if title_text.is_empty():
		title_text = "Phần thưởng!"
	closable = false
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	# bỏ khung popup mặc định: màn thưởng dùng bố cục riêng nổi trên nền tối
	panel.add_theme_stylebox_override("panel", StyleBoxEmpty.new())
	title_label.get_parent().get_parent().visible = false
	# tia sáng xoay (2 lớp quay ngược chiều)
	_rays = _make_rays(Color(1, 0.86, 0.45, 0.85))
	_rays2 = _make_rays(Color(1, 0.95, 0.75, 0.45))
	_rays2.rotation = 0.3
	# tiêu đề trên ruy băng
	var head := Control.new()
	head.custom_minimum_size = Vector2(0, 150)
	b.add_child(head)
	if ResourceLoader.exists("res://assets/ui/ribbon.svg"):
		var rib := TextureRect.new()
		rib.texture = Sprites.ui("ribbon")
		rib.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rib.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		rib.set_anchors_preset(Control.PRESET_FULL_RECT)
		rib.mouse_filter = Control.MOUSE_FILTER_IGNORE
		head.add_child(rib)
	var title := UIKit.label(title_text.to_upper(), "TitleLabel", 44)
	title.set_anchors_preset(Control.PRESET_FULL_RECT)
	title.offset_top = -14
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(title)
	# rương (nếu có) rung rồi bật
	var items: Array = rewards.duplicate()
	if not items.is_empty() and str(items[0]["icon"]).begins_with("chest_"):
		var chest_item: Dictionary = items.pop_front()
		_chest = UIKit.icon(str(chest_item["icon"]), 190)
		_chest.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		b.add_child(_chest)
		_wait = 1.1
		var t := create_tween()
		t.tween_interval(0.15)
		for i in 7:
			t.tween_property(_chest, "rotation", 0.14 * (1 if i % 2 == 0 else -1), 0.07)
		t.tween_property(_chest, "rotation", 0.0, 0.05)
		t.tween_property(_chest, "scale", Vector2(1.35, 1.35), 0.12)
		t.tween_property(_chest, "scale", Vector2(0.9, 0.9), 0.15)
		AudioManager.play("chest_open")
	# lưới ô thưởng
	var center := CenterContainer.new()
	b.add_child(center)
	var grid := GridContainer.new()
	grid.columns = clampi(items.size(), 1, 3)
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	center.add_child(grid)
	var compact: bool = items.size() > 6
	for r: Dictionary in items:
		var tile := _make_tile(r, compact)
		tile.modulate.a = 0.0
		grid.add_child(tile)
		_tiles.append(tile)
	# nút nhận
	_ok = UIKit.button("NHẬN TẤT CẢ ✨", "RedButton", "", 320)
	_ok.custom_minimum_size = Vector2(320, 84)
	_ok.add_theme_font_size_override("font_size", 32)
	_ok.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_ok.pressed.connect(close)
	_ok.modulate.a = 0.0
	b.add_child(_ok)
	AudioManager.play("purchase")


func _make_rays(col: Color) -> TextureRect:
	var r := TextureRect.new()
	if ResourceLoader.exists("res://assets/ui/rays.svg"):
		r.texture = Sprites.ui("rays")
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	r.size = Vector2(980, 980)
	r.pivot_offset = r.size * 0.5
	r.modulate = col
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(r)
	move_child(r, 1)   # ngay trên lớp nền tối, dưới bảng thưởng
	return r


## Ô thưởng: thẻ kem viền vàng (thẻ đầu bếp thì viền theo độ hiếm), icon to, số lượng nổi bật.
func _make_tile(r: Dictionary, compact: bool) -> Control:
	var text: String = str(r["text"])
	var amount: String = ""
	var label: String = text
	if text.begins_with("+"):
		var sp := text.find(" ")
		amount = text.substr(0, sp) if sp > 0 else text
		label = text.substr(sp + 1) if sp > 0 else ""
	var card_id: String = str(r.get("card", ""))
	var tile := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("fffdf6")
	sb.set_corner_radius_all(24)
	sb.set_border_width_all(4)
	sb.border_color = Color("f08a76")
	sb.shadow_color = Color(0.25, 0.12, 0.05, 0.28)
	sb.shadow_size = 12
	sb.shadow_offset = Vector2(0, 6)
	sb.set_content_margin_all(10)
	if not card_id.is_empty():
		sb.border_color = Color(str(Progress.cards_data["rarity_colors"][Progress.card_info(card_id)["rarity"]]))
		sb.bg_color = Color("fffaf0")
	tile.add_theme_stylebox_override("panel", sb)
	tile.custom_minimum_size = Vector2(150, 0) if compact else Vector2(186, 0)
	var v := UIKit.vbox(0)
	tile.add_child(v)
	var ic := UIKit.icon(str(r["icon"]), 70 if compact else 108)
	ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(ic)
	if not amount.is_empty():
		var a := UIKit.label(amount, "TitleLabel", 30 if compact else 40)
		a.add_theme_color_override("font_color", Color("ffe27a"))
		a.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(a)
	var l := UIKit.label(label, "", 17 if compact else 20)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(130 if compact else 160, 0)
	v.add_child(l)
	return tile


func _process(delta: float) -> void:
	_t += delta
	var vs := get_viewport_rect().size
	for r in [_rays, _rays2]:
		if r:
			r.position = vs * 0.5 - r.size * 0.5 + Vector2(0, -60)
	_rays.rotation += delta * 0.25
	_rays2.rotation -= delta * 0.15
	if _chest:
		_chest.pivot_offset = _chest.size * 0.5
	if _wait > 0.0:
		_wait -= delta
		return
	if _shown < _tiles.size():
		if _t >= 0.16:
			_t = 0.0
			_reveal(_tiles[_shown], _shown)
			_shown += 1
	elif _ok.modulate.a == 0.0:
		_ok.modulate.a = 1.0
		_ok.pulse = true
		Juice.bounce(_ok, 1.4)


func _reveal(tile: Control, idx: int) -> void:
	tile.modulate.a = 1.0
	tile.pivot_offset = tile.size * 0.5
	tile.scale = Vector2(0.3, 0.3)
	var t := create_tween()
	t.tween_property(tile, "scale", Vector2(1.12, 1.12), 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(tile, "scale", Vector2.ONE, 0.1)
	var rw: Dictionary = rewards[idx + (1 if _chest else 0)]
	if rw.has("card"):
		var legend: bool = Progress.card_info(str(rw["card"])).get("rarity", "") == "legend"
		AudioManager.play("legendary" if legend else "card_flip", 0.0 if legend else 0.1)
		if legend:
			tile.modulate = Color(1.5, 1.3, 0.7)
			create_tween().tween_property(tile, "modulate", Color.WHITE, 0.7)
	else:
		AudioManager.play("coin" if str(rw["icon"]) == "coin" else "pop", 0.15)
	if UIKit.main:
		UIKit.main.call("sparkle_at", tile.get_global_rect().get_center())
