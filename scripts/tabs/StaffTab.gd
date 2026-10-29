extends TabBase
## Tab Nhân viên: Đầu bếp, Bồi bàn, Thu ngân, Lễ tân + Quản lý + giờ offline.

const STAFF_IDS: Array[String] = ["chef", "waiter", "cashier", "receptionist"]

var _cards: Dictionary = {}
var _manager: UpgradeCard
var _offline: UpgradeCard


func _build() -> void:
	var list := UIKit.tab_sheet(self, "NHÂN VIÊN", "Nhân viên làm việc ở mọi khu đã mở")
	for id in STAFF_IDS:
		var s: Dictionary = GameState.staff_data[id]
		var c := UpgradeCard.new()
		c.setup(Sprites.tex(str(s["sprite"])), str(s["name"]), 2)
		c.action.connect(_on_action.bind(id, c))
		list.add_child(c)
		_cards[id] = c
	list.add_child(UIKit.section("Quản lý quán"))
	var m: Dictionary = GameState.staff_data["manager"]
	_manager = UpgradeCard.new()
	_manager.setup(Sprites.tex(str(m["sprite"])), str(m["name"]), 1)
	_manager.action.connect(_on_manager)
	list.add_child(_manager)
	_offline = UpgradeCard.new()
	_offline.setup(Sprites.ui("clock"), "Két sắt offline", 1)
	_offline.action.connect(_on_offline)
	list.add_child(_offline)


func _refresh() -> void:
	var g := GameState
	for id in STAFF_IDS:
		var c: UpgradeCard = _cards[id]
		var s: Dictionary = g.staff_data[id]
		var count: int = g.staff_count(id)
		var mx: int = int(s["max_count"])
		if not g.staff_unlocked(id):
			c.dim(true)
			c.set_info("", "Mở khóa ở cấp quán %d" % int(s["unlock_level"]), str(s["desc"]))
			c.set_button(0, "Khóa", false, "", "lock")
			c.hide_button(1)
			continue
		c.dim(false)
		var lv: int = g.staff_level(id)
		var spd := "Tốc độ x%s → x%s" % [NumberFormat.fmt_dec(g.staff_speed_at(id, lv)),
			NumberFormat.fmt_dec(g.staff_speed_at(id, lv + 1))]
		c.set_info("Cấp %d" % lv, spd, "Số lượng: %d/%d • %s" % [count, mx, str(s["desc"])])
		if count >= mx:
			c.set_button(0, "Đủ người", false, "GreenButton", "check")
		else:
			var hc: float = g.hire_cost(id)
			c.set_button(0, "Thuê  " + NumberFormat.fmt(hc), g.can_afford(hc), "GreenButton", "coin", true)
		var uc: float = g.staff_upgrade_cost(id)
		c.set_button(1, "Cấp+  " + NumberFormat.fmt(uc), count > 0 and g.can_afford(uc), "", "coin", true)
	# Quản lý
	var m: Dictionary = g.staff_data["manager"]
	if g.manager:
		_manager.dim(false)
		_manager.set_info("Đã thuê", "Quán tự vận hành, kể cả khi offline", str(m["desc"]))
		_manager.set_button(0, "Đã thuê", false, "GreenButton", "check")
	elif not g.staff_unlocked("manager"):
		_manager.dim(true)
		_manager.set_info("", "Mở khóa ở cấp quán %d" % int(m["unlock_level"]), str(m["desc"]))
		_manager.set_button(0, "Khóa", false, "", "lock")
	else:
		_manager.dim(false)
		_manager.set_info("", "Quán tự vận hành, kể cả khi offline", str(m["desc"]))
		var mc: float = g.manager_cost()
		_manager.set_button(0, "Thuê  " + NumberFormat.fmt(mc), g.can_afford(mc), "GreenButton", "coin", true)
	# giờ offline
	var mx_h: int = int(g.bal("offline_max_hours", 12))
	_offline.set_info("%d/%d giờ" % [g.offline_hours, mx_h], "Thu nhập offline tối đa %d giờ" % g.offline_cap_hours(),
		"Thu nhập khi vắng mặt: %d%% (100%% khi có Quản lý)" % int((1.0 if g.manager else g.bal("offline_rate_no_manager", 0.4)) * 100.0))
	if g.offline_hours >= mx_h:
		_offline.set_button(0, "Tối đa", false, "GreenButton", "check")
	else:
		var oc: float = g.offline_hour_cost()
		_offline.set_button(0, "+1 giờ  " + NumberFormat.fmt(oc), g.can_afford(oc), "", "coin", true)


func _on_action(idx: int, id: String, card: UpgradeCard) -> void:
	var ok: bool = GameState.hire(id) if idx == 0 else GameState.upgrade_staff(id)
	if ok:
		Juice.shake(card, 6.0)
		_sparkle(card.buttons[idx])
	_refresh()


func _on_manager(_idx: int) -> void:
	if GameState.hire_manager():
		Juice.shake(_manager, 6.0)
		_sparkle(_manager.buttons[0])
	_refresh()


func _on_offline(_idx: int) -> void:
	if GameState.buy_offline_hour():
		Juice.shake(_offline, 6.0)
		_sparkle(_offline.buttons[0])
	_refresh()
