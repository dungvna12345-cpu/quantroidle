class_name Shipper
extends Walker
## Shipper giao đồ ăn (cơ chế chương Sài Gòn): chạy tới cổng, chờ một lúc rồi đi.
## Người chơi chạm vào khi shipper đang chờ để giao đơn và nhận tiền ngay.

signal left   # đã rời khỏi màn hình, InnArea giải phóng node

var wait_time: float = 20.0
var exit_point: Vector2 = Vector2(-6, 0)
var _state: String = "coming"   # coming -> waiting -> leaving
var _wait_left: float = 0.0


func _ready() -> void:
	speed = 2.4
	set_sprite("cust_3")
	body.modulate = Color(0.75, 1.0, 0.85)
	var tag := Label.new()
	tag.text = "🛵 SHIPPER"
	tag.theme_type_variation = "WhiteLabel"
	tag.add_theme_font_size_override("font_size", 18)
	tag.add_theme_color_override("font_color", Color("7cf2c4"))
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tag.size = Vector2(180, 26)
	tag.position = Vector2(-90, -128)
	tag.z_index = 29
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tag)
	arrived.connect(_on_arrived)


func can_deliver() -> bool:
	return _state == "waiting"


func hit_rect() -> Rect2:
	return Rect2(position.x - 45, position.y - 120, 90, 130)


func _on_arrived() -> void:
	match _state:
		"coming":
			_state = "waiting"
			_wait_left = wait_time
			show_bubble("bubble", "icon_order")
			say("Có đơn giao không chủ quán ơi?")
		"leaving":
			left.emit()


## Chạm vào shipper: giao đơn, nhận tiền, shipper chạy đi.
func deliver() -> float:
	if _state != "waiting":
		return 0.0
	var g := GameState.claim_delivery()
	AudioManager.play("coin")
	AudioManager.vibrate(25)
	show_bubble("face_heart")
	say("Giao liền nha! +%s" % NumberFormat.fmt(g))
	var jt := create_tween()
	jt.tween_property(body, "scale", Vector2(1.2, 0.85), 0.1)
	jt.tween_property(body, "scale", Vector2.ONE, 0.12)
	_leave()
	return g


func _leave() -> void:
	_state = "leaving"
	walk(PackedVector2Array([exit_point]))


func _process(delta: float) -> void:
	super(delta)
	if _state == "waiting":
		_wait_left -= delta
		if _wait_left <= 0.0:
			show_bubble("face_neutral")
			say("Thôi chạy đơn khác vậy...")
			_leave()
