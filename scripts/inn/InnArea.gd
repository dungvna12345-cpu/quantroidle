class_name InnArea
extends Node2D
## Một khu của quán (Sảnh, Sân vườn, VIP, Tầng trọ).
## Dựng cảnh từ data/areas.json, tìm đường bằng AStar2D trên các lối đi, điều phối khách và nhân viên.

signal object_tapped(area_id: String, kind: String, index: int)

const CustomerScene := preload("res://scenes/inn/Customer.tscn")
const WaiterScene := preload("res://scenes/inn/Waiter.tscn")
const TableScene := preload("res://scenes/inn/Table.tscn")
const RoomScene := preload("res://scenes/inn/Room.tscn")
const KitchenScene := preload("res://scenes/inn/Kitchen.tscn")
const CashierScene := preload("res://scenes/inn/Cashier.tscn")
const InnPetScript := preload("res://scripts/inn/InnPet.gd")
const SneakyThiefScript := preload("res://scripts/inn/SneakyThief.gd")
const TravelingMerchantScript := preload("res://scripts/inn/TravelingMerchant.gd")
const FortuneGodScript := preload("res://scripts/inn/FortuneGod.gd")
const WeatherSystemScript := preload("res://scripts/fx/WeatherSystem.gd")
const PAY_SPOTS := 5
const RUSH_EXTRA := 10

var area_id: String = ""
var info: Dictionary = {}
var kind: String = "dining"
var size_w: int = 10
var size_h: int = 10
var road_y: float = 10.0
var gate_x: float = 2.0

# các lớp vẽ
var ground: Node2D
var floor_deco: Node2D
var back: Node2D
var walls: Node2D
var objects: Node2D

# tìm đường
var nav := AStar2D.new()
var points: Dictionary = {}
var _lines: Dictionary = {}
var _next_id: int = 0

var tables: Array[Table] = []
var table_cust: Array = []
var rooms: Array[Room] = []
var kitchen: Kitchen
var cashier: Cashier
var waiters: Array[Waiter] = []
var customers: Array[Customer] = []
var queue: Array[Customer] = []
var payers: Array[Customer] = []
var wait_pay: Array[Customer] = []
var ready_orders: Array[Dictionary] = []
var receptionist: Sprite2D
var manager_sprite: Sprite2D
var pet: Node2D = null
var thief: Node2D = null
var merchant: Node2D = null
var fortune_god: Node2D = null
var weather: Node2D = null
var aisle_cols: Array = []
var aisle_rows: Array = []
var _thief_spawn_timer: float = 35.0
var _merchant_spawn_timer: float = 45.0
var _fortune_god_spawn_timer: float = 65.0
var _critic_spawn_timer: float = 85.0
var _decor_nodes: Array[Node] = []
var _wing_tiles: Dictionary = {}     # wing id -> [Sprite2D]
var _wing_sites: Dictionary = {}     # wing id -> {"sign", "barrier"}
var _wing_open_state: Dictionary = {}
var _glows: Array[Sprite2D] = []
var _ambient: CPUParticles2D
var _site_t: float = 0.0
static var _glow_tex: Texture2D
var _spawn_t: float = 0.0
var _chat_t: float = 3.0


func setup(id: String) -> void:
	area_id = id
	info = GameState.area_info(id)
	kind = str(info["kind"])
	size_w = int(info["size"][0])
	size_h = int(info["size"][1])
	road_y = float(info["road_y"])
	gate_x = float(info["gate_x"])
	aisle_cols = info.get("aisle_cols", [])
	aisle_rows = info.get("aisle_rows", [])
	_make_layers()
	_build_ground()
	_build_walls()
	_apply_chapter_theme()
	_build_scenery()
	_build_nav()
	if kind == "dining":
		_build_dining()
	else:
		_build_lodging()
	_build_decor()
	_build_chapter_props()
	_build_staff_sprites()
	_build_pet()
	_build_wing_sites()
	_build_glows()
	_build_ambient()
	_build_weather()
	refresh()
	GameState.state_changed.connect(refresh)
	GameState.area_changed.connect(_on_area_changed)
	GameState.rush_requested.connect(_on_rush)
	GameState.event_started.connect(_on_event)
	GameState.wing_opened.connect(_on_wing_opened)


# =====================================================================
# Dựng cảnh
# =====================================================================

func _layer(z: int, y_sort: bool) -> Node2D:
	var n := Node2D.new()
	n.z_index = z
	n.y_sort_enabled = y_sort
	add_child(n)
	return n


func _make_layers() -> void:
	ground = _layer(-30, false)
	floor_deco = _layer(-25, false)
	back = _layer(-20, true)
	walls = _layer(-15, true)
	objects = _layer(0, true)


func _put(layer: Node2D, sprite_id: String, g: Vector2) -> Sprite2D:
	var s := Sprites.make(sprite_id)
	s.position = Iso.to_world(g)
	layer.add_child(s)
	return s


func _floor_id(x: int, y: int) -> String:
	match str(info["floor"]):
		"wood":
			return "floor_wood_a" if (x + y) % 2 == 0 else "floor_wood_b"
		"stone":
			return "floor_stone_a" if (x + y) % 2 == 0 else "floor_stone_b"
		"vip":
			return "floor_vip"
	return "grass_%d" % (absi(x * 7 + y * 13) % 3)


## Khu trong nhà: không có cỏ/đường đất, sàn gỗ chạy ra tới mép màn hình như ảnh mẫu.
func indoor() -> bool:
	return str(info["walls"]) != "fence"


## Lớp nền phẳng rất lớn nằm dưới các ô sàn: phủ kín màn hình khi thu nhỏ/màn hình dài, không còn lộ nền trống.
## Trong nhà: chỉ phủ phần phía trước tường (sau tường để màu kem của nền). Ngoài trời: phủ cỏ toàn bộ.
const BACKDROP_REACH := 80.0


func _build_backdrop() -> void:
	var poly := Polygon2D.new()
	var L: float = BACKDROP_REACH
	var corners: Array[Vector2]
	if indoor():
		corners = [Vector2(-0.5, -0.5), Vector2(L, -0.5), Vector2(L, L), Vector2(-0.5, L)]
		poly.color = Color("d6a36c")   # cùng tông với ô sàn ngoài (floor_out)
	else:
		corners = [Vector2(-L, -L), Vector2(L, -L), Vector2(L, L), Vector2(-L, L)]
		poly.color = Color("92cc60")   # cùng tông với ô cỏ
	var pts := PackedVector2Array()
	for g: Vector2 in corners:
		pts.append(Iso.to_world(g))
	poly.polygon = pts
	poly.z_index = -1
	ground.add_child(poly)


func _build_ground() -> void:
	_build_backdrop()
	var inside_house := indoor()
	for y in range(-6, size_h + 5):
		for x in range(-7, size_w + 8):
			var inside: bool = x >= 0 and x < size_w and y >= 0 and y < size_h
			var id: String
			if inside:
				id = _floor_id(x, y)
				var wid := _wing_at(x)
				if not wid.is_empty():
					var spr := _put(ground, id, Vector2(x, y))
					if not _wing_tiles.has(wid):
						_wing_tiles[wid] = []
					(_wing_tiles[wid] as Array).append(spr)
					continue
			elif inside_house:
				# sau tường thì bỏ trống (thấy nền ấm), phía trước là sàn gỗ + thảm đỏ lối vào
				if x < 0 or y < 0:
					continue
				id = "carpet_runner" if y == int(road_y) else ("floor_out_a" if (x + y) % 2 == 0 else "floor_out_b")
			elif y == int(road_y):
				id = "dirt_a" if x % 2 == 0 else "dirt_b"
			elif x == int(gate_x) and y > size_h and y < int(road_y):
				id = "dirt_a"
			else:
				id = "grass_%d" % (absi(x * 5 + y * 11) % 3)
			_put(ground, id, Vector2(x, y))
	if inside_house:
		return
	# bờ sàn dày ở hai cạnh trước
	var mat: String = ""
	match str(info["floor"]):
		"wood":
			mat = "wood"
		"stone", "vip":
			mat = "stone"
	if not mat.is_empty():
		for x in size_w:
			_put(ground, "edge_%s_l" % mat, Vector2(x, size_h - 1))
		for y in size_h:
			_put(ground, "edge_%s_r" % mat, Vector2(size_w - 1, y))


func _build_walls() -> void:
	var wk: String = str(info["walls"])
	var feats: Dictionary = info.get("wall_features", {})
	var fl: Dictionary = feats.get("l", {})
	var fr: Dictionary = feats.get("r", {})
	if wk == "fence":
		for y in size_h:
			_put(walls, "fence_y", Vector2(-0.5, y))
		for x in size_w:
			_put(walls, "fence_x", Vector2(x, -0.5))
	else:
		for y in size_h:
			var f: String = str(fl.get(str(y), ""))
			_put(walls, "wall_%s_l%s" % [wk, "" if f.is_empty() else "_" + f], Vector2(0, y))
		for x in size_w:
			var f2: String = str(fr.get(str(x), ""))
			_put(walls, "wall_%s_r%s" % [wk, "" if f2.is_empty() else "_" + f2], Vector2(x, 0))
	if indoor():
		# cột gỗ dọc tường, mỗi 3 ô một cột
		var y := 0
		while y <= size_h:
			_put(walls, "wall_post", Vector2(-0.5, y - 0.5)).position.y += 1.0
			y += 3
		var x := 3
		while x <= size_w:
			_put(walls, "wall_post", Vector2(x - 0.5, -0.5)).position.y += 1.0
			x += 3
		return
	# hàng rào phía trước + cổng vào (khu ngoài trời)
	for x in size_w:
		if x == int(gate_x):
			continue
		_put(objects, "fence_x", Vector2(x, size_h - 0.5))
	_put(objects, "gate", Vector2(gate_x, size_h - 0.5))
	for y in size_h:
		_put(objects, "fence_y", Vector2(size_w - 0.5, y))


## Mỗi chương tô màu tường và sàn khác nhau (Hội An vàng, Sài Gòn xanh...).
func _apply_chapter_theme() -> void:
	var ch := GameState.chapter_info()
	var wt: Array = ch.get("wall_tint", [1, 1, 1])
	var ft: Array = ch.get("floor_tint", [1, 1, 1])
	walls.modulate = Color(float(wt[0]), float(wt[1]), float(wt[2]))
	ground.modulate = Color(float(ft[0]), float(ft[1]), float(ft[2]))


func _build_scenery() -> void:
	if indoor():
		return
	for item: Array in info.get("scenery", []):
		var g := Vector2(float(item[1]), float(item[2]))
		var layer: Node2D = back if (g.x < -0.5 or g.y < -0.5) else objects
		var s := _put(layer, str(item[0]), g)
		if str(item[0]) == "signpost":
			var l := Label.new()
			l.text = str(info["name"]).to_upper()
			l.theme_type_variation = "WhiteLabel"
			l.add_theme_font_size_override("font_size", 40)
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
			l.size = Vector2(170, 64)
			l.position = Vector2(-85, -205)
			l.mouse_filter = Control.MOUSE_FILTER_IGNORE
			s.add_child(l)


func _wing_at(x: int) -> String:
	for w: Dictionary in info.get("wings", []):
		if x >= int(w["x0"]) and x <= int(w["x1"]):
			return str(w["id"])
	return ""


## Phòng chưa mở: sàn tối, rào chắn và biển "MỞ RỘNG" ghi giá (chạm để mở).
func _build_wing_sites() -> void:
	var wl: Array = info.get("wings", [])
	for wi in wl.size():
		var w: Dictionary = wl[wi]
		var wid: String = w["id"]
		var barrier := Node2D.new()
		barrier.y_sort_enabled = true
		objects.add_child(barrier)
		for y in size_h:
			var fs := Sprites.make("fence_y")
			fs.position = Iso.to_world(Vector2(float(w["x0"]) - 0.5, y))
			barrier.add_child(fs)
		var center := Vector2((float(w["x0"]) + float(w["x1"])) * 0.5, size_h * 0.45)
		var sign := Node2D.new()
		sign.position = Iso.to_world(center)
		sign.z_index = 30
		add_child(sign)
		var card := PanelContainer.new()
		card.theme_type_variation = "Card"
		card.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var v := UIKit.vbox(0)
		card.add_child(v)
		var ic := UIKit.icon("icon_house", 64)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		var t1 := UIKit.label("MỞ RỘNG", "HeaderLabel", 26)
		t1.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t1)
		var t2 := UIKit.label(str(w["name"]), "", 24)
		t2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t2)
		var t3 := UIKit.label("", "GreenLabel", 22)
		t3.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		v.add_child(t3)
		sign.add_child(card)
		card.position = Vector2(-110, -170)
		card.custom_minimum_size = Vector2(220, 0)
		# công nhân + thanh tiến độ khi đang thi công
		var crew := Node2D.new()
		crew.position = Iso.to_world(center + Vector2(0.6, 1.4))
		crew.z_index = 2
		add_child(crew)
		for k in 2:
			var wk := Sprites.make("cust_3")
			wk.position = Vector2(-60 + k * 120, 0)
			wk.scale = Vector2(0.55 * (1 if k == 0 else -1), 0.55)
			crew.add_child(wk)
		var dust := CPUParticles2D.new()
		dust.texture = Sprites.ui("puff")
		dust.amount = 14
		dust.lifetime = 1.2
		dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
		dust.emission_rect_extents = Vector2(110, 10)
		dust.direction = Vector2(0, -1)
		dust.spread = 40.0
		dust.initial_velocity_min = 20.0
		dust.initial_velocity_max = 60.0
		dust.gravity = Vector2(0, -10)
		dust.scale_amount_min = 0.12
		dust.scale_amount_max = 0.3
		dust.color = Color(0.85, 0.75, 0.6, 0.7)
		crew.add_child(dust)
		var bar := WorldBar.new()
		bar.bar_width = 180.0
		bar.bar_height = 18.0
		bar.fill_color = Color("ffc93c")
		bar.position = Vector2(0, -150)
		crew.add_child(bar)
		_wing_sites[wid] = {"sign": sign, "barrier": barrier, "price": t3, "index": wi, "card": card,
			"crew": crew, "bar": bar, "title": t1, "wing": w}
		_wing_open_state[wid] = GameState.wing_unlocked(area_id, wid)
	_apply_wings(false)


func _apply_wings(animate: bool) -> void:
	for w: Dictionary in info.get("wings", []):
		var wid: String = w["id"]
		var open := GameState.wing_unlocked(area_id, wid)
		var col := Color.WHITE if open else Color(0.55, 0.5, 0.46)
		for spr: Sprite2D in _wing_tiles.get(wid, []):
			if animate and open:
				spr.modulate = Color(1.6, 1.4, 0.9)
				var tw := spr.create_tween()
				tw.tween_interval(randf_range(0.0, 0.5))
				tw.tween_property(spr, "modulate", col, 0.5)
			else:
				spr.modulate = col
		var site: Dictionary = _wing_sites.get(wid, {})
		if site.is_empty():
			continue
		(site["sign"] as Node2D).visible = not open
		(site["barrier"] as Node2D).visible = not open
		var building := GameState.wing_building(area_id, wid)
		(site["crew"] as Node2D).visible = building
		if not open:
			var lv: int = int(w.get("unlock_level", 1))
			var lbl: Label = site["price"]
			(site["title"] as Label).text = "ĐANG XÂY" if building else "MỞ RỘNG"
			if building:
				lbl.text = NumberFormat.fmt_clock(GameState.wing_build_left(area_id, wid)) + " • chạm để xây nhanh"
			else:
				lbl.text = ("Cần cấp %d" % lv) if GameState.level < lv else NumberFormat.fmt(GameState.wing_cost(area_id, wid)) + " vàng"


## Công trường: công nhân đóng búa, thanh tiến độ; xây xong thì khai trương.
func _update_sites(delta: float) -> void:
	if _wing_sites.is_empty():
		return
	_site_t += delta
	for wid: String in _wing_sites:
		var site: Dictionary = _wing_sites[wid]
		var open := GameState.wing_unlocked(area_id, wid)
		if open and not bool(_wing_open_state.get(wid, false)):
			_wing_open_state[wid] = true
			_apply_wings(true)
			GameState.wing_opened.emit(area_id, wid)
			GameState.show_toast("Khai trương " + str((site["wing"] as Dictionary)["name"]) + "!")
			continue
		if not GameState.wing_building(area_id, wid):
			continue
		var crew: Node2D = site["crew"]
		for k in 2:
			var wk: Sprite2D = crew.get_child(k)
			wk.position.y = -absf(sin(_site_t * 9.0 + k * 1.7)) * 10.0
			wk.rotation = sin(_site_t * 9.0 + k * 1.7) * 0.12
		var total: float = float((site["wing"] as Dictionary).get("build_seconds", 30))
		(site["bar"] as WorldBar).ratio = 1.0 - GameState.wing_build_left(area_id, wid) / total
		(crew.get_child(2) as CPUParticles2D).emitting = visible
		if fmod(_site_t, 0.5) < delta:
			(site["price"] as Label).text = NumberFormat.fmt_clock(GameState.wing_build_left(area_id, wid)) + " • chạm để xây nhanh"
			if visible and fmod(_site_t, 1.0) < delta:
				AudioManager.play("click", 0.3, 0.2)


func _on_wing_opened(id: String, wing_id: String) -> void:
	if id != area_id:
		return
	_apply_wings(true)
	refresh()
	for t in tables:
		if t.visible and GameState.table_wing(area_id, t.index) == wing_id:
			Juice.pop(t.body, Vector2(Sprites.SCALE, Sprites.SCALE), 0.4)
	if visible:
		AudioManager.play("levelup")
		AudioManager.vibrate(80)


func _build_dining() -> void:
	kitchen = KitchenScene.instantiate()
	add_child(kitchen)
	kitchen.setup(self, info["kitchen"])
	kitchen.dish_ready.connect(_on_dish_ready)
	_put(objects, "shelf", _v(info["shelf"]))
	var spots: Array = info["tables"]
	for i in spots.size():
		var t: Table = TableScene.instantiate()
		objects.add_child(t)
		t.setup(self, i, _v(spots[i]))
		tables.append(t)
		table_cust.append(null)
	cashier = CashierScene.instantiate()
	objects.add_child(cashier)
	cashier.setup(self, _v(info["cashier"]), "cashier")
	cashier.paid.connect(_on_paid)


func _build_lodging() -> void:
	_put(objects, "shelf", _v(info["shelf"]))
	var beds: Array = info["beds"]
	for i in beds.size():
		var r: Room = RoomScene.instantiate()
		objects.add_child(r)
		r.setup(self, i, _v(beds[i]))
		rooms.append(r)
	cashier = CashierScene.instantiate()
	objects.add_child(cashier)
	cashier.setup(self, _v(info["cashier"]), "receptionist")


func _build_staff_sprites() -> void:
	if kind == "dining":
		receptionist = _put(objects, "receptionist", _v(info["receptionist"]))
	manager_sprite = _put(objects, "manager", Vector2(size_w - 0.9, size_h - 1.3))


func _build_pet() -> void:
	if kind != "dining":
		return
	pet = InnPetScript.new()
	objects.add_child(pet)
	pet.setup(self)
	var sx: float = float(aisle_cols[1]) if aisle_cols.size() > 1 else 3.5
	var sy: float = float(aisle_rows[1]) if aisle_rows.size() > 1 else 3.5
	pet.place(Vector2(sx, sy))


## Đồ đặc trưng của chương (đèn lồng Hội An, xe máy Sài Gòn, lò sưởi Đà Lạt...) đặt ở sảnh.
func _build_chapter_props() -> void:
	if area_id != "hall":
		return
	for item: Array in GameState.chapter_info().get("props", []):
		_put(objects, str(item[0]), Vector2(float(item[1]), float(item[2])))


## Ánh đèn buổi tối: quầng sáng ấm ở bếp, cửa sổ, đèn lồng (mờ dần theo độ tối).
func _glow_texture() -> Texture2D:
	if _glow_tex == null:
		var grad := Gradient.new()
		grad.set_color(0, Color(1.0, 0.85, 0.5, 0.9))
		grad.add_point(0.45, Color(1.0, 0.7, 0.35, 0.35))
		grad.set_color(grad.get_point_count() - 1, Color(1.0, 0.6, 0.3, 0.0))
		var gt := GradientTexture2D.new()
		gt.gradient = grad
		gt.fill = GradientTexture2D.FILL_RADIAL
		gt.fill_from = Vector2(0.5, 0.5)
		gt.fill_to = Vector2(1.0, 0.5)
		gt.width = 128
		gt.height = 128
		_glow_tex = gt
	return _glow_tex


func _add_glow(world_pos: Vector2, radius: float) -> void:
	var g := Sprite2D.new()
	g.texture = _glow_texture()
	g.position = world_pos
	g.scale = Vector2(radius / 64.0, radius / 128.0)
	g.z_index = 60
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	g.material = mat
	g.modulate.a = 0.0
	add_child(g)
	_glows.append(g)


func _build_glows() -> void:
	for g in _glows:
		g.queue_free()
	_glows.clear()
	if kitchen:
		for st in kitchen.stoves:
			_add_glow(Iso.to_world(Vector2(float(st["x"]), kitchen.row_y)) + Vector2(0, -50), 120.0)
	if indoor():
		var feats: Dictionary = info.get("wall_features", {})
		for y_str: String in (feats.get("l", {}) as Dictionary):
			if str(feats["l"][y_str]) == "window":
				_add_glow(Iso.to_world(Vector2(-0.3, float(y_str))) + Vector2(0, -100), 110.0)
		for x_str: String in (feats.get("r", {}) as Dictionary):
			if str(feats["r"][x_str]) == "window":
				_add_glow(Iso.to_world(Vector2(float(x_str), -0.3)) + Vector2(0, -100), 110.0)
	var slots: Dictionary = info.get("decor_slots", {})
	var lanterns: Array = slots.get("lantern", [])
	for i in mini(GameState.decor_count(area_id, "lantern"), lanterns.size()):
		_add_glow(Iso.to_world(_v(lanterns[i])) + Vector2(14, -60), 150.0)
	if area_id == "hall":
		for item: Array in GameState.chapter_info().get("props", []):
			_add_glow(Iso.to_world(Vector2(float(item[1]), float(item[2]))) + Vector2(0, -70), 130.0)


func _update_lights() -> void:
	if not visible:
		return
	var n: float = GameState.night_factor()
	for g in _glows:
		g.modulate.a = n * 0.85


## Hạt không khí: bụi lấp lánh trong nhà, cánh hoa rơi ngoài vườn.
func _build_ambient() -> void:
	_ambient = CPUParticles2D.new()
	var b := bounds()
	_ambient.position = b.get_center()
	_ambient.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_ambient.emission_rect_extents = b.size * 0.45
	_ambient.texture = Sprites.ui("sparkle")
	_ambient.lifetime = 7.0
	_ambient.amount = 26
	_ambient.preprocess = 7.0
	_ambient.z_index = 50
	if indoor():
		_ambient.direction = Vector2(0.3, -1)
		_ambient.initial_velocity_min = 4.0
		_ambient.initial_velocity_max = 12.0
		_ambient.gravity = Vector2(0, -2)
		_ambient.scale_amount_min = 0.05
		_ambient.scale_amount_max = 0.1
		_ambient.color = Color(1, 0.95, 0.8, 0.45)
	else:
		_ambient.direction = Vector2(1, 1)
		_ambient.initial_velocity_min = 10.0
		_ambient.initial_velocity_max = 25.0
		_ambient.gravity = Vector2(6, 14)
		_ambient.angular_velocity_min = -90.0
		_ambient.angular_velocity_max = 90.0
		_ambient.scale_amount_min = 0.08
		_ambient.scale_amount_max = 0.14
		_ambient.color = Color(1, 0.7, 0.8, 0.8)
	var grad := Gradient.new()
	grad.set_color(0, Color(1, 1, 1, 0))
	grad.add_point(0.2, Color(1, 1, 1, 1))
	grad.set_color(grad.get_point_count() - 1, Color(1, 1, 1, 0))
	_ambient.color_ramp = grad
	add_child(_ambient)
	if weather != null and is_instance_valid(weather):
		weather.queue_free()
	weather = WeatherSystemScript.new()
	add_child(weather)


func _build_decor() -> void:
	for n in _decor_nodes:
		n.queue_free()
	_decor_nodes.clear()
	var slots: Dictionary = info.get("decor_slots", {})
	for k: String in slots:
		var list: Array = slots[k]
		var count: int = mini(GameState.decor_count(area_id, k), list.size())
		for i in count:
			var slot: Array = list[i]
			var g := Vector2(float(slot[0]), float(slot[1]))
			var s: Sprite2D
			match k:
				"painting":
					var side: String = str(slot[2]) if slot.size() > 2 else "l"
					s = Sprites.make("painting_" + side)
					s.position = Iso.to_world(g) + Vector2(0, 0.5)
					walls.add_child(s)
				"rug":
					s = _put(floor_deco, "rug", g)
				_:
					s = _put(objects, str(GameState.decor_data[k]["sprite"]), g)
			_decor_nodes.append(s)


func _v(a: Variant) -> Vector2:
	var arr: Array = a
	return Vector2(float(arr[0]), float(arr[1]))


# =====================================================================
# Tìm đường: lưới lối đi (hàng & cột) + điểm đặc biệt nối vào lối đi gần nhất
# =====================================================================

func _add_pt(p: Vector2) -> int:
	var id := _next_id
	_next_id += 1
	nav.add_point(id, p)
	return id


func _build_nav() -> void:
	var rows: Array = info["aisle_rows"]
	var cols: Array = info["aisle_cols"]
	for ri in rows.size():
		_lines["r%d" % ri] = []
	for ci in cols.size():
		_lines["c%d" % ci] = []
	for ri in rows.size():
		for ci in cols.size():
			var id := _add_pt(Vector2(float(cols[ci]), float(rows[ri])))
			(_lines["r%d" % ri] as Array).append([float(cols[ci]), id])
			(_lines["c%d" % ci] as Array).append([float(rows[ri]), id])
	_add_special("door", Vector2(gate_x, size_h - 0.8))
	if kind == "dining":
		_add_special("post", _v(info["waiter_post"]))
		var k: Dictionary = info["kitchen"]
		_add_special("pickup", Vector2(float(k["pass_x"]), float(k["row_y"]) + 1.3))
		var spots: Array = info["tables"]
		for i in spots.size():
			var tg := _v(spots[i])
			_add_special("seat_%d" % i, tg + Table.SEAT_OFFSET)
			_add_special("serve_%d" % i, tg + Vector2(0.62, 0.05))
		var cg := _v(info["cashier"])
		for kk in PAY_SPOTS:
			_add_special("pay_%d" % kk, cg + Vector2(0.85, 0.7 * kk))
	else:
		var beds: Array = info["beds"]
		for i in beds.size():
			_add_special("bed_%d" % i, _v(beds[i]) + Vector2(0.0, 0.62))
	# nối các điểm liên tiếp trên từng lối đi
	for key: String in _lines:
		var arr: Array = _lines[key]
		arr.sort_custom(func(a: Array, b: Array) -> bool: return float(a[0]) < float(b[0]))
		for i in range(1, arr.size()):
			var a_id: int = arr[i - 1][1]
			var b_id: int = arr[i][1]
			if a_id != b_id:
				nav.connect_points(a_id, b_id)


func _add_special(pname: String, pos: Vector2) -> void:
	var rows: Array = info["aisle_rows"]
	var cols: Array = info["aisle_cols"]
	var x0: float = float(cols[0])
	var x1: float = float(cols[cols.size() - 1])
	var y0: float = float(rows[0])
	var y1: float = float(rows[rows.size() - 1])
	var best_key: String = ""
	var best_d: float = INF
	var best_proj := Vector2.ZERO
	var best_coord: float = 0.0
	for ri in rows.size():
		var proj := Vector2(clampf(pos.x, x0, x1), float(rows[ri]))
		var d := proj.distance_to(pos)
		if d < best_d:
			best_d = d
			best_key = "r%d" % ri
			best_proj = proj
			best_coord = proj.x
	for ci in cols.size():
		var proj := Vector2(float(cols[ci]), clampf(pos.y, y0, y1))
		var d := proj.distance_to(pos)
		if d < best_d:
			best_d = d
			best_key = "c%d" % ci
			best_proj = proj
			best_coord = proj.y
	var id := _add_pt(pos)
	points[pname] = id
	if best_d < 0.02:
		(_lines[best_key] as Array).append([best_coord, id])
	else:
		var pid := _add_pt(best_proj)
		(_lines[best_key] as Array).append([best_coord, pid])
		nav.connect_points(id, pid)


func point_pos(pname: String) -> Vector2:
	return nav.get_point_position(points[pname])


## Đường đi từ vị trí hiện tại tới một điểm đặt tên.
func path_to(from_grid: Vector2, pname: String) -> PackedVector2Array:
	var start: int = nav.get_closest_point(from_grid)
	return nav.get_point_path(start, points[pname])


func _exit_path(from_grid: Vector2) -> PackedVector2Array:
	var p := path_to(from_grid, "door")
	p.append(Vector2(gate_x, size_h - 0.5))
	p.append(Vector2(gate_x, road_y))
	p.append(Vector2(-7.0, road_y))
	return p


func _enter_path(target: String) -> PackedVector2Array:
	var p := PackedVector2Array([Vector2(gate_x, size_h - 0.5), point_pos("door")])
	p.append_array(path_to(point_pos("door"), target))
	return p


# =====================================================================
# Vòng lặp điều phối
# =====================================================================

func _process(delta: float) -> void:
	if not GameState.area_unlocked(area_id):
		return
	_spawn_t += delta
	if _spawn_t >= GameState.spawn_interval(area_id):
		_spawn_t = 0.0
		if _can_spawn():
			spawn_customer()
	if kind == "dining":
		_dispatch_dining()
		_update_payers()
		_update_thief(delta)
		_update_merchant(delta)
		_update_fortune_god(delta)
		_update_critic(delta)
	else:
		_dispatch_lodging()
	_chatter(delta)
	_update_sites(delta)
	_update_lights()


func _update_merchant(delta: float) -> void:
	if merchant != null and is_instance_valid(merchant):
		return
	_merchant_spawn_timer -= delta
	if _merchant_spawn_timer <= 0.0:
		_merchant_spawn_timer = randf_range(65.0, 95.0)
		_spawn_merchant()


func _spawn_merchant() -> void:
	if kind != "dining":
		return
	merchant = TravelingMerchantScript.new()
	merchant.area = self
	objects.add_child(merchant)
	var sx: float = float(size_w) + 4.0
	var sy: float = float(road_y)
	var ex: float = -6.0
	var ey: float = float(road_y)
	merchant.place(Vector2(sx, sy))
	merchant.walk(PackedVector2Array([Vector2(float(gate_x) + 1.0, sy), Vector2(ex, ey)]))
	merchant.arrived.connect(func() -> void:
		if merchant != null and is_instance_valid(merchant):
			merchant.queue_free()
			merchant = null
	)
	GameState.show_toast("🎁 THƯƠNG BUÔN PHƯƠNG XA GHÉ QUÁN! Chạm để mở rương báu!")
	AudioManager.play("levelup")


func _update_thief(delta: float) -> void:
	if thief != null and is_instance_valid(thief):
		return
	_thief_spawn_timer -= delta
	if _thief_spawn_timer <= 0.0:
		_thief_spawn_timer = randf_range(50.0, 85.0)
		_spawn_thief()


func _spawn_thief() -> void:
	if kind != "dining" or aisle_cols.size() < 2 or aisle_rows.size() < 2:
		return
	thief = SneakyThiefScript.new()
	objects.add_child(thief)
	var sx: float = float(aisle_cols[0])
	var sy: float = float(aisle_rows[0])
	var tx: float = float(aisle_cols[aisle_cols.size() - 1])
	var ty: float = float(aisle_rows[aisle_rows.size() - 1])
	thief.setup(self, Vector2(sx, sy), Vector2(tx, ty))
	thief.caught.connect(func(_t): thief = null)
	thief.escaped.connect(func(_t): thief = null)
	GameState.show_toast("🚨 CẢNH BÁO: CHUỘT NHẮT TRỘM VÀNG! ĐẬP NHANH! 🚨")
	if pet != null and is_instance_valid(pet) and GameState.pet_level >= 4:
		pet.say("Có trộm kìa sen ơi! Bắt lẹ! 🐾")
		pet.show_bubble("face_angry")


func _update_fortune_god(delta: float) -> void:
	if fortune_god != null and is_instance_valid(fortune_god):
		return
	_fortune_god_spawn_timer -= delta
	if _fortune_god_spawn_timer <= 0.0:
		_fortune_god_spawn_timer = randf_range(80.0, 130.0)
		_spawn_fortune_god()


func _spawn_fortune_god() -> void:
	if kind != "dining":
		return
	fortune_god = FortuneGodScript.new()
	fortune_god.area = self
	objects.add_child(fortune_god)
	var sx: float = float(size_w) + 4.0
	var sy: float = float(road_y)
	var ex: float = -6.0
	var ey: float = float(road_y)
	fortune_god.place(Vector2(sx, sy))
	fortune_god.walk(PackedVector2Array([Vector2(float(gate_x) + 1.2, sy), Vector2(ex, ey)]))
	fortune_god.tapped.connect(func() -> void:
		if UIKit.main:
			UIKit.main.call("open_fortune_storm")
	)
	fortune_god.arrived.connect(func() -> void:
		if fortune_god != null and is_instance_valid(fortune_god):
			fortune_god.queue_free()
			fortune_god = null
	)
	GameState.show_toast("🧧 THẦN TÀI GIÁ ĐÁO! Chạm vào Thần Tài để nhận Mưa Lì Xì!")
	AudioManager.play("legendary")


func _update_critic(delta: float) -> void:
	_critic_spawn_timer -= delta
	if _critic_spawn_timer <= 0.0:
		_critic_spawn_timer = randf_range(95.0, 150.0)
		_spawn_critic()


func _spawn_critic() -> void:
	if kind != "dining":
		return
	var free_tbl := _free_table()
	if free_tbl >= 0:
		var c: Customer = CustomerScene.instantiate()
		c.ctype = "critic"
		c.base_sprite = "customer_tourist"
		c.area = self
		objects.add_child(c)
		c.place(Vector2(size_w + 4.0, road_y))
		customers.append(c)
		queue.append(c)
		c.set_state(Customer.S.ROAD)
		_relayout_queue()
		GameState.show_toast("⭐ NHÀ PHÊ BÌNH ẨM THỰC ĐÃ BÍ MẬT GHÉ QUÁN!")
		AudioManager.play("levelup")


func _build_weather() -> void:
	if weather == null or not is_instance_valid(weather):
		weather = WeatherSystemScript.new()
		weather.z_index = 75
		add_child(weather)


## Thỉnh thoảng một vị khách nói gì đó cho quán thêm sống động.
func _chatter(delta: float) -> void:
	if not visible:
		return
	_chat_t -= delta
	if _chat_t > 0.0:
		return
	_chat_t = randf_range(2.0, 4.5)
	var pool: Array[Customer] = []
	for c in customers:
		if c.visible and c.state in [Customer.S.QUEUE, Customer.S.ORDER, Customer.S.EAT]:
			pool.append(c)
	if pool.is_empty():
		return
	var c: Customer = pool[randi() % pool.size()]
	var kind_key := "eat" if c.state == Customer.S.EAT else "queue"
	if c.golden:
		kind_key = "golden"
	elif c.ctype in ["picky", "tourist"] and randf() < 0.6:
		kind_key = c.ctype
	var text := Story.chatter(kind_key)
	if c.state == Customer.S.EAT and randf() < 0.35:
		text = "%s ở đây số một!" % str(GameState.dish_info(c.dish_id).get("name", "Món"))
	c.say(text)


func _can_spawn() -> bool:
	if kind == "dining":
		return queue.size() < int(GameState.bal("max_queue", 6))
	var free: int = 0
	for r in rooms:
		if r.is_free():
			free += 1
	return queue.size() < mini(free, 3)


func spawn_customer(golden: bool = false) -> void:
	var c: Customer = CustomerScene.instantiate()
	c.golden = golden
	c.ctype = "normal" if golden else _roll_type()
	var list: Array = info["customer_sprites"]
	c.base_sprite = str(list[randi() % list.size()])
	if c.ctype == "regular":
		c.regular_id = Story.pick_regular()
		var rinfo := Story.regular_info(c.regular_id)
		if not rinfo.is_empty():
			c.base_sprite = str(rinfo["sprite"])
	c.area = self
	objects.add_child(c)
	c.place(Vector2(size_w + 4.0, road_y))
	customers.append(c)
	queue.append(c)
	c.set_state(Customer.S.ROAD)
	_relayout_queue()


## Loại khách: khó tính (ít kiên nhẫn, boa đậm), du lịch (trả gấp đôi), khách quen (trả thêm, nhiều EXP).
func _roll_type() -> String:
	if kind != "dining":
		return "normal"
	var r := randf()
	var g := GameState
	if r < 0.04:
		return "wealth"
	if r < 0.08:
		return "critic"
	if r < g.bal("picky_chance", 0.12):
		return "picky"
	r -= g.bal("picky_chance", 0.12)
	if r < g.bal("tourist_chance", 0.12):
		return "tourist"
	r -= g.bal("tourist_chance", 0.12)
	if r < g.bal("regular_chance", 0.08):
		return "regular"
	return "normal"


func queue_spot(k: int) -> Vector2:
	return Vector2(gate_x + 0.85 * k, road_y)


func _relayout_queue() -> void:
	for i in queue.size():
		var c := queue[i]
		c.queue_index = i
		var spot := queue_spot(i)
		if c.state == Customer.S.ROAD:
			c.walk_to(spot)
		elif c.state == Customer.S.QUEUE and c.grid.distance_to(spot) > 0.01:
			c.walk_to(spot)


func _free_table() -> int:
	for i in tables.size():
		if tables[i].unlocked() and table_cust[i] == null:
			return i
	return -1


func _dispatch_dining() -> void:
	for w in waiters:
		if not w.is_free():
			continue
		# ưu tiên mang món đã nấu xong
		if not ready_orders.is_empty():
			var o: Dictionary = ready_orders.pop_front()
			if is_instance_valid(o["cust"]):
				w.go_deliver(o)
			else:
				kitchen.remove_ready_icon(o)
			continue
		if queue.is_empty():
			continue
		var c := queue[0]
		if c.state != Customer.S.QUEUE:
			continue
		var t := _free_table()
		if t < 0:
			continue
		table_cust[t] = c   # giữ chỗ
		c.table = t
		c.set_state(Customer.S.CALLED)
		c.show_bubble("")
		w.go_seat(c, t)


## Bồi bàn tới cửa: khách bắt đầu đi theo vào bàn.
func start_lead(_w: Waiter, task: Dictionary) -> bool:
	var t: int = int(task["table"])
	var c: Customer = task.get("cust", null)
	if c == null or not is_instance_valid(c) or c.state != Customer.S.CALLED:
		if table_cust[t] == c:
			table_cust[t] = null
		return false
	queue.erase(c)
	_relayout_queue()
	c.set_state(Customer.S.WALK_IN)
	c.show_bubble("")
	c.walk(_enter_path("seat_%d" % t))
	return true


func customer_seated(c: Customer) -> void:
	c.set_state(Customer.S.ORDER)
	c.sit(true)
	c.place(tables[c.table].seat_grid())
	c.dish_id = GameState.random_dish()
	c.show_bubble("bubble", "dish_" + c.dish_id)
	kitchen.add_order({"cust": c, "dish": c.dish_id, "table": c.table, "rush": c.rushed})


func _on_dish_ready(o: Dictionary) -> void:
	ready_orders.append(o)


func take_dish(o: Dictionary) -> void:
	kitchen.remove_ready_icon(o)


func deliver(o: Dictionary) -> void:
	var c: Customer = o["cust"]
	if not is_instance_valid(c) or c.state != Customer.S.ORDER:
		return
	tables[c.table].show_dish(c.dish_id)
	c.start_eat(GameState.bal("eat_time", 3.0))
	if visible:
		AudioManager.play("pop", 0.15, 0.1)


func _bill(c: Customer) -> float:
	var v: float = GameState.dish_sell_price(c.dish_id) * GameState.table_mult(area_id, c.table) * float(info["price_mult"])
	v *= GameState.wing_price_mult(area_id, c.table)
	if c.golden:
		v *= GameState.golden_mult()
	match c.ctype:
		"wealth":
			v *= 10.0
		"critic":
			v *= 3.0
		"tourist":
			v *= 2.0
		"regular":
			v *= 1.3
	return v


func customer_finished_eating(c: Customer) -> void:
	tables[c.table].show_dish("")
	var chance: float = GameState.tip_chance(area_id) + (0.4 if c.ctype == "picky" else 0.0)
	if randf() < chance:
		var ratio: float = GameState.bal("tip_ratio", 0.5) * (3.0 if c.ctype == "picky" else 1.0)
		tables[c.table].add_tip(_bill(c) * ratio)
	if c.ctype == "wealth":
		GameState.add_diamonds(1)
		GameState.show_toast("Thần Tài gửi lại 1 Kim Cương lộc! 💎")
	elif c.ctype == "critic":
		GameState.show_toast("Nhà Phê Bình Bác Sáu đánh giá 5 SAO! ⭐⭐⭐⭐⭐")
		if UIKit.main:
			UIKit.main.call_deferred("open_food_critic")
	c.set_state(Customer.S.WAIT_PAY)
	wait_pay.append(c)


func _update_payers() -> void:
	while not wait_pay.is_empty() and payers.size() < PAY_SPOTS:
		var c: Customer = wait_pay.pop_front()
		if not is_instance_valid(c):
			continue
		# rời bàn -> bàn trống cho khách sau
		table_cust[c.table] = null
		c.sit(false)
		c.pay_index = payers.size()
		payers.append(c)
		c.set_state(Customer.S.TO_PAY)
		c.walk(path_to(c.grid, "pay_%d" % c.pay_index))
	if not payers.is_empty() and not cashier.busy():
		var f := payers[0]
		if f.state == Customer.S.PAY_QUEUE and not f.moving:
			f.set_state(Customer.S.PAYING)
			cashier.begin(f)


func _relayout_payers() -> void:
	for i in payers.size():
		var c := payers[i]
		c.pay_index = i
		var spot := point_pos("pay_%d" % i)
		if c.state == Customer.S.PAY_QUEUE:
			c.walk_to(spot)
		elif c.state == Customer.S.TO_PAY:
			c.walk(path_to(c.grid, "pay_%d" % i))


func _on_paid(c: Customer) -> void:
	payers.erase(c)
	_relayout_payers()
	if not is_instance_valid(c):
		return
	var at := to_global(Iso.to_world(cashier.grid) + Vector2(0, -70))
	GameState.earn(_bill(c), at, visible)
	GameState.customer_served(c.dish_id)
	if c.ctype == "regular":
		GameState.add_xp(2.0)
		Story.serve_regular(c.regular_id)
	if visible:
		AudioManager.play("coin", 0.12)
	c.show_bubble("face_heart")
	c.set_state(Customer.S.LEAVE)
	c.walk(_exit_path(c.grid))


func customer_gave_up(c: Customer) -> void:
	queue.erase(c)
	_relayout_queue()
	c.set_state(Customer.S.LEAVE)
	c.show_bubble("face_angry")
	c.walk_to(Vector2(-7.0, road_y))


func customer_left(c: Customer) -> void:
	customers.erase(c)
	queue.erase(c)
	c.queue_free()


# --- tầng trọ
func _free_room() -> int:
	for i in rooms.size():
		if rooms[i].is_free():
			return i
	return -1


func _dispatch_lodging() -> void:
	if queue.is_empty():
		return
	var c := queue[0]
	if c.state != Customer.S.QUEUE:
		return
	var r := _free_room()
	if r < 0:
		return
	rooms[r].reserved = true
	c.room = r
	queue.erase(c)
	_relayout_queue()
	c.set_state(Customer.S.TO_BED)
	c.show_bubble("")
	c.walk(_enter_path("bed_%d" % r))


func guest_in_bed(c: Customer) -> void:
	c.visible = false
	c.set_state(Customer.S.SLEEP)
	rooms[c.room].start_sleep(c)


func guest_woke(r: Room, c: Customer) -> void:
	var at := to_global(r.position + Vector2(0, -60))
	GameState.earn(GameState.room_rent(area_id, r.index), at, visible)
	GameState.customer_served("")
	if visible:
		AudioManager.play("coin", 0.12)
	if not is_instance_valid(c):
		return
	c.visible = true
	c.place(r.approach_grid())
	c.show_bubble("face_heart")
	c.set_state(Customer.S.LEAVE)
	c.walk(_exit_path(c.grid))


## Sự kiện: khách sộp (khách vàng trả x10) và mưa tiền boa ở khu đang xem.
func _on_event(ev: Dictionary) -> void:
	if GameState.current_area != area_id or not GameState.area_unlocked(area_id) or kind != "dining":
		return
	for i in int(ev.get("golden", 0)):
		spawn_customer(true)
	var tips: float = float(ev.get("tips", 0.0))
	if tips > 0.0:
		var avg: float = 0.0
		var list := GameState.unlocked_dishes()
		for d in list:
			avg += GameState.dish_price(d)
		avg /= maxf(1.0, list.size())
		for t in tables:
			if t.unlocked():
				t.add_tip(avg * tips)


func _on_rush(count: int) -> void:
	if GameState.current_area != area_id:
		return
	var cap: int = int(GameState.bal("max_queue", 6)) + RUSH_EXTRA
	for i in count:
		if queue.size() >= cap:
			break
		spawn_customer()


# =====================================================================
# Làm mới & chạm
# =====================================================================

func refresh() -> void:
	if not _wing_sites.is_empty():
		_apply_wings(false)
	for t in tables:
		t.refresh()
	for r in rooms:
		r.refresh()
	if kitchen:
		kitchen.refresh_chefs()
	if kind == "dining":
		var want: int = GameState.staff_count("waiter")
		while waiters.size() < want:
			var w: Waiter = WaiterScene.instantiate()
			w.area = self
			w.post_offset = Vector2(0.45 * waiters.size(), 0.35 * waiters.size())
			objects.add_child(w)
			w.place(point_pos("post") + w.post_offset)
			waiters.append(w)
		receptionist.visible = GameState.staff_count("receptionist") > 0
	manager_sprite.visible = GameState.manager


func _on_area_changed(id: String) -> void:
	if id == area_id:
		_apply_wings(false)
		_build_decor()
		_build_glows()
		refresh()


## Xử lý chạm (toạ độ cục bộ). Trả về true nếu đã xử lý.
func tap(p: Vector2) -> bool:
	if thief and thief.visible and thief.hit_rect().has_point(p):
		return thief.hit()
	if pet and pet.visible and pet.hit_rect().has_point(p):
		pet.pet_interaction()
		if UIKit.main and randf() < 0.5:
			UIKit.main.call_deferred("open_pet")
		return true
	if merchant and is_instance_valid(merchant) and merchant.visible and merchant.hit_rect().has_point(p):
		merchant.interact()
		if UIKit.main:
			UIKit.main.call("open_mystery_chest")
		return true
	if fortune_god and is_instance_valid(fortune_god) and fortune_god.visible and fortune_god.hit_rect().has_point(p):
		fortune_god.interact()
		return true
	if kitchen and kitchen.visible and kitchen.hit_rect().has_point(p):
		if UIKit.main:
			UIKit.main.call("open_cooking")
			return true
	for t in tables:
		if t.tip_value > 0.0 and t.tip_hit_rect().has_point(p):
			t.collect_tip()
			return true
	var best: Customer = null
	for c in customers:
		if c.visible and c.hit_rect().has_point(p):
			if best == null or c.position.y > best.position.y:
				best = c
	if best != null and best.rush():
		GameState.add_daily("tap", 1)
		# combo: chạm liên tiếp nhanh được thưởng thêm vàng, càng dài càng nhiều
		var n := GameState.register_combo(to_global(best.position + Vector2(0, -90)))
		if n >= 2:
			var avg: float = GameState.dish_price(GameState.random_dish())
			GameState.earn(avg * 0.15 * mini(n, 25), to_global(best.position + Vector2(0, -60)), visible)
		if kitchen:
			kitchen.rush_order(best)
		AudioManager.play("pop", 0.15)
		GameState.fire_tutorial("tap_customer")
		return true
	if kitchen and kitchen.hit(p):
		object_tapped.emit(area_id, "kitchen", 0)
		return true
	if cashier and cashier.hit_rect().has_point(p):
		object_tapped.emit(area_id, "cashier" if kind == "dining" else "reception", 0)
		return true
	for wid: String in _wing_sites:
		var site: Dictionary = _wing_sites[wid]
		var sg: Node2D = site["sign"]
		var crew: Node2D = site["crew"]
		if crew.visible and Rect2(crew.position + Vector2(-140, -200), Vector2(280, 230)).has_point(p):
			# chạm công trường: xây nhanh thêm 1.5 giây
			GameState.speed_build(area_id, wid, 1.5)
			GameState.register_combo(to_global(crew.position + Vector2(0, -120)))
			Juice.pop(crew, Vector2.ONE, 0.1)
			AudioManager.play("click", 0.2)
			_apply_wings(false)
			return true
		if sg.visible and Rect2(sg.position + Vector2(-120, -180), Vector2(240, 200)).has_point(p):
			object_tapped.emit(area_id, "wing", int(site["index"]))
			return true
	for t in tables:
		if t.visible and t.hit_rect().has_point(p):
			object_tapped.emit(area_id, "table", t.index)
			return true
	for r in rooms:
		if r.visible and r.hit_rect().has_point(p):
			object_tapped.emit(area_id, "room", r.index)
			return true
	# Chạm tương tác hồ sen sân vườn
	if area_id == "garden":
		var gp := Iso.to_grid(p)
		if gp.x >= 6.0 and gp.y <= 6.5:
			_feed_koi(p)
			return true
	return false


func _feed_koi(p: Vector2) -> void:
	AudioManager.play("pop", 0.25)
	AudioManager.vibrate(20)
	var bubble := Sprite2D.new()
	bubble.texture = Sprites.ui("heart")
	bubble.position = p + Vector2(0, -10)
	bubble.scale = Vector2(0.45, 0.45)
	bubble.z_index = 70
	add_child(bubble)
	var tw := bubble.create_tween()
	tw.tween_property(bubble, "position:y", p.y - 45.0, 0.6).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(bubble, "modulate:a", 0.0, 0.6)
	tw.tween_callback(bubble.queue_free)

	var bonus_gold: int = int(GameState.income_rate() * 3.0) + 88
	GameState.add_gold(bonus_gold)
	GameState.register_combo(to_global(p + Vector2(0, -30)))
	if randf() < 0.25:
		GameState.add_diamonds(1)
		GameState.show_toast("🐟 Đàn cá Koi quẫy đuôi tặng bạn 1 Kim Cương!")
	else:
		GameState.show_toast("🐟 Bạn đã cho cá Koi ăn: Đàn cá vui vẻ nhả tiền vàng!")


## Vùng camera được phép di chuyển (toạ độ cục bộ).
func bounds() -> Rect2:
	var corners := [Vector2(-2.5, -2.5), Vector2(size_w + 2.5, -2.5), Vector2(size_w + 2.5, size_h + 2.5),
		Vector2(-2.5, size_h + 2.5)]
	var r := Rect2(Iso.to_world(corners[0]), Vector2.ZERO)
	for g: Vector2 in corners:
		r = r.expand(Iso.to_world(g))
	r.position.y -= 160.0
	r.size.y += 160.0
	return r


## Bề rộng phần quán gốc (không tính phòng mở rộng chưa mở) để camera căn giữa.
func base_w() -> int:
	var w: int = size_w
	for wing: Dictionary in info.get("wings", []):
		if not GameState.wing_unlocked(area_id, str(wing["id"])):
			w = mini(w, int(wing["x0"]))
	return w


func focus_point() -> Vector2:
	return Iso.to_world(Vector2(base_w() * 0.5, size_h * 0.55))


## Vị trí màn hình cục bộ của khách đứng đầu hàng (cho hướng dẫn chơi).
func first_queue_customer() -> Customer:
	for c in queue:
		if c.state == Customer.S.QUEUE:
			return c
	return null


func first_table_pos() -> Vector2:
	if tables.is_empty():
		return focus_point()
	return tables[0].position


## Kích hoạt phục vụ nhanh & cổ vũ toàn quán khi bấm nút BẮT ĐẦU ở giữa
func cheer_all() -> void:
	for t in tables:
		if t.tip_value > 0.0:
			t.collect_tip()
	var count := 0
	for c in customers:
		if c.visible and c.rush():
			count += 1
			if count <= 5:
				GameState.register_combo(to_global(c.position + Vector2(0, -90)))
				Juice.bounce(c, 1.2)
	AudioManager.play("bell")

