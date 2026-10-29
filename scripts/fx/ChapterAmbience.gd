extends Node2D
## Không khí riêng của từng chương, vẽ đè lên cảnh quán (data/chapters.json -> "ambience"):
##   leaves   Hà Nội: lá vàng mùa thu rơi
##   lanterns Hội An: đèn lồng thả trôi lên, sáng rực về đêm
##   neon     Sài Gòn: đốm đèn neon hồng / xanh lung linh về đêm
##   fog      Đà Lạt: dải sương trôi, dày lên khi có Sương lạnh
##   royal    Huế: cánh mai vàng rơi và ánh kim lấp lánh

var mode: String = ""
var bounds: Rect2 = Rect2(-800, -200, 1600, 1200)
var _parts: Array[Dictionary] = []
var _t: float = 0.0
var _fog_level: float = 0.0


func setup(ambience: String, area_bounds: Rect2) -> void:
	mode = ambience
	bounds = area_bounds
	_parts.clear()
	var n: int = {"leaves": 16, "lanterns": 12, "neon": 18, "fog": 7, "royal": 18}.get(mode, 0)
	for i in n:
		_parts.append(_spawn(true))


func _rand_pos() -> Vector2:
	return Vector2(randf_range(bounds.position.x, bounds.end.x), randf_range(bounds.position.y, bounds.end.y))


func _spawn(anywhere: bool) -> Dictionary:
	var p := _rand_pos()
	match mode:
		"leaves", "royal":
			if not anywhere:
				p.y = bounds.position.y - 20.0
			return {"pos": p, "vy": randf_range(28.0, 55.0), "sway": randf_range(0.6, 1.6), "ph": randf() * TAU,
				"rot": randf() * TAU, "spin": randf_range(-1.6, 1.6), "size": randf_range(7.0, 12.0),
				"hue": randf()}
		"lanterns":
			if not anywhere:
				p.y = bounds.end.y + 30.0
			return {"pos": p, "vy": -randf_range(10.0, 22.0), "sway": randf_range(0.4, 0.9), "ph": randf() * TAU,
				"size": randf_range(13.0, 20.0), "hue": randf()}
		"neon":
			return {"pos": p, "vx": randf_range(-8.0, 8.0), "vy": randf_range(-6.0, 6.0), "ph": randf() * TAU,
				"size": randf_range(18.0, 46.0), "hue": randf()}
		"fog":
			if not anywhere:
				p.x = bounds.position.x - 400.0
			return {"pos": p, "vx": randf_range(10.0, 22.0), "size": randf_range(260.0, 460.0), "ph": randf() * TAU}
	return {"pos": p}


func _process(delta: float) -> void:
	if mode.is_empty():
		return
	_t += delta
	var target_fog: float = 1.0 if (mode == "fog" and GameState.feature_id() == "cold_snap" and GameState.feature_active()) else 0.0
	_fog_level = move_toward(_fog_level, target_fog, delta * 0.4)
	for i in _parts.size():
		var p: Dictionary = _parts[i]
		var pos: Vector2 = p["pos"]
		match mode:
			"leaves", "royal":
				pos.y += float(p["vy"]) * delta
				pos.x += sin(_t * float(p["sway"]) + float(p["ph"])) * 22.0 * delta
				p["rot"] = float(p["rot"]) + float(p["spin"]) * delta
				if pos.y > bounds.end.y + 20.0:
					_parts[i] = _spawn(false)
					continue
			"lanterns":
				pos.y += float(p["vy"]) * delta
				pos.x += sin(_t * float(p["sway"]) + float(p["ph"])) * 10.0 * delta
				if pos.y < bounds.position.y - 40.0:
					_parts[i] = _spawn(false)
					continue
			"neon":
				pos += Vector2(float(p["vx"]), float(p["vy"])) * delta
				if not bounds.grow(60.0).has_point(pos):
					_parts[i] = _spawn(true)
					continue
			"fog":
				pos.x += float(p["vx"]) * (1.0 + _fog_level) * delta
				if pos.x > bounds.end.x + 400.0:
					_parts[i] = _spawn(false)
					continue
		p["pos"] = pos
	queue_redraw()


func _draw() -> void:
	var night: float = GameState.night_factor()
	match mode:
		"leaves":
			for p in _parts:
				var c := Color("e8a33d").lerp(Color("c9542b"), float(p["hue"]))
				c.a = 0.85
				_ellipse(p["pos"], float(p["rot"]), float(p["size"]), float(p["size"]) * 0.45, c)
		"royal":
			for p in _parts:
				_flower(p["pos"], float(p["rot"]), float(p["size"]) * 0.55, Color(1.0, 0.82, 0.2, 0.9))
				if sin(_t * 3.0 + float(p["ph"])) > 0.92:
					draw_circle(p["pos"], 3.0, Color(1, 1, 0.85, 0.9))
		"lanterns":
			var a: float = lerpf(0.35, 1.0, night)
			if GameState.feature_id() == "lantern_night" and GameState.feature_active():
				a = 1.0
			for p in _parts:
				var pos: Vector2 = p["pos"]
				var s: float = p["size"]
				var body := Color("e4472f").lerp(Color("f2a03d"), float(p["hue"]))
				draw_circle(pos, s * 2.4, Color(1.0, 0.7, 0.3, 0.16 * a))
				draw_circle(pos, s * 1.5, Color(1.0, 0.75, 0.35, 0.22 * a))
				_ellipse(pos, 0.0, s, s * 1.2, Color(body, a))
				draw_rect(Rect2(pos + Vector2(-s * 0.5, -s * 1.3), Vector2(s, s * 0.25)), Color(0.95, 0.75, 0.25, a))
				draw_rect(Rect2(pos + Vector2(-s * 0.5, s * 1.05), Vector2(s, s * 0.25)), Color(0.95, 0.75, 0.25, a))
		"neon":
			var a: float = lerpf(0.12, 0.6, night)
			var cols: Array[Color] = [Color("ff4fa3"), Color("3fe0e8"), Color("9b6bff"), Color("ffd84f")]
			for p in _parts:
				var c: Color = cols[int(float(p["hue"]) * cols.size()) % cols.size()]
				var flick: float = 0.75 + 0.25 * sin(_t * 4.0 + float(p["ph"]))
				draw_circle(p["pos"], float(p["size"]), Color(c, 0.18 * a * flick))
				draw_circle(p["pos"], float(p["size"]) * 0.45, Color(c, 0.35 * a * flick))
		"fog":
			var a: float = lerpf(0.10, 0.34, _fog_level)
			for p in _parts:
				var w: float = p["size"]
				var breath: float = 0.85 + 0.15 * sin(_t * 0.5 + float(p["ph"]))
				_ellipse(p["pos"], 0.0, w, w * 0.22, Color(0.96, 0.98, 1.0, a * breath))
				_ellipse(p["pos"] + Vector2(w * 0.3, -w * 0.06), 0.0, w * 0.6, w * 0.16, Color(1, 1, 1, a * 0.8 * breath))


func _ellipse(pos: Vector2, rot: float, rx: float, ry: float, c: Color) -> void:
	draw_set_transform(pos, rot, Vector2(1.0, ry / maxf(0.01, rx)))
	draw_circle(Vector2.ZERO, rx, c)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _flower(pos: Vector2, rot: float, r: float, c: Color) -> void:
	for k in 5:
		var ang: float = rot + TAU * float(k) / 5.0
		_ellipse(pos + Vector2(cos(ang), sin(ang)) * r, ang, r, r * 0.6, c)
	draw_circle(pos, r * 0.45, Color(0.85, 0.45, 0.1, c.a))
