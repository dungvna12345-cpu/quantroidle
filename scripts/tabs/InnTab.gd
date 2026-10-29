extends TabBase
## Tab Quán (màn chính): lớp phủ trong suốt trên cảnh quán, bố cục kiểu game mobile.
## Trái: bộ đếm món + hộp quà. Phải: cột menu (khu, thuê nhân viên, cửa hàng/x2).
## Giữa trên: tên khu + mũi tên chuyển khu.

var _name_label: Label
var _sub_label: Label
var _left: JuicyButton
var _right: JuicyButton
var _dish_count: Label
var _dish_badge: Control
var _gift_badge: Control
var _house_badge: Control
var _staff_badge: Control
var _bolt_badge: Control
var _order_badge: Control
var _event_box: PanelContainer
var _event_title: Label
var _event_desc: Label
var _special_label: Label
var _wheel_badge: Control
var _research_badge: Control
var _goal_stars: Array[TextureRect] = []
var _goal_badge: Control
var _named: Dictionary = {}
var _ch_box: PanelContainer
var _ch_bar: ProgressBar
var _ch_text: Label
var _boost_label: Label
var _rate_label: Label
var _hint: JuicyButton
var _hint_action: Callable = Callable()


func _build() -> void:
	# --- tên khu ở giữa
	var top := HBoxContainer.new()
	top.set_anchors_preset(Control.PRESET_CENTER_TOP)
	top.offset_left = -200
	top.offset_right = 200
	top.offset_top = 0
	top.offset_bottom = 68
	top.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_theme_constant_override("separation", 6)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(top)
	_left = _arrow("arrow_left", -1)
	top.add_child(_left)
	var pill := UIKit.panel("AreaPill")
	pill.custom_minimum_size = Vector2(250, 0)
	top.add_child(pill)
	var pv := UIKit.vbox(-8)
	pill.add_child(pv)
	_name_label = UIKit.label("", "ResourceLabel", 24)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(_name_label)
	_sub_label = UIKit.label("", "SmallLabel", 16)
	_sub_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(_sub_label)
	_right = _arrow("arrow_right", 1)
	top.add_child(_right)

	_rate_label = UIKit.label("", "SideLabel", 17)
	_rate_label.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_rate_label.offset_left = -160
	_rate_label.offset_right = 160
	_rate_label.offset_top = 68
	_rate_label.offset_bottom = 96
	_rate_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_rate_label)

	# --- sao mục tiêu chương (bấm để xem)
	var goal_btn := UIKit.button("", "IconButton", "")
	goal_btn.set_anchors_preset(Control.PRESET_CENTER_TOP)
	goal_btn.offset_left = -84
	goal_btn.offset_right = 84
	goal_btn.offset_top = 96
	goal_btn.offset_bottom = 142
	goal_btn.pressed.connect(_open_goals)
	add_child(goal_btn)
	var stars := UIKit.hbox(2)
	stars.set_anchors_preset(Control.PRESET_FULL_RECT)
	stars.alignment = BoxContainer.ALIGNMENT_CENTER
	stars.mouse_filter = Control.MOUSE_FILTER_IGNORE
	goal_btn.add_child(stars)
	for i in 3:
		var s := UIKit.icon("star_empty", 40)
		stars.add_child(s)
		_goal_stars.append(s)

	# --- góc trái: thẻ món đặc biệt gọn gàng + nút Bộ sưu tập
	var dish_card := UIKit.panel("Card")
	dish_card.position = Vector2(12, 6)
	dish_card.size = Vector2(148, 56)
	dish_card.custom_minimum_size = Vector2(148, 56)
	add_child(dish_card)
	var dch := UIKit.hbox(6)
	dch.set_anchors_preset(Control.PRESET_FULL_RECT)
	dch.alignment = BoxContainer.ALIGNMENT_CENTER
	dish_card.add_child(dch)
	dch.add_child(UIKit.icon("icon_plate", 36))
	var dcv := UIKit.vbox(-6)
	dcv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dch.add_child(dcv)
	_dish_count = UIKit.label("0 MÓN", "SideLabel", 14)
	dcv.add_child(_dish_count)
	_special_label = UIKit.label("", "SmallLabel", 12)
	_special_label.clip_text = true
	_special_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	dcv.add_child(_special_label)
	var dish_click := UIKit.button("", "IconButton", "")
	dish_click.set_anchors_preset(Control.PRESET_FULL_RECT)
	dish_click.pressed.connect(_go_tab.bind(2))
	dish_card.add_child(dish_click)

	var cards := _icon_button("icon_cards", 52, Vector2(14, 70))
	cards.pressed.connect(_open_popup.bind("open_collection"))
	_named["cards"] = cards

	var cook_btn := _icon_button("icon_plate", 52, Vector2(14, 130))
	cook_btn.pressed.connect(_open_popup.bind("open_cooking"))
	_named["cooking"] = cook_btn

	var fortune_btn := _icon_button("gift", 52, Vector2(14, 190))
	fortune_btn.pressed.connect(_open_popup.bind("open_fortune"))
	_named["fortune"] = fortune_btn

	var wheel_btn := _icon_button("icon_wheel", 52, Vector2(14, 250))
	wheel_btn.pressed.connect(_open_popup.bind("open_wheel"))
	_named["wheel_hud"] = wheel_btn

	var chest_btn := _icon_button("chest_gold", 52, Vector2(14, 310))
	chest_btn.pressed.connect(_open_popup.bind("open_mystery_chest"))
	_named["chest_hud"] = chest_btn

	var pet_btn := _icon_button("icon_staff", 52, Vector2(14, 370))
	pet_btn.pressed.connect(_open_popup.bind("open_pet"))
	_named["pet_hud"] = pet_btn

	var critic_btn := _icon_button("icon_trophy", 52, Vector2(14, 430))
	critic_btn.pressed.connect(_open_popup.bind("open_food_critic"))
	_named["critic_hud"] = critic_btn

	var storm_btn := _icon_button("gift", 52, Vector2(14, 490))
	storm_btn.pressed.connect(_open_popup.bind("open_fortune_storm"))
	_named["storm_hud"] = storm_btn

	# --- cột 5 thẻ nổi bên phải theo Concept A
	var side_col := UIKit.vbox(8)
	side_col.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	side_col.offset_left = -106
	side_col.offset_right = -12
	side_col.offset_top = 10
	side_col.offset_bottom = 470
	add_child(side_col)

	# 1. QUẢN LÝ (mở mục tiêu, đơn tiệc, nghiên cứu)
	var btn_manage := _side_card(side_col, "gear", "QUẢN LÝ")
	btn_manage.pressed.connect(_open_goals)
	_goal_badge = _badge(btn_manage, Vector2(66, -4))
	_named["goals"] = btn_manage
	_named["orders"] = btn_manage
	_named["research"] = btn_manage

	# 2. THỰC ĐƠN (mở tab Thực đơn)
	var btn_menu := _side_card(side_col, "icon_book", "THỰC ĐƠN")
	btn_menu.pressed.connect(_go_tab.bind(2))
	_dish_badge = _badge(btn_menu, Vector2(66, -4))
	_named["menu"] = btn_menu

	# 3. NÂNG CẤP (mở tab Mở rộng / Nâng cấp quán)
	var btn_upgrade := _side_card(side_col, "icon_upgrade", "NÂNG CẤP")
	btn_upgrade.pressed.connect(_go_tab.bind(3))
	_house_badge = _badge(btn_upgrade, Vector2(66, -4))
	_named["upgrade"] = btn_upgrade

	# 4. SỰ KIỆN (mở sự kiện / vòng quay)
	var btn_event := _side_card(side_col, "gift", "SỰ KIỆN")
	btn_event.pressed.connect(_open_event_or_wheel)
	_gift_badge = _badge(btn_event, Vector2(66, -4))
	_named["events"] = btn_event
	_named["wheel"] = btn_event

	# 5. CỬA HÀNG (mở Shop & mua Buff x2)
	var btn_shop := _side_card(side_col, "icon_shop_roof", "CỬA HÀNG")
	btn_shop.pressed.connect(_open_shop)
	_bolt_badge = _badge(btn_shop, Vector2(66, -4))
	_named["shop"] = btn_shop
	_boost_label = UIKit.label("", "SideLabel", 12)
	_boost_label.add_theme_color_override("font_color", Color("e04f38"))
	_boost_label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_boost_label.offset_top = -18
	_boost_label.offset_bottom = 2
	_boost_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	btn_shop.add_child(_boost_label)

	# --- thông báo sự kiện
	_event_box = UIKit.panel("Highlight")
	_event_box.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_event_box.offset_left = -170
	_event_box.offset_right = 170
	_event_box.offset_top = 240
	_event_box.offset_bottom = 316
	_event_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_event_box.visible = false
	add_child(_event_box)
	var eh := UIKit.hbox(8)
	_event_box.add_child(eh)
	eh.add_child(UIKit.icon("icon_event", 54))
	var ev := UIKit.vbox(-6)
	ev.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	eh.add_child(ev)
	_event_title = UIKit.label("", "", 24)
	_event_title.add_theme_color_override("font_color", Color("c4483e"))
	ev.add_child(_event_title)
	_event_desc = UIKit.label("", "SmallLabel", 18)
	ev.add_child(_event_desc)
	GameState.event_started.connect(_on_event_started)

	# --- thử thách của Giám đốc Phát
	_ch_box = UIKit.panel("Card")
	_ch_box.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_ch_box.offset_left = -190
	_ch_box.offset_right = 190
	_ch_box.offset_top = 150
	_ch_box.offset_bottom = 236
	_ch_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ch_box.visible = false
	add_child(_ch_box)
	var chh := UIKit.hbox(8)
	_ch_box.add_child(chh)
	chh.add_child(UIKit.icon("portrait_phat", 56))
	var chv := UIKit.vbox(2)
	chv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chh.add_child(chv)
	_ch_text = UIKit.label("", "", 19)
	_ch_text.add_theme_color_override("font_color", Color("6b3fa0"))
	chv.add_child(_ch_text)
	_ch_bar = ProgressBar.new()
	_ch_bar.custom_minimum_size = Vector2(0, 20)
	_ch_bar.show_percentage = false
	chv.add_child(_ch_bar)

	# --- gợi ý dưới đáy
	# nút gợi ý việc nên làm tiếp theo
	_hint = UIKit.button("", "", "hand", 0)
	_hint.add_theme_font_size_override("font_size", 21)
	_hint.add_theme_constant_override("icon_max_width", 34)
	_hint.clip_text = true
	_hint.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hint.offset_left = -300
	_hint.offset_right = 300
	_hint.offset_top = -78
	_hint.offset_bottom = -12
	_hint.pressed.connect(_on_hint)
	add_child(_hint)


func _arrow(icon_id: String, dir: int) -> JuicyButton:
	var b := UIKit.button("", "IconButton", icon_id)
	b.custom_minimum_size = Vector2(60, 60)
	b.add_theme_constant_override("icon_max_width", 46)
	b.pressed.connect(_step.bind(dir))
	return b


func _icon_button(icon_id: String, px: float, pos: Vector2) -> JuicyButton:
	var b := UIKit.button("", "IconButton", icon_id)
	b.add_theme_constant_override("icon_max_width", int(px))
	b.position = pos
	b.size = Vector2(px, px)
	b.custom_minimum_size = Vector2(px, px)
	add_child(b)
	return b


func _side_card(parent: Control, icon_id: String, title: String) -> JuicyButton:
	var b := JuicyButton.new()
	b.theme_type_variation = "SideCard"
	b.custom_minimum_size = Vector2(94, 82)
	b.size = Vector2(94, 82)
	parent.add_child(b)
	var vb := UIKit.vbox(1)
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(vb)
	var ic := TextureRect.new()
	ic.name = "Icon"
	ic.texture = Sprites.ui(icon_id)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.custom_minimum_size = Vector2(40, 40)
	vb.add_child(ic)
	var lb := UIKit.label(title, "SideLabel", 13)
	lb.name = "Title"
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(lb)
	return b


func _can_upgrade_dishes() -> bool:
	for did in GameState.unlocked_dishes():
		if GameState.can_afford(GameState.dish_upgrade_cost(did)):
			return true
	return false


func _open_event_or_wheel() -> void:
	if Progress.free_spin():
		_open_popup("open_wheel")
	elif GameState.login_claimable() or GameState.quests_claimable_count() > 0:
		_go_tab(4)
	else:
		_open_popup("open_wheel")


## Chấm đỏ có dấu "!" báo có việc cần làm.
func _badge(parent: Control, pos: Vector2) -> Control:
	var p := UIKit.panel("Badge")
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	p.position = pos
	var l := UIKit.label("!", "WhiteLabel", 22)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	p.add_child(l)
	parent.add_child(p)
	return p


func _process(delta: float) -> void:
	super(delta)
	if not visible:
		return
	var g := GameState
	var active := g.boost_active()
	_boost_label.text = NumberFormat.fmt_clock(g.boost_left()) if active else ""
	var rate: float = g.measured_rate if g.measured_rate > 0.0 else g.estimate_rate()
	_rate_label.text = "+%s vàng/giây • %s%s" % [NumberFormat.fmt_dec(rate), g.day_name(),
		" (khách +25%)" if g.is_evening() else ""]
	var ch := Story.challenge
	_ch_box.visible = not ch.is_empty()
	if _ch_box.visible:
		var prog := Story.challenge_progress()
		var unit := "khách" if str(ch["type"]) == "serve" else "vàng"
		_ch_text.text = "Thử thách: %s/%s %s • %s" % [NumberFormat.fmt(prog), NumberFormat.fmt(float(ch["target"])), unit,
			NumberFormat.fmt_clock(float(ch["left"]))]
		_ch_bar.max_value = float(ch["target"])
		_ch_bar.value = minf(prog, float(ch["target"]))
	_event_box.visible = not g.current_event.is_empty()
	if _event_box.visible:
		_event_title.text = str(g.current_event["name"])
		_event_desc.text = "%s • còn %ds" % [str(g.current_event["desc"]), int(ceil(g.event_left))]


func _refresh() -> void:
	var g := GameState
	var info := g.area_info(g.current_area)
	_name_label.text = str(info["name"])
	var idx: int = g.area_index(g.current_area)
	_sub_label.text = "%s • Chương %d: %s" % [g.owner_name, g.chapter + 1, str(g.chapter_info()["city"])]
	_left.disabled = _neighbor(-1).is_empty()
	_right.disabled = _neighbor(1).is_empty()
	_left.visible = not _left.disabled
	_right.visible = not _right.disabled
	_dish_count.text = "%d MÓN ĂN" % g.unlocked_dishes().size()
	if _dish_badge:
		_dish_badge.visible = _can_upgrade_dishes()
	if _gift_badge:
		_gift_badge.visible = g.login_claimable() or g.quests_claimable_count() > 0 or Progress.free_spin()
	if _house_badge:
		_house_badge.visible = _can_open_area() or g.can_advance_chapter()
	if _bolt_badge:
		_bolt_badge.visible = not g.boost_active() and g.diamonds >= 20
	_update_hint()
	var can_learn := false
	for r: Dictionary in Progress.research_data:
		if Progress.can_research(str(r["id"])):
			can_learn = true
	var st := Progress.stars()
	for i in 3:
		_goal_stars[i].texture = Sprites.ui("star" if i < st else "star_empty")
	if _goal_badge:
		_goal_badge.visible = Progress.star_claimable() or g.can_advance_chapter() or g.orders_ready_count() > 0 or can_learn
	var sp: Dictionary = g.dish_info(g.daily_special())
	_special_label.text = "⭐ %s x2" % str(sp.get("name", "Phở"))


## Gợi ý việc nên làm tiếp theo (ưu tiên phần thưởng, rồi mục tiêu chương, rồi nâng cấp rẻ nhất).
func _update_hint() -> void:
	var s := _suggest()
	_hint.text = str(s["text"])
	_hint_action = s["action"]
	_hint.pulse = _hint_action.is_valid()


func _suggest() -> Dictionary:
	var g := GameState
	var m := UIKit.main
	if Progress.star_claimable():
		return {"text": "Mục tiêu đạt sao: nhận rương thưởng!", "action": Callable(m, "open_goals")}
	if g.can_advance_chapter():
		return {"text": "Đủ 3 sao! Lên đường tới quán mới", "action": Callable(m, "_select_tab").bind(3)}
	if g.orders_ready_count() > 0:
		return {"text": "Đơn tiệc đã đủ món: nhận thưởng lớn!", "action": Callable(m, "open_orders")}
	if Progress.free_spin():
		return {"text": "Lượt quay may mắn miễn phí hôm nay!", "action": Callable(m, "open_wheel")}
	if g.login_claimable():
		return {"text": "Nhận quà đăng nhập hôm nay", "action": Callable(m, "_select_tab").bind(4)}
	# theo mục tiêu chương chưa xong
	for goal: Dictionary in Progress.goals():
		if Progress.goal_done(goal):
			continue
		match str(goal["type"]):
			"dish":
				var did: String = str(goal["id"])
				if int(g.dish_levels.get(did, 0)) > 0 and g.can_afford(g.dish_upgrade_cost(did)):
					return {"text": "Nâng %s (mục tiêu chương)" % str(g.dish_info(did)["name"]), "action": Callable(m, "_select_tab").bind(2)}
			"tables":
				for a: Dictionary in g.areas_data:
					var aid: String = a["id"]
					if not g.area_unlocked(aid) or a["kind"] != "dining":
						continue
					var tl: Array = g.areas[aid]["tables"]
					for i in tl.size():
						if int(tl[i]) == 0 and g.table_slot_open(aid, i) and g.can_afford(g.table_unlock_cost(aid)):
							return {"text": "Mở thêm bàn (mục tiêu chương)", "action": Callable(m, "_on_object_tapped").bind(aid, "table", i)}
			"staff":
				var sid: String = str(goal["id"])
				if g.staff_unlocked(sid) and g.can_afford(g.hire_cost(sid)):
					return {"text": "Thuê thêm %s (mục tiêu chương)" % str(g.staff_data[sid]["name"]).to_lower(), "action": Callable(m, "_select_tab").bind(1)}
			"area":
				if g.can_afford(g.area_unlock_cost(str(goal["id"]))) and g.level >= int(g.area_info(str(goal["id"]))["unlock_level"]):
					return {"text": "Mở khu %s (mục tiêu chương)" % str(g.area_info(str(goal["id"]))["name"]), "action": Callable(m, "_select_tab").bind(3)}
	for w: Dictionary in g.wings(g.current_area):
		if g.can_unlock_wing(g.current_area, str(w["id"])):
			var wi: int = g.wings(g.current_area).find(w)
			return {"text": "Mở rộng quán: %s" % str(w["name"]), "action": Callable(m, "_on_object_tapped").bind(g.current_area, "wing", wi)}
	if not g.manager and g.staff_unlocked("manager") and g.can_afford(g.manager_cost()):
		return {"text": "Thuê Quản lý để quán tự chạy khi offline", "action": Callable(m, "_select_tab").bind(1)}
	var best := ""
	var best_cost: float = INF
	for did in g.unlocked_dishes():
		var c := g.dish_upgrade_cost(did)
		if c < best_cost:
			best_cost = c
			best = did
	if not best.is_empty() and g.can_afford(best_cost):
		return {"text": "Nâng món %s để bán giá cao hơn" % str(g.dish_info(best)["name"]), "action": Callable(m, "_select_tab").bind(2)}
	return {"text": "Chạm liên tục vào khách để tạo combo!", "action": Callable()}


func _on_hint() -> void:
	if _hint_action.is_valid():
		_hint_action.call()


func _can_open_area() -> bool:
	for w: Dictionary in GameState.wings(GameState.current_area):
		if GameState.can_unlock_wing(GameState.current_area, str(w["id"])):
			return true
	for a: Dictionary in GameState.areas_data:
		var id: String = a["id"]
		if not GameState.area_unlocked(id) and GameState.level >= int(a["unlock_level"]) \
				and GameState.can_afford(GameState.area_unlock_cost(id)):
			return true
	return false


func _can_hire() -> bool:
	for id in ["chef", "waiter", "cashier", "receptionist"]:
		if GameState.staff_unlocked(id) and GameState.staff_count(id) < int(GameState.staff_data[id]["max_count"]) \
				and GameState.can_afford(GameState.hire_cost(id)):
			return true
	return false


## Khu đã mở kế tiếp theo hướng dir.
func _neighbor(dir: int) -> String:
	var n: int = GameState.areas_data.size()
	var i: int = GameState.area_index(GameState.current_area)
	for k in range(1, n):
		var j: int = i + dir * k
		if j < 0 or j >= n:
			return ""
		var id: String = GameState.areas_data[j]["id"]
		if GameState.area_unlocked(id):
			return id
	return ""


func _step(dir: int) -> void:
	var id := _neighbor(dir)
	if not id.is_empty() and UIKit.main:
		UIKit.main.call("go_to_area", id)


## Vị trí các nút cho hướng dẫn chơi.
func button_center(id: String) -> Vector2:
	var b: Control = _named.get(id, null)
	if b == null or not b.is_visible_in_tree():
		return Vector2(-1, -1)
	var r := b.get_global_rect()
	return Vector2(r.get_center().x, r.end.y - 10)


func _go_tab(i: int) -> void:
	if UIKit.main:
		UIKit.main.call("_select_tab", i)


func _on_event_started(_ev: Dictionary) -> void:
	_event_box.pivot_offset = _event_box.size * 0.5
	Juice.bounce(_event_box, 2.0)


func _open_goals() -> void:
	if UIKit.main:
		UIKit.main.call("open_goals")


func _open_popup(fn: String) -> void:
	if UIKit.main:
		UIKit.main.call(fn)


func _open_orders() -> void:
	if UIKit.main:
		UIKit.main.call("open_orders")


func _open_shop() -> void:
	if UIKit.main:
		UIKit.main.call("open_shop")
