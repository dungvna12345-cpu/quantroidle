extends PopupBase
## Bộ sưu tập đầu bếp nổi tiếng: 12 thẻ (Thường / Hiếm / Huyền thoại).
## Rút thẻ bằng kim cương, trùng thẻ thì thẻ lên cấp và chỉ số tăng.

const RewardScene := preload("res://scenes/ui/RewardPopup.tscn")

var _tiles: Dictionary = {}
var _count: Label
var _btn1: JuicyButton
var _btn10: JuicyButton


func _init() -> void:
	title_text = "Bộ sưu tập"
	panel_width = 670.0


func _build(b: VBoxContainer) -> void:
	_count = centered_label("", "HeaderLabel", 26)
	b.add_child(_count)

	var btn_gb := UIKit.button("XEM SỔ TAY THỰC KHÁCH", "RedButton", "", 360)
	btn_gb.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	btn_gb.pressed.connect(func():
		close()
		if UIKit.main:
			UIKit.main.call("open_guestbook")
	)
	b.add_child(btn_gb)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(0, 700)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	b.add_child(sc)
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 10)
	grid.add_theme_constant_override("v_separation", 10)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(grid)
	for c: Dictionary in Progress.card_list():
		var tile := PanelContainer.new()
		tile.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var v := UIKit.vbox(0)
		tile.add_child(v)
		var pic := TextureRect.new()
		pic.texture = Sprites.tex(str(c["sprite"]))
		pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pic.custom_minimum_size = Vector2(0, 110)
		v.add_child(pic)
		var name_l := UIKit.label(str(c["name"]), "", 19)
		name_l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(name_l)
		var lvl := UIKit.label("", "SmallLabel", 16)
		lvl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(lvl)
		var bon := UIKit.label("", "GreenLabel", 16)
		bon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		bon.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(bon)
		grid.add_child(tile)
		_tiles[c["id"]] = {"tile": tile, "pic": pic, "lvl": lvl, "bon": bon}
	var row := UIKit.hbox(12)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(row)
	_btn1 = UIKit.button("Rút 1  %d" % int(Progress.cards_data["pull_cost"]), "BlueButton", "diamond", 250)
	_btn1.pressed.connect(_pull.bind(1))
	row.add_child(_btn1)
	_btn10 = UIKit.button("Rút 10  %d" % int(Progress.cards_data["pull10_cost"]), "GreenButton", "diamond", 260)
	_btn10.pressed.connect(_pull.bind(10))
	row.add_child(_btn10)
	b.add_child(centered_label("Tỉ lệ: Thường 70% • Hiếm 25% • Huyền thoại 5%", "SmallLabel", 18))
	Progress.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	_count.text = "Đã có %d/%d đầu bếp" % [Progress.cards_owned(), Progress.card_list().size()]
	var names: Dictionary = Progress.cards_data["bonus_names"]
	var rnames: Dictionary = Progress.cards_data["rarity_names"]
	for c: Dictionary in Progress.card_list():
		var id: String = c["id"]
		var t: Dictionary = _tiles[id]
		var owned := Progress.card_copies(id) > 0
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color("fff6e6") if owned else Color("e8dccb")
		sb.set_corner_radius_all(18)
		sb.set_border_width_all(5)
		sb.border_color = Color(str(Progress.cards_data["rarity_colors"][c["rarity"]]))
		sb.set_content_margin_all(8)
		(t["tile"] as PanelContainer).add_theme_stylebox_override("panel", sb)
		(t["pic"] as TextureRect).modulate = Color.WHITE if owned else Color(0.1, 0.08, 0.06, 0.7)
		var lv := Progress.card_level(id)
		var nxt := Progress.card_next_copies(id)
		(t["lvl"] as Label).text = "%s • Cấp %d" % [str(rnames[c["rarity"]]), lv] + ("" if nxt < 0 or not owned else " (%d/%d)" % [Progress.card_copies(id), nxt])
		var per: float = float(c["value"])
		var txt: String
		if str(c["bonus"]) == "golden":
			txt = "+x%d %s" % [int(per * maxi(1, lv)), str(names[c["bonus"]])]
		else:
			txt = "+%d%% %s" % [int(round(per * maxi(1, lv) * 100.0)), str(names[c["bonus"]])]
		(t["bon"] as Label).text = txt if owned else "Chưa có"
	_btn1.disabled = GameState.diamonds < int(Progress.cards_data["pull_cost"])
	_btn10.disabled = GameState.diamonds < int(Progress.cards_data["pull10_cost"])


func _pull(n: int) -> void:
	var got := Progress.pull_paid(n)
	if got.is_empty():
		return
	var rewards: Array = []
	for id: Variant in got:
		rewards.append(Progress._card_reward(str(id)))
	var p: PopupBase = RewardScene.instantiate()
	p.title_text = "Rút thẻ!"
	p.set("rewards", rewards)
	UIKit.main.call("open_popup", p)
	_refresh()
