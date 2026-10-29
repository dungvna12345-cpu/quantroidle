extends PopupBase
## Popup nâng cấp riêng của một vật trong quán (bàn, bếp, quầy thu ngân, phòng trọ).
## Hiện cấp, chỉ số hiện tại -> sau khi nâng, giá, nút Nâng cấp và Nâng x10.

var area_id: String = "hall"
var kind: String = "table"
var index: int = 0

var _icon: TextureRect
var _level: Label
var _stat_now: Label
var _stat_next: Label
var _note: Label
var _btn1: JuicyButton
var _btn10: JuicyButton


func _build(b: VBoxContainer) -> void:
	title_text = _title()
	title_label.text = title_text
	var top := UIKit.hbox(18)
	b.add_child(top)
	var icon_bg := UIKit.panel("Highlight")
	top.add_child(icon_bg)
	_icon = TextureRect.new()
	_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_icon.custom_minimum_size = Vector2(150, 150)
	_icon.texture = Sprites.tex(_icon_id())
	icon_bg.add_child(_icon)
	var info := UIKit.vbox(6)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	top.add_child(info)
	_level = UIKit.label("", "HeaderLabel")
	info.add_child(_level)
	var stat_row := UIKit.hbox(8)
	info.add_child(stat_row)
	_stat_now = UIKit.label("", "", 26)
	stat_row.add_child(_stat_now)
	var arrow := UIKit.label("→", "", 26)
	stat_row.add_child(arrow)
	_stat_next = UIKit.label("", "GreenLabel", 28)
	stat_row.add_child(_stat_next)
	_note = UIKit.label("", "SmallLabel")
	_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_note.custom_minimum_size = Vector2(380, 0)
	info.add_child(_note)
	var row := UIKit.hbox(14)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(row)
	_btn1 = UIKit.button("", "", "coin", 250)
	_btn1.pressed.connect(_buy.bind(1))
	row.add_child(_btn1)
	_btn10 = UIKit.button("", "GreenButton", "coin", 250)
	_btn10.pressed.connect(_buy.bind(10))
	row.add_child(_btn10)
	GameState.gold_changed.connect(_on_gold)
	_refresh()
	GameState.fire_tutorial("popup_object")


func _title() -> String:
	match kind:
		"table":
			return "Bàn số %d" % (index + 1)
		"kitchen":
			return "Bếp nấu"
		"cashier":
			return "Quầy thu ngân"
		"room":
			return "Phòng %d" % (index + 1)
		"reception":
			return "Quầy lễ tân"
		"wing":
			return str(_wing().get("name", "Mở rộng"))
	return ""


func _wing() -> Dictionary:
	var wl: Array = GameState.wings(area_id)
	return wl[index] if index < wl.size() else {}


func _icon_id() -> String:
	match kind:
		"table":
			var on: bool = GameState.table_level(area_id, index) > 0
			return "table_%d" % (GameState.table_tier(area_id, index) if on else 1)
		"kitchen":
			return "stove"
		"cashier", "reception":
			return "cashier_counter"
		"room":
			return "bed"
		"wing":
			return "table_2"
	return "coin"


func _locked() -> bool:
	if kind == "table":
		return GameState.table_level(area_id, index) <= 0
	if kind == "room":
		return GameState.room_level(area_id, index) <= 0
	return false


func _on_gold(_v: float) -> void:
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	_icon.texture = Sprites.tex(_icon_id())
	var g := GameState
	if kind == "wing":
		var w := _wing()
		var lv: int = int(w.get("unlock_level", 1))
		_level.text = "Mở rộng quán"
		var n_tables: int = (w.get("tables", []) as Array).size() + (w.get("beds", []) as Array).size()
		_stat_now.text = "+%d %s" % [n_tables, "phòng" if w.has("beds") else "bàn"]
		_stat_next.text = "x%s tiền khách" % NumberFormat.fmt_dec(float(w.get("price_mult", 1.0)))
		_note.text = str(w.get("desc", ""))
		var cost := g.wing_cost(area_id, str(w["id"]))
		_btn10.visible = false
		if g.wing_building(area_id, str(w["id"])):
			_level.text = "Đang thi công"
			_note.text = "Còn %s. Chạm vào công trường trong quán để xây nhanh hơn." % NumberFormat.fmt_clock(g.wing_build_left(area_id, str(w["id"])))
			var dc := g.build_skip_cost(area_id, str(w["id"]))
			_btn1.text = "Xây ngay  %d" % dc
			_btn1.icon = Sprites.ui("diamond")
			_btn1.theme_type_variation = "BlueButton"
			_btn1.disabled = g.diamonds < dc
			_btn1.pulse = not _btn1.disabled
			_btn1.visible = true
			return
		if g.level < lv:
			_btn1.text = "Cần cấp quán %d" % lv
			_btn1.disabled = true
			_btn1.pulse = false
			_btn1.visible = true
		else:
			_set_btn(_btn1, "Mở rộng  " + NumberFormat.fmt(cost), cost)
		return
	if _locked():
		_level.text = "Chưa mở khóa"
		var cost: float = g.table_unlock_cost(area_id) if kind == "table" else g.room_unlock_cost(area_id)
		if kind == "table":
			_stat_now.text = "Thêm 1 bàn"
			_stat_next.text = "x%s thu nhập" % NumberFormat.fmt_dec(g.table_mult_at(1))
			_note.text = "Mở thêm bàn để phục vụ nhiều khách cùng lúc."
		else:
			_stat_now.text = "Phòng mới"
			_stat_next.text = "%s/lượt" % NumberFormat.fmt(g.room_rent_at(area_id, 1) * g.income_mult())
			_note.text = "Khách thuê phòng ngủ và trả tiền khi rời đi."
		_set_btn(_btn1, "Mở khóa  " + NumberFormat.fmt(cost), cost)
		_btn10.visible = false
		return
	_btn10.visible = true
	match kind:
		"table":
			var lv: int = g.table_level(area_id, index)
			_level.text = "Cấp %d" % lv
			_stat_now.text = "x%s" % NumberFormat.fmt_dec(g.table_mult_at(lv))
			_stat_next.text = "x%s" % NumberFormat.fmt_dec(g.table_mult_at(lv + 1))
			var fixed: int = int(g.area_info(area_id).get("table_tier", 0))
			if fixed > 0:
				_note.text = "Hệ số tiền khách trả tại bàn này. Bàn VIP sang trọng."
			else:
				_note.text = "Hệ số tiền khách trả tại bàn này.\nCấp %d: bàn gỗ tốt • Cấp %d: bàn VIP" % [
					int(g.bal("table_tier2_level", 10)), int(g.bal("table_tier3_level", 25))]
			_set_btn(_btn1, "Nâng cấp  " + NumberFormat.fmt(g.table_upgrade_cost(area_id, index, 1)),
				g.table_upgrade_cost(area_id, index, 1))
			_set_btn(_btn10, "Nâng x10  " + NumberFormat.fmt(g.table_upgrade_cost(area_id, index, 10)),
				g.table_upgrade_cost(area_id, index, 10))
		"kitchen":
			var lv2: int = int(g.areas[area_id]["kitchen"])
			_level.text = "Cấp %d" % lv2
			_stat_now.text = "x%s" % NumberFormat.fmt_dec(g.kitchen_speed_at(lv2))
			_stat_next.text = "x%s" % NumberFormat.fmt_dec(g.kitchen_speed_at(lv2 + 1))
			_note.text = "Tốc độ nấu của mọi bếp lò trong khu này."
			_set_btn(_btn1, "Nâng cấp  " + NumberFormat.fmt(g.kitchen_upgrade_cost(area_id, 1)), g.kitchen_upgrade_cost(area_id, 1))
			_set_btn(_btn10, "Nâng x10  " + NumberFormat.fmt(g.kitchen_upgrade_cost(area_id, 10)), g.kitchen_upgrade_cost(area_id, 10))
		"cashier":
			var lv3: int = int(g.areas[area_id]["cashier"])
			_level.text = "Cấp %d" % lv3
			_stat_now.text = "x%s" % NumberFormat.fmt_dec(g.cashier_speed_at(lv3))
			_stat_next.text = "x%s" % NumberFormat.fmt_dec(g.cashier_speed_at(lv3 + 1))
			_note.text = "Tốc độ tính tiền. Mỗi cấp tăng thêm %.1f%% cơ hội nhận tiền boa (hiện %d%%)." % [
				g.bal("cashier_tip_per_level", 0.005) * 100.0, int(round(g.tip_chance(area_id) * 100.0))]
			_set_btn(_btn1, "Nâng cấp  " + NumberFormat.fmt(g.cashier_upgrade_cost(area_id, 1)), g.cashier_upgrade_cost(area_id, 1))
			_set_btn(_btn10, "Nâng x10  " + NumberFormat.fmt(g.cashier_upgrade_cost(area_id, 10)), g.cashier_upgrade_cost(area_id, 10))
		"room":
			var lv4: int = g.room_level(area_id, index)
			_level.text = "Cấp %d" % lv4
			_stat_now.text = NumberFormat.fmt(g.room_rent_at(area_id, lv4))
			_stat_next.text = NumberFormat.fmt(g.room_rent_at(area_id, lv4 + 1))
			_note.text = "Tiền phòng mỗi lượt khách ngủ (%d giây)." % int(g.area_info(area_id)["room"]["sleep_time"])
			_set_btn(_btn1, "Nâng cấp  " + NumberFormat.fmt(g.room_upgrade_cost(area_id, index, 1)), g.room_upgrade_cost(area_id, index, 1))
			_set_btn(_btn10, "Nâng x10  " + NumberFormat.fmt(g.room_upgrade_cost(area_id, index, 10)), g.room_upgrade_cost(area_id, index, 10))
		"reception":
			_level.text = "%d/%d phòng" % [g.rooms_unlocked(area_id), (g.areas[area_id]["rooms"] as Array).size()]
			_stat_now.text = "Lễ tân"
			_stat_next.text = "luôn sẵn sàng"
			_note.text = "Chạm vào giường có ổ khóa để mở thêm phòng, chạm giường đã mở để nâng tiền phòng."
			_btn1.visible = false
			_btn10.visible = false


func _set_btn(b: JuicyButton, text: String, cost: float) -> void:
	b.text = text
	b.disabled = not GameState.can_afford(cost)
	b.pulse = not b.disabled
	b.visible = true


func _buy(n: int) -> void:
	var ok: bool = false
	var g := GameState
	if kind == "wing":
		var wid := str(_wing().get("id", ""))
		ok = g.skip_build(area_id, wid) if g.wing_building(area_id, wid) else g.unlock_wing(area_id, wid)
		if ok:
			close()
			return
	elif _locked():
		ok = g.unlock_table(area_id, index) if kind == "table" else g.unlock_room(area_id, index)
	else:
		match kind:
			"table":
				ok = g.upgrade_table(area_id, index, n)
			"kitchen":
				ok = g.upgrade_kitchen(area_id, n)
			"cashier":
				ok = g.upgrade_cashier(area_id, n)
			"room":
				ok = g.upgrade_room(area_id, index, n)
	if ok:
		Juice.shake(panel, 7.0)
		if UIKit.main:
			var btn: JuicyButton = _btn1 if n == 1 else _btn10
			UIKit.main.call("sparkle_at", btn.get_global_rect().get_center())
	_refresh()
