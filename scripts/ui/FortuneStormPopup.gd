class_name FortuneStormPopup
extends PopupBase
## Minigame Mưa Lì Xì Thần Tài:
## Trong 10 giây, hàng chục bao lì xì đỏ may mắn sẽ rơi lả tả từ trên trời xuống.
## Người chơi bấm nhanh để bắt lì xì nhận mưa Tiền Vàng và Kim Cương!

var _game_active: bool = true
var _time_left: float = 10.0
var _collected_count: int = 0
var _total_gold: float = 0.0
var _total_diamonds: int = 0

var _canvas: Control
var _time_label: Label
var _stats_label: Label
var _finish_btn: JuicyButton

var _envelopes: Array[Dictionary] = []
var _floaters: Array[Dictionary] = []
var _spawn_timer: float = 0.0

func _init() -> void:
	title_text = "Mưa Lì Xì Thần Tài 🧧"
	panel_width = 680.0
	closable = false # Chỉ đóng khi hết giờ hoặc bấm hoàn tất

func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Chạm nhanh vào các bao lì xì đang rơi để thu thập tài lộc!", "BodyLabel", 20)
	b.add_child(sub)

	# Bảng thống kê phía trên
	var stat_box := PanelContainer.new()
	stat_box.theme_type_variation = "Card"
	b.add_child(stat_box)

	var stat_h := UIKit.hbox(16)
	stat_h.alignment = BoxContainer.ALIGNMENT_CENTER
	stat_box.add_child(stat_h)

	_time_label = UIKit.label("⏳ Thời gian: 10.0s", "HeaderLabel", 22)
	_time_label.add_theme_color_override("font_color", Color("ef4444"))
	stat_h.add_child(_time_label)

	_stats_label = UIKit.label("🧧 Bắt được: 0 | 🪙 0 | 💎 0", "HeaderLabel", 20)
	_stats_label.add_theme_color_override("font_color", Color("d97706"))
	stat_h.add_child(_stats_label)

	# Khu vực hứng lì xì tương tác
	_canvas = Control.new()
	_canvas.custom_minimum_size = Vector2(640, 460)
	_canvas.mouse_filter = Control.MOUSE_FILTER_STOP
	_canvas.gui_input.connect(_on_canvas_input)
	_canvas.draw.connect(_draw_canvas)
	b.add_child(_canvas)

	# Nút hoàn tất (ẩn ban đầu)
	_finish_btn = UIKit.button("Thu Hoạch Tài Lộc ✨", "GreenButton", "", 320)
	_finish_btn.visible = false
	_finish_btn.pressed.connect(close)
	b.add_child(_finish_btn)

	# Sinh 6 bao lì xì đầu tiên ngay lập tức
	for i in range(6):
		_spawn_envelope(randf_range(20.0, 400.0))

func _on_canvas_input(event: InputEvent) -> void:
	if not _game_active:
		return
	# chỉ nghe chuột: project bật emulate_mouse_from_touch nên một lần chạm đã sinh sự kiện chuột,
	# nghe thêm ScreenTouch sẽ bắt 2 bao lì xì cho một lần chạm
	if event is InputEventMouseButton and event.pressed:
		_check_click(event.position)

func _check_click(pos: Vector2) -> void:
	var hit_index := -1
	for i in range(_envelopes.size() - 1, -1, -1):
		var env := _envelopes[i]
		var ep: Vector2 = env["pos"]
		var rect := Rect2(ep.x - 28, ep.y - 36, 56, 72)
		if rect.has_point(pos):
			hit_index = i
			break

	if hit_index >= 0:
		var env := _envelopes[hit_index]
		_envelopes.remove_at(hit_index)
		_collected_count += 1

		var is_diamond: bool = bool(env["is_diamond"])
		if is_diamond:
			var d_val: int = int(env["val"])
			_total_diamonds += d_val
			GameState.add_diamonds(d_val)
			_add_floater(pos, "+%d 💎" % d_val, Color("38bdf8"))
			AudioManager.play("levelup", 0.1)
		else:
			var g_val: float = float(env["val"])
			_total_gold += g_val
			GameState.add_gold(g_val)
			_add_floater(pos, "+%s 🪙" % NumberFormat.fmt(g_val), Color("facc15"))
			AudioManager.play_pitch("coin", randf_range(1.1, 1.4))

		AudioManager.vibrate(15)
		_update_labels()

func _add_floater(pos: Vector2, text: String, col: Color) -> void:
	_floaters.append({
		"pos": pos,
		"text": text,
		"color": col,
		"life": 0.8,
		"max_life": 0.8
	})

func _spawn_envelope(start_y: float = -40.0) -> void:
	var cw: float = _canvas.size.x if _canvas.size.x > 0 else 640.0
	var is_gem: bool = randf() < 0.18
	var val: float
	if is_gem:
		val = float(randi_range(1, 2))
	else:
		var base := maxf(880.0, GameState.income_rate() * 15.0)
		val = base * randf_range(0.8, 2.2)

	_envelopes.append({
		"pos": Vector2(randf_range(40.0, cw - 40.0), start_y),
		"vel_y": randf_range(110.0, 220.0),
		"wobble_phase": randf() * TAU,
		"wobble_speed": randf_range(2.0, 4.0),
		"rot": randf_range(-0.2, 0.2),
		"is_diamond": is_gem,
		"val": val
	})

func _process(delta: float) -> void:
	if _game_active:
		_time_left -= delta
		if _time_left <= 0.0:
			_time_left = 0.0
			_game_active = false
			_on_game_over()

		_spawn_timer += delta
		if _spawn_timer >= 0.28:
			_spawn_timer = 0.0
			_spawn_envelope()

		# Di chuyển bao lì xì
		var cw: float = _canvas.size.x if _canvas.size.x > 0 else 640.0
		var ch: float = _canvas.size.y if _canvas.size.y > 0 else 460.0
		var surviving: Array[Dictionary] = []
		for env in _envelopes:
			env["wobble_phase"] += delta * float(env["wobble_speed"])
			var wobble := sin(float(env["wobble_phase"])) * 45.0 * delta
			env["pos"].x = clampf(env["pos"].x + wobble, 30.0, cw - 30.0)
			env["pos"].y += float(env["vel_y"]) * delta
			env["rot"] = sin(float(env["wobble_phase"])) * 0.25
			if env["pos"].y < ch + 50.0:
				surviving.append(env)
		_envelopes = surviving

	# Cập nhật số bay (floaters)
	var surviving_floaters: Array[Dictionary] = []
	for f in _floaters:
		f["life"] -= delta
		f["pos"].y -= delta * 45.0
		if f["life"] > 0.0:
			surviving_floaters.append(f)
	_floaters = surviving_floaters

	_update_labels()
	if _canvas:
		_canvas.queue_redraw()

func _on_game_over() -> void:
	AudioManager.play("celebrate")
	AudioManager.vibrate(60)
	_finish_btn.visible = true
	GameState.show_toast("🧧 Thần Tài Ban Lộc: Bạn đã bắt được %d bao lì xì!" % _collected_count)
	if UIKit.main:
		UIKit.main.call("burst_sparkles", panel.get_global_rect().get_center(), 24)

func _update_labels() -> void:
	if _time_label:
		_time_label.text = "⏳ Thời gian: %.1fs" % _time_left
	if _stats_label:
		_stats_label.text = "🧧 Đã bắt: %d | 🪙 %s | 💎 %d" % [
			_collected_count,
			NumberFormat.fmt(_total_gold),
			_total_diamonds
		]

func _draw_canvas() -> void:
	var cw: float = _canvas.size.x if _canvas.size.x > 0 else 640.0
	var ch: float = _canvas.size.y if _canvas.size.y > 0 else 460.0

	# Nền tranh thủy mặc may mắn
	_canvas.draw_rect(Rect2(0, 0, cw, ch), Color(0.98, 0.94, 0.88, 0.65))
	_canvas.draw_rect(Rect2(0, 0, cw, ch), Color("f59e0b"), false, 2.5)

	# Vẽ từng bao lì xì
	for env in _envelopes:
		var p: Vector2 = env["pos"]
		var rot: float = float(env["rot"])
		var is_gem: bool = bool(env["is_diamond"])

		_canvas.draw_set_transform(p, rot, Vector2.ONE)

		# Thân bao lì xì
		var bg_col := Color("dc2626") if not is_gem else Color("0284c7")
		var w := 44.0
		var h := 58.0
		_canvas.draw_rect(Rect2(-w * 0.5, -h * 0.5, w, h), bg_col)
		_canvas.draw_rect(Rect2(-w * 0.5, -h * 0.5, w, h), Color("facc15"), false, 2.0)

		# Nắp bao lì xì hình tam giác
		var flap := PackedVector2Array([
			Vector2(-w * 0.5, -h * 0.5),
			Vector2(0, -h * 0.5 + 14),
			Vector2(w * 0.5, -h * 0.5)
		])
		_canvas.draw_colored_polygon(flap, Color("b91c1c") if not is_gem else Color("0369a1"))
		_canvas.draw_polyline(flap, Color("facc15"), 1.8)

		# Hoa văn đồng tiền vàng giữa bao
		_canvas.draw_circle(Vector2(0, 4), 10.0, Color("facc15"))
		_canvas.draw_rect(Rect2(-3, 1, 6, 6), Color("b91c1c") if not is_gem else Color("0369a1"))

		_canvas.draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

	# Vẽ số bay (Floaters)
	for f in _floaters:
		var alpha: float = float(f["life"]) / float(f["max_life"])
		var col: Color = f["color"]
		col.a = alpha
		_canvas.draw_string(
			ThemeDB.fallback_font,
			f["pos"] as Vector2,
			str(f["text"]),
			HORIZONTAL_ALIGNMENT_CENTER,
			-1,
			22,
			col
		)
