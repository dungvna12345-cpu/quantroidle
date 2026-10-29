class_name SunRays
extends Node2D
## Tia nắng xoay chậm phía sau ngôi sao/huy hiệu; mờ dần ra phía ngoài.

var radius: float = 130.0
var rays: int = 12
var tint: Color = Color("ffd98a")
var spin_speed: float = 0.35


func _process(delta: float) -> void:
	rotation += delta * spin_speed


func _draw() -> void:
	for i in rays:
		var a0: float = TAU * float(i) / float(rays)
		var a1: float = a0 + TAU / float(rays) * 0.5
		var pts := PackedVector2Array([Vector2.ZERO, Vector2(cos(a0), sin(a0)) * radius, Vector2(cos(a1), sin(a1)) * radius])
		var cols := PackedColorArray([
			Color(tint.r, tint.g, tint.b, 0.55),
			Color(tint.r, tint.g, tint.b, 0.0),
			Color(tint.r, tint.g, tint.b, 0.0)])
		draw_polygon(pts, cols)
