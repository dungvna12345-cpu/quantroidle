class_name Kitchen
extends Node2D
## Khu bếp: quầy, bếp lò, nồi, đầu bếp. Nhận đơn từ khách, nấu (thanh tiến độ trên bếp), đưa ra quầy chuyển món.

signal dish_ready(order: Dictionary)

const ChefScene := preload("res://scenes/inn/Chef.tscn")

var area: InnArea
var row_y: float = 0.0
var stoves: Array[Dictionary] = []   # {"x", "chef", "bar", "steam", "order", "left", "total"}
var orders: Array[Dictionary] = []   # đơn chờ nấu
var pass_x: float = 3.0
var ready_icons: Array[Sprite2D] = []


func setup(a: InnArea, info: Dictionary) -> void:
	area = a
	row_y = float(info["row_y"])
	pass_x = float(info["pass_x"])
	var stove_xs: Array = info["stoves"]
	for x in range(int(info["x_from"]), int(info["x_to"]) + 1):
		var g := Vector2(x, row_y)
		var is_stove: bool = stove_xs.has(x) or stove_xs.has(float(x))
		var spr := Sprites.make("stove" if is_stove else "kitchen_counter")
		spr.position = Iso.to_world(g)
		area.objects.add_child(spr)
		if is_stove:
			var pot := Sprites.make("pot")
			# nồi đặt trên mặt bếp (ảnh 2x nên toạ độ con nhân đôi)
			pot.scale = Vector2.ONE
			pot.position = Vector2(-28, -92)
			spr.add_child(pot)
			var bar := WorldBar.new()
			bar.position = Iso.to_world(g) + Vector2(0, -104)
			bar.visible = false
			add_child(bar)
			var steam := _make_steam()
			steam.position = Iso.to_world(g) + Vector2(-14, -80)
			add_child(steam)
			stoves.append({"x": float(x), "chef": null, "bar": bar, "steam": steam, "order": {}, "left": 0.0, "total": 1.0})
	refresh_chefs()


func hit_rect() -> Rect2:
	if stoves.is_empty():
		return Rect2()
	var p0: Vector2 = Iso.to_world(Vector2(float(stoves[0]["x"]), row_y))
	var p1: Vector2 = Iso.to_world(Vector2(float(stoves[stoves.size() - 1]["x"]), row_y))
	var min_x := minf(p0.x, p1.x) - 70
	var max_x := maxf(p0.x, p1.x) + 70
	var min_y := minf(p0.y, p1.y) - 130
	var max_y := maxf(p0.y, p1.y) + 40
	return Rect2(min_x, min_y, max_x - min_x, max_y - min_y)


func _make_steam() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.texture = Sprites.ui("puff")
	p.amount = 10
	p.lifetime = 1.4
	p.emitting = false
	p.direction = Vector2(0, -1)
	p.spread = 18.0
	p.gravity = Vector2(0, -20)
	p.initial_velocity_min = 25.0
	p.initial_velocity_max = 45.0
	p.scale_amount_min = 0.12
	p.scale_amount_max = 0.22
	var curve := Curve.new()
	curve.add_point(Vector2(0, 0.4))
	curve.add_point(Vector2(1, 1.0))
	p.scale_amount_curve = curve
	var grad := Gradient.new()
	grad.set_color(0, Color(1, 1, 1, 0.8))
	grad.set_color(1, Color(1, 1, 1, 0.0))
	p.color_ramp = grad
	p.z_index = 35
	return p


## Đồng bộ số đầu bếp với số đã thuê (tối đa bằng số bếp lò).
func refresh_chefs() -> void:
	var want: int = mini(GameState.staff_count("chef"), stoves.size())
	for i in stoves.size():
		var st: Dictionary = stoves[i]
		if i < want and st["chef"] == null:
			var c: Chef = ChefScene.instantiate()
			c.kitchen = self
			c.stove_index = i
			c.home = Vector2(float(st["x"]), row_y + 0.95)
			c.pass_spot = Vector2(pass_x, row_y + 0.95)
			area.objects.add_child(c)
			c.place(c.home)
			st["chef"] = c


func add_order(o: Dictionary) -> void:
	orders.append(o)


## Khách được chạm: đơn đang nấu của khách đó nấu nhanh gấp đôi.
func rush_order(c: Customer) -> void:
	for o in orders:
		if o["cust"] == c:
			o["rush"] = true
	for st in stoves:
		var o: Dictionary = st["order"]
		if not o.is_empty() and o["cust"] == c:
			o["rush"] = true


func _process(delta: float) -> void:
	for st in stoves:
		var chef: Chef = st["chef"]
		var o: Dictionary = st["order"]
		var bar: WorldBar = st["bar"]
		var steam: CPUParticles2D = st["steam"]
		if o.is_empty():
			# bếp rảnh + đầu bếp đã về chỗ -> nhận đơn tiếp theo
			if chef != null and chef.is_free() and not orders.is_empty():
				o = _pop_valid_order()
				if not o.is_empty():
					st["order"] = o
					var t: float = GameState.cook_time(str(o["dish"]), area.area_id)
					st["total"] = t
					st["left"] = t
					chef.start_cooking(o)
					bar.visible = true
					steam.emitting = area.visible
					if area.visible:
						AudioManager.play("sizzle", 0.1, 1.5)
		else:
			var rate: float = GameState.bal("tap_rush_mult", 2.0) if o.get("rush", false) else 1.0
			st["left"] = float(st["left"]) - delta * rate
			bar.ratio = 1.0 - float(st["left"]) / float(st["total"])
			if float(st["left"]) <= 0.0:
				st["order"] = {}
				bar.visible = false
				steam.emitting = false
				chef.finish_cooking()


func _pop_valid_order() -> Dictionary:
	while not orders.is_empty():
		var o: Dictionary = orders.pop_front()
		if is_instance_valid(o["cust"]):
			return o
	return {}


func is_cooking() -> bool:
	for st in stoves:
		if not (st["order"] as Dictionary).is_empty():
			return true
	return false


## Đầu bếp đặt món lên quầy chuyển món.
func dish_delivered_to_pass(o: Dictionary) -> void:
	var icon := Sprites.make("dish_" + str(o["dish"]))
	icon.scale = Vector2(0.22, 0.22)
	var slot: int = ready_icons.size()
	icon.position = Iso.to_world(Vector2(pass_x - 0.25 + 0.22 * (slot % 3), row_y - 0.1)) + Vector2(0, -46 - 8 * floori(slot / 3.0))
	icon.z_index = 20
	add_child(icon)
	ready_icons.append(icon)
	o["icon"] = icon
	dish_ready.emit(o)


func remove_ready_icon(o: Dictionary) -> void:
	var icon: Sprite2D = o.get("icon", null)
	if icon != null and is_instance_valid(icon):
		ready_icons.erase(icon)
		icon.queue_free()


func hit(local_pos: Vector2) -> bool:
	for st in stoves:
		var p := Iso.to_world(Vector2(float(st["x"]), row_y))
		if Rect2(p + Vector2(-70, -110), Vector2(140, 130)).has_point(local_pos):
			return true
	var a := Iso.to_world(Vector2(pass_x, row_y))
	return Rect2(a + Vector2(-70, -80), Vector2(140, 100)).has_point(local_pos)
