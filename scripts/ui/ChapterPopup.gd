extends PopupBase
## Sang chương mới, hai màn:
##   1. Tổng kết chương vừa xong (khách, vàng, cấp, sao, Danh tiếng nhận được)
##   2. Giới thiệu chương mới (ảnh quán, thành phố, đặc sản, đặc trưng, đồ trang trí riêng, hệ số thu nhập)

var _t: float = 0.0
var _page: VBoxContainer


func _init() -> void:
	title_text = "CHƯƠNG MỚI!"
	closable = false
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	_page = UIKit.vbox(14)
	b.add_child(_page)
	var s := GameState.last_summary
	if not s.is_empty() and int(s.get("chapter", -1)) == GameState.chapter - 1:
		_build_summary(s)
	else:
		_build_intro()
	AudioManager.play("levelup")
	AudioManager.vibrate(80)


func _clear_page() -> void:
	for c in _page.get_children():
		c.queue_free()


func _go_intro() -> void:
	var t := create_tween()
	t.tween_property(_page, "modulate:a", 0.0, 0.18)
	t.tween_callback(func() -> void:
		_clear_page()
		_build_intro()
		AudioManager.play("whoosh")
	)
	t.tween_property(_page, "modulate:a", 1.0, 0.22)


# ---------------------------------------------------------------------
# Màn 1: tổng kết
# ---------------------------------------------------------------------

func _build_summary(s: Dictionary) -> void:
	var g := GameState
	var prev: int = int(s["chapter"])
	var pinfo := g.chapter_info(prev)
	title_label.text = "TỔNG KẾT CHƯƠNG"
	var pic := _picture(str(pinfo["thumb"]), 150)
	_page.add_child(pic)
	_page.add_child(centered_label("Chương %d: %s đã hoàn thành!" % [prev + 1, str(pinfo["name"])], "HeaderLabel", 30))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	_page.add_child(grid)
	var stats := [
		["icon_customers", NumberFormat.fmt(float(s.get("customers", 0))), "khách đã phục vụ"],
		["coin", NumberFormat.fmt(float(s.get("gold", 0))), "vàng kiếm được"],
		["exp", "Cấp %d" % int(s.get("level", 1)), "cấp quán đạt được"],
		["star", "%d/3 sao" % int(s.get("stars", 0)), "mục tiêu chương"],
	]
	for i in stats.size():
		var tile := _stat_tile(stats[i][0], stats[i][1], stats[i][2])
		grid.add_child(tile)
		tile.modulate.a = 0.0
		tile.scale = Vector2(0.8, 0.8)
		var tw := tile.create_tween().set_parallel(true)
		tw.tween_property(tile, "modulate:a", 1.0, 0.25).set_delay(0.15 + i * 0.12)
		tw.tween_property(tile, "scale", Vector2.ONE, 0.3).set_delay(0.15 + i * 0.12) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	var box := UIKit.panel("Highlight")
	_page.add_child(box)
	var rep: int = int(s.get("reputation", 0))
	box.add_child(centered_label("+%d Danh tiếng  •  +%d%% thu nhập vĩnh viễn" % [
		rep, int(round(rep * g.bal("prestige_bonus", 0.1) * 100.0))], "GreenLabel", 24))
	var next := UIKit.button("Lên đường tới %s" % str(g.chapter_info()["city"]), "GreenButton", "arrow_right", 380)
	next.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	next.pressed.connect(_go_intro)
	_page.add_child(next)


func _stat_tile(icon_id: String, value: String, caption: String) -> Control:
	var p := UIKit.panel("Card")
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.resized.connect(func() -> void: p.pivot_offset = p.size * 0.5)
	var h := UIKit.hbox(10)
	p.add_child(h)
	h.add_child(UIKit.icon(icon_id, 52))
	var v := UIKit.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	v.add_child(UIKit.label(value, "", 28))
	v.add_child(UIKit.label(caption, "SmallLabel", 17))
	return p


# ---------------------------------------------------------------------
# Màn 2: giới thiệu chương mới
# ---------------------------------------------------------------------

func _build_intro() -> void:
	var g := GameState
	var info := g.chapter_info()
	title_label.text = "CHƯƠNG MỚI!"
	var pic := _picture(str(info["thumb"]), 220)
	_page.add_child(pic)
	pic.scale = Vector2(0.6, 0.6)
	pic.modulate.a = 0.0
	var tw := pic.create_tween().set_parallel(true)
	tw.tween_property(pic, "scale", Vector2.ONE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(pic, "modulate:a", 1.0, 0.25)
	_page.add_child(centered_label("Chương %d: %s" % [g.chapter + 1, str(info["name"])], "HeaderLabel", 34))
	var desc := centered_label("%s — %s" % [str(info["city"]), str(info["desc"])], "", 22)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_page.add_child(desc)
	var box := UIKit.panel("Highlight")
	_page.add_child(box)
	var v := UIKit.vbox(2)
	box.add_child(v)
	v.add_child(centered_label("Thu nhập mọi món x%s" % NumberFormat.fmt_dec(float(info["income_mult"])), "GreenLabel", 28))
	v.add_child(centered_label("Danh tiếng: %d (+%d%% thu nhập) • +20 kim cương" % [
		g.reputation, int(g.reputation * g.bal("prestige_bonus", 0.1) * 100.0)], "SmallLabel", 20))
	# đặc sản
	var spec_id := g.specialty()
	_page.add_child(_info_row(Sprites.tex("dish_" + spec_id), "Đặc sản: " + str(g.dish_info(spec_id).get("name", "")),
		"Bán giá x%s cả chương" % NumberFormat.fmt_dec(float(info.get("specialty_mult", 1.5)))))
	# đặc trưng
	var f := g.chapter_feature()
	if not f.is_empty():
		_page.add_child(_info_row(Sprites.tex(str(f.get("icon", "star"))), "Đặc trưng: " + str(f.get("name", "")),
			str(f.get("desc", ""))))
	# đồ trang trí riêng
	var props: Array = info.get("props", [])
	if not props.is_empty():
		var row := UIKit.hbox(10)
		row.alignment = BoxContainer.ALIGNMENT_CENTER
		_page.add_child(row)
		row.add_child(UIKit.label("Trang trí riêng:", "SmallLabel", 19))
		var seen: Array = []
		for item: Array in props:
			if seen.has(item[0]):
				continue
			seen.append(item[0])
			row.add_child(UIKit.icon(str(item[0]), 54, false))
	var ok := UIKit.button("Khai trương!", "GreenButton", "", 320)
	ok.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	ok.pressed.connect(close)
	_page.add_child(ok)


func _info_row(tex: Texture2D, title: String, text: String) -> Control:
	var p := UIKit.panel("Card")
	var h := UIKit.hbox(12)
	p.add_child(h)
	var ic := TextureRect.new()
	ic.texture = tex
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.custom_minimum_size = Vector2(64, 64)
	h.add_child(ic)
	var v := UIKit.vbox(0)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var t := UIKit.label(title, "HeaderLabel", 22)
	v.add_child(t)
	var d := UIKit.label(text, "SmallLabel", 18)
	d.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(d)
	return p


func _picture(thumb: String, h: float) -> TextureRect:
	var pic := TextureRect.new()
	pic.texture = Sprites.ui(thumb)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pic.custom_minimum_size = Vector2(0, h)
	pic.resized.connect(func() -> void: pic.pivot_offset = pic.size * 0.5)
	return pic


func _process(delta: float) -> void:
	_t += delta
	if _t > 0.35 and UIKit.main:
		_t = 0.0
		var vs := get_viewport_rect().size
		UIKit.main.call("sparkle_at", Vector2(randf_range(0.15, 0.85) * vs.x, randf_range(0.15, 0.45) * vs.y))
