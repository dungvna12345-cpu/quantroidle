extends PopupBase
## Đơn đặt tiệc: phục vụ đủ số phần một món để nhận thưởng vàng + kim cương. Có thể đổi đơn bằng kim cương.

var _rows: Array[Dictionary] = []


func _init() -> void:
	title_text = "Đơn đặt tiệc"
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	b.add_child(centered_label("Khách đặt tiệc! Phục vụ đủ số phần món được yêu cầu để nhận thưởng lớn.", "SmallLabel", 20))
	for i in GameState.orders.size():
		var card := UIKit.panel("Card")
		b.add_child(card)
		var h := UIKit.hbox(12)
		card.add_child(h)
		var icon := TextureRect.new()
		icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.custom_minimum_size = Vector2(88, 88)
		h.add_child(icon)
		var v := UIKit.vbox(2)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(v)
		var title := UIKit.label("", "", 26)
		v.add_child(title)
		var sub := UIKit.label("", "SmallLabel", 19)
		sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(sub)
		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(0, 26)
		bar.show_percentage = false
		v.add_child(bar)
		var bar_text := UIKit.label("", "WhiteLabel", 17)
		bar_text.set_anchors_preset(Control.PRESET_FULL_RECT)
		bar_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		bar_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		bar.add_child(bar_text)
		var btns := UIKit.vbox(6)
		btns.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		h.add_child(btns)
		var claim := UIKit.button("Nhận", "GreenButton", "", 150)
		claim.pressed.connect(_claim.bind(i))
		btns.add_child(claim)
		var skip := UIKit.button("Đổi  %d" % int(GameState.orders_data.get("skip_diamonds", 3)), "BlueButton", "diamond", 150)
		skip.custom_minimum_size = Vector2(150, 52)
		skip.add_theme_font_size_override("font_size", 20)
		skip.pressed.connect(_skip.bind(i))
		btns.add_child(skip)
		_rows.append({"card": card, "icon": icon, "title": title, "sub": sub, "bar": bar, "bar_text": bar_text,
			"claim": claim, "skip": skip})
	GameState.orders_changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	var g := GameState
	for i in _rows.size():
		var o: Dictionary = g.orders[i]
		var r: Dictionary = _rows[i]
		var d: Dictionary = g.dish_info(str(o["dish"]))
		(r["icon"] as TextureRect).texture = Sprites.tex("dish_" + str(o["dish"]))
		(r["title"] as Label).text = "%s: %d phần %s" % [str(o["theme"]), int(o["need"]), str(d["name"])]
		(r["sub"] as Label).text = "Thưởng: %s vàng + kim cương" % NumberFormat.fmt(g.order_reward_gold())
		var bar: ProgressBar = r["bar"]
		bar.max_value = float(o["need"])
		bar.value = float(o["have"])
		(r["bar_text"] as Label).text = "%d/%d" % [int(o["have"]), int(o["need"])]
		var ready := g.order_ready(i)
		var claim: JuicyButton = r["claim"]
		claim.disabled = not ready
		claim.pulse = ready
		(r["skip"] as JuicyButton).disabled = g.diamonds < int(g.orders_data.get("skip_diamonds", 3))


func _claim(i: int) -> void:
	if GameState.claim_order(i):
		Juice.shake(_rows[i]["card"] as Control, 7.0)
		if UIKit.main:
			var at: Vector2 = (_rows[i]["claim"] as Control).get_global_rect().get_center()
			UIKit.main.call("sparkle_at", at)
			UIKit.main.call("burst_coins", at, 8, 0.0)
	_refresh()


func _skip(i: int) -> void:
	GameState.skip_order(i)
	_refresh()
