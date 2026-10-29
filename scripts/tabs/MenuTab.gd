extends TabBase
## Tab Thực đơn: 24 món, món đặc biệt hôm nay, giá bán, thời gian nấu, cấp quán cần để mở. Nâng cấp món tăng giá bán.

var _cards: Array[UpgradeCard] = []
var _special: Label


func _build() -> void:
	var list := UIKit.tab_sheet(self, "THỰC ĐƠN", "Khách gọi ngẫu nhiên các món đã mở. Món đắt nấu lâu hơn.")
	var box := UIKit.panel("Highlight")
	list.add_child(box)
	var row := UIKit.hbox(10)
	box.add_child(row)
	row.add_child(UIKit.icon("star", 48))
	_special = UIKit.label("", "", 22)
	_special.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_special.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(_special)
	for d: Dictionary in GameState.dishes:
		var c := UpgradeCard.new()
		c.setup(Sprites.tex("dish_" + str(d["id"])), str(d["name"]), 2)
		c.action.connect(_on_action.bind(str(d["id"]), c))
		list.add_child(c)
		_cards.append(c)


func _refresh() -> void:
	var g := GameState
	var sp_id := g.daily_special()
	_special.text = "Món đặc biệt hôm nay: %s, bán giá x%s và được gọi nhiều hơn. Đổi món mỗi ngày." % [
		str(g.dish_info(sp_id)["name"]), NumberFormat.fmt_dec(g.bal("special_mult", 2.0))]
	for i in _cards.size():
		var d: Dictionary = g.dishes[i]
		var id: String = d["id"]
		var c := _cards[i]
		var lv: int = int(g.dish_levels[id])
		var cook: String = "%s giây" % NumberFormat.fmt_dec(float(d["cook_time"]))
		if lv <= 0:
			c.dim(true)
			c.set_info("", "Mở ở cấp quán %d" % int(d["unlock_level"]),
				"Giá %s • Nấu %s" % [NumberFormat.fmt(float(d["price"])), cook])
			c.set_button(0, "Khóa", false, "", "lock")
			c.hide_button(1)
			continue
		c.dim(false)
		var now: float = g.dish_price(id)
		var nxt: float = g.dish_price_at(id, lv + 1)
		var tag := "Cấp %d" % lv + (" • x2" if id == sp_id else "") + (" • đặc sản" if id == g.specialty() else "")
		c.set_info(tag, "Giá %s → %s" % [NumberFormat.fmt(now), NumberFormat.fmt(nxt)],
			"Nấu %s • Cấp %d giá x2" % [cook, (floori((lv - 1) / g.bal("dish_double_every", 10)) + 1) * int(g.bal("dish_double_every", 10)) + 1])
		var c1: float = g.dish_upgrade_cost(id, 1)
		var c10: float = g.dish_upgrade_cost(id, 10)
		c.set_button(0, "Cấp+  " + NumberFormat.fmt(c1), g.can_afford(c1), "", "coin", true)
		c.set_button(1, "x10  " + NumberFormat.fmt(c10), g.can_afford(c10), "GreenButton", "coin", false)


func _on_action(idx: int, id: String, card: UpgradeCard) -> void:
	if GameState.upgrade_dish(id, 1 if idx == 0 else 10):
		Juice.shake(card, 6.0)
		_sparkle(card.buttons[idx])
	_refresh()
