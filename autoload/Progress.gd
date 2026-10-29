extends Node
## Tiến trình dài hạn: mục tiêu chương (3 sao), cây nghiên cứu, bộ sưu tập thẻ đầu bếp,
## vòng quay may mắn và rương. Phần lớn được giữ lại qua mọi chương.

signal changed

var goals_data: Dictionary = {}
var research_data: Array = []
var cards_data: Dictionary = {}
var wheel_data: Dictionary = {}

var research_points: int = 0
var research: Dictionary = {}        # id -> cấp
var cards: Dictionary = {}           # id -> số bản đã có
var stars_claimed: Dictionary = {}   # "chương" -> số sao đã nhận rương
var wheel_date: String = ""          # ngày đã dùng lượt quay miễn phí


func _ready() -> void:
	goals_data = GameState._load_json("goals.json")
	research_data = GameState._load_json("research.json")
	cards_data = GameState._load_json("cards.json")
	wheel_data = GameState._load_json("wheel.json")


func reset() -> void:
	research_points = 0
	research = {}
	cards = {}
	stars_claimed = {}
	wheel_date = ""
	changed.emit()


func to_dict() -> Dictionary:
	return {"rp": research_points, "research": research, "cards": cards, "stars": stars_claimed, "wheel": wheel_date}


func from_dict(d: Dictionary) -> void:
	reset()
	research_points = int(d.get("rp", 0))
	for key in ["research", "cards", "stars"]:
		var v: Variant = d.get(key, {})
		if v is Dictionary:
			var target: Dictionary = research if key == "research" else (cards if key == "cards" else stars_claimed)
			for k: String in v:
				target[k] = int(v[k])
	wheel_date = str(d.get("wheel", ""))


# =====================================================================
# Chỉ số cộng thêm từ nghiên cứu + thẻ
# =====================================================================

## Tổng bonus theo loại: income, cook, walk, spawn, tip, offline, order, golden, event, patience.
func bonus(kind: String) -> float:
	var total: float = 0.0
	for r: Dictionary in research_data:
		if r["id"] == kind:
			total += float(r["value"]) * research_level(kind)
	for c: Dictionary in cards_data.get("cards", []):
		if c["bonus"] == kind:
			total += float(c["value"]) * card_level(str(c["id"]))
	return total


# =====================================================================
# Mục tiêu chương
# =====================================================================

func goals() -> Array:
	var all: Array = goals_data.get("chapters", [])
	if all.is_empty():
		return []
	return all[clampi(GameState.chapter, 0, all.size() - 1)]


## Tiến độ một mục tiêu: Vector2(hiện tại, cần đạt).
func goal_progress(g: Dictionary) -> Vector2:
	var gs := GameState
	var need: float = float(g.get("n", 1))
	match str(g["type"]):
		"level":
			return Vector2(gs.level, need)
		"tables":
			var t: int = 0
			for id: String in gs.areas:
				t += gs.tables_unlocked(id) if (gs.areas[id]["tables"] as Array).size() > 0 else 0
			return Vector2(t, need)
		"rooms":
			return Vector2(gs.rooms_unlocked("lodging"), need)
		"dish":
			return Vector2(int(gs.dish_levels.get(str(g["id"]), 0)), need)
		"customers":
			return Vector2(gs.run_customers, need)
		"staff":
			return Vector2(gs.staff_count(str(g["id"])), need)
		"area":
			return Vector2(1.0 if gs.area_unlocked(str(g["id"])) else 0.0, 1.0)
		"earn":
			return Vector2(gs.run_gold, need)
		"decor":
			var n: int = 0
			for id: String in gs.areas:
				for k: String in gs.areas[id]["decor"]:
					n += int(gs.areas[id]["decor"][k])
			return Vector2(n, need)
	return Vector2(0, 1)


func goal_text(g: Dictionary) -> String:
	var gs := GameState
	var n: int = int(g.get("n", 1))
	match str(g["type"]):
		"level":
			return "Đạt cấp quán %d" % n
		"tables":
			return "Mở tổng cộng %d bàn ăn" % n
		"rooms":
			return "Mở %d phòng trọ" % n
		"dish":
			return "Nâng %s lên cấp %d" % [str(gs.dish_info(str(g["id"])).get("name", "")), n]
		"customers":
			return "Phục vụ %s khách trong chương này" % NumberFormat.fmt(n)
		"staff":
			return "Có %d %s" % [n, str(gs.staff_data[str(g["id"])]["name"]).to_lower()]
		"area":
			return "Mở khu %s" % str(gs.area_info(str(g["id"])).get("name", ""))
		"earn":
			return "Kiếm %s vàng trong chương này" % NumberFormat.fmt(n)
		"decor":
			return "Mua %d món trang trí" % n
	return ""


func goal_icon(g: Dictionary) -> String:
	match str(g["type"]):
		"level":
			return "star"
		"tables":
			return "icon_house"
		"rooms":
			return "icon_house"
		"dish":
			return "dish_" + str(g["id"])
		"customers":
			return "icon_customers"
		"staff":
			return "icon_staff"
		"area":
			return str(GameState.area_info(str(g["id"])).get("thumb", "icon_house"))
		"earn":
			return "gold_bag"
		"decor":
			return "icon_plant"
	return "star"


func goal_done(g: Dictionary) -> bool:
	var p := goal_progress(g)
	return p.x >= p.y


func goals_done() -> int:
	var n: int = 0
	for g: Dictionary in goals():
		if goal_done(g):
			n += 1
	return n


func stars() -> int:
	var per: int = maxi(1, int(goals_data.get("stars_per_goals", 2)))
	return mini(3, floori(goals_done() / float(per)))


func stars_taken() -> int:
	return int(stars_claimed.get(str(GameState.chapter), 0))


func star_claimable() -> bool:
	return stars_taken() < stars()


## Nhận rương của sao kế tiếp. Trả về danh sách phần thưởng để hiện popup.
func claim_star() -> Array:
	if not star_claimable():
		return []
	var i: int = stars_taken()
	var r: Dictionary = goals_data["star_rewards"][i]
	stars_claimed[str(GameState.chapter)] = i + 1
	var out: Array = []
	GameState.add_diamonds(int(r["diamonds"]))
	out.append({"icon": "diamond", "text": "+%d kim cương" % int(r["diamonds"])})
	research_points += int(r["rp"])
	out.append({"icon": "icon_rp", "text": "+%d Sách nghiên cứu" % int(r["rp"])})
	out.append_array(open_chest(str(r["chest"])))
	changed.emit()
	return out


# =====================================================================
# Cây nghiên cứu
# =====================================================================

func research_level(id: String) -> int:
	return int(research.get(id, 0))


func research_total() -> int:
	var t: int = 0
	for k: String in research:
		t += int(research[k])
	return t


func research_info(id: String) -> Dictionary:
	for r: Dictionary in research_data:
		if r["id"] == id:
			return r
	return {}


func research_cost(id: String) -> int:
	var r := research_info(id)
	return int(r["cost"]) + int(r["cost_add"]) * research_level(id)


func research_unlocked(id: String) -> bool:
	return research_total() >= int(research_info(id).get("need", 0))


func can_research(id: String) -> bool:
	var r := research_info(id)
	return research_unlocked(id) and research_level(id) < int(r["max"]) and research_points >= research_cost(id)


func buy_research(id: String) -> bool:
	if not can_research(id):
		return false
	research_points -= research_cost(id)
	research[id] = research_level(id) + 1
	changed.emit()
	GameState.notify_state()
	return true


# =====================================================================
# Bộ sưu tập thẻ đầu bếp
# =====================================================================

func card_list() -> Array:
	return cards_data.get("cards", [])


func card_info(id: String) -> Dictionary:
	for c: Dictionary in card_list():
		if c["id"] == id:
			return c
	return {}


func card_copies(id: String) -> int:
	return int(cards.get(id, 0))


## Cấp thẻ theo số bản trùng: 1, 3, 6, 10, 15, 25 bản -> cấp 1..6.
func card_level(id: String) -> int:
	var copies := card_copies(id)
	var lv: int = 0
	for need: Variant in cards_data.get("level_copies", [1]):
		if copies >= int(need):
			lv += 1
	return lv


func card_next_copies(id: String) -> int:
	for need: Variant in cards_data.get("level_copies", [1]):
		if card_copies(id) < int(need):
			return int(need)
	return -1


func cards_owned() -> int:
	var n: int = 0
	for c: Dictionary in card_list():
		if card_copies(str(c["id"])) > 0:
			n += 1
	return n


func _roll_card() -> String:
	var chances: Dictionary = cards_data["rarity_chance"]
	var r: float = randf()
	var rarity: String = "common"
	if r < float(chances["legend"]):
		rarity = "legend"
	elif r < float(chances["legend"]) + float(chances["rare"]):
		rarity = "rare"
	var pool: Array = []
	for c: Dictionary in card_list():
		if c["rarity"] == rarity:
			pool.append(c["id"])
	return str(pool[randi() % pool.size()])


## Rút n thẻ miễn phí (từ rương / vòng quay). Trả về danh sách id.
func pull_free(n: int) -> Array:
	var got: Array = []
	for i in n:
		var id := _roll_card()
		cards[id] = card_copies(id) + 1
		got.append(id)
	changed.emit()
	GameState.notify_state()
	return got


## Rút thẻ bằng kim cương (1 hoặc 10 thẻ).
func pull_paid(n: int) -> Array:
	var cost: int = int(cards_data["pull10_cost"]) if n >= 10 else int(cards_data["pull_cost"])
	if not GameState.try_spend_diamonds(cost):
		return []
	return pull_free(10 if n >= 10 else 1)


# =====================================================================
# Vòng quay & rương
# =====================================================================

func free_spin() -> bool:
	return GameState.clock_ok() and GameState.today() > wheel_date


## Quay: chọn ô theo trọng số, trao thưởng ngay. Trả về {index, rewards}.
func spin() -> Dictionary:
	if free_spin():
		wheel_date = GameState.today()
	elif not GameState.try_spend_diamonds(int(wheel_data.get("spin_cost", 10))):
		return {}
	var segs: Array = wheel_data["segments"]
	var total: float = 0.0
	for s: Dictionary in segs:
		total += float(s["weight"])
	var roll: float = randf() * total
	var idx: int = 0
	for i in segs.size():
		roll -= float(segs[i]["weight"])
		if roll <= 0.0:
			idx = i
			break
	var rewards := _give(segs[idx])
	changed.emit()
	return {"index": idx, "rewards": rewards}


func _gold_for(minutes: float) -> float:
	return floor(maxf(200.0 * float(GameState.chapter_info().get("income_mult", 1)), GameState.income_rate() * 60.0 * minutes))


func _give(seg: Dictionary) -> Array:
	var out: Array = []
	match str(seg["type"]):
		"gold":
			var g := _gold_for(float(seg["minutes"]))
			GameState.add_gold(g)
			out.append({"icon": "coin", "text": "+%s vàng" % NumberFormat.fmt(g)})
		"diamonds":
			GameState.add_diamonds(int(seg["n"]))
			out.append({"icon": "diamond", "text": "+%d kim cương" % int(seg["n"])})
		"rp":
			research_points += int(seg["n"])
			out.append({"icon": "icon_rp", "text": "+%d Sách nghiên cứu" % int(seg["n"])})
		"card":
			for id: Variant in pull_free(int(seg["n"])):
				out.append(_card_reward(str(id)))
		"boost":
			var now: float = Time.get_unix_time_from_system()
			GameState.boost_until = maxf(now, GameState.boost_until) + float(seg["minutes"]) * 60.0
			out.append({"icon": "bolt", "text": "Thu nhập x2 trong %d phút" % int(seg["minutes"])})
		"chest":
			out.append_array(open_chest(str(seg["chest"])))
	return out


func _card_reward(id: String) -> Dictionary:
	var c := card_info(id)
	var rn: Dictionary = cards_data["rarity_names"]
	return {"icon": str(c["sprite"]), "text": "Thẻ %s (%s)" % [str(c["name"]), str(rn[c["rarity"]])], "card": id}


## Mở rương: vàng + kim cương + sách + thẻ ngẫu nhiên.
func open_chest(chest_id: String) -> Array:
	var ch: Dictionary = wheel_data["chests"][chest_id]
	var out: Array = [{"icon": chest_id, "text": str(ch["name"]) + ":"}]
	var g := _gold_for(float(ch["gold_minutes"]))
	GameState.add_gold(g)
	out.append({"icon": "coin", "text": "+%s vàng" % NumberFormat.fmt(g)})
	var dm: Array = ch["diamonds"]
	var d: int = randi_range(int(dm[0]), int(dm[1]))
	GameState.add_diamonds(d)
	out.append({"icon": "diamond", "text": "+%d kim cương" % d})
	var rpr: Array = ch["rp"]
	var rp: int = randi_range(int(rpr[0]), int(rpr[1]))
	if rp > 0:
		research_points += rp
		out.append({"icon": "icon_rp", "text": "+%d Sách nghiên cứu" % rp})
	for id: Variant in pull_free(int(ch["cards"])):
		out.append(_card_reward(str(id)))
	changed.emit()
	return out


## Số việc có thể làm ngay (cho chấm đỏ).
func alerts() -> int:
	var n: int = 0
	if star_claimable():
		n += 1
	if free_spin():
		n += 1
	for r: Dictionary in research_data:
		if can_research(str(r["id"])):
			n += 1
			break
	return n
