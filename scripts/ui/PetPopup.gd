class_name PetPopup
extends PopupBase
## Popup Quản Lý & Chăm Sóc Thú Cưng (Mèo Chiêu Tài / Cún Cảnh)
## Cho thú cưng ăn cá tươi, chơi đùa cuộn len, nâng cấp tình cảm và mở khóa đặc quyền!

var _cat_visual: Control
var _level_label: Label
var _exp_bar: ProgressBar
var _exp_label: Label
var _feed_btn: JuicyButton
var _play_btn: JuicyButton
var _perks_vbox: VBoxContainer
var _t: float = 0.0

const PERKS := [
	{"level": 1, "icon": "🐾", "title": "Bé Mèo Lanh Lợi", "desc": "Tự động nhặt tiền boa khách để lại trên bàn ăn."},
	{"level": 2, "icon": "✨", "title": "Hút Khách Đại Tài", "desc": "Tăng 20% cơ hội xuất hiện Khách Sộp & Đại Gia VIP."},
	{"level": 3, "icon": "🧹", "title": "Gom Tiền Thần Tốc", "desc": "Mỗi 15 giây tự động gom sạch toàn bộ tiền boa trên các bàn."},
	{"level": 4, "icon": "🚨", "title": "Vệ Sĩ Quán Trọ", "desc": "Phát hiện và dọa tên trộm vàng bỏ chạy tức thì!"},
	{"level": 5, "icon": "👑", "title": "Mèo Hoàng Kim", "desc": "Ban phước lành +15% toàn bộ doanh thu vĩnh viễn!"}
]

func _init() -> void:
	title_text = "Mèo Chiêu Tài Quán Trọ"
	panel_width = 660.0

func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Vuốt ve, chăm sóc để Mèo cưng mang lại tài lộc và may mắn!", "BodyLabel", 21)
	b.add_child(sub)

	# 1. Khu vực hiển thị Mèo cưng dễ thương
	var center_box := CenterContainer.new()
	center_box.custom_minimum_size = Vector2(0, 160)
	b.add_child(center_box)

	_cat_visual = Control.new()
	_cat_visual.custom_minimum_size = Vector2(180, 150)
	_cat_visual.draw.connect(_draw_cat_portrait)
	center_box.add_child(_cat_visual)

	# 2. Bảng Cấp độ & Thanh Cảm Tình (Affection XP)
	var stat_panel := PanelContainer.new()
	stat_panel.theme_type_variation = "Card"
	b.add_child(stat_panel)

	var stat_v := UIKit.vbox(8)
	stat_panel.add_child(stat_v)

	var top_row := UIKit.hbox(10)
	stat_v.add_child(top_row)

	_level_label = UIKit.label("CẤP ĐỘ 1: MÈO TẬP SỰ", "HeaderLabel", 22)
	_level_label.add_theme_color_override("font_color", Color("d98a12"))
	top_row.add_child(_level_label)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_row.add_child(spacer)

	_exp_label = UIKit.label("0 / 100 Điểm Thân Thiết", "SmallLabel", 18)
	top_row.add_child(_exp_label)

	_exp_bar = ProgressBar.new()
	_exp_bar.custom_minimum_size = Vector2(0, 24)
	_exp_bar.show_percentage = false
	stat_v.add_child(_exp_bar)

	# 3. Hai nút hành động: Cho ăn & Chơi đùa
	var act_row := UIKit.hbox(16)
	act_row.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(act_row)

	_feed_btn = UIKit.button("Cho Ăn Cá Tươi 🐟", "GreenButton", "", 270)
	_feed_btn.pressed.connect(_on_feed)
	act_row.add_child(_feed_btn)

	_play_btn = UIKit.button("Chơi Cuộn Len 🧶", "OrangeButton", "", 270)
	_play_btn.pressed.connect(_on_play)
	act_row.add_child(_play_btn)

	# 4. Danh sách Đặc Quyền Thần Tài
	var perk_title := centered_label("🌟 ĐẶC QUYỀN THẦN TÀI MỞ KHÓA", "SideLabel", 19)
	b.add_child(perk_title)

	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 200)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	b.add_child(scroll)

	_perks_vbox = UIKit.vbox(10)
	_perks_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_perks_vbox)

	_refresh_ui()

func _get_max_xp(lvl: int) -> float:
	return GameState.pet_xp_needed(lvl)

func _get_feed_cost() -> float:
	return maxf(500.0, GameState.income_rate() * 18.0)

func _refresh_ui() -> void:
	var lvl: int = GameState.pet_level
	var max_xp: float = _get_max_xp(lvl)
	var cur_xp: float = GameState.pet_xp
	
	var titles: Array[String] = ["", "MÈO TẬP SỰ", "MÈO MAY MẮN", "MÈO CHIÊU TÀI", "MÈO THẦN BẢO HỘ", "HOÀNG THƯỢNG KIM NGÂN"]
	var t_title: String = titles[mini(lvl, titles.size() - 1)] if lvl < titles.size() else "ĐẠI THẦN BẢO QUÁN"
	_level_label.text = "CẤP ĐỘ %d: %s" % [lvl, t_title]
	
	_exp_bar.max_value = max_xp
	_exp_bar.value = cur_xp
	_exp_label.text = "%d / %d Cảm Tình" % [int(cur_xp), int(max_xp)]
	
	var cost := _get_feed_cost()
	_feed_btn.text = "Cho Ăn Cá 🐟 (%s)" % NumberFormat.fmt(cost)
	_feed_btn.disabled = GameState.gold < cost
	
	# Cập nhật danh sách đặc quyền
	for c in _perks_vbox.get_children():
		c.queue_free()
		
	for p in PERKS:
		var p_lvl: int = int(p["level"])
		var unlocked := lvl >= p_lvl
		
		var row := PanelContainer.new()
		row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.theme_type_variation = "Card"
		if not unlocked:
			row.modulate = Color(0.7, 0.7, 0.7, 0.6)
		_perks_vbox.add_child(row)
		
		var rh := UIKit.hbox(12)
		row.add_child(rh)
		
		var icon_lbl := UIKit.label(str(p["icon"]), "", 32)
		rh.add_child(icon_lbl)
		
		var rv := UIKit.vbox(2)
		rv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rh.add_child(rv)
		
		var r_title := UIKit.label(str(p["title"]) + (" (Đã Mở)" if unlocked else " (Cần Cấp %d)" % p_lvl), "HeaderLabel", 18)
		if unlocked:
			r_title.add_theme_color_override("font_color", Color("16a34a"))
		rv.add_child(r_title)
		
		var r_desc := UIKit.label(str(p["desc"]), "SmallLabel", 16)
		rv.add_child(r_desc)

func _on_feed() -> void:
	var cost := _get_feed_cost()
	if not GameState.try_spend(cost):
		return

	AudioManager.play("purchase")
	AudioManager.play("coin", 0.1)

	if GameState.add_pet_xp(35.0):
		AudioManager.play("levelup")
		AudioManager.play("legendary", 0.2)
		GameState.toast.emit("🐾 Mèo Chiêu Tài đã lên CẤP %d! Mở khóa đặc quyền mới!" % GameState.pet_level)
		GameState.add_diamonds(10)
	else:
		GameState.toast.emit("🐾 Meo meo! Mèo cưng rất thích cá tươi (+35 Cảm tình)!")
		
	if UIKit.main:
		UIKit.main.call("burst_sparkles", panel.get_global_rect().get_center(), 14)
	_refresh_ui()

func _on_play() -> void:
	var cost := _get_feed_cost() * 0.5
	if not GameState.try_spend(cost):
		return

	AudioManager.play("pop")
	GameState.toast.emit("🧶 Mèo cưng vờn cuộn len! Toàn quán phấn khởi phục vụ nhanh x2 (30s)!")
	GameState.trigger_rush(10)

	if GameState.add_pet_xp(20.0):
		AudioManager.play("levelup")
		GameState.toast.emit("🐾 Mèo Chiêu Tài đã lên CẤP %d!" % GameState.pet_level)
		
	if UIKit.main:
		UIKit.main.call("burst_sparkles", panel.get_global_rect().get_center(), 10)
	_refresh_ui()

func _process(delta: float) -> void:
	_t += delta * 3.0
	if _cat_visual:
		_cat_visual.queue_redraw()

func _draw_cat_portrait() -> void:
	var c := _cat_visual.size * 0.5 + Vector2(0, 10.0 + sin(_t) * 3.5)
	var paw_swing := sin(_t * 1.8) * 8.0
	
	# Hào quang vàng may mắn
	var aura_col := Color(1.0, 0.88, 0.4, 0.35 + sin(_t * 2.0) * 0.1)
	_cat_visual.draw_circle(c, 56.0, aura_col)
	
	# Đuôi mèo ngoe nguẩy
	var tail_pts := PackedVector2Array([
		c + Vector2(-28, 12),
		c + Vector2(-42, -5 + sin(_t * 1.5) * 8.0),
		c + Vector2(-36, -26 + cos(_t * 1.5) * 10.0)
	])
	_cat_visual.draw_polyline(tail_pts, Color("e07a3f"), 7.0, true)
	_cat_visual.draw_circle(tail_pts[2], 5.0, Color("3d2c25"))
	
	# Chân mèo
	_cat_visual.draw_circle(c + Vector2(-16, 32), 9.0, Color("fdf6eb"))
	_cat_visual.draw_circle(c + Vector2(16, 32), 9.0, Color("fdf6eb"))
	
	# Thân mèo béo tròn
	_cat_visual.draw_colored_polygon(_ellipse(c + Vector2(0, 10), 32.0, 26.0), Color("fdf6eb"))
	_cat_visual.draw_colored_polygon(_ellipse(c + Vector2(14, 6), 14.0, 18.0), Color("e07a3f"))
	_cat_visual.draw_colored_polygon(_ellipse(c + Vector2(-16, 12), 12.0, 14.0), Color("3d2c25"))
	
	# Đầu mèo tròn xoe
	var head_c := c + Vector2(0, -18)
	_cat_visual.draw_colored_polygon(_ellipse(head_c, 26.0, 22.0), Color("fdf6eb"))
	_cat_visual.draw_colored_polygon(_ellipse(head_c + Vector2(10, -6), 12.0, 12.0), Color("e07a3f"))
	
	# Tai mèo
	var ear_l := PackedVector2Array([head_c + Vector2(-18, -12), head_c + Vector2(-22, -34), head_c + Vector2(-4, -20)])
	var ear_r := PackedVector2Array([head_c + Vector2(4, -20), head_c + Vector2(22, -34), head_c + Vector2(18, -12)])
	_cat_visual.draw_colored_polygon(ear_l, Color("3d2c25"))
	_cat_visual.draw_colored_polygon(ear_r, Color("e07a3f"))
	_cat_visual.draw_circle(head_c + Vector2(-14, -20), 5.0, Color("fca5a5"))
	_cat_visual.draw_circle(head_c + Vector2(14, -20), 5.0, Color("fca5a5"))
	
	# Vẫy tay Chiêu Tài (Waving Paw)
	var paw_c := head_c + Vector2(24, -10 + paw_swing)
	_cat_visual.draw_circle(paw_c, 8.0, Color("fdf6eb"))
	_cat_visual.draw_circle(paw_c, 4.5, Color("fca5a5"))
	
	# Mắt mèo cười híp mí hạnh phúc (^_^ hoặc long lanh)
	_cat_visual.draw_arc(head_c + Vector2(-8, -4), 6.0, PI * 1.1, PI * 1.9, 10, Color("221815"), 3.0)
	_cat_visual.draw_arc(head_c + Vector2(8, -4), 6.0, PI * 1.1, PI * 1.9, 10, Color("221815"), 3.0)
	
	# Mũi hồng + Miệng cười
	_cat_visual.draw_circle(head_c + Vector2(0, 3), 3.0, Color("f472b6"))
	_cat_visual.draw_arc(head_c + Vector2(-4, 7), 4.5, 0, PI, 8, Color("221815"), 2.0)
	_cat_visual.draw_arc(head_c + Vector2(4, 7), 4.5, 0, PI, 8, Color("221815"), 2.0)
	
	# Ria mép mèo
	_cat_visual.draw_line(head_c + Vector2(-12, 3), head_c + Vector2(-28, 1), Color("8c7569"), 2.0)
	_cat_visual.draw_line(head_c + Vector2(-12, 7), head_c + Vector2(-27, 9), Color("8c7569"), 2.0)
	_cat_visual.draw_line(head_c + Vector2(12, 3), head_c + Vector2(28, 1), Color("8c7569"), 2.0)
	_cat_visual.draw_line(head_c + Vector2(12, 7), head_c + Vector2(27, 9), Color("8c7569"), 2.0)
	
	# Vòng cổ đỏ & Chuông vàng
	_cat_visual.draw_line(head_c + Vector2(-12, 16), head_c + Vector2(12, 16), Color("e11d48"), 5.5)
	_cat_visual.draw_circle(head_c + Vector2(0, 20), 6.5, Color("facc15"))
	_cat_visual.draw_circle(head_c + Vector2(0, 20), 2.0, Color("78350f"))
	
	# Nón lá nếu cấp >= 2
	if GameState.pet_level >= 2:
		var hat_pts := PackedVector2Array([
			head_c + Vector2(-30, -22),
			head_c + Vector2(0, -48),
			head_c + Vector2(30, -22)
		])
		_cat_visual.draw_colored_polygon(hat_pts, Color("fef08a"))
		_cat_visual.draw_polyline(hat_pts, Color("ca8a04"), 3.0, true)

func _ellipse(pos: Vector2, rx: float, ry: float, n: int = 24) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var a: float = TAU * float(i) / float(n)
		pts.append(pos + Vector2(cos(a) * rx, sin(a) * ry))
	return pts

