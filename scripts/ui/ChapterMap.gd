extends Control

const ChapterThemeScript := preload("res://scripts/ui/ChapterTheme.gd")
## Bản đồ hành trình dọc Việt Nam: mỗi chương là một điểm dừng (data/chapters.json -> "map_pos"),
## nối với nhau theo thứ tự chơi. Chương đã qua có dấu tích, chương hiện tại phát sáng,
## chương sau bị khoá. Chạm vào một điểm để xem chi tiết (tín hiệu `selected`).

signal selected(index: int)

const NODE_R := 34.0
# Hình dáng Việt Nam giản lược, toạ độ chuẩn hoá 0..1 trong khung bản đồ (đi theo chiều kim đồng hồ từ phía bắc).
const OUTLINE: Array[Vector2] = [
	Vector2(0.10, 0.08), Vector2(0.18, 0.04), Vector2(0.30, 0.02), Vector2(0.45, 0.03), Vector2(0.58, 0.06),
	Vector2(0.63, 0.11), Vector2(0.53, 0.17), Vector2(0.46, 0.22), Vector2(0.45, 0.28), Vector2(0.51, 0.36),
	Vector2(0.59, 0.43), Vector2(0.67, 0.50), Vector2(0.73, 0.58), Vector2(0.77, 0.66), Vector2(0.75, 0.74),
	Vector2(0.67, 0.80), Vector2(0.57, 0.86), Vector2(0.47, 0.92), Vector2(0.37, 0.97), Vector2(0.32, 0.91),
	Vector2(0.37, 0.85), Vector2(0.44, 0.80), Vector2(0.55, 0.76), Vector2(0.61, 0.66), Vector2(0.59, 0.56),
	Vector2(0.55, 0.49), Vector2(0.47, 0.43), Vector2(0.38, 0.33), Vector2(0.30, 0.27), Vector2(0.22, 0.21),
	Vector2(0.12, 0.15),
]
const ISLANDS: Array[Vector2] = [
	Vector2(0.86, 0.40), Vector2(0.89, 0.42), Vector2(0.84, 0.43),
	Vector2(0.90, 0.76), Vector2(0.93, 0.79), Vector2(0.88, 0.81),
]

var selected_index: int = 0
var _t: float = 0.0
var _bg := StyleBoxFlat.new()


func _init() -> void:
	custom_minimum_size = Vector2(0, 640)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mouse_filter = Control.MOUSE_FILTER_PASS
	_bg.bg_color = Color("cfe9f2")
	_bg.border_color = Color("9ccbdb")
	_bg.set_border_width_all(4)
	_bg.set_corner_radius_all(26)


func _ready() -> void:
	selected_index = GameState.chapter


func _process(delta: float) -> void:
	_t += delta
	if is_visible_in_tree():
		queue_redraw()


## Khung chứa bản đồ (giữ tỉ lệ dọc, căn giữa).
func _map_rect() -> Rect2:
	var h: float = size.y - 40.0
	var w: float = minf(size.x - 40.0, h * 0.72)
	return Rect2(Vector2((size.x - w) * 0.5, 20.0), Vector2(w, h))


func _px(n: Vector2) -> Vector2:
	var r := _map_rect()
	return r.position + n * r.size


func node_pos(i: int) -> Vector2:
	var mp: Array = GameState.chapter_info(i).get("map_pos", [0.5, 0.1 + 0.18 * i])
	return _px(Vector2(float(mp[0]), float(mp[1])))


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		for i in GameState.chapters_data.size():
			if node_pos(i).distance_to(event.position) <= NODE_R * 1.5:
				selected_index = i
				AudioManager.play("click")
				selected.emit(i)
				queue_redraw()
				return


func _draw() -> void:
	var g := GameState
	draw_style_box(_bg, Rect2(Vector2.ZERO, size))
	# sóng biển
	for k in 6:
		var y: float = 60.0 + k * (size.y - 100.0) / 5.0
		var x0: float = size.x * 0.70 + sin(_t * 0.8 + k) * 10.0
		draw_arc(Vector2(x0, y), 14.0, PI * 1.1, PI * 1.9, 8, Color(1, 1, 1, 0.55), 3.0)
		draw_arc(Vector2(x0 + 30.0, y + 8.0), 14.0, PI * 1.1, PI * 1.9, 8, Color(1, 1, 1, 0.4), 3.0)
	# đất liền
	var land := PackedVector2Array()
	for p in OUTLINE:
		land.append(_px(p))
	if not Geometry2D.triangulate_polygon(land).is_empty():
		draw_colored_polygon(land, Color("f6e7c8"))
	var closed := land.duplicate()
	closed.append(land[0])
	draw_polyline(closed, Color("c9a77a"), 4.0, true)
	for p in ISLANDS:
		draw_circle(_px(p), 4.0, Color("e9d3a8"))
	# tuyến đường giữa các chương
	var n: int = g.chapters_data.size()
	for i in n - 1:
		_draw_route(node_pos(i), node_pos(i + 1), i < g.chapter)
	# các điểm dừng
	var font := get_theme_default_font()
	for i in n:
		_draw_stop(i, font)


func _route_points(a: Vector2, b: Vector2) -> PackedVector2Array:
	var mid := (a + b) * 0.5
	var normal := (b - a).orthogonal().normalized()
	var ctrl := mid + normal * (a.distance_to(b) * 0.25)
	var pts := PackedVector2Array()
	for s in 25:
		var t: float = float(s) / 24.0
		pts.append(a.lerp(ctrl, t).lerp(ctrl.lerp(b, t), t))
	return pts


func _draw_route(a: Vector2, b: Vector2, done: bool) -> void:
	var pts := _route_points(a, b)
	if done:
		draw_polyline(pts, ChapterThemeScript.accent(), 7.0, true)
		return
	# đường nét đứt chạy dần cho chặng chưa đi
	var offset: int = int(_t * 4.0) % 2
	for s in pts.size() - 1:
		if (s + offset) % 2 == 0:
			draw_line(pts[s], pts[s + 1], Color("a8998a"), 5.0, true)


func _draw_stop(i: int, font: Font) -> void:
	var g := GameState
	var ch := g.chapter_info(i)
	var c := node_pos(i)
	var done := i < g.chapter
	var current := i == g.chapter
	var r: float = NODE_R * (1.15 if i == selected_index else 1.0)
	var ring: Color = Color("5aa86a") if done else (ChapterThemeScript.color("header", i) if current else Color("b9ada0"))
	if current:
		var pulse: float = 0.5 + 0.5 * sin(_t * 3.0)
		draw_circle(c, r + 10.0 + pulse * 8.0, Color(ring, 0.25 * (1.0 - pulse) + 0.1))
	if i == selected_index:
		draw_arc(c, r + 8.0, 0.0, TAU, 40, Color(1, 1, 1, 0.95), 4.0, true)
	draw_circle(c, r + 5.0, ring)
	draw_circle(c, r, Color("fffaf0"))
	var tex := Sprites.ui(str(ch.get("thumb", "")))
	if tex:
		var tint := Color.WHITE if (done or current) else Color(0.55, 0.55, 0.55, 0.85)
		draw_texture_rect(tex, Rect2(c - Vector2(r, r) * 0.8, Vector2(r, r) * 1.6), false, tint)
	var badge := c + Vector2(r * 0.75, r * 0.75)
	if done:
		draw_circle(badge, 13.0, Color("5aa86a"))
		draw_texture_rect(Sprites.ui("check"), Rect2(badge - Vector2(10, 10), Vector2(20, 20)), false)
	elif not current:
		draw_circle(badge, 13.0, Color("8f8478"))
		draw_texture_rect(Sprites.ui("lock"), Rect2(badge - Vector2(10, 10), Vector2(20, 20)), false)
	# tên chặng: bên phải nếu điểm nằm nửa trái, ngược lại bên trái
	var right_side: bool = c.x < size.x * 0.55
	var text := "%d. %s" % [i + 1, str(ch.get("city", ""))]
	var fs: int = 24
	var w: float = 220.0
	var pos := Vector2(c.x + r + 14.0, c.y + 8.0) if right_side else Vector2(c.x - r - 14.0 - w, c.y + 8.0)
	var align := HORIZONTAL_ALIGNMENT_LEFT if right_side else HORIZONTAL_ALIGNMENT_RIGHT
	draw_string_outline(font, pos, text, align, w, fs, 8, Color("fffaf0"))
	draw_string(font, pos, text, align, w, fs, Color("6f4636") if not done else Color("4e774c"))
	if current:
		var tag := "Bạn đang ở đây"
		var tp := pos + Vector2(0, 26)
		draw_string_outline(font, tp, tag, align, w, 18, 6, Color("fffaf0"))
		draw_string(font, tp, tag, align, w, 18, ChapterThemeScript.color("accent", i))
