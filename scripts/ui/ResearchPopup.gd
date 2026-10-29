extends PopupBase
## Cây nghiên cứu: dùng Sách nghiên cứu mở nâng cấp vĩnh viễn (giữ qua mọi chương).
## 3 tầng, tầng sau mở khi tổng cấp nghiên cứu đủ yêu cầu.

var _rp_label: Label
var _cards: Dictionary = {}


func _init() -> void:
	title_text = "Nghiên cứu"
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	var top := UIKit.hbox(8)
	top.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_child(UIKit.icon("icon_rp", 48))
	_rp_label = UIKit.label("", "HeaderLabel", 30)
	top.add_child(_rp_label)
	b.add_child(top)
	b.add_child(centered_label("Nhận Sách từ rương sao chương, vòng quay và rương vàng. Nâng cấp giữ mãi qua mọi chương.", "SmallLabel", 19))
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(0, 760)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	b.add_child(sc)
	var list := UIKit.vbox(10)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(list)
	var tier := 0
	for r: Dictionary in Progress.research_data:
		if int(r["tier"]) != tier:
			tier = int(r["tier"])
			var need: int = int(r.get("need", 0))
			list.add_child(UIKit.section("Tầng %d%s" % [tier, "" if need == 0 else " (cần tổng %d cấp nghiên cứu)" % need]))
		var c := UpgradeCard.new()
		c.setup(Sprites.ui(str(r["icon"])), str(r["name"]), 1)
		c.action.connect(_buy.bind(str(r["id"]), c))
		list.add_child(c)
		_cards[r["id"]] = c
	Progress.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	_rp_label.text = "%d Sách • tổng cấp %d" % [Progress.research_points, Progress.research_total()]
	for id: String in _cards:
		var c: UpgradeCard = _cards[id]
		var r := Progress.research_info(id)
		var lv := Progress.research_level(id)
		var mx: int = int(r["max"])
		var open := Progress.research_unlocked(id)
		c.dim(not open)
		var now: String = _effect(r, lv)
		c.set_info("Cấp %d/%d" % [lv, mx], str(r["desc"]), "Hiện tại: " + now)
		if not open:
			c.set_button(0, "Khóa", false, "", "lock")
		elif lv >= mx:
			c.set_button(0, "Tối đa", false, "GreenButton", "check")
		else:
			c.set_button(0, "Học  %d" % Progress.research_cost(id), Progress.can_research(id), "BlueButton", "icon_rp", true)


func _effect(r: Dictionary, lv: int) -> String:
	var v: float = float(r["value"]) * lv
	match str(r["id"]):
		"offline":
			return "+%d giờ" % int(v)
		"golden":
			return "+x%d" % int(v)
	return "+%d%%" % int(round(v * 100.0))


func _buy(_idx: int, id: String, card: UpgradeCard) -> void:
	if Progress.buy_research(id):
		Juice.shake(card, 6.0)
		AudioManager.play("purchase")
		if UIKit.main:
			UIKit.main.call("sparkle_at", card.buttons[0].get_global_rect().get_center())
	_refresh()
