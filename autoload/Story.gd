extends Node
## Cốt truyện "Quán Trọ Của Bà": cảnh hội thoại theo mốc, thử thách có giờ của Giám đốc Phát,
## khách quen có tên với độ thân thiết. Main hiện cảnh khi màn hình rảnh.

signal changed

var data: Dictionary = {}
var seen: Dictionary = {}              # id cảnh -> true
var challenge_won: Dictionary = {}     # "chương" -> true
var friendship: Dictionary = {}        # id khách quen -> số lần phục vụ
var pending: Array[String] = []        # cảnh chờ hiện
var last_rewards: Array = []           # phần thưởng hiện sau cảnh

# thử thách đang chạy (không lưu: thoát game là huỷ, lần sau Phát thách lại)
var challenge: Dictionary = {}
var _retry_t: float = 0.0
var _check_t: float = 0.0
var _cust_samples: Array[int] = []
var _sample_t: float = 0.0
var enabled: bool = true   # tắt khi chạy công cụ kiểm thử


func _ready() -> void:
	data = GameState._load_json("story.json")
	GameState.world_reset.connect(_on_world_reset)


func reset() -> void:
	seen = {}
	challenge_won = {}
	friendship = {}
	pending.clear()
	challenge = {}
	changed.emit()


func to_dict() -> Dictionary:
	return {"seen": seen, "won": challenge_won, "friends": friendship}


func from_dict(d: Dictionary) -> void:
	reset()
	for key in ["seen", "won", "friends"]:
		var v: Variant = d.get(key, {})
		if v is Dictionary:
			var target: Dictionary = seen if key == "seen" else (challenge_won if key == "won" else friendship)
			for k: String in v:
				target[k] = v[k]


func _on_world_reset() -> void:
	challenge = {}
	pending.clear()
	_cust_samples.clear()


# =====================================================================
# Kích hoạt cảnh theo mốc
# =====================================================================

func chapter_no() -> int:
	return GameState.chapter + 1


func has_scene(id: String) -> bool:
	return (data.get("scenes", {}) as Dictionary).has(id) or id.begins_with("reg:")


func _queue(id: String, once: bool = true) -> void:
	if not has_scene(id) or pending.has(id):
		return
	if once and seen.get(id, false):
		return
	pending.append(id)


func _process(delta: float) -> void:
	if not enabled:
		return
	_sample_t += delta
	if _sample_t >= 5.0:
		_sample_t = 0.0
		_cust_samples.append(GameState.run_customers)
		while _cust_samples.size() > 13:
			_cust_samples.remove_at(0)
	_update_challenge(delta)
	_check_t += delta
	if _check_t < 0.5:
		return
	_check_t = 0.0
	var g := GameState
	var n := chapter_no()
	var st := Progress.stars()
	if g.chapter == 0:
		_queue("intro")
		if g.total_customers >= 1:
			_queue("first_serve")
	else:
		_queue("ch%d_start" % n)
	if g.level >= 3:
		_queue("lv3")
	if st >= 1:
		_queue("ch%d_star1" % n)
		# Phát thách đấu sau mốc 1 sao, thua thì một lúc sau thách lại
		if not challenge_won.get(str(n), false) and challenge.is_empty() and seen.get("ch%d_star1" % n, false):
			_retry_t -= 0.5
			if _retry_t <= 0.0:
				_queue("ch%d_challenge" % n, false)
	if st >= 2:
		_queue("ch%d_star2" % n)
	if st >= 3:
		_queue("finale" if g.is_last_chapter() else "ch%d_end" % n)


func has_pending() -> bool:
	return not pending.is_empty()


func pop_pending() -> String:
	return pending.pop_front() if not pending.is_empty() else ""


## Danh sách lời thoại của một cảnh (cảnh khách quen tạo động).
func scene_lines(id: String) -> Array:
	if id.begins_with("reg:"):
		var parts := id.split(":")
		var r := regular_info(parts[1])
		var k: int = int(parts[2])
		return [{"who": parts[1], "text": str((r["stories"] as Array)[k])},
			{"who": "lan", "text": "Khách quen tặng quà cho quán mình nè chị!"}]
	return (data["scenes"] as Dictionary).get(id, [])


func character(who: String) -> Dictionary:
	var c: Dictionary = (data.get("characters", {}) as Dictionary).get(who, {"name": who, "portrait": "", "color": "#6b4128"})
	if who == "me":
		c = c.duplicate()
		c["name"] = GameState.owner_name
		var p := "portrait_" + GameState.avatar
		c["portrait"] = p if ResourceLoader.exists("res://assets/ui/%s.svg" % p) else GameState.avatar
	return c


## Main gọi khi cảnh kết thúc.
func scene_finished(id: String) -> void:
	seen[id] = true
	if id.ends_with("_challenge"):
		start_challenge()
	changed.emit()


# =====================================================================
# Thử thách của Giám đốc Phát
# =====================================================================

func challenge_info() -> Dictionary:
	var list: Array = data.get("challenges", [])
	return list[clampi(GameState.chapter, 0, list.size() - 1)]


func _customers_per_sec() -> float:
	if _cust_samples.size() < 3:
		return 0.15
	return float(_cust_samples[-1] - _cust_samples[0]) / ((_cust_samples.size() - 1) * 5.0)


func start_challenge() -> void:
	var c := challenge_info()
	var secs: float = float(c["seconds"])
	var target: float
	if str(c["type"]) == "serve":
		target = maxf(float(c["min"]), ceil(_customers_per_sec() * secs * float(c["factor"])))
	else:
		target = maxf(float(c["min"]), floor(GameState.income_rate() * secs * float(c["factor"])))
	challenge = {"type": c["type"], "target": target, "left": secs, "total": secs,
		"start": GameState.run_customers if str(c["type"]) == "serve" else GameState.run_gold}
	GameState.show_toast("Thử thách của Phát bắt đầu!")
	changed.emit()


func challenge_progress() -> float:
	if challenge.is_empty():
		return 0.0
	if str(challenge["type"]) == "serve":
		return float(GameState.run_customers) - float(challenge["start"])
	return GameState.run_gold - float(challenge["start"])


func _update_challenge(delta: float) -> void:
	if challenge.is_empty():
		return
	challenge["left"] = float(challenge["left"]) - delta
	var n := chapter_no()
	if challenge_progress() >= float(challenge["target"]):
		challenge = {}
		challenge_won[str(n)] = true
		_give_challenge_reward()
		_queue("ch%d_win" % n, false)
		changed.emit()
	elif float(challenge["left"]) <= 0.0:
		challenge = {}
		_retry_t = float(data.get("challenge_retry_seconds", 120))
		_queue("ch%d_lose" % n, false)
		changed.emit()


func _give_challenge_reward() -> void:
	var r: Dictionary = data.get("challenge_reward", {})
	var g: float = floor(maxf(500.0 * GameState.cost_mult(), GameState.income_rate() * 60.0 * float(r.get("gold_minutes", 10))))
	GameState.add_gold(g)
	GameState.add_diamonds(int(r.get("diamonds", 15)))
	Progress.research_points += int(r.get("rp", 2))
	Progress.changed.emit()
	last_rewards = [
		{"icon": "coin", "text": "+%s vàng" % NumberFormat.fmt(g)},
		{"icon": "diamond", "text": "+%d kim cương" % int(r.get("diamonds", 15))},
		{"icon": "icon_rp", "text": "+%d Sách nghiên cứu" % int(r.get("rp", 2))},
	]


# =====================================================================
# Khách quen có tên
# =====================================================================

func regulars() -> Array:
	return data.get("regulars", [])


func regular_info(id: String) -> Dictionary:
	for r: Dictionary in regulars():
		if r["id"] == id:
			return r
	return {}


func pick_regular() -> String:
	var list := regulars()
	if list.is_empty():
		return ""
	return str(list[randi() % list.size()]["id"])


func friend_level(id: String) -> int:
	var n: int = int(friendship.get(id, 0))
	var lv: int = 0
	for t: Variant in data.get("regular_thresholds", []):
		if n >= int(t):
			lv += 1
	return lv


func next_threshold(id: String) -> int:
	var n: int = int(friendship.get(id, 0))
	for t: Variant in data.get("regular_thresholds", []):
		if n < int(t):
			return int(t)
	return -1


## Phục vụ xong một khách quen: tăng thân thiết, đủ mốc thì mở chuyện + quà.
func serve_regular(id: String) -> void:
	if id.is_empty():
		return
	var before := friend_level(id)
	friendship[id] = int(friendship.get(id, 0)) + 1
	var after := friend_level(id)
	if after > before:
		var rw: Dictionary = (data["regular_rewards"] as Array)[after - 1]
		last_rewards = []
		if rw.has("diamonds"):
			GameState.add_diamonds(int(rw["diamonds"]))
			last_rewards.append({"icon": "diamond", "text": "+%d kim cương" % int(rw["diamonds"])})
		if rw.has("rp"):
			Progress.research_points += int(rw["rp"])
			last_rewards.append({"icon": "icon_rp", "text": "+%d Sách nghiên cứu" % int(rw["rp"])})
		if rw.has("cards"):
			for cid: Variant in Progress.pull_free(int(rw["cards"])):
				last_rewards.append(Progress._card_reward(str(cid)))
		Progress.changed.emit()
		_queue("reg:%s:%d" % [id, after - 1])
	changed.emit()


## Lời nói ngẫu nhiên của khách trong quán.
func chatter(kind: String) -> String:
	var pool: Array = (data.get("chatter", {}) as Dictionary).get(kind, [])
	if pool.is_empty():
		return ""
	return str(pool[randi() % pool.size()])
