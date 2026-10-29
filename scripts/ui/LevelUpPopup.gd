extends PopupBase
## Popup chúc mừng lên cấp kèm pháo hoa và danh sách mở khóa.

var new_level: int = 2
var unlocks: Array = []
var _fireworks: Array[CPUParticles2D] = []
var _fw_t: float = 0.0


func _init() -> void:
	title_text = "LÊN CẤP!"
	closable = false


func _build(b: VBoxContainer) -> void:
	panel_width = 620.0
	# Ẩn header mặc định để dùng banner ruy băng san hô Concept A
	if title_label and title_label.get_parent() and title_label.get_parent().get_parent():
		title_label.get_parent().get_parent().visible = false

	# Ruy băng tiêu đề Concept A
	var head := Control.new()
	head.custom_minimum_size = Vector2(0, 115)
	b.add_child(head)
	if ResourceLoader.exists("res://assets/ui/ribbon.svg"):
		var rib := TextureRect.new()
		rib.texture = Sprites.ui("ribbon")
		rib.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rib.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		rib.set_anchors_preset(Control.PRESET_FULL_RECT)
		rib.mouse_filter = Control.MOUSE_FILTER_IGNORE
		head.add_child(rib)
	var title := UIKit.label("LÊN CẤP QUÁN!", "TitleLabel", 38)
	title.set_anchors_preset(Control.PRESET_FULL_RECT)
	title.offset_top = -12
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(title)

	# Khung ngôi sao toả sáng
	var star_box := Control.new()
	star_box.custom_minimum_size = Vector2(0, 175)
	b.add_child(star_box)
	var ray_holder := Control.new()
	ray_holder.set_anchors_preset(Control.PRESET_CENTER)
	ray_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	star_box.add_child(ray_holder)
	ray_holder.add_child(SunRays.new())
	var star := UIKit.icon("star", 170)
	star.set_anchors_preset(Control.PRESET_CENTER)
	star.offset_left = -85
	star.offset_top = -85
	star.offset_right = 85
	star.offset_bottom = 85
	star_box.add_child(star)
	var num := UIKit.label(str(new_level), "TitleLabel", 64)
	num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	num.set_anchors_preset(Control.PRESET_FULL_RECT)
	num.offset_top = 10
	star_box.add_child(num)
	star.pivot_offset = Vector2(85, 85)
	var spin := create_tween().set_loops()
	spin.tween_property(star, "scale", Vector2(1.08, 1.08), 0.5).set_trans(Tween.TRANS_SINE)
	spin.tween_property(star, "scale", Vector2(0.96, 0.96), 0.5).set_trans(Tween.TRANS_SINE)
	star.modulate.a = 0.0
	num.modulate.a = 0.0
	var pop := create_tween().set_parallel(true)
	pop.tween_property(star, "modulate:a", 1.0, 0.12)
	pop.tween_property(num, "modulate:a", 1.0, 0.1).set_delay(0.12)

	# Lời chúc
	var sub := UIKit.label("Chúc mừng! Quán Trọ đã đạt cấp %d!" % new_level, "HeaderLabel", 26)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.add_child(sub)

	# Danh sách mở khóa dạng thẻ kem ấm cúng
	for u: Dictionary in unlocks:
		var card := PanelContainer.new()
		var csb := StyleBoxFlat.new()
		csb.bg_color = Color("fff9ef")
		csb.set_corner_radius_all(18)
		csb.set_border_width_all(2)
		csb.border_color = Color("f5cca0")
		csb.shadow_color = Color(0.2, 0.1, 0.05, 0.15)
		csb.shadow_size = 6
		csb.shadow_offset = Vector2(0, 3)
		csb.set_content_margin_all(10)
		card.add_theme_stylebox_override("panel", csb)
		var row := UIKit.hbox(14)
		card.add_child(row)
		var uic := UIKit.icon(str(u["icon"]), 52)
		uic.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(uic)
		var l := UIKit.label(str(u["text"]), "", 23)
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		b.add_child(card)

	# Gợi ý cấp tiếp theo
	var nxt := _next_unlock()
	if not nxt.is_empty():
		var nl := UIKit.label("Cấp %d sẽ mở: %s" % [new_level + 1, nxt], "SmallLabel", 21)
		nl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		nl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.add_child(nl)

	# Thẻ nhận kim cương
	var reward_card := PanelContainer.new()
	var rsb := StyleBoxFlat.new()
	rsb.bg_color = Color("fef4e2")
	rsb.set_corner_radius_all(22)
	rsb.set_border_width_all(2)
	rsb.border_color = Color("ffd166")
	rsb.set_content_margin_all(8)
	reward_card.add_theme_stylebox_override("panel", rsb)
	reward_card.custom_minimum_size = Vector2(280, 0)
	reward_card.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var reward := UIKit.hbox(10)
	reward.alignment = BoxContainer.ALIGNMENT_CENTER
	reward.add_child(UIKit.icon("diamond", 38))
	reward.add_child(UIKit.label("+%d kim cương" % int(GameState.bal("level_up_diamonds", 2)), "TitleLabel", 24))
	reward_card.add_child(reward)
	b.add_child(reward_card)

	# Nút hành động
	var ok := UIKit.button("TUYỆT VỜI!", "RedButton", "", 320)
	ok.custom_minimum_size = Vector2(320, 80)
	ok.add_theme_font_size_override("font_size", 30)
	ok.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	ok.pressed.connect(close)
	b.add_child(ok)

	AudioManager.play("levelup")
	AudioManager.vibrate(60)
	for i in 3:
		var fw := _make_firework()
		add_child(fw)
		_fireworks.append(fw)
	_launch()


func _next_unlock() -> String:
	var g := GameState
	var lv := new_level + 1
	var out: Array[String] = []
	for d: Dictionary in g.dishes:
		if int(d["unlock_level"]) == lv:
			out.append("món " + str(d["name"]))
	for a: Dictionary in g.areas_data:
		if int(a["unlock_level"]) == lv:
			out.append("khu " + str(a["name"]))
		for w: Dictionary in a.get("wings", []):
			if int(w["unlock_level"]) == lv:
				out.append("phòng " + str(w["name"]))
	for id: String in g.staff_data:
		if int(g.staff_data[id]["unlock_level"]) == lv:
			out.append(str(g.staff_data[id]["name"]).to_lower())
	return ", ".join(out)


func _make_firework() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.texture = Sprites.ui("sparkle")
	p.amount = 46
	p.lifetime = 1.3
	p.one_shot = true
	p.explosiveness = 0.95
	p.emitting = false
	p.spread = 180.0
	p.gravity = Vector2(0, 260)
	p.initial_velocity_min = 180.0
	p.initial_velocity_max = 380.0
	p.scale_amount_min = 0.12
	p.scale_amount_max = 0.3
	p.angular_velocity_min = -200.0
	p.angular_velocity_max = 200.0
	var grad := Gradient.new()
	grad.set_color(0, Color.WHITE)
	grad.set_color(1, Color(1, 1, 1, 0))
	p.color_ramp = grad
	return p


func _launch() -> void:
	var vs: Vector2 = get_viewport_rect().size
	var colors := [Color("ffd166"), Color("ff8f7a"), Color("8fd9a8"), Color("8ecbf0"), Color("f4a6c8")]
	for fw in _fireworks:
		fw.position = Vector2(randf_range(0.15, 0.85) * vs.x, randf_range(0.12, 0.4) * vs.y)
		fw.color = colors[randi() % colors.size()]
		fw.restart()
		fw.emitting = true


func _process(delta: float) -> void:
	_fw_t += delta
	if _fw_t > 0.9:
		_fw_t = 0.0
		_launch()
