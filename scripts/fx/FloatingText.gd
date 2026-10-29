class_name FloatingText
extends Label
## Chữ nổi lên rồi mờ dần (vd. "+12" khi nhận vàng).

var start: Vector2 = Vector2.ZERO
var color: Color = Color("ffe27a")


func _ready() -> void:
	theme_type_variation = "WhiteLabel"
	if not has_theme_font_size_override("font_size"):
		add_theme_font_size_override("font_size", 32)
	add_theme_color_override("font_color", color)
	add_theme_constant_override("outline_size", 9)
	horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	size = Vector2(240, 44)
	position = start - Vector2(120, 22)
	pivot_offset = size * 0.5
	scale = Vector2(0.5, 0.5)
	var t := create_tween().set_parallel(true)
	t.tween_property(self, "scale", Vector2.ONE, 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	t.tween_property(self, "position:y", position.y - 70.0, 0.9).set_ease(Tween.EASE_OUT)
	t.tween_property(self, "modulate:a", 0.0, 0.35).set_delay(0.6)
	t.chain().tween_callback(queue_free)
