extends Node
## Trạng thái game: tiền, cấp quán, nâng cấp, nhiệm vụ.
## Mọi con số cân bằng đọc từ res://data/*.json. Giao diện lắng nghe các signal bên dưới.

signal gold_changed(value: float)
signal diamonds_changed(value: int)
signal exp_changed(xp: float, need: float)
signal leveled_up(new_level: int, unlocks: Array)
signal state_changed                       # nâng cấp, thuê, mở khóa... -> UI và cảnh làm mới
signal area_changed(area_id: String)       # mở khóa khu / mua trang trí
signal current_area_changed(area_id: String)
signal quests_changed
signal coin_fx(world_pos: Vector2, amount: float)
signal toast(text: String)
signal tutorial_event(event_id: String)
signal purchased(kind: String)
signal rush_requested(count: int)
signal settings_changed
signal world_reset
signal event_started(ev: Dictionary)
signal event_ended
signal orders_changed
signal wing_opened(area_id: String, wing_id: String)
signal combo_hit(count: int, world_pos: Vector2)
signal fever_started(duration: float)
signal fever_ended

var fever_time: float = 0.0

const DATA_DIR := "res://data/"

# ---------- Dữ liệu cân bằng ----------
var balance: Dictionary = {}
var dishes: Array = []
var staff_data: Dictionary = {}
var areas_data: Array = []
var decor_data: Dictionary = {}
var quest_data: Dictionary = {}
var shop_data: Array = []
var events_data: Dictionary = {}
var orders_data: Dictionary = {}
var chapters_data: Array = []
var guests_data: Array = []
var guest_claimed: Dictionary = {}

# ---------- Trạng thái lưu ----------
var gold: float = 0.0
var diamonds: int = 0
var level: int = 1
var xp: float = 0.0
var run_gold: float = 0.0          # vàng kiếm trong lượt hiện tại (tính Danh tiếng)
var run_customers: int = 0         # khách phục vụ trong chương hiện tại (mục tiêu chương)
var lifetime_gold: float = 0.0
var total_customers: int = 0
var reputation: int = 0            # điểm Danh tiếng từ tái khởi nghiệp
var chapter: int = 0               # chương hiện tại (0 = Phố Cổ)
var just_advanced: bool = false    # vừa sang chương mới -> hiện popup chúc mừng
var dish_levels: Dictionary = {}   # id -> cấp (0 = chưa mở)
var staff: Dictionary = {}         # id -> {"count", "level"}
var manager: bool = false
var offline_hours: int = 2
var areas: Dictionary = {}         # id -> {"unlocked", "tables", "kitchen", "cashier", "decor", "rooms"}
var current_area: String = "hall"
var boost_until: float = 0.0       # unix time hết hạn x2
var daily: Dictionary = {}
var achievements: Dictionary = {}  # id -> số mốc đã nhận
var login: Dictionary = {}
var settings: Dictionary = {"music": true, "sfx": true, "vibrate": true}
var tutorial_done: bool = false
var tutorial2_done: bool = false   # hướng dẫn tính năng mới (mục tiêu, nghiên cứu...)
var max_time_seen: float = 0.0      # chống chỉnh lùi đồng hồ
var time_tampered: bool = false
var owner_name: String = "Quán Trọ"
var avatar: String = "avatar"
var data_errors: Array[String] = []
var measured_rate: float = 0.0     # vàng/giây đo thực tế (dùng cho offline)
var pending_offline: float = 0.0
var pending_offline_seconds: float = 0.0
var upgrades_bought: int = 0
var tips_collected: int = 0
var orders: Array = []             # đơn đặt tiệc: {"theme", "dish", "need", "have"}
var pet_level: int = 1
var pet_xp: float = 0.0

# ---------- Sự kiện ngẫu nhiên (không lưu) ----------
var current_event: Dictionary = {}
var event_left: float = 0.0
var _event_wait: float = 0.0

# ---------- Biến tạm ----------
var _rate_bucket: float = 0.0
var _rate_buckets: Array[float] = []
var _rate_clock: float = 0.0
var _day_check: float = 0.0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_load_data()
	new_game()


func _load_json(file_name: String) -> Variant:
	var path := DATA_DIR + file_name
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Không đọc được " + path)
		return null
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed == null:
		push_error("JSON lỗi: " + path)
		data_errors.append("File dữ liệu bị lỗi cú pháp: " + file_name)
	return parsed


func _load_data() -> void:
	balance = _load_json("balance.json")
	dishes = _load_json("dishes.json")
	staff_data = _load_json("staff.json")
	areas_data = _load_json("areas.json")
	decor_data = _load_json("decor.json")
	quest_data = _load_json("quests.json")
	shop_data = _load_json("shop.json")
	events_data = _load_json("events.json")
	orders_data = _load_json("orders.json")
	chapters_data = _load_json("chapters.json")
	guests_data = _load_json("guests.json")
	_flatten_wings()


## Gộp bàn / giường của các phòng mở rộng vào danh sách chung của khu, ghi lại bàn nào thuộc phòng nào.
func _flatten_wings() -> void:
	for a: Dictionary in areas_data:
		var tables: Array = a.get("tables", [])
		var beds: Array = a.get("beds", [])
		var tw: Array = []
		var bw: Array = []
		for i in tables.size():
			tw.append("")
		for i in beds.size():
			bw.append("")
		for w: Dictionary in a.get("wings", []):
			for t: Variant in w.get("tables", []):
				tables.append(t)
				tw.append(w["id"])
			for t: Variant in w.get("beds", []):
				beds.append(t)
				bw.append(w["id"])
		a["tables"] = tables
		if a.has("beds"):
			a["beds"] = beds
		a["table_wing"] = tw
		a["bed_wing"] = bw


func bal(key: String, default_value: float = 0.0) -> float:
	return float(balance.get(key, default_value))


# =====================================================================
# Khởi tạo / lưu
# =====================================================================

func new_game(keep_meta: bool = false) -> void:
	if not keep_meta:
		chapter = 0
	gold = float(chapter_info().get("start_gold", bal("start_gold")))
	level = 1
	xp = 0.0
	run_gold = 0.0
	run_customers = 0
	manager = false
	offline_hours = int(bal("offline_base_hours", 2))
	current_area = "hall"
	boost_until = 0.0
	measured_rate = 0.0
	pending_offline = 0.0
	pending_offline_seconds = 0.0
	dish_levels = {}
	for d: Dictionary in dishes:
		dish_levels[d["id"]] = 1 if int(d["unlock_level"]) <= 1 else 0
	staff = {}
	for id: String in staff_data:
		if id == "manager":
			continue
		staff[id] = {"count": int(staff_data[id]["start_count"]), "level": 1}
	areas = {}
	for a: Dictionary in areas_data:
		areas[a["id"]] = _default_area(a)
	if not keep_meta:
		diamonds = int(bal("start_diamonds"))
		lifetime_gold = 0.0
		total_customers = 0
		reputation = 0
		achievements = {}
		login = {"day": 0, "last": ""}
		daily = {}
		settings = {"music": true, "sfx": true, "vibrate": true}
		tutorial_done = false
		upgrades_bought = 0
		tips_collected = 0
	_check_daily_reset()
	orders = []
	_fill_orders()
	current_event = {}
	_event_wait = float(events_data.get("first_delay", 50))
	_rate_buckets.clear()
	_rate_bucket = 0.0


func _default_area(a: Dictionary) -> Dictionary:
	var tables: Array = []
	var spots: Array = a.get("tables", [])
	for i in spots.size():
		tables.append(1 if i < int(a.get("start_tables", 0)) else 0)
	var rooms: Array = []
	var beds: Array = a.get("beds", [])
	for i in beds.size():
		rooms.append(1 if i < int(a.get("start_rooms", 0)) else 0)
	return {
		"unlocked": int(a["unlock_cost"]) == 0,
		"tables": tables,
		"kitchen": 1,
		"cashier": 1,
		"decor": {},
		"rooms": rooms,
		"wings": {},
	}


func to_dict() -> Dictionary:
	return {
		"version": int(bal("save_version", 1)),
		"gold": gold, "diamonds": diamonds, "level": level, "xp": xp,
		"run_gold": run_gold, "run_customers": run_customers, "lifetime_gold": lifetime_gold, "total_customers": total_customers,
		"reputation": reputation, "dish_levels": dish_levels, "staff": staff, "manager": manager,
		"offline_hours": offline_hours, "areas": areas, "current_area": current_area,
		"boost_until": boost_until, "daily": daily, "achievements": achievements, "login": login,
		"settings": settings, "tutorial_done": tutorial_done, "tutorial2_done": tutorial2_done, "max_time_seen": max_time_seen,
		"owner_name": owner_name, "avatar": avatar, "measured_rate": measured_rate,
		"pending_offline": pending_offline, "pending_offline_seconds": pending_offline_seconds,
		"upgrades_bought": upgrades_bought, "tips_collected": tips_collected,
		"orders": orders, "chapter": chapter, "just_advanced": just_advanced,
		"pet_level": pet_level, "pet_xp": pet_xp, "guest_claimed": guest_claimed,
	}


## Nạp dữ liệu từ file lưu. Trường thiếu giữ mặc định để tương thích bản cũ.
func from_dict(d: Dictionary) -> void:
	d = migrate_save(d)
	new_game()
	var version: int = int(d.get("version", 1))
	if version > int(bal("save_version", 1)):
		push_warning("File lưu mới hơn phiên bản game")
	gold = float(d.get("gold", gold))
	diamonds = int(d.get("diamonds", diamonds))
	level = maxi(1, int(d.get("level", 1)))
	xp = float(d.get("xp", 0.0))
	run_gold = float(d.get("run_gold", 0.0))
	run_customers = int(d.get("run_customers", 0))
	lifetime_gold = float(d.get("lifetime_gold", 0.0))
	total_customers = int(d.get("total_customers", 0))
	reputation = int(d.get("reputation", 0))
	chapter = clampi(int(d.get("chapter", 0)), 0, maxi(0, chapters_data.size() - 1))
	just_advanced = bool(d.get("just_advanced", false))
	pet_level = clampi(int(d.get("pet_level", 1)), 1, 5)
	pet_xp = float(d.get("pet_xp", 0.0))
	var gc: Variant = d.get("guest_claimed", {})
	guest_claimed = Dictionary(gc) if gc is Dictionary else {}
	manager = bool(d.get("manager", false))
	offline_hours = clampi(int(d.get("offline_hours", offline_hours)), 1, int(bal("offline_max_hours", 12)))
	boost_until = float(d.get("boost_until", 0.0))
	tutorial_done = bool(d.get("tutorial_done", false))
	tutorial2_done = bool(d.get("tutorial2_done", tutorial_done))
	max_time_seen = float(d.get("max_time_seen", 0.0))
	owner_name = str(d.get("owner_name", "Quán Trọ"))
	avatar = str(d.get("avatar", "avatar"))
	measured_rate = float(d.get("measured_rate", 0.0))
	pending_offline = float(d.get("pending_offline", 0.0))
	pending_offline_seconds = float(d.get("pending_offline_seconds", 0.0))
	upgrades_bought = int(d.get("upgrades_bought", 0))
	tips_collected = int(d.get("tips_collected", 0))
	var dl: Variant = d.get("dish_levels", {})
	if dl is Dictionary:
		for id: String in dish_levels:
			dish_levels[id] = int((dl as Dictionary).get(id, dish_levels[id]))
	var st: Variant = d.get("staff", {})
	if st is Dictionary:
		for id: String in staff:
			var s: Variant = (st as Dictionary).get(id, null)
			if s is Dictionary:
				staff[id]["count"] = clampi(int(s.get("count", 0)), 0, int(staff_data[id]["max_count"]))
				staff[id]["level"] = maxi(1, int(s.get("level", 1)))
	var ar: Variant = d.get("areas", {})
	if ar is Dictionary:
		for id: String in areas:
			var a: Variant = (ar as Dictionary).get(id, null)
			if a is Dictionary:
				_merge_area(id, a)
	var cur: String = str(d.get("current_area", "hall"))
	if areas.has(cur) and areas[cur]["unlocked"]:
		current_area = cur
	for key in ["daily", "achievements", "login", "settings"]:
		var v: Variant = d.get(key, null)
		if v is Dictionary:
			var target: Dictionary = get(key)
			for k: String in v:
				target[k] = v[k]
	var od: Variant = d.get("orders", [])
	if od is Array and not (od as Array).is_empty():
		orders = []
		for o: Variant in od:
			if o is Dictionary and dish_levels.has(str(o.get("dish", ""))):
				orders.append({"theme": str(o.get("theme", "")), "dish": str(o["dish"]),
					"need": int(o.get("need", 5)), "have": int(o.get("have", 0))})
		_fill_orders()
	# đảm bảo món đủ cấp đều đã mở (khi data thay đổi giữa các phiên bản)
	for dd: Dictionary in dishes:
		if int(dd["unlock_level"]) <= level and int(dish_levels[dd["id"]]) == 0:
			dish_levels[dd["id"]] = 1
	_check_daily_reset()


func _merge_area(id: String, a: Dictionary) -> void:
	var cur: Dictionary = areas[id]
	cur["unlocked"] = bool(a.get("unlocked", cur["unlocked"]))
	cur["kitchen"] = maxi(1, int(a.get("kitchen", 1)))
	cur["cashier"] = maxi(1, int(a.get("cashier", 1)))
	for key in ["tables", "rooms"]:
		var src: Variant = a.get(key, [])
		if src is Array:
			var dst: Array = cur[key]
			for i in mini(dst.size(), (src as Array).size()):
				dst[i] = maxi(0, int(src[i]))
	var wg: Variant = a.get("wings", {})
	if wg is Dictionary:
		cur["wings"] = (wg as Dictionary).duplicate()
	var dec: Variant = a.get("decor", {})
	if dec is Dictionary:
		var out: Dictionary = {}
		for k: String in dec:
			out[k] = clampi(int(dec[k]), 0, decor_max(id, k))
		cur["decor"] = out


# =====================================================================
# Vòng lặp: đo thu nhập thực tế, reset nhiệm vụ ngày
# =====================================================================

func _process(delta: float) -> void:
	_rate_clock += delta
	if _rate_clock >= 5.0:
		_rate_clock -= 5.0
		_rate_buckets.append(_rate_bucket)
		_rate_bucket = 0.0
		var max_buckets: int = maxi(1, int(bal("rate_window_seconds", 300) / 5.0))
		while _rate_buckets.size() > max_buckets:
			_rate_buckets.remove_at(0)
		# đủ 1 phút dữ liệu thì cập nhật tốc độ thực tế
		if _rate_buckets.size() >= 12:
			var total: float = 0.0
			for v in _rate_buckets:
				total += v
			measured_rate = total / (_rate_buckets.size() * 5.0)
	_update_event(delta)
	if fever_time > 0.0:
		fever_time -= delta
		if fever_time <= 0.0:
			fever_time = 0.0
			fever_ended.emit()
	day_t = fmod(day_t + delta, bal("day_cycle_seconds", 480))
	_day_check += delta
	if _day_check >= 2.0:
		_day_check = 0.0
		_watch_clock()
		_check_daily_reset()


func start_fever(duration: float = 30.0) -> void:
	fever_time = maxf(fever_time, duration)
	fever_started.emit(duration)
	AudioManager.play("levelup")
	show_toast("🔥 GIỜ VÀNG BÙNG NỔ! THU NHẬP x3! 🔥")


func is_fever() -> bool:
	return fever_time > 0.0


func fever_left() -> float:
	return fever_time


## Tốc độ thu nhập dùng cho offline và túi vàng.
func income_rate() -> float:
	return maxf(measured_rate, estimate_rate() * 0.5)


## Ước tính lý thuyết khi chưa đủ dữ liệu đo.
func estimate_rate() -> float:
	var total: float = 0.0
	var avg_price: float = 0.0
	var n: int = 0
	for d: Dictionary in dishes:
		if dish_levels[d["id"]] > 0:
			avg_price += dish_price(d["id"])
			n += 1
	if n > 0:
		avg_price /= n
	for a: Dictionary in areas_data:
		var id: String = a["id"]
		if not areas[id]["unlocked"]:
			continue
		if a["kind"] == "lodging":
			for i in (areas[id]["rooms"] as Array).size():
				if areas[id]["rooms"][i] > 0:
					total += room_rent(id, i) / float(a["room"]["sleep_time"] + 8)
		else:
			var tables: int = 0
			for lv: int in areas[id]["tables"]:
				if lv > 0:
					tables += 1
			var cap: float = minf(tables, 1.0 + staff_count("waiter") * 1.6)
			total += cap * bal("fallback_rate_per_table") * avg_price * float(a["price_mult"]) / 10.0
	return total * income_mult()


func _track_rate(v: float) -> void:
	_rate_bucket += v


# =====================================================================
# Công thức
# =====================================================================

## Hệ số giá theo chương: chương sau thu nhập cao hơn thì giá cũng cao hơn (nhưng chậm hơn thu nhập).
func cost_mult() -> float:
	return float(chapter_info().get("cost_mult", 1.0))


func cost_at(base: float, lv: int) -> float:
	return floor(base * cost_mult() * pow(bal("cost_growth", 1.15), lv))


## Tổng giá mua n cấp liên tiếp bắt đầu từ cấp lv.
func cost_n(base: float, lv: int, n: int) -> float:
	var total: float = 0.0
	for i in n:
		total += cost_at(base, lv + i)
	return total


func area_info(id: String) -> Dictionary:
	for a: Dictionary in areas_data:
		if a["id"] == id:
			return a
	return {}


func area_index(id: String) -> int:
	for i in areas_data.size():
		if areas_data[i]["id"] == id:
			return i
	return 0


func income_mult() -> float:
	var m: float = (1.0 + bal("prestige_bonus", 0.1) * reputation) * float(chapter_info().get("income_mult", 1))
	m *= 1.0 + Progress.bonus("income")
	if boost_active():
		m *= 2.0
	if is_fever():
		m *= 3.0
	if pet_level >= 5:
		m *= 1.15
	return m


func boost_active() -> bool:
	return boost_until > Time.get_unix_time_from_system()


func boost_left() -> float:
	return maxf(0.0, boost_until - Time.get_unix_time_from_system())


func exp_needed() -> float:
	return round(bal("exp_base", 8) * pow(bal("exp_growth", 1.3), level - 1))


# --- món ăn
func dish_info(id: String) -> Dictionary:
	for d: Dictionary in dishes:
		if d["id"] == id:
			return d
	return {}


func dish_price(id: String) -> float:
	var d := dish_info(id)
	var lv: int = maxi(1, int(dish_levels.get(id, 1)))
	var doubles: int = floori((lv - 1) / bal("dish_double_every", 10))
	return float(d["price"]) * (1.0 + bal("dish_mult_per_level", 0.25) * (lv - 1)) * pow(2.0, doubles)


func dish_price_at(id: String, lv: int) -> float:
	var old: int = dish_levels[id]
	dish_levels[id] = lv
	var p := dish_price(id)
	dish_levels[id] = old
	return p


func dish_upgrade_cost(id: String, n: int = 1) -> float:
	var d := dish_info(id)
	return cost_n(float(d["upgrade_base"]), int(dish_levels[id]) - 1, n)


func unlocked_dishes() -> Array[String]:
	var out: Array[String] = []
	for d: Dictionary in dishes:
		if int(dish_levels[d["id"]]) > 0:
			out.append(d["id"])
	return out


func random_dish() -> String:
	var list := unlocked_dishes()
	if list.is_empty():
		return dishes[0]["id"]
	# món đặc biệt hôm nay được gọi nhiều hơn
	if randf() < bal("special_order_chance", 0.3):
		return daily_special()
	return list[randi() % list.size()]


## Món đặc biệt hôm nay (đổi mỗi ngày) bán giá x2.
func daily_special() -> String:
	var list := unlocked_dishes()
	if list.is_empty():
		return dishes[0]["id"]
	return list[absi(today().hash()) % list.size()]


## Giá bán thực tế: tính cả món đặc biệt và sự kiện lễ hội.
func dish_sell_price(id: String) -> float:
	var p := dish_price(id)
	if id == daily_special():
		p *= bal("special_mult", 2.0)
	if id == specialty():
		p *= float(chapter_info().get("specialty_mult", 1.5))
	return p * event_price_mult()


## Thời gian nấu thực tế tại một khu (món đắt nấu lâu hơn, bếp và đầu bếp giỏi nấu nhanh hơn).
func cook_time(dish_id: String, area_id: String) -> float:
	var d := dish_info(dish_id)
	var fever_boost: float = 2.0 if is_fever() else 1.0
	return float(d["cook_time"]) / (kitchen_speed(area_id) * staff_speed("chef") * (1.0 + Progress.bonus("cook")) * fever_boost)


# --- bàn
func table_level(area_id: String, i: int) -> int:
	return int(areas[area_id]["tables"][i])


func table_mult(area_id: String, i: int) -> float:
	return 1.0 + bal("table_mult_per_level", 0.2) * maxi(0, table_level(area_id, i) - 1)


func table_mult_at(lv: int) -> float:
	return 1.0 + bal("table_mult_per_level", 0.2) * maxi(0, lv - 1)


func table_tier(area_id: String, i: int) -> int:
	var fixed: int = int(area_info(area_id).get("table_tier", 0))
	if fixed > 0:
		return fixed
	var lv := table_level(area_id, i)
	if lv >= int(bal("table_tier3_level", 25)):
		return 3
	if lv >= int(bal("table_tier2_level", 10)):
		return 2
	return 1


func table_upgrade_cost(area_id: String, i: int, n: int = 1) -> float:
	var base: float = bal("table_upgrade_base") * float(area_info(area_id)["upgrade_mult"])
	return cost_n(base, table_level(area_id, i), n)


func tables_unlocked(area_id: String) -> int:
	var n: int = 0
	for lv: int in areas[area_id]["tables"]:
		if lv > 0:
			n += 1
	return n


func table_unlock_cost(area_id: String) -> float:
	var a := area_info(area_id)
	var extra: int = maxi(0, tables_unlocked(area_id) - int(a["start_tables"]))
	return floor(float(a["table_unlock_base"]) * cost_mult() * pow(float(a["table_unlock_mul"]), extra))


# --- bếp & quầy
func kitchen_speed(area_id: String) -> float:
	return 1.0 + bal("kitchen_speed_per_level", 0.1) * (int(areas[area_id]["kitchen"]) - 1)


func kitchen_speed_at(lv: int) -> float:
	return 1.0 + bal("kitchen_speed_per_level", 0.1) * (lv - 1)


func kitchen_upgrade_cost(area_id: String, n: int = 1) -> float:
	var base: float = bal("kitchen_upgrade_base") * float(area_info(area_id)["upgrade_mult"])
	return cost_n(base, int(areas[area_id]["kitchen"]), n)


func cashier_speed(area_id: String) -> float:
	return cashier_speed_at(int(areas[area_id]["cashier"]))


func cashier_speed_at(lv: int) -> float:
	return 1.0 + bal("cashier_speed_per_level", 0.15) * (lv - 1)


func cashier_upgrade_cost(area_id: String, n: int = 1) -> float:
	var base: float = bal("cashier_upgrade_base") * float(area_info(area_id)["upgrade_mult"])
	return cost_n(base, int(areas[area_id]["cashier"]), n)


func pay_time(area_id: String) -> float:
	var crew: float = maxf(1.0, staff_count("cashier"))
	return bal("pay_time", 1.4) / (cashier_speed(area_id) * staff_speed("cashier") * crew)


func tip_chance(area_id: String) -> float:
	return bal("tip_chance", 0.25) + bal("cashier_tip_per_level", 0.005) * (int(areas[area_id]["cashier"]) - 1) \
			+ Progress.bonus("tip")


# --- phòng trọ
func room_level(area_id: String, i: int) -> int:
	return int(areas[area_id]["rooms"][i])


func room_rent(area_id: String, i: int) -> float:
	return room_rent_at(area_id, room_level(area_id, i))


func room_rent_at(area_id: String, lv: int) -> float:
	var r: Dictionary = area_info(area_id)["room"]
	return float(r["rent"]) * (1.0 + float(r["rent_per_level"]) * maxi(0, lv - 1))


func room_upgrade_cost(area_id: String, i: int, n: int = 1) -> float:
	return cost_n(bal("room_upgrade_base"), room_level(area_id, i), n)


func rooms_unlocked(area_id: String) -> int:
	var n: int = 0
	for lv: int in areas[area_id]["rooms"]:
		if lv > 0:
			n += 1
	return n


func room_unlock_cost(area_id: String) -> float:
	var a := area_info(area_id)
	var r: Dictionary = a["room"]
	var extra: int = maxi(0, rooms_unlocked(area_id) - int(a["start_rooms"]))
	return floor(float(r["unlock_base"]) * cost_mult() * pow(float(r["unlock_mul"]), extra))


# --- nhân viên
func staff_count(id: String) -> int:
	if not staff.has(id):
		return 0
	return int(staff[id]["count"])


func staff_level(id: String) -> int:
	if not staff.has(id):
		return 1
	return int(staff[id]["level"])


func staff_speed(id: String) -> float:
	return staff_speed_at(id, staff_level(id))


func staff_speed_at(id: String, lv: int) -> float:
	return 1.0 + float(staff_data[id]["speed_per_level"]) * (lv - 1)


func hire_cost(id: String) -> float:
	var s: Dictionary = staff_data[id]
	var extra: int = maxi(0, staff_count(id) - int(s["start_count"]))
	return floor(float(s["hire_base"]) * cost_mult() * pow(float(s["hire_mul"]), extra))


func staff_upgrade_cost(id: String, n: int = 1) -> float:
	return cost_n(float(staff_data[id]["upgrade_base"]), staff_level(id), n)


func staff_unlocked(id: String) -> bool:
	return level >= int(staff_data[id]["unlock_level"])


func offline_hour_cost() -> float:
	var steps: int = offline_hours - int(bal("offline_base_hours", 2))
	return floor(bal("offline_hour_cost_base") * cost_mult() * pow(bal("offline_hour_cost_mul"), steps))


# --- khu & trang trí
func satisfaction(area_id: String) -> float:
	var total: float = 0.0
	var dec: Dictionary = areas[area_id]["decor"]
	for k: String in dec:
		total += float(decor_data[k]["bonus"]) * int(dec[k])
	return total


func decor_max(area_id: String, kind: String) -> int:
	var slots: Dictionary = area_info(area_id).get("decor_slots", {})
	return (slots.get(kind, []) as Array).size()


func decor_count(area_id: String, kind: String) -> int:
	return int(areas[area_id]["decor"].get(kind, 0))


func decor_cost(area_id: String, kind: String) -> float:
	var d: Dictionary = decor_data[kind]
	var m: float = float(area_info(area_id).get("decor_cost_mult", 1.0))
	return floor(float(d["cost"]) * m * cost_mult() * pow(float(d["cost_mul"]), decor_count(area_id, kind)))


func area_unlock_cost(id: String) -> float:
	return floor(float(area_info(id)["unlock_cost"]) * cost_mult())


func manager_cost() -> float:
	return floor(float(staff_data["manager"]["cost"]) * cost_mult())


func spawn_interval(area_id: String) -> float:
	var bonus: float = satisfaction(area_id) + Progress.bonus("spawn")
	var rc: int = staff_count("receptionist")
	if rc > 0:
		bonus += float(staff_data["receptionist"]["spawn_bonus"]) * rc * staff_speed("receptionist")
	if is_evening():
		bonus += bal("evening_spawn_bonus", 0.25)
	var iv: float = maxf(bal("min_spawn_interval", 0.5), bal("base_spawn_interval", 3.0) / (1.0 + bonus))
	if is_fever():
		iv /= 2.5
	return iv / event_spawn_mult()


func patience() -> float:
	var p: float = bal("patience", 30)
	if staff_count("receptionist") > 0:
		p *= 1.0 + float(staff_data["receptionist"]["patience_bonus"])
	return p * (1.0 + Progress.bonus("patience"))


func area_unlocked(id: String) -> bool:
	return areas.has(id) and bool(areas[id]["unlocked"])


# =====================================================================
# Thu chi
# =====================================================================

## Cộng vàng do kinh doanh (áp dụng hệ số thu nhập). Trả về số vàng thực nhận.
func earn(amount: float, world_pos: Vector2 = Vector2.ZERO, show_fx: bool = true) -> float:
	var v: float = amount * income_mult()
	add_gold(v, true)
	if show_fx:
		coin_fx.emit(world_pos, v)
	return v


## Cộng vàng thẳng (thưởng, offline...). counts_as_income: tính vào nhiệm vụ & đo tốc độ.
func add_gold(v: float, counts_as_income: bool = false) -> void:
	gold += v
	run_gold += v
	lifetime_gold += v
	if counts_as_income:
		_track_rate(v)
		add_daily("earn", v)
	gold_changed.emit(gold)


func add_diamonds(n: int) -> void:
	diamonds += n
	diamonds_changed.emit(diamonds)


func can_afford(cost: float) -> bool:
	return gold + 0.001 >= cost


func try_spend(cost: float) -> bool:
	if not can_afford(cost):
		toast.emit("Không đủ vàng!")
		return false
	gold -= cost
	gold_changed.emit(gold)
	return true


func try_spend_diamonds(n: int) -> bool:
	if diamonds < n:
		toast.emit("Không đủ kim cương!")
		return false
	diamonds -= n
	diamonds_changed.emit(diamonds)
	return true


func add_xp(v: float) -> void:
	xp += v
	while xp >= exp_needed():
		xp -= exp_needed()
		level += 1
		var unlocks := _unlocks_for_level(level)
		add_diamonds(int(bal("level_up_diamonds", 2)))
		leveled_up.emit(level, unlocks)
		state_changed.emit()
	exp_changed.emit(xp, exp_needed())


## Mở khóa món theo cấp quán và trả danh sách mô tả những gì mới mở.
func _unlocks_for_level(lv: int) -> Array:
	var out: Array = []
	for d: Dictionary in dishes:
		if int(d["unlock_level"]) == lv and int(dish_levels[d["id"]]) == 0:
			dish_levels[d["id"]] = 1
			out.append({"icon": "dish_" + str(d["id"]), "text": "Món mới: " + str(d["name"])})
	for id: String in staff_data:
		if int(staff_data[id]["unlock_level"]) == lv and lv > 1:
			out.append({"icon": staff_data[id]["sprite"], "text": "Nhân viên mới: " + str(staff_data[id]["name"])})
	for a: Dictionary in areas_data:
		if int(a["unlock_level"]) == lv and lv > 1:
			out.append({"icon": a["thumb"], "text": "Có thể mở khu: " + str(a["name"])})
	return out


## Khách đã trả tiền xong.
func customer_served(dish_id: String) -> void:
	total_customers += 1
	add_daily("serve", 1)
	run_customers += 1
	_progress_orders(dish_id)
	add_xp(float(dish_info(dish_id).get("exp", 1)))


func request_coin_fx(world_pos: Vector2, amount: float) -> void:
	coin_fx.emit(world_pos, amount)


func show_toast(text: String) -> void:
	toast.emit(text)


func fire_tutorial(event_id: String) -> void:
	tutorial_event.emit(event_id)


func notify_state() -> void:
	state_changed.emit()


func notify_area(area_id: String) -> void:
	area_changed.emit(area_id)


func _bought(kind: String) -> void:
	upgrades_bought += 1
	add_daily("upgrade", 1)
	purchased.emit(kind)
	state_changed.emit()


# =====================================================================
# Hành động mua bán
# =====================================================================

func unlock_table(area_id: String, i: int) -> bool:
	if table_level(area_id, i) > 0:
		return false
	if not try_spend(table_unlock_cost(area_id)):
		return false
	areas[area_id]["tables"][i] = 1
	_bought("table")
	area_changed.emit(area_id)
	fire_tutorial("unlock_table")
	return true


func upgrade_table(area_id: String, i: int, n: int = 1) -> bool:
	if not try_spend(table_upgrade_cost(area_id, i, n)):
		return false
	areas[area_id]["tables"][i] = table_level(area_id, i) + n
	_bought("table")
	return true


func upgrade_kitchen(area_id: String, n: int = 1) -> bool:
	if not try_spend(kitchen_upgrade_cost(area_id, n)):
		return false
	areas[area_id]["kitchen"] = int(areas[area_id]["kitchen"]) + n
	_bought("kitchen")
	return true


func upgrade_cashier(area_id: String, n: int = 1) -> bool:
	if not try_spend(cashier_upgrade_cost(area_id, n)):
		return false
	areas[area_id]["cashier"] = int(areas[area_id]["cashier"]) + n
	_bought("cashier")
	return true


func unlock_room(area_id: String, i: int) -> bool:
	if room_level(area_id, i) > 0:
		return false
	if not try_spend(room_unlock_cost(area_id)):
		return false
	areas[area_id]["rooms"][i] = 1
	_bought("room")
	area_changed.emit(area_id)
	return true


func upgrade_room(area_id: String, i: int, n: int = 1) -> bool:
	if not try_spend(room_upgrade_cost(area_id, i, n)):
		return false
	areas[area_id]["rooms"][i] = room_level(area_id, i) + n
	_bought("room")
	return true


func upgrade_dish(id: String, n: int = 1) -> bool:
	if int(dish_levels[id]) <= 0:
		return false
	if not try_spend(dish_upgrade_cost(id, n)):
		return false
	dish_levels[id] = int(dish_levels[id]) + n
	_bought("dish")
	fire_tutorial("upgrade_dish")
	return true


func hire(id: String) -> bool:
	if not staff_unlocked(id):
		toast.emit("Cần cấp quán %d" % int(staff_data[id]["unlock_level"]))
		return false
	if staff_count(id) >= int(staff_data[id]["max_count"]):
		return false
	if not try_spend(hire_cost(id)):
		return false
	staff[id]["count"] = staff_count(id) + 1
	_bought("hire")
	fire_tutorial("hire")
	return true


func upgrade_staff(id: String, n: int = 1) -> bool:
	if staff_count(id) <= 0:
		toast.emit("Hãy thuê nhân viên trước")
		return false
	if not try_spend(staff_upgrade_cost(id, n)):
		return false
	staff[id]["level"] = staff_level(id) + n
	_bought("staff")
	fire_tutorial("hire")
	return true


func hire_manager() -> bool:
	if manager:
		return false
	if not staff_unlocked("manager"):
		toast.emit("Cần cấp quán %d" % int(staff_data["manager"]["unlock_level"]))
		return false
	if not try_spend(manager_cost()):
		return false
	manager = true
	_bought("manager")
	return true


func buy_offline_hour() -> bool:
	if offline_hours >= int(bal("offline_max_hours", 12)):
		return false
	if not try_spend(offline_hour_cost()):
		return false
	offline_hours += 1
	_bought("offline")
	return true


func unlock_area(id: String) -> bool:
	var a := area_info(id)
	if area_unlocked(id):
		return false
	if level < int(a["unlock_level"]):
		toast.emit("Cần cấp quán %d" % int(a["unlock_level"]))
		return false
	if not try_spend(area_unlock_cost(id)):
		return false
	areas[id]["unlocked"] = true
	_bought("area")
	area_changed.emit(id)
	toast.emit("Đã mở khu " + str(a["name"]) + "!")
	return true


func buy_decor(area_id: String, kind: String) -> bool:
	if decor_count(area_id, kind) >= decor_max(area_id, kind):
		return false
	if not try_spend(decor_cost(area_id, kind)):
		return false
	areas[area_id]["decor"][kind] = decor_count(area_id, kind) + 1
	_bought("decor")
	area_changed.emit(area_id)
	return true


func set_current_area(id: String) -> void:
	if not area_unlocked(id) or id == current_area:
		return
	current_area = id
	current_area_changed.emit(id)


func set_setting(key: String, value: bool) -> void:
	settings[key] = value
	settings_changed.emit()


# =====================================================================
# Offline
# =====================================================================

## Tính vàng offline theo tốc độ thực tế của quán.
func compute_offline(seconds: float) -> float:
	var t: float = minf(seconds, offline_cap_hours() * 3600.0)
	var factor: float = 1.0 if manager else bal("offline_rate_no_manager", 0.4)
	# x2 đã hết hạn thì không tính vào tốc độ offline
	var rate: float = income_rate()
	if not boost_active() and measured_rate > 0.0 and boost_until > 0.0:
		rate = minf(rate, measured_rate)
	return floor(rate * t * factor)


## Giờ offline tối đa, tính cả nghiên cứu "Két sắt lớn".
func offline_cap_hours() -> int:
	return offline_hours + int(Progress.bonus("offline"))


func claim_offline(double: bool) -> bool:
	if pending_offline <= 0.0:
		return false
	var amount := pending_offline
	if double:
		if not try_spend_diamonds(int(bal("offline_x2_diamonds", 5))):
			return false
		amount *= 2.0
	pending_offline = 0.0
	pending_offline_seconds = 0.0
	add_gold(amount)
	return true


# =====================================================================
# Cửa hàng kim cương
# =====================================================================

func shop_gold_amount(item: Dictionary) -> float:
	return floor(maxf(float(item.get("min_gold", 0)), income_rate() * 60.0 * float(item.get("minutes", 1))))


func shop_buy(item: Dictionary) -> bool:
	if not try_spend_diamonds(int(item["cost"])):
		return false
	match str(item["type"]):
		"boost":
			var now: float = Time.get_unix_time_from_system()
			boost_until = maxf(now, boost_until) + float(item["minutes"]) * 60.0
			toast.emit("Thu nhập x2 đã bật!")
		"rush":
			rush_requested.emit(int(item["count"]))
			toast.emit("Khách đang kéo đến!")
		"gold":
			var g := shop_gold_amount(item)
			add_gold(g)
			toast.emit("+" + NumberFormat.fmt(g) + " vàng")
	purchased.emit("shop")
	state_changed.emit()
	return true


# =====================================================================
# Nhiệm vụ, thành tích, đăng nhập
# =====================================================================

func today() -> String:
	return Time.get_date_string_from_system()


func seconds_to_midnight() -> float:
	var t: Dictionary = Time.get_time_dict_from_system()
	return 86400.0 - (int(t["hour"]) * 3600 + int(t["minute"]) * 60 + int(t["second"]))


func _check_daily_reset() -> void:
	var d := today()
	if d > str(daily.get("date", "")):
		daily = {"date": d, "progress": {}, "claimed": {}}
		quests_changed.emit()


func add_daily(stat: String, v: float) -> void:
	var prog: Dictionary = daily.get("progress", {})
	prog[stat] = float(prog.get(stat, 0.0)) + v
	daily["progress"] = prog
	quests_changed.emit()


func daily_progress(q: Dictionary) -> float:
	return float((daily.get("progress", {}) as Dictionary).get(q["stat"], 0.0))


func daily_claimed(q: Dictionary) -> bool:
	return bool((daily.get("claimed", {}) as Dictionary).get(q["id"], false))


func daily_gold_reward(q: Dictionary) -> float:
	return floor(float(q["gold"]) * pow(float(quest_data.get("daily_gold_growth", 1.25)), level - 1))


func claim_daily(q: Dictionary) -> bool:
	if daily_claimed(q) or daily_progress(q) < float(q["goal"]):
		return false
	var claimed: Dictionary = daily.get("claimed", {})
	claimed[q["id"]] = true
	daily["claimed"] = claimed
	add_gold(daily_gold_reward(q))
	add_diamonds(int(q["diamonds"]))
	quests_changed.emit()
	return true


func stat_value(stat: String) -> float:
	match stat:
		"lifetime_gold":
			return lifetime_gold
		"total_customers":
			return float(total_customers)
		"dishes_unlocked":
			return float(unlocked_dishes().size())
		"level":
			return float(level)
	return 0.0


func achievement_tier(a: Dictionary) -> int:
	return int(achievements.get(a["id"], 0))


func achievement_claimable(a: Dictionary) -> bool:
	var t := achievement_tier(a)
	var tiers: Array = a["tiers"]
	return t < tiers.size() and stat_value(a["stat"]) >= float(tiers[t])


func claim_achievement(a: Dictionary) -> bool:
	if not achievement_claimable(a):
		return false
	var t := achievement_tier(a)
	achievements[a["id"]] = t + 1
	add_diamonds(int(a["diamonds"][t]))
	quests_changed.emit()
	return true


func login_claimable() -> bool:
	return today() > str(login.get("last", ""))


func login_index() -> int:
	return int(login.get("day", 0)) % 7


func claim_login() -> bool:
	if not login_claimable():
		return false
	var rewards: Array = quest_data["login"]
	var r: Dictionary = rewards[login_index()]
	login["day"] = int(login.get("day", 0)) + 1
	login["last"] = today()
	if int(r["gold"]) > 0:
		add_gold(float(r["gold"]))
	if int(r["diamonds"]) > 0:
		add_diamonds(int(r["diamonds"]))
	quests_changed.emit()
	return true


func quests_claimable_count() -> int:
	var n: int = 0
	for q: Dictionary in quest_data["daily"]:
		if not daily_claimed(q) and daily_progress(q) >= float(q["goal"]):
			n += 1
	for a: Dictionary in quest_data["achievements"]:
		if achievement_claimable(a):
			n += 1
	if login_claimable():
		n += 1
	return n


# =====================================================================
# Tái khởi nghiệp
# =====================================================================

## Chỉ ở chương cuối: các chương trước dùng "Sang chương mới" thay cho bán quán.
func can_prestige() -> bool:
	return is_last_chapter() and level >= int(bal("prestige_level", 20))


func prestige_gain() -> int:
	return maxi(1, floori(sqrt(run_gold / bal("prestige_divisor", 100000))))


func do_prestige() -> bool:
	if not can_prestige():
		return false
	var gain := prestige_gain()
	reputation += gain
	var keep_diamonds := diamonds
	new_game(true)
	diamonds = keep_diamonds
	world_reset.emit()
	return true


func reset_everything() -> void:
	new_game(false)
	world_reset.emit()


# =====================================================================
# Sự kiện ngẫu nhiên: giờ cao điểm, lễ hội, khách sộp, mưa tiền boa
# =====================================================================

func _update_event(delta: float) -> void:
	if not current_event.is_empty():
		event_left -= delta
		if event_left <= 0.0:
			current_event = {}
			event_ended.emit()
			_event_wait = randf_range(float(events_data.get("interval_min", 90)), float(events_data.get("interval_max", 150))) \
					* maxf(0.3, 1.0 - Progress.bonus("event"))
		return
	_event_wait -= delta
	if _event_wait <= 0.0:
		start_event("")


## Bắt đầu một sự kiện (id rỗng = ngẫu nhiên).
func start_event(id: String) -> void:
	var list: Array = events_data.get("list", [])
	if list.is_empty():
		return
	var ev: Dictionary = list[randi() % list.size()]
	for e: Dictionary in list:
		if e["id"] == id:
			ev = e
	current_event = ev
	event_left = float(ev["duration"])
	event_started.emit(ev)
	toast.emit(str(ev["name"]) + " " + str(ev["desc"]))


func event_active(id: String) -> bool:
	return not current_event.is_empty() and current_event["id"] == id


func event_spawn_mult() -> float:
	return float(current_event.get("spawn_mult", 1.0))


func event_price_mult() -> float:
	return float(current_event.get("price_mult", 1.0))


func golden_mult() -> float:
	return float(events_data.get("golden_mult", 10.0)) + Progress.bonus("golden")


# =====================================================================
# Đơn đặt tiệc: phục vụ đủ số phần một món để nhận thưởng lớn
# =====================================================================

func _fill_orders() -> void:
	var slots: int = int(orders_data.get("slots", 3))
	while orders.size() < slots:
		orders.append(_new_order())


func _new_order() -> Dictionary:
	var list := unlocked_dishes()
	var used: Array = []
	for o: Dictionary in orders:
		used.append(o["dish"])
	var choices: Array = []
	for d in list:
		if not used.has(d):
			choices.append(d)
	if choices.is_empty():
		choices = list
	var themes: Array = orders_data.get("themes", ["Tiệc"])
	var need: int = int(round(float(orders_data.get("base_count", 6)) + float(orders_data.get("count_per_level", 0.5)) * level))
	return {"theme": str(themes[randi() % themes.size()]), "dish": str(choices[randi() % choices.size()]),
		"need": need, "have": 0}


func _progress_orders(dish_id: String) -> void:
	var changed := false
	for o: Dictionary in orders:
		if o["dish"] == dish_id and int(o["have"]) < int(o["need"]):
			o["have"] = int(o["have"]) + 1
			changed = true
	if changed:
		orders_changed.emit()


func order_reward_gold() -> float:
	return floor(maxf(float(orders_data.get("min_gold", 300)), income_rate() * 60.0 * float(orders_data.get("reward_minutes", 4.0))) \
			* (1.0 + Progress.bonus("order")))


func order_ready(i: int) -> bool:
	var o: Dictionary = orders[i]
	return int(o["have"]) >= int(o["need"])


func claim_order(i: int) -> bool:
	if i < 0 or i >= orders.size() or not order_ready(i):
		return false
	add_gold(order_reward_gold(), true)
	add_diamonds(randi_range(int(orders_data.get("diamonds_min", 1)), int(orders_data.get("diamonds_max", 3))))
	add_daily("order", 1)
	orders[i] = _new_order()
	orders_changed.emit()
	purchased.emit("order")
	return true


func skip_order(i: int) -> bool:
	if not try_spend_diamonds(int(orders_data.get("skip_diamonds", 3))):
		return false
	orders[i] = _new_order()
	orders_changed.emit()
	return true


func orders_ready_count() -> int:
	var n: int = 0
	for i in orders.size():
		if order_ready(i):
			n += 1
	return n


# =====================================================================
# Chương: mỗi chương là một quán ở thành phố mới, thu nhập cao hơn
# =====================================================================

func chapter_info(i: int = -1) -> Dictionary:
	var idx: int = chapter if i < 0 else i
	if chapters_data.is_empty():
		return {}
	return chapters_data[clampi(idx, 0, chapters_data.size() - 1)]


func is_last_chapter() -> bool:
	return chapter >= chapters_data.size() - 1


func next_chapter_level() -> int:
	return int(chapter_info().get("next_level", 0))


## Sang chương mới khi đạt đủ 3 sao mục tiêu chương.
func can_advance_chapter() -> bool:
	return not is_last_chapter() and Progress.stars() >= 3


## Sang chương mới: quán mới ở thành phố mới, giữ kim cương, Danh tiếng, thành tích.
func advance_chapter() -> bool:
	if not can_advance_chapter():
		return false
	var keep_diamonds := diamonds
	reputation += prestige_gain()
	chapter += 1
	new_game(true)
	diamonds = keep_diamonds + 20
	just_advanced = true
	world_reset.emit()
	return true


# =====================================================================
# Đặc sản, chống gian lận giờ, chuyển đổi save, kiểm tra dữ liệu
# =====================================================================

## Món đặc sản của chương hiện tại (bán giá cao hơn).
func specialty() -> String:
	return str(chapter_info().get("specialty", ""))


## Phát hiện đồng hồ bị chỉnh lùi: không cho nhận quà theo ngày / offline từ thời gian giả.
func _watch_clock() -> void:
	var now: float = Time.get_unix_time_from_system()
	if now + 300.0 < max_time_seen:
		if not time_tampered:
			time_tampered = true
			toast.emit("Đồng hồ máy bị chỉnh lùi, quà theo ngày tạm khóa")
		return
	time_tampered = false
	max_time_seen = maxf(max_time_seen, now)


func clock_ok() -> bool:
	return Time.get_unix_time_from_system() + 300.0 >= max_time_seen


## Nâng file lưu cũ lên định dạng mới, từng bước theo version.
func migrate_save(d: Dictionary) -> Dictionary:
	var v: int = int(d.get("version", 1))
	if v < 2:
		# v1 -> v2: thêm chương, đơn tiệc, tiến trình; chưa có hướng dẫn tính năng mới
		if not d.has("chapter"):
			d["chapter"] = 0
		d["tutorial2_done"] = false
		v = 2
	d["version"] = v
	return d


## Kiểm tra liên kết giữa các file data. Trả về danh sách lỗi (rỗng = ổn).
func validate_data() -> Array[String]:
	var errs: Array[String] = data_errors.duplicate()
	var dish_ids: Array = []
	for dd: Dictionary in dishes:
		dish_ids.append(dd["id"])
		if not ResourceLoader.exists("res://assets/sprites/dish_%s.svg" % dd["id"]) and Sprites.tex("dish_" + str(dd["id"])) == null:
			errs.append("Thiếu ảnh món: " + str(dd["id"]))
	for c: Dictionary in chapters_data:
		if not dish_ids.has(str(c.get("specialty", ""))):
			errs.append("Đặc sản không tồn tại ở chương " + str(c["id"]))
	for chap: Array in Progress.goals_data.get("chapters", []):
		for g: Dictionary in chap:
			if str(g["type"]) == "dish" and not dish_ids.has(str(g["id"])):
				errs.append("Mục tiêu dùng món không tồn tại: " + str(g["id"]))
	for c: Dictionary in Progress.card_list():
		if not ResourceLoader.exists("res://assets/sprites/%s.svg" % c["sprite"]):
			errs.append("Thiếu ảnh thẻ: " + str(c["sprite"]))
	return errs


# =====================================================================
# Phòng mở rộng (mỗi khu có thêm phòng nối dài, mở bằng vàng)
# =====================================================================

func wings(area_id: String) -> Array:
	return area_info(area_id).get("wings", [])


func wing_info(area_id: String, wing_id: String) -> Dictionary:
	for w: Dictionary in wings(area_id):
		if w["id"] == wing_id:
			return w
	return {}


## Giá trị lưu: true (đã mở) hoặc mốc thời gian unix xây xong (đang thi công).
func wing_unlocked(area_id: String, wing_id: String) -> bool:
	if wing_id.is_empty():
		return true
	var v: Variant = (areas[area_id].get("wings", {}) as Dictionary).get(wing_id, false)
	if v is bool:
		return v
	return Time.get_unix_time_from_system() >= float(v)


func wing_building(area_id: String, wing_id: String) -> bool:
	var v: Variant = (areas[area_id].get("wings", {}) as Dictionary).get(wing_id, false)
	return not (v is bool) and Time.get_unix_time_from_system() < float(v)


func wing_build_left(area_id: String, wing_id: String) -> float:
	var v: Variant = (areas[area_id].get("wings", {}) as Dictionary).get(wing_id, false)
	if v is bool:
		return 0.0
	return maxf(0.0, float(v) - Time.get_unix_time_from_system())


## Chạm công trường: xây nhanh thêm vài giây.
func speed_build(area_id: String, wing_id: String, seconds: float) -> void:
	var wd: Dictionary = areas[area_id].get("wings", {})
	var v: Variant = wd.get(wing_id, false)
	if v is bool:
		return
	wd[wing_id] = float(v) - seconds


func build_skip_cost(area_id: String, wing_id: String) -> int:
	return maxi(1, ceili(wing_build_left(area_id, wing_id) / 60.0) * int(bal("build_skip_diamonds_per_min", 1)))


func skip_build(area_id: String, wing_id: String) -> bool:
	if not wing_building(area_id, wing_id):
		return false
	if not try_spend_diamonds(build_skip_cost(area_id, wing_id)):
		return false
	(areas[area_id]["wings"] as Dictionary)[wing_id] = Time.get_unix_time_from_system() - 0.1
	return true


func wing_cost(area_id: String, wing_id: String) -> float:
	return floor(float(wing_info(area_id, wing_id).get("cost", 0)) * cost_mult())


func table_wing(area_id: String, i: int) -> String:
	var tw: Array = area_info(area_id).get("table_wing", [])
	return str(tw[i]) if i < tw.size() else ""


func bed_wing(area_id: String, i: int) -> String:
	var bw: Array = area_info(area_id).get("bed_wing", [])
	return str(bw[i]) if i < bw.size() else ""


## Ô bàn có dùng được không (thuộc sảnh gốc hoặc phòng đã mở).
func table_slot_open(area_id: String, i: int) -> bool:
	return wing_unlocked(area_id, table_wing(area_id, i))


func bed_slot_open(area_id: String, i: int) -> bool:
	return wing_unlocked(area_id, bed_wing(area_id, i))


func wing_price_mult(area_id: String, i: int) -> float:
	var w := table_wing(area_id, i)
	if w.is_empty():
		return 1.0
	return float(wing_info(area_id, w).get("price_mult", 1.0))


func can_unlock_wing(area_id: String, wing_id: String) -> bool:
	var w := wing_info(area_id, wing_id)
	return area_unlocked(area_id) and not wing_unlocked(area_id, wing_id) and not wing_building(area_id, wing_id) \
			and level >= int(w.get("unlock_level", 1)) \
			and can_afford(wing_cost(area_id, wing_id))


func unlock_wing(area_id: String, wing_id: String) -> bool:
	var w := wing_info(area_id, wing_id)
	if w.is_empty() or wing_unlocked(area_id, wing_id) or wing_building(area_id, wing_id):
		return false
	if level < int(w.get("unlock_level", 1)):
		toast.emit("Cần cấp quán %d" % int(w["unlock_level"]))
		return false
	if not try_spend(wing_cost(area_id, wing_id)):
		return false
	var wd: Dictionary = areas[area_id].get("wings", {})
	# bắt đầu thi công: xong sau build_seconds (chạm công trường để xây nhanh hơn)
	wd[wing_id] = Time.get_unix_time_from_system() + float(w.get("build_seconds", 30))
	areas[area_id]["wings"] = wd
	_bought("wing")
	area_changed.emit(area_id)
	toast.emit("Bắt đầu thi công: " + str(w["name"]) + "! Chạm công trường để xây nhanh")
	return true


# =====================================================================
# Combo khi chạm khách liên tục
# =====================================================================

var combo: int = 0
var _combo_last: int = -100000


## Ghi nhận một lần chạm khách. Chạm trong vòng 1.6 giây thì combo tăng. Trả về số combo.
func register_combo(world_pos: Vector2) -> int:
	var now := Time.get_ticks_msec()
	combo = combo + 1 if now - _combo_last <= 1600 else 1
	_combo_last = now
	combo_hit.emit(combo, world_pos)
	if combo == 12 or combo == 28 or combo == 50:
		start_fever(20.0)
		AudioManager.play("celebrate")
		AudioManager.vibrate(40)
		show_toast("🔥 COMBO ĐẠT x%d! KÍCH HOẠT GIỜ VÀNG FEVER THẦN TỐC x3! 🔥" % combo)
	return combo


# =====================================================================
# Ngày và đêm (chu kỳ rút gọn): sáng -> trưa -> hoàng hôn -> tối -> đêm
# =====================================================================

var day_t: float = 60.0


## 0..1 trong một ngày.
func day_phase() -> float:
	return day_t / maxf(1.0, bal("day_cycle_seconds", 480))


func day_name() -> String:
	var p := day_phase()
	if p < 0.12:
		return "Bình minh"
	if p < 0.5:
		return "Ban ngày"
	if p < 0.62:
		return "Hoàng hôn"
	if p < 0.88:
		return "Buổi tối"
	return "Đêm khuya"


## Buổi tối là giờ ăn tối: khách đến đông hơn.
func is_evening() -> bool:
	var p := day_phase()
	return p >= 0.62 and p < 0.88


## Độ tối 0 (ban ngày) .. 1 (đêm), chuyển mượt.
func night_factor() -> float:
	var p := day_phase()
	if p < 0.12:
		return lerpf(0.7, 0.0, p / 0.12)
	if p < 0.5:
		return 0.0
	if p < 0.62:
		return lerpf(0.0, 0.55, (p - 0.5) / 0.12)
	if p < 0.88:
		return lerpf(0.55, 1.0, (p - 0.62) / 0.26)
	return lerpf(1.0, 0.7, (p - 0.88) / 0.12)


func day_tint() -> Color:
	var p := day_phase()
	var n := night_factor()
	var dusk := Color(1.0, 0.86, 0.72)
	var night := Color(0.52, 0.56, 0.82)
	if p >= 0.5 and p < 0.66:
		return Color.WHITE.lerp(dusk, n / 0.55)
	return Color.WHITE.lerp(dusk, minf(1.0, n * 1.5)).lerp(night, maxf(0.0, n - 0.3) / 0.7)
