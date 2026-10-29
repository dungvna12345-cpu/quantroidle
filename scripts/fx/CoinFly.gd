class_name CoinFly
extends TextureRect
## Đồng vàng bay theo đường cong từ vị trí trong quán lên ô vàng trên cùng.

signal landed

var from: Vector2 = Vector2.ZERO
var to: Vector2 = Vector2.ZERO
var delay: float = 0.0
var _ctrl: Vector2 = Vector2.ZERO


func _ready() -> void:
	texture = Sprites.ui("coin")
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	size = Vector2(44, 44)
	pivot_offset = size * 0.5
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	position = from - size * 0.5
	# điểm điều khiển lệch ngang ngẫu nhiên để các đồng xu bay toả ra
	_ctrl = from.lerp(to, 0.35) + Vector2(randf_range(-160, 160), randf_range(-60, 120))
	scale = Vector2(0.4, 0.4)
	var t := create_tween()
	if delay > 0.0:
		modulate.a = 0.0
		t.tween_interval(delay)
		t.tween_property(self, "modulate:a", 1.0, 0.01)
	t.tween_property(self, "scale", Vector2(1.15, 1.15), 0.12).set_trans(Tween.TRANS_BACK)
	t.tween_method(_move, 0.0, 1.0, 0.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	t.tween_callback(_finish)


func _move(k: float) -> void:
	var a := from.lerp(_ctrl, k)
	var b := _ctrl.lerp(to, k)
	position = a.lerp(b, k) - size * 0.5
	scale = Vector2.ONE * lerpf(1.15, 0.7, k)
	rotation = k * TAU * 0.5


func _finish() -> void:
	landed.emit()
	queue_free()
