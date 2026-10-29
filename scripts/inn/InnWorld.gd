class_name InnWorld
extends Node2D
## Thế giới chứa các khu của quán + camera: kéo để di chuyển, chụm 2 ngón / lăn chuột để phóng to, có giới hạn biên.

signal object_tapped(area_id: String, kind: String, index: int)

const AreaScene := preload("res://scenes/inn/InnArea.tscn")
const AREA_SPACING := 4000.0
const DRAG_THRESHOLD := 14.0

var camera: Camera2D
var areas: Dictionary = {}       # id -> InnArea
var input_enabled: bool = true
var zoom_level: float = 0.7
var zoom_min: float = 0.45
var zoom_max: float = 1.6

var _touches: Dictionary = {}
var _pressed: bool = false
var _dragging: bool = false
var _press_pos: Vector2 = Vector2.ZERO
var _pinch_dist: float = 0.0
var _pinch_zoom: float = 1.0
var _current: InnArea
var day_tint: CanvasModulate


func _ready() -> void:
	camera = Camera2D.new()
	add_child(camera)
	# màu trời theo giờ trong ngày (chỉ ảnh hưởng cảnh, không ảnh hưởng giao diện)
	day_tint = CanvasModulate.new()
	add_child(day_tint)
	camera.make_current()
	for i in GameState.areas_data.size():
		var id: String = GameState.areas_data[i]["id"]
		var a: InnArea = AreaScene.instantiate()
		a.position = Vector2(i * AREA_SPACING, 0)
		a.visible = false
		add_child(a)
		a.setup(id)
		a.object_tapped.connect(_on_object_tapped)
		areas[id] = a
	show_area(GameState.current_area, true)
	get_viewport().size_changed.connect(_on_resize)


func _process(_delta: float) -> void:
	day_tint.color = GameState.day_tint()


func _on_object_tapped(area_id: String, kind: String, index: int) -> void:
	object_tapped.emit(area_id, kind, index)


func current() -> InnArea:
	return _current


func show_area(id: String, reset_view: bool = true) -> void:
	if not areas.has(id):
		id = "hall"
	for k: String in areas:
		(areas[k] as InnArea).visible = k == id
	_current = areas[id]
	if reset_view:
		_fit_zoom()
		camera.position = _current.position + _current.focus_point()
		_apply_camera()


func _fit_zoom() -> void:
	var vw: float = get_viewport_rect().size.x
	var area_w: float = (_current.base_w() + _current.size_h) * Iso.HALF_W
	var fit: float = vw / (area_w * 0.82)
	zoom_min = clampf(fit * 0.7, 0.3, 1.0)
	zoom_max = 1.7
	zoom_level = clampf(fit * 1.5, zoom_min, zoom_max)


func _on_resize() -> void:
	if _current:
		_apply_camera()


func screen_to_world(p: Vector2) -> Vector2:
	var vs: Vector2 = get_viewport_rect().size
	return camera.position + (p - vs * 0.5) / zoom_level


func world_to_screen(p: Vector2) -> Vector2:
	var vs: Vector2 = get_viewport_rect().size
	return (p - camera.position) * zoom_level + vs * 0.5


func _apply_camera() -> void:
	camera.zoom = Vector2(zoom_level, zoom_level)
	# giữ camera trong biên của khu đang xem
	var b: Rect2 = _current.bounds()
	b.position += _current.position
	var half: Vector2 = get_viewport_rect().size * 0.5 / zoom_level
	var p := camera.position
	if b.size.x <= half.x * 2.0:
		p.x = b.get_center().x
	else:
		p.x = clampf(p.x, b.position.x + half.x, b.end.x - half.x)
	if b.size.y <= half.y * 2.0:
		p.y = b.get_center().y
	else:
		p.y = clampf(p.y, b.position.y + half.y, b.end.y - half.y)
	camera.position = p


func _zoom_at(screen_pos: Vector2, new_zoom: float) -> void:
	var before := screen_to_world(screen_pos)
	zoom_level = clampf(new_zoom, zoom_min, zoom_max)
	var after := screen_to_world(screen_pos)
	camera.position += before - after
	_apply_camera()


func _unhandled_input(event: InputEvent) -> void:
	if not input_enabled or _current == null:
		_pressed = false
		_touches.clear()
		return
	if event is InputEventScreenTouch:
		var st := event as InputEventScreenTouch
		if st.pressed:
			_touches[st.index] = st.position
		else:
			_touches.erase(st.index)
		if _touches.size() == 2:
			_start_pinch()
	elif event is InputEventScreenDrag:
		var sd := event as InputEventScreenDrag
		_touches[sd.index] = sd.position
		if _touches.size() >= 2:
			_update_pinch()
	elif event is InputEventMagnifyGesture:
		var mg := event as InputEventMagnifyGesture
		_zoom_at(mg.position, zoom_level * mg.factor)
	elif event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_WHEEL_UP and mb.pressed:
			_zoom_at(mb.position, zoom_level * 1.1)
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN and mb.pressed:
			_zoom_at(mb.position, zoom_level / 1.1)
		elif mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_pressed = true
				_dragging = false
				_press_pos = mb.position
			else:
				if _pressed and not _dragging and _touches.size() < 2:
					_tap(mb.position)
				_pressed = false
	elif event is InputEventMouseMotion and _pressed:
		var mm := event as InputEventMouseMotion
		if _touches.size() >= 2:
			_dragging = true
			return
		if not _dragging and mm.position.distance_to(_press_pos) > DRAG_THRESHOLD:
			_dragging = true
		if _dragging:
			camera.position -= mm.relative / zoom_level
			_apply_camera()


func _start_pinch() -> void:
	var pts: Array = _touches.values()
	_pinch_dist = maxf(1.0, (pts[0] as Vector2).distance_to(pts[1]))
	_pinch_zoom = zoom_level
	_dragging = true


func _update_pinch() -> void:
	var pts: Array = _touches.values()
	var a: Vector2 = pts[0]
	var b: Vector2 = pts[1]
	var d: float = maxf(1.0, a.distance_to(b))
	_zoom_at((a + b) * 0.5, _pinch_zoom * d / _pinch_dist)


func _tap(screen_pos: Vector2) -> void:
	var w := screen_to_world(screen_pos)
	_current.tap(_current.to_local(w))


## Vị trí màn hình của một điểm thế giới (dùng cho hiệu ứng UI).
func global_to_screen(p: Vector2) -> Vector2:
	return world_to_screen(p)
