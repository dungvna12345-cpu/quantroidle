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


const ActivityHubScript := preload("res://scripts/ui/ActivityHubPopup.gd")

func _build() -> void:
	# --- Biển hiệu tên khu ở giữa (kiểu biển gỗ truyền thống)
	var top := HBoxContainer.new()
	top.set_anchors_preset(Control.PRESET_CENTER_TOP)
	top.offset_left = -180
	top.offset_right = 180
	top.offset_top = 16
	top.offset_bottom = 76
	top.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_theme_constant_override("separation", 6)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(top)

	_left = _arrow("arrow_left", -1)
	top.add_child(_left)

	var pill := PanelContainer.new()
	pill.theme_type_variation = "AreaPill"
	pill.custom_minimum_size = Vector2(230, 58)
	top.add_child(pill)

	var pv := UIKit.vbox(-6)
	pv.alignment = BoxContainer.ALIGNMENT_CENTER
	pv.set_anchors_preset(Control.PRESET_FULL_RECT)
	pill.add_child(pv)

	_name_label = UIKit.label("", "ResourceLabel", 22)
	_name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(_name_label)

	_rate_label = UIKit.label("", "SmallLabel", 14)
	_rate_label.add_theme_color_override("font_color", Color("fde68a"))
	_rate_label.add_theme_color_override("font_outline_color", Color("1d0d06"))
	_rate_label.add_theme_constant_override("outline_size", 3)
	_rate_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(_rate_label)

	var pill_btn := UIKit.button("", "IconButton", "")
	pill_btn.set_anchors_preset(Control.PRESET_FULL_RECT)
	pill_btn.pressed.connect(_open_goals)
	pill.add_child(pill_btn)

	_right = _arrow("arrow_right", 1)
	top.add_child(_right)

	# --- Sao mục tiêu chương (gắn gọn gàng ngay dưới biển hiệu)
	var goal_btn := UIKit.button("", "IconButton", "")
	goal_btn.set_anchors_preset(Control.PRESET_CENTER_TOP)
	goal_btn.offset_left = -60
	goal_btn.offset_right = 60
	goal_btn.offset_top = 68
	goal_btn.offset_bottom = 96
	goal_btn.pressed.connect(_open_goals)
	add_child(goal_btn)
	var stars := UIKit.hbox(4)
	stars.set_anchors_preset(Control.PRESET_FULL_RECT)
	stars.alignment = BoxContainer.ALIGNMENT_CENTER
	stars.mouse_filter = Control.MOUSE_FILTER_IGNORE
	goal_btn.add_child(stars)
	for i in 3:
		var s := UIKit.icon("star_empty", 24)
		stars.add_child(s)
		_goal_stars.append(s)

	# --- Cột trái: NÚT PHÚC LỢI & HOẠT ĐỘNG (Gộp 8 minigame, vòng quay, rút quẻ)
	var act_btn := JuicyButton.new()
	act_btn.theme_type_variation = "SideCard"
	act_btn.position = Vector2(14, 8)
	act_btn.size = Vector2(82, 82)
	act_btn.custom_minimum_size = Vector2(82, 82)
	act_btn.pressed.connect(_open_activity_hub)
	add_child(act_btn)
	var avb := UIKit.vbox(2)
	avb.set_anchors_preset(Control.PRESET_FULL_RECT)
	avb.alignment = BoxContainer.ALIGNMENT_CENTER
	avb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	act_btn.add_child(avb)
	var aic := TextureRect.new()
	aic.texture = Sprites.ui("gift")
	aic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	aic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	aic.custom_minimum_size = Vector2(40, 40)
	avb.add_child(aic)
	var alb := UIKit.label("PHÚC LỢI", "SideLabel", 12)
	alb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	avb.add_child(alb)
	_gift_badge = _badge(act_btn, Vector2(56, -4))

	# Ánh xạ toàn bộ nút cũ vào nút Phúc Lợi để đảm bảo tương thích hướng dẫn & dev tools
	for k in ["cards", "cooking", "fortune", "wheel_hud", "chest_hud", "pet_hud", "critic_hud", "storm_hud", "events", "wheel"]:
		_named[k] = act_btn

	# Thẻ món đặc biệt thu nhỏ bên dưới nút Phúc Lợi
	var dish_card := UIKit.panel("CounterBar")
	dish_card.position = Vector2(14, 96)
	dish_card.size = Vector2(144, 46)
	dish_card.custom_minimum_size = Vector2(144, 46)
	add_child(dish_card)
	var dch := UIKit.hbox(6)
	dch.set_anchors_preset(Control.PRESET_FULL_RECT)
	dch.alignment = BoxContainer.ALIGNMENT_CENTER
	dish_card.add_child(dch)
	dch.add_child(UIKit.icon("icon_plate", 26))
	var dcv := UIKit.vbox(-6)
	dcv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dch.add_child(dcv)
	_dish_count = UIKit.label("0 MÓN", "ResourceLabel", 13)
	_dish_count.add_theme_color_override("font_color", Color("fef3c7"))
	dcv.add_child(_dish_count)
	_special_label = UIKit.label("", "SmallLabel", 11)
	_special_label.clip_text = true
	_special_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_special_label.add_theme_color_override("font_color", Color("fde68a"))
	dcv.add_child(_special_label)
	var dish_click := UIKit.button("", "IconButton", "")
	dish_click.set_anchors_preset(Control.PRESET_FULL_RECT)
	dish_click.pressed.connect(_go_tab.bind(1))
	dish_card.add_child(dish_click)
	_named["menu"] = dish_click

	# --- Cột phải: NÚT QUẢN LÝ (Mục tiêu chương, đơn tiệc, nghiên cứu)
	var manage_btn := JuicyButton.new()
	manage_btn.theme_type_variation = "SideCard"
	manage_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	manage_btn.offset_left = -94
	manage_btn.offset_right = -12
	manage_btn.offset_top = 8
	manage_btn.offset_bottom = 90
	manage_btn.custom_minimum_size = Vector2(82, 82)
	manage_btn.pressed.connect(_open_goals)
	add_child(manage_btn)
	var mvb := UIKit.vbox(2)
	mvb.set_anchors_preset(Control.PRESET_FULL_RECT)
	mvb.alignment = BoxContainer.ALIGNMENT_CENTER
	mvb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	manage_btn.add_child(mvb)
	var mic := TextureRect.new()
	mic.texture = Sprites.ui("icon_book")
	mic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	mic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	mic.custom_minimum_size = Vector2(38, 38)
	mvb.add_child(mic)
	var mlb := UIKit.label("QUẢN LÝ", "SideLabel", 12)
	mlb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mvb.add_child(mlb)
	_goal_badge = _badge(manage_btn, Vector2(56, -4))
	_named["goals"] = manage_btn
	_named["orders"] = manage_btn
	_named["research"] = manage_btn

	# Nút Cửa Hàng / Buff x2 nhỏ gọn bên dưới Quản Lý
	var shop_btn := JuicyButton.new()
	shop_btn.theme_type_variation = "SideCard"
	shop_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	shop_btn.offset_left = -94
	shop_btn.offset_right = -12
	shop_btn.offset_top = 96
	shop_btn.offset_bottom = 168
	shop_btn.custom_minimum_size = Vector2(82, 72)
	shop_btn.pressed.connect(_open_shop)
	add_child(shop_btn)
	var svb := UIKit.vbox(1)
	svb.set_anchors_preset(Control.PRESET_FULL_RECT)
	svb.alignment = BoxContainer.ALIGNMENT_CENTER
	svb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	shop_btn.add_child(svb)
	var sic := TextureRect.new()
	sic.texture = Sprites.ui("icon_shop_roof")
	sic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	sic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	sic.custom_minimum_size = Vector2(34, 34)
	svb.add_child(sic)
	var slb := UIKit.label("CỬA HÀNG", "SideLabel", 11)
	slb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	svb.add_child(slb)
	_boost_label = UIKit.label("", "SideLabel", 11)
	_boost_label.add_theme_color_override("font_color", Color("c0392b"))
	_boost_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	svb.add_child(_boost_label)
	_bolt_badge = _badge(shop_btn, Vector2(56, -4))
	_named["shop"] = shop_btn

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

	# --- Gợi ý việc nên làm tiếp theo (chỉ hiện khi có việc cần làm)
	_hint = UIKit.button("", "Highlight", "hand", 0)
	_hint.add_theme_font_size_override("font_size", 18)
	_hint.add_theme_constant_override("icon_max_width", 28)
	_hint.clip_text = true
	_hint.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_hint.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_hint.offset_left = -260
	_hint.offset_right = 160
	_hint.offset_top = -68
	_hint.offset_bottom = -14
	_hint.pressed.connect(_on_hint)
	_hint.visible = false
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
	var status_text := ""
	if not g.feature_status().is_empty():
		status_text = " • " + g.feature_status()
	elif g.is_evening():
		status_text = " • Tối (khách +25%)"
	_rate_label.text = "+%s/s • %s%s" % [NumberFormat.fmt_dec(rate), g.day_name(), status_text]
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
	_special_label.text = "%s x2" % str(sp.get("name", "Phở"))


## Gợi ý việc nên làm tiếp theo (ưu tiên phần thưởng, rồi mục tiêu chương, rồi nâng cấp rẻ nhất).
func _update_hint() -> void:
	var s := _suggest()
	var txt: String = str(s.get("text", ""))
	_hint.text = txt
	_hint_action = s.get("action", Callable())
	_hint.pulse = _hint_action.is_valid()
	_hint.visible = not txt.is_empty()


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


func _open_activity_hub() -> void:
	if UIKit.main:
		var p: PopupBase = ActivityHubScript.new()
		UIKit.main.call("open_popup", p)
