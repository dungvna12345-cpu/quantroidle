extends TabBase
## Tab Mở rộng: 4 khu (mở bằng vàng), trang trí cho khu đang xem, tái khởi nghiệp.

const ChapterThemeScript := preload("res://scripts/ui/ChapterTheme.gd")
const ChapterMapScript := preload("res://scripts/ui/ChapterMap.gd")
const ConfirmScene := preload("res://scenes/ui/ConfirmPopup.tscn")

var _area_cards: Array[UpgradeCard] = []
var _decor_title: Label
var _decor_info: Label
var _decor_cards: Dictionary = {}
var _prestige: UpgradeCard
var _wing_title: Label
var _wing_box: VBoxContainer
var _wing_cards: Array[UpgradeCard] = []
var _prestige_title: Label
var _map: Control
var _chapter_card: UpgradeCard
var _feature_icon: TextureRect
var _feature_title: Label
var _feature_desc: Label
var _sel_chapter: int = 0


func _build() -> void:
	var list := UIKit.tab_sheet(self, "MỞ RỘNG", "Mở khu mới, trang trí, và đưa quán sang thành phố mới")
	list.add_child(UIKit.section("Hành trình quán (chương)"))
	_sel_chapter = GameState.chapter
	_map = ChapterMapScript.new()
	_map.selected.connect(_on_map_selected)
	list.add_child(_map)
	_chapter_card = UpgradeCard.new()
	_chapter_card.setup(Sprites.ui(str(GameState.chapter_info()["thumb"])), "", 1)
	_chapter_card.icon_rect.custom_minimum_size = Vector2(110, 84)
	_chapter_card.action.connect(func(_b: int) -> void: _on_chapter(0, _sel_chapter, _chapter_card))
	list.add_child(_chapter_card)
	# đặc trưng (cơ chế riêng) của chương đang chọn
	var fp := UIKit.panel("Highlight")
	list.add_child(fp)
	var fh := UIKit.hbox(12)
	fp.add_child(fh)
	_feature_icon = UIKit.icon("coin", 72, false)
	fh.add_child(_feature_icon)
	var fv := UIKit.vbox(2)
	fv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fh.add_child(fv)
	_feature_title = UIKit.label("", "HeaderLabel", 24)
	fv.add_child(_feature_title)
	_feature_desc = UIKit.label("", "SmallLabel", 19)
	_feature_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fv.add_child(_feature_desc)
	list.add_child(UIKit.section("Các khu của quán"))
	for a: Dictionary in GameState.areas_data:
		var c := UpgradeCard.new()
		c.setup(Sprites.ui(str(a["thumb"])), str(a["name"]), 1)
		c.action.connect(_on_area.bind(str(a["id"]), c))
		list.add_child(c)
		_area_cards.append(c)
	_wing_title = UIKit.section("Mở rộng phòng")
	list.add_child(_wing_title)
	_wing_box = UIKit.vbox(10)
	list.add_child(_wing_box)
	_decor_title = UIKit.section("Trang trí")
	list.add_child(_decor_title)
	_decor_info = UIKit.label("", "GreenLabel")
	_decor_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	list.add_child(_decor_info)
	for k: String in GameState.decor_data:
		var d: Dictionary = GameState.decor_data[k]
		var c := UpgradeCard.new()
		c.setup(Sprites.tex(str(d["sprite"])), str(d["name"]), 1)
		c.action.connect(_on_decor.bind(k, c))
		list.add_child(c)
		_decor_cards[k] = c
	_prestige_title = UIKit.section("Mở chuỗi quán mới (chương cuối)")
	list.add_child(_prestige_title)
	_prestige = UpgradeCard.new()
	_prestige.setup(Sprites.ui("prestige"), "Bán quán, làm lại", 1)
	_prestige.action.connect(_on_prestige)
	list.add_child(_prestige)


func _refresh() -> void:
	var g := GameState
	_refresh_chapter()
	for i in _area_cards.size():
		var a: Dictionary = g.areas_data[i]
		var id: String = a["id"]
		var c := _area_cards[i]
		var extra := ""
		if a["kind"] == "dining":
			extra = "%d/%d bàn" % [g.tables_unlocked(id), (g.areas[id]["tables"] as Array).size()]
		else:
			extra = "%d/%d phòng" % [g.rooms_unlocked(id), (g.areas[id]["rooms"] as Array).size()]
		if g.area_unlocked(id):
			c.dim(false)
			c.set_info("", str(a["desc"]), "Đã mở • " + extra)
			if g.current_area == id:
				c.set_button(0, "Đang xem", false, "GreenButton", "check")
			else:
				c.set_button(0, "Đến xem", true, "BlueButton", "arrow_right")
		elif g.level < int(a["unlock_level"]):
			c.dim(true)
			c.set_info("", str(a["desc"]), "Cần cấp quán %d" % int(a["unlock_level"]))
			c.set_button(0, "Cấp %d" % int(a["unlock_level"]), false, "", "lock")
		else:
			c.dim(false)
			var cost: float = g.area_unlock_cost(id)
			c.set_info("", str(a["desc"]), "Chưa mở")
			c.set_button(0, "Mở  " + NumberFormat.fmt(cost), g.can_afford(cost), "GreenButton", "coin", true)
	# phòng mở rộng của khu đang xem
	var wl := g.wings(g.current_area)
	_wing_title.text = "Mở rộng phòng: " + str(g.area_info(g.current_area)["name"])
	_wing_title.visible = not wl.is_empty()
	_wing_box.visible = not wl.is_empty()
	while _wing_cards.size() < wl.size():
		var idx: int = _wing_cards.size()
		var wc := UpgradeCard.new()
		wc.setup(Sprites.tex("table_2"), "", 1)
		wc.action.connect(_on_wing.bind(idx, wc))
		_wing_box.add_child(wc)
		_wing_cards.append(wc)
	for i in _wing_cards.size():
		var wc := _wing_cards[i]
		wc.visible = i < wl.size()
		if not wc.visible:
			continue
		var w: Dictionary = wl[i]
		var wid: String = w["id"]
		wc.title_label.text = str(w["name"])
		if g.wing_unlocked(g.current_area, wid):
			wc.dim(false)
			wc.set_info("Đã mở", str(w["desc"]))
			wc.set_button(0, "Đã mở", false, "GreenButton", "check")
		elif g.wing_building(g.current_area, wid):
			wc.dim(false)
			wc.set_info("", str(w["desc"]), "Đang thi công • còn " + NumberFormat.fmt_time(g.wing_build_left(g.current_area, wid)))
			wc.set_button(0, "Đang xây", false, "", "clock")
		elif g.level < int(w["unlock_level"]):
			wc.dim(true)
			wc.set_info("", str(w["desc"]), "Cần cấp quán %d" % int(w["unlock_level"]))
			wc.set_button(0, "Cấp %d" % int(w["unlock_level"]), false, "", "lock")
		else:
			wc.dim(false)
			var wcost := g.wing_cost(g.current_area, wid)
			wc.set_info("", str(w["desc"]), "Chạm biển MỞ RỘNG trong quán hoặc mua tại đây")
			wc.set_button(0, "Mở  " + NumberFormat.fmt(wcost), g.can_afford(wcost), "GreenButton", "coin", true)
	# trang trí cho khu đang xem
	var cur: String = g.current_area
	var info: Dictionary = g.area_info(cur)
	_decor_title.text = "Trang trí: " + str(info["name"])
	_decor_info.text = "Sự hài lòng +%d%% → khách đến nhanh hơn (1 khách mỗi %s giây)" % [
		int(round(g.satisfaction(cur) * 100.0)), NumberFormat.fmt_dec(g.spawn_interval(cur))]
	for k: String in _decor_cards:
		var c: UpgradeCard = _decor_cards[k]
		var d: Dictionary = g.decor_data[k]
		var mx: int = g.decor_max(cur, k)
		var have: int = g.decor_count(cur, k)
		c.visible = mx > 0
		if mx <= 0:
			continue
		c.set_info("%d/%d" % [have, mx], "+%d%% hài lòng mỗi món" % int(round(float(d["bonus"]) * 100.0)))
		if have >= mx:
			c.set_button(0, "Đã đủ", false, "GreenButton", "check")
		else:
			var cost2: float = g.decor_cost(cur, k)
			c.set_button(0, "Mua  " + NumberFormat.fmt(cost2), g.can_afford(cost2), "", "coin", true)
	# tái khởi nghiệp: chỉ ở chương cuối (các chương trước dùng "Lên đường")
	_prestige.visible = g.is_last_chapter()
	_prestige_title.visible = g.is_last_chapter()
	var lvl_need: int = int(g.bal("prestige_level", 20))
	var bonus: int = int(round(g.bal("prestige_bonus", 0.1) * 100.0))
	if g.can_prestige():
		_prestige.dim(false)
		_prestige.set_info("Danh tiếng: %d" % g.reputation,
			"Nhận +%d Danh tiếng (mỗi điểm +%d%% thu nhập vĩnh viễn)" % [g.prestige_gain(), bonus],
			"Quán, món, nhân viên về ban đầu. Giữ kim cương và thành tích.")
		_prestige.set_button(0, "Bán quán", true, "RedButton", "prestige", true)
	else:
		_prestige.dim(true)
		_prestige.set_info("Danh tiếng: %d" % g.reputation,
			"Đạt cấp quán %d để bán quán nhận Danh tiếng" % lvl_need,
			"Mỗi điểm Danh tiếng +%d%% thu nhập vĩnh viễn" % bonus)
		_prestige.set_button(0, "Cấp %d" % lvl_need, false, "", "lock")


func _on_area(_idx: int, id: String, card: UpgradeCard) -> void:
	if GameState.area_unlocked(id):
		if UIKit.main:
			UIKit.main.call("go_to_area", id)
		return
	if GameState.unlock_area(id):
		Juice.shake(card, 6.0)
		_sparkle(card.buttons[0])
		AudioManager.play("levelup")
	_refresh()


func _on_wing(_idx: int, i: int, card: UpgradeCard) -> void:
	var wl := GameState.wings(GameState.current_area)
	if i < wl.size() and GameState.unlock_wing(GameState.current_area, str(wl[i]["id"])):
		Juice.shake(card, 6.0)
		_sparkle(card.buttons[0])
		if UIKit.main:
			UIKit.main.call("_select_tab", 0)
	_refresh()


func _on_decor(_idx: int, kind: String, card: UpgradeCard) -> void:
	if GameState.buy_decor(GameState.current_area, kind):
		Juice.shake(card, 6.0)
		_sparkle(card.buttons[0])
	_refresh()


func _on_map_selected(i: int) -> void:
	_sel_chapter = i
	_refresh_chapter()


## Thẻ chi tiết + đặc trưng của chương đang chọn trên bản đồ.
func _refresh_chapter() -> void:
	var g := GameState
	var i: int = _sel_chapter
	var ch: Dictionary = g.chapters_data[i]
	var cc := _chapter_card
	cc.icon_rect.texture = Sprites.ui(str(ch["thumb"]))
	cc.title_label.text = "%d. %s (%s)" % [i + 1, str(ch["name"]), str(ch["city"])]
	var spec: Dictionary = g.dish_info(str(ch.get("specialty", "")))
	var mult := "Thu nhập x%s • Đặc sản: %s" % [NumberFormat.fmt_dec(float(ch["income_mult"])), str(spec.get("name", "?"))]
	if i < g.chapter:
		cc.dim(true)
		cc.set_info("", str(ch["desc"]), "Đã hoàn thành • " + mult)
		cc.set_button(0, "Đã qua", false, "", "check")
	elif i == g.chapter:
		cc.dim(false)
		var need := "Chương cuối" if g.is_last_chapter() else "Mục tiêu %d/3 sao" % Progress.stars()
		cc.set_info("", str(ch["desc"]), mult + " • " + need)
		cc.set_button(0, "Hiện tại", false, "GreenButton", "check")
	elif i == g.chapter + 1:
		cc.dim(not g.can_advance_chapter())
		cc.set_info("", str(ch["desc"]), mult + " • Cần 3 sao mục tiêu chương")
		if g.can_advance_chapter():
			cc.set_button(0, "Lên đường", true, "RedButton", "arrow_right", true)
		else:
			cc.set_button(0, "%d/3 sao" % Progress.stars(), true, "", "star")
	else:
		cc.dim(true)
		cc.set_info("", str(ch["desc"]), mult + " • Hoàn thành chương trước")
		cc.set_button(0, "Khóa", false, "", "lock")
	var f: Dictionary = ch.get("feature", {})
	_feature_icon.texture = Sprites.tex(str(f.get("icon", "star")))
	_feature_title.text = "Đặc trưng: " + str(f.get("name", ""))
	_feature_desc.text = str(f.get("desc", ""))
	_feature_title.add_theme_color_override("font_color", ChapterThemeScript.color("accent", i))


func _on_chapter(_idx: int, i: int, _card: UpgradeCard) -> void:
	if i != GameState.chapter + 1:
		return
	if not GameState.can_advance_chapter():
		UIKit.main.call("open_goals")
		return
	var ch := GameState.chapter_info(i)
	var c: PopupBase = ConfirmScene.instantiate()
	c.title_text = "Sang chương mới"
	c.set("message", "Chuyển tới %s (%s)?
Thu nhập x%s. Quán mới bắt đầu lại từ đầu.
Giữ kim cương, Danh tiếng (+%d) và thành tích, nhận thêm 20 kim cương." % [
		str(ch["name"]), str(ch["city"]), NumberFormat.fmt_dec(float(ch["income_mult"])), GameState.prestige_gain()])
	c.set("yes_text", "Lên đường!")
	c.connect("answered", _on_chapter_answer)
	UIKit.main.call("open_popup", c)


func _on_chapter_answer(yes: bool) -> void:
	if yes:
		GameState.advance_chapter()


func _on_prestige(_idx: int) -> void:
	var c: PopupBase = ConfirmScene.instantiate()
	c.title_text = "Tái khởi nghiệp"
	c.set("message", "Bán quán để nhận +%d Danh tiếng?\nVàng, cấp quán, món ăn, nhân viên và các khu sẽ về ban đầu.\nKim cương, thành tích và Danh tiếng được giữ lại." % GameState.prestige_gain())
	c.set("yes_text", "Bán quán")
	c.set("yes_variation", "RedButton")
	c.connect("answered", _on_prestige_answer)
	UIKit.main.call("open_popup", c)


func _on_prestige_answer(yes: bool) -> void:
	if yes:
		GameState.do_prestige()
