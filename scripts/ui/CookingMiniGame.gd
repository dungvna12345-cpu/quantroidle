class_name CookingMiniGame
extends PopupBase
## Mini-game "Trổ Tài Nấu Nướng" (Master Chef Cooking Rush):
## Người chơi căn nhịp xào chảo đúng vạch xanh để tạo món ăn thượng hạng!

class TimingBar extends Control:
	var needle_pos: float = 0.0 # 0.0 to 1.0
	var moving: bool = true
	var speed: float = 1.8
	var _t: float = 0.0

	func _process(delta: float) -> void:
		if moving:
			_t += delta * speed
			needle_pos = (sin(_t) + 1.0) * 0.5
			queue_redraw()

	func _draw() -> void:
		var w: float = size.x
		var h: float = size.y
		var r: float = 12.0

		# 1. Nền thanh trượt
		draw_rect(Rect2(0, 0, w, h), Color("2e221d"), true, -1.0)
		draw_rect(Rect2(0, 0, w, h), Color("5c4033"), false, 3.0)

		# 2. Vùng Vàng "Khá Tốt" (30% -> 70%)
		var y_start := w * 0.30
		var y_w := w * 0.40
		draw_rect(Rect2(y_start, 2, y_w, h - 4), Color("eab308"), true)

		# 3. Vùng Xanh "Hoàn Hảo" (42% -> 58%)
		var g_start := w * 0.42
		var g_w := w * 0.16
		draw_rect(Rect2(g_start, 2, g_w, h - 4), Color("22c55e"), true)

		# 4. Vạch Vàng Kim "Thần Bếp" (48% -> 52%)
		var k_start := w * 0.485
		var k_w := w * 0.03
		draw_rect(Rect2(k_start, 0, k_w, h), Color("fef08a"), true)

		# 5. Kim chỉ màu đỏ cam chuyển động
		var nx := needle_pos * w
		var pts := PackedVector2Array([
			Vector2(nx - 8, -6),
			Vector2(nx + 8, -6),
			Vector2(nx, h + 6)
		])
		draw_colored_polygon(pts, Color("ef4444"))
		draw_polyline(pts, Color.WHITE, 2.0, true)


var _bar: TimingBar
var _action_btn: JuicyButton
var _result_label: Label
var _wok_icon: TextureRect
var _flame_t: float = 0.0
var _played: bool = false


func _init() -> void:
	title_text = "Trổ Tài Nấu Nướng"
	panel_width = 650.0


func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Căn đúng vạch XANH LÁ để tạo Món Ăn Thượng Hạng!", "BodyLabel", 22)
	b.add_child(sub)

	# Chảo lửa xèo xèo
	var center_box := CenterContainer.new()
	center_box.custom_minimum_size = Vector2(0, 140)
	b.add_child(center_box)

	_wok_icon = TextureRect.new()
	_wok_icon.texture = Sprites.tex("chef_phong")
	_wok_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_wok_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_wok_icon.custom_minimum_size = Vector2(120, 120)
	_wok_icon.pivot_offset = Vector2(60, 60)
	center_box.add_child(_wok_icon)

	# Thanh căn nhịp
	var bar_margin := MarginContainer.new()
	bar_margin.add_theme_constant_override("margin_top", 15)
	bar_margin.add_theme_constant_override("margin_bottom", 15)
	bar_margin.add_theme_constant_override("margin_left", 30)
	bar_margin.add_theme_constant_override("margin_right", 30)
	b.add_child(bar_margin)

	_bar = TimingBar.new()
	_bar.custom_minimum_size = Vector2(520, 42)
	bar_margin.add_child(_bar)

	# Chú thích các vùng
	var leg := UIKit.hbox(20)
	leg.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(leg)
	leg.add_child(_legend_item(Color("eab308"), "Ngon (+1x)"))
	leg.add_child(_legend_item(Color("22c55e"), "Tuyệt Hảo (+3x)"))
	leg.add_child(_legend_item(Color("fef08a"), "Thần Bếp (+6x & Kim Cương)"))

	_result_label = centered_label("", "HeaderLabel", 26)
	b.add_child(_result_label)

	_action_btn = UIKit.button("XÀO CHẢO NGAY!", "RedButton", "", 320)
	_action_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_action_btn.pressed.connect(_on_cook_press)
	b.add_child(_action_btn)


func _legend_item(c: Color, text: String) -> HBoxContainer:
	var h := UIKit.hbox(6)
	var dot := ColorRect.new()
	dot.custom_minimum_size = Vector2(16, 16)
	dot.color = c
	h.add_child(dot)
	h.add_child(UIKit.label(text, "SmallLabel", 18))
	return h


func _process(delta: float) -> void:
	if not _played and _wok_icon:
		_flame_t += delta * 8.0
		_wok_icon.rotation = sin(_flame_t) * 0.08
		_wok_icon.scale = Vector2.ONE * (1.0 + sin(_flame_t * 1.5) * 0.05)


func _on_cook_press() -> void:
	if _played:
		close()
		return
	_played = true
	_bar.moving = false

	var pos := _bar.needle_pos
	var dist := absf(pos - 0.5)

	Juice.bounce(_wok_icon, 1.4)
	AudioManager.play("coin", 0.1)

	if dist <= 0.035:
		# THẦN BẾP (PERFECT)!
		AudioManager.play("levelup", 0.15)
		AudioManager.play("bell", 0.1)
		_result_label.text = "THẦN BẾP XUẤT THẾ! MÓN ĂN HOÀNG KIM!"
		_result_label.modulate = Color("facc15")
		var gold := maxf(888.0, GameState.income_rate() * 60.0)
		GameState.add_gold(gold)
		GameState.add_diamonds(1)
		GameState.start_fever(20.0)
		GameState.show_toast("THẦN BẾP HOÀN HẢO! +%s Vàng & +1 Kim Cương!" % NumberFormat.fmt(gold), "diamond")
	elif dist <= 0.09:
		# TUYỆT HẢO
		AudioManager.play("bell", 0.1)
		_result_label.text = "MÓN ĂN TUYỆT HẢO! KHÁCH KHEN NỨC NỞ!"
		_result_label.modulate = Color("22c55e")
		var gold := maxf(388.0, GameState.income_rate() * 25.0)
		GameState.add_gold(gold)
		GameState.start_fever(10.0)
		GameState.show_toast("MÓN TUYỆT HẢO! +%s Vàng!" % NumberFormat.fmt(gold))
	else:
		# BÌNH THƯỜNG
		_result_label.text = "Món Ăn Thơm Ngon, Vừa Vị!"
		_result_label.modulate = Color("e07a3f")
		var gold := maxf(120.0, GameState.income_rate() * 10.0)
		GameState.add_gold(gold)
		GameState.show_toast("+%s Vàng!" % NumberFormat.fmt(gold))

	if UIKit.main:
		for i in 6:
			UIKit.main.call("sparkle_at", _action_btn.global_position + Vector2(randf_range(-100, 100), randf_range(-40, 20)))

	_action_btn.text = "NHẬN THƯỞNG"
