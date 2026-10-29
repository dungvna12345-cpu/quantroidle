class_name Walker
extends Node2D
## Nhân vật đi theo danh sách điểm trên lưới isometric.
## Hoạt ảnh đi bộ: nhún + lắc nhẹ bằng code; có bong bóng cảm xúc trên đầu.

signal arrived

const BUBBLE_POS := Vector2(18, -108)
const CHAR_SCALE := 1.15   # nhân vật to hơn cho dễ nhìn
const BOB_PER_TILE := 4.4  # pha nhún (radian) mỗi ô đi được: nhịp bước theo quãng đường, không theo tốc độ

var grid: Vector2 = Vector2.ZERO
var path: PackedVector2Array = PackedVector2Array()
var speed: float = 2.5
var speed_mult: float = 1.0
var moving: bool = false
var facing: float = 1.0
var body: Sprite2D
var bubble: Sprite2D
var bubble_icon: Sprite2D
var sprite_id: String = ""

var _bob_t: float = 0.0
var _walked: float = 0.0   # quãng đường (ô) vừa đi trong khung hình này
var _bubble_kind: String = ""
var _bubble_icon_id: String = ""
var shadow: Polygon2D
var _breath_t: float = randf() * TAU   # lệch pha thở để các nhân vật không nhún cùng nhịp
var _lift: float = 0.0


func _init() -> void:
	shadow = Polygon2D.new()
	var pts := PackedVector2Array()
	for i in 20:
		var a: float = TAU * float(i) / 20.0
		pts.append(Vector2(cos(a) * 26.0, sin(a) * 9.0))
	shadow.polygon = pts
	shadow.color = Color(0.45, 0.25, 0.18, 0.2)
	shadow.position = Vector2(0, -2)
	add_child(shadow)
	body = Sprite2D.new()
	add_child(body)
	bubble = Sprite2D.new()
	bubble.z_index = 30
	bubble.position = BUBBLE_POS
	bubble.visible = false
	add_child(bubble)
	bubble_icon = Sprite2D.new()
	bubble_icon.z_index = 31
	bubble_icon.position = BUBBLE_POS + Vector2(0, -28)
	bubble_icon.visible = false
	add_child(bubble_icon)


func set_sprite(id: String) -> void:
	if id == sprite_id:
		return
	sprite_id = id
	Sprites.apply(body, id)


func place(g: Vector2) -> void:
	grid = g
	path = PackedVector2Array()
	moving = false
	position = Iso.to_world(g)


## Đi theo danh sách điểm (toạ độ lưới). Mảng rỗng => đứng yên.
func walk(points: PackedVector2Array) -> void:
	path = points
	# bỏ các điểm trùng vị trí hiện tại
	while path.size() > 0 and path[0].distance_to(grid) < 0.01:
		path.remove_at(0)
	moving = path.size() > 0
	if not moving:
		arrived.emit()


func walk_to(g: Vector2) -> void:
	walk(PackedVector2Array([g]))


func face(dir: float) -> void:
	if absf(dir) > 0.01:
		facing = signf(dir)


func _process(delta: float) -> void:
	if moving:
		var step: float = speed * speed_mult * delta
		var step0: float = step
		while step > 0.0 and path.size() > 0:
			var target: Vector2 = path[0]
			var d: float = grid.distance_to(target)
			if d <= step:
				grid = target
				step -= d
				path.remove_at(0)
			else:
				var dir: Vector2 = (target - grid) / d
				grid += dir * step
				step = 0.0
				# hướng trên màn hình: x_world tỉ lệ (dx - dy)
				face(dir.x - dir.y)
		_walked = step0 - step
		position = Iso.to_world(grid)
		if path.is_empty():
			moving = false
			arrived.emit()
	_animate(delta)


func _animate(delta: float) -> void:
	_breath_t += delta
	var squash := Vector2.ONE
	if moving:
		_bob_t += _walked * BOB_PER_TILE
		_walked = 0.0
		var hop: float = absf(sin(_bob_t))
		body.position.y = -hop * 6.0
		body.rotation = sin(_bob_t) * 0.07
		# giãn khi bật lên, dẹt khi chạm đất
		squash = Vector2(1.0 - 0.05 * hop, 1.0 + 0.07 * hop - 0.03)
		_lift = hop
	else:
		_walked = 0.0
		body.position.y = lerpf(body.position.y, 0.0, minf(1.0, delta * 12.0))
		body.rotation = lerpf(body.rotation, 0.0, minf(1.0, delta * 12.0))
		_lift = lerpf(_lift, 0.0, minf(1.0, delta * 12.0))
		# thở nhẹ khi đứng yên
		var br: float = sin(_breath_t * 2.2)
		squash = Vector2(1.0 - 0.008 * br, 1.0 + 0.014 * br)
	body.scale = Vector2(Sprites.SCALE * CHAR_SCALE * facing * squash.x, Sprites.SCALE * CHAR_SCALE * squash.y)
	# bóng nhỏ lại khi nhân vật nhấc lên
	var ss: float = 1.0 - 0.18 * _lift
	shadow.scale = Vector2(ss, ss)
	shadow.color.a = 0.2 - 0.06 * _lift


## kind: "" (ẩn), "bubble", "face_happy", "face_neutral", "face_angry", "face_heart", "bubble_zzz"
func show_bubble(kind: String, icon_id: String = "") -> void:
	if kind == _bubble_kind and icon_id == _bubble_icon_id:
		return
	_bubble_kind = kind
	_bubble_icon_id = icon_id
	if kind.is_empty():
		bubble.visible = false
		bubble_icon.visible = false
		return
	Sprites.apply(bubble, kind)
	bubble.visible = true
	Juice.pop(bubble, Vector2(Sprites.SCALE, Sprites.SCALE), 0.25)
	if icon_id.is_empty():
		bubble_icon.visible = false
	else:
		Sprites.apply(bubble_icon, icon_id)
		bubble_icon.scale = Vector2(0.3, 0.3)
		bubble_icon.visible = true


func bubble_kind() -> String:
	return _bubble_kind


## Bong bóng lời nói ngắn trên đầu (vd. "Ngon tuyệt!"), tự mờ đi.
func say(text: String) -> void:
	if text.is_empty():
		return
	var old := get_node_or_null("Say")
	if old:
		old.queue_free()
	var p := PanelContainer.new()
	p.name = "Say"
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("fffaf0")
	sb.set_corner_radius_all(16)
	sb.set_border_width_all(3)
	sb.border_color = Color("e8b49a")
	sb.content_margin_left = 12
	sb.content_margin_right = 12
	sb.content_margin_top = 2
	sb.content_margin_bottom = 4
	p.add_theme_stylebox_override("panel", sb)
	p.z_index = 45
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 20)
	l.add_theme_color_override("font_color", Color("6f4636"))
	p.add_child(l)
	add_child(p)
	p.position = Vector2(-60, -150)
	p.scale = Vector2(0.6, 0.6)
	var t := p.create_tween()
	t.tween_property(p, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_interval(2.2)
	t.tween_property(p, "modulate:a", 0.0, 0.4)
	t.tween_callback(p.queue_free)


## Hình chữ nhật để chạm (toạ độ cục bộ của khu).
func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-38, -116), Vector2(76, 120))
