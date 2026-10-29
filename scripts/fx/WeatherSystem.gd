extends Node2D
## Hệ thống Thời Tiết & Ánh Sáng Tuyệt Đẹp cho Quán Trọ Idle.
## 3 Chế độ: Nắng Hoa Rơi, Mưa Rào Phố Cổ, Đêm Trăng Đom Đóm Phát Sáng (chỉ là hiệu ứng hình ảnh).

enum WeatherType { PETALS, RAIN, FIREFLIES }

var current_weather: WeatherType = WeatherType.PETALS
var weather_timer: float = 85.0
var _bounds: Rect2 = Rect2(-300, -200, 1000, 1400)

# Cấu trúc cho cánh hoa / hạt mưa / đom đóm
var _particles: Array[Dictionary] = []
var _ripples: Array[Dictionary] = []

func _ready() -> void:
	z_index = 80
	set_process(true)
	_setup_weather(WeatherType.PETALS)

func _process(delta: float) -> void:
	weather_timer -= delta
	if weather_timer <= 0.0:
		weather_timer = randf_range(80.0, 120.0)
		_cycle_weather()
		
	# Cập nhật hạt
	match current_weather:
		WeatherType.PETALS:
			_update_petals(delta)
		WeatherType.RAIN:
			_update_rain(delta)
		WeatherType.FIREFLIES:
			_update_fireflies(delta)
			
	# Cập nhật gợn sóng nước mưa
	var alive_ripples: Array[Dictionary] = []
	for r in _ripples:
		r["radius"] += delta * 45.0
		r["alpha"] -= delta * 1.4
		if r["alpha"] > 0.0:
			alive_ripples.append(r)
	_ripples = alive_ripples
	
	queue_redraw()

func _cycle_weather() -> void:
	if GameState.is_evening():
		_setup_weather(WeatherType.FIREFLIES)
	else:
		var next_w := WeatherType.RAIN if current_weather == WeatherType.PETALS else WeatherType.PETALS
		_setup_weather(next_w)

func _setup_weather(w: WeatherType) -> void:
	current_weather = w
	_particles.clear()
	_ripples.clear()
	
	match w:
		WeatherType.PETALS:
			for i in 25:
				_particles.append({
					"pos": Vector2(randf_range(_bounds.position.x, _bounds.end.x), randf_range(_bounds.position.y, _bounds.end.y)),
					"vel": Vector2(randf_range(15.0, 35.0), randf_range(25.0, 45.0)),
					"rot": randf() * TAU,
					"rot_vel": randf_range(-2.0, 2.0),
					"scale": randf_range(4.0, 8.0),
					"color": Color("ffa8b8") if randf() < 0.6 else Color("ffd1dc")
				})
		WeatherType.RAIN:
			for i in 60:
				_particles.append({
					"pos": Vector2(randf_range(_bounds.position.x, _bounds.end.x), randf_range(_bounds.position.y, _bounds.end.y)),
					"speed": randf_range(450.0, 650.0),
					"length": randf_range(16.0, 28.0)
				})
			GameState.show_toast("🌧️ MƯA RÀO PHỐ CỔ: Thực khách ghé quán trú mưa thưởng thức món nóng sốt!")
			AudioManager.play("whoosh")
		WeatherType.FIREFLIES:
			for i in 20:
				_particles.append({
					"base_pos": Vector2(randf_range(_bounds.position.x, _bounds.end.x), randf_range(_bounds.position.y, _bounds.end.y)),
					"phase_x": randf() * TAU,
					"phase_y": randf() * TAU,
					"speed_x": randf_range(0.8, 1.8),
					"speed_y": randf_range(0.6, 1.4),
					"pulse_phase": randf() * TAU,
					"radius": randf_range(25.0, 55.0)
				})

func _update_petals(delta: float) -> void:
	for p in _particles:
		p["pos"] += p["vel"] * delta
		p["rot"] += p["rot_vel"] * delta
		if p["pos"].y > _bounds.end.y:
			p["pos"].y = _bounds.position.y - 10.0
			p["pos"].x = randf_range(_bounds.position.x, _bounds.end.x)
		if p["pos"].x > _bounds.end.x:
			p["pos"].x = _bounds.position.x

func _update_rain(delta: float) -> void:
	var angle_vec := Vector2(-0.35, 1.0).normalized()
	for p in _particles:
		p["pos"] += angle_vec * p["speed"] * delta
		if p["pos"].y > _bounds.end.y:
			p["pos"].y = _bounds.position.y - randf_range(10.0, 50.0)
			p["pos"].x = randf_range(_bounds.position.x, _bounds.end.x)
			if randf() < 0.25:
				_ripples.append({
					"pos": p["pos"] + Vector2(0, randf_range(400.0, 600.0)),
					"radius": 2.0,
					"alpha": 0.65
				})

func _update_fireflies(delta: float) -> void:
	for p in _particles:
		p["phase_x"] += p["speed_x"] * delta
		p["phase_y"] += p["speed_y"] * delta
		p["pulse_phase"] += delta * 2.5

func _draw() -> void:
	match current_weather:
		WeatherType.PETALS:
			for p in _particles:
				var s: float = float(p["scale"])
				var pts := PackedVector2Array([
					Vector2(0, -s),
					Vector2(s * 0.6, 0),
					Vector2(0, s),
					Vector2(-s * 0.6, 0)
				])
				draw_set_transform(p["pos"] as Vector2, float(p["rot"]), Vector2.ONE)
				draw_colored_polygon(pts, p["color"] as Color)
				draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
				
		WeatherType.RAIN:
			var angle_vec := Vector2(-0.35, 1.0).normalized()
			var col := Color(0.75, 0.88, 1.0, 0.42)
			for p in _particles:
				var start: Vector2 = p["pos"]
				var end: Vector2 = start + angle_vec * float(p["length"])
				draw_line(start, end, col, 1.5, true)
			for r in _ripples:
				var r_col := Color(0.8, 0.92, 1.0, float(r["alpha"]))
				draw_arc(r["pos"] as Vector2, float(r["radius"]), 0.0, TAU, 16, r_col, 1.2, true)
				
		WeatherType.FIREFLIES:
			for p in _particles:
				var px: float = float(p["phase_x"])
				var py: float = float(p["phase_y"])
				var rad: float = float(p["radius"])
				var offset: Vector2 = Vector2(cos(px), sin(py)) * rad
				var center: Vector2 = (p["base_pos"] as Vector2) + offset
				var alpha: float = (sin(float(p["pulse_phase"])) * 0.5 + 0.5) * 0.75 + 0.25
				# Vòng sáng đom đóm
				draw_circle(center, 7.0, Color(0.85, 1.0, 0.3, alpha * 0.35))
				draw_circle(center, 2.5, Color(1.0, 1.0, 0.6, alpha))
