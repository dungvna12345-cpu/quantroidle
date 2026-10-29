extends TabBase
## Tab Nhiệm vụ: quà đăng nhập 7 ngày, nhiệm vụ hằng ngày (reset 0h), thành tích theo mốc.

var _login_days: Array[PanelContainer] = []
var _login_btn: JuicyButton
var _reset_label: Label
var _daily_rows: Array[Dictionary] = []
var _ach_rows: Array[Dictionary] = []
var _friend_rows: Array[Dictionary] = []


func _build() -> void:
	var list := UIKit.tab_sheet(self, "NHIỆM VỤ", "Hoàn thành để nhận vàng và kim cương")
	# --- quà đăng nhập
	list.add_child(UIKit.section("Quà đăng nhập 7 ngày"))
	var card := UIKit.panel("Card")
	list.add_child(card)
	var lv := UIKit.vbox(12)
	card.add_child(lv)
	var grid := GridContainer.new()
	grid.columns = 7
	grid.add_theme_constant_override("h_separation", 6)
	lv.add_child(grid)
	var rewards: Array = GameState.quest_data["login"]
	for i in rewards.size():
		var r: Dictionary = rewards[i]
		var p := PanelContainer.new()
		p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var v := UIKit.vbox(0)
		p.add_child(v)
		var day := UIKit.label("Ngày %d" % (i + 1), "SmallLabel", 16)
		day.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(day)
		var is_gold: bool = int(r["gold"]) > 0 and int(r["diamonds"]) == 0
		var ic := UIKit.icon("coin" if is_gold else ("gift" if int(r["gold"]) > 0 else "diamond"), 40)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		var amt: String = NumberFormat.fmt(float(r["gold"])) if is_gold else str(int(r["diamonds"]))
		var al := UIKit.label(amt, "", 18)
		al.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(al)
		grid.add_child(p)
		_login_days.append(p)
	_login_btn = UIKit.button("", "GreenButton", "gift", 360)
	_login_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_login_btn.pressed.connect(_claim_login)
	lv.add_child(_login_btn)
	# --- nhiệm vụ ngày
	var head := UIKit.hbox(8)
	head.add_child(UIKit.section("Nhiệm vụ hằng ngày"))
	head.add_child(UIKit.spacer())
	_reset_label = UIKit.label("", "SmallLabel")
	_reset_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_reset_label)
	list.add_child(head)
	for q: Dictionary in GameState.quest_data["daily"]:
		var row := _make_row(list, "check", str(q["name"]))
		row["quest"] = q
		(row["btn"] as JuicyButton).pressed.connect(_claim_daily.bind(q, row))
		_daily_rows.append(row)
	# --- khách quen
	list.add_child(UIKit.section("Khách quen"))
	for r: Dictionary in Story.regulars():
		var row := _make_row(list, "portrait_" + str(r["sprite"]), str(Story.character(str(r["id"]))["name"]))
		row["reg"] = r
		(row["btn"] as JuicyButton).visible = false
		_friend_rows.append(row)
	# --- thành tích
	list.add_child(UIKit.section("Thành tích"))
	for a: Dictionary in GameState.quest_data["achievements"]:
		var row := _make_row(list, "star", str(a["name"]))
		row["ach"] = a
		(row["btn"] as JuicyButton).pressed.connect(_claim_ach.bind(a, row))
		_ach_rows.append(row)


func _make_row(list: VBoxContainer, icon_id: String, title: String) -> Dictionary:
	var card := UIKit.panel("Card")
	list.add_child(card)
	var h := UIKit.hbox(12)
	card.add_child(h)
	h.add_child(UIKit.icon(icon_id, 64))
	var v := UIKit.vbox(4)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	h.add_child(v)
	var t := UIKit.label(title, "", 24)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(t)
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
	var btn := UIKit.button("Nhận", "GreenButton", "", 150)
	btn.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	h.add_child(btn)
	return {"card": card, "title": t, "sub": sub, "bar": bar, "bar_text": bar_text, "btn": btn}


func _process(delta: float) -> void:
	super(delta)
	if visible:
		_reset_label.text = "Làm mới sau " + NumberFormat.fmt_clock(GameState.seconds_to_midnight())


func _refresh() -> void:
	var g := GameState
	# đăng nhập
	var idx: int = g.login_index()
	var can: bool = g.login_claimable()
	for i in _login_days.size():
		var p := _login_days[i]
		var sb := StyleBoxFlat.new()
		sb.set_corner_radius_all(14)
		sb.set_content_margin_all(4)
		sb.set_border_width_all(3)
		var claimed_today: bool = not can and i == (idx + 6) % 7
		# vừa nhận ngày 7 thì idx quay về 0: cả tuần đều đã nhận
		var week_done: bool = not can and idx == 0 and int(g.login.get("day", 0)) > 0
		if i < idx or claimed_today or week_done:
			sb.bg_color = Color("d8f0c8")
			sb.border_color = Color("7bd35b")
		elif i == idx and can:
			sb.bg_color = Color("fff1b8")
			sb.border_color = Color("f2a541")
		else:
			sb.bg_color = Color("f3ead9")
			sb.border_color = Color("e2d2b6")
		p.add_theme_stylebox_override("panel", sb)
	if can:
		_login_btn.text = "Nhận quà ngày %d" % (idx + 1)
		_login_btn.disabled = false
		_login_btn.pulse = true
	else:
		_login_btn.text = "Quay lại vào ngày mai"
		_login_btn.disabled = true
		_login_btn.pulse = false
	# nhiệm vụ ngày
	for row in _daily_rows:
		var q: Dictionary = row["quest"]
		var prog: float = minf(g.daily_progress(q), float(q["goal"]))
		var bar: ProgressBar = row["bar"]
		bar.max_value = float(q["goal"])
		bar.value = prog
		(row["bar_text"] as Label).text = "%s/%s" % [NumberFormat.fmt(prog), NumberFormat.fmt(float(q["goal"]))]
		(row["sub"] as Label).text = "Thưởng: %s vàng + %d kim cương" % [NumberFormat.fmt(g.daily_gold_reward(q)), int(q["diamonds"])]
		var btn: JuicyButton = row["btn"]
		if g.daily_claimed(q):
			btn.text = "Đã nhận"
			btn.disabled = true
			btn.pulse = false
		else:
			btn.text = "Nhận"
			btn.disabled = prog < float(q["goal"])
			btn.pulse = not btn.disabled
	# khách quen
	for row in _friend_rows:
		var r: Dictionary = row["reg"]
		var id: String = r["id"]
		var n: int = int(Story.friendship.get(id, 0))
		var nxt: int = Story.next_threshold(id)
		var lv: int = Story.friend_level(id)
		(row["sub"] as Label).text = "Thân thiết cấp %d/3 • Thích món %s" % [lv,
			str(g.dish_info(str(r["dish"])).get("name", ""))]
		var bar: ProgressBar = row["bar"]
		bar.max_value = float(nxt if nxt > 0 else n)
		bar.value = float(n)
		(row["bar_text"] as Label).text = ("%d/%d lần ghé" % [n, nxt]) if nxt > 0 else "Bạn thân của quán"
	# thành tích
	for row in _ach_rows:
		var a: Dictionary = row["ach"]
		var tiers: Array = a["tiers"]
		var t: int = g.achievement_tier(a)
		var bar: ProgressBar = row["bar"]
		var btn: JuicyButton = row["btn"]
		var val: float = g.stat_value(str(a["stat"]))
		if t >= tiers.size():
			(row["sub"] as Label).text = "%s • Đã hoàn thành mọi mốc" % str(a["desc"])
			bar.max_value = 1.0
			bar.value = 1.0
			(row["bar_text"] as Label).text = "Hoàn thành"
			btn.text = "Xong"
			btn.disabled = true
			btn.pulse = false
			continue
		var goal: float = float(tiers[t])
		(row["sub"] as Label).text = "%s • Mốc %d/%d • Thưởng %d kim cương" % [str(a["desc"]), t + 1, tiers.size(), int(a["diamonds"][t])]
		bar.max_value = goal
		bar.value = minf(val, goal)
		(row["bar_text"] as Label).text = "%s/%s" % [NumberFormat.fmt(minf(val, goal)), NumberFormat.fmt(goal)]
		btn.text = "Nhận"
		btn.disabled = not g.achievement_claimable(a)
		btn.pulse = not btn.disabled


func _claim_login() -> void:
	if GameState.claim_login():
		AudioManager.play("purchase")
		_sparkle(_login_btn)
		if UIKit.main:
			UIKit.main.call("burst_coins", _login_btn.get_global_rect().get_center(), 6, 0.0)
	_refresh()


func _claim_daily(q: Dictionary, row: Dictionary) -> void:
	if GameState.claim_daily(q):
		AudioManager.play("purchase")
		Juice.shake(row["card"] as Control, 6.0)
		_sparkle(row["btn"] as Control)
		if UIKit.main:
			UIKit.main.call("burst_coins", (row["btn"] as Control).get_global_rect().get_center(), 6, 0.0)
	_refresh()


func _claim_ach(a: Dictionary, row: Dictionary) -> void:
	if GameState.claim_achievement(a):
		AudioManager.play("purchase")
		Juice.shake(row["card"] as Control, 6.0)
		_sparkle(row["btn"] as Control)
	_refresh()
