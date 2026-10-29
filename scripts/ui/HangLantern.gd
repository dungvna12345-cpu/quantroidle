class_name HangLantern
extends Node2D
## Đèn lồng treo vẽ bằng code (gốc ở đỉnh dây treo, toạ độ (0,0)), có quầng sáng ấm.
## Dùng để trang trí khung popup; xoay quanh gốc để đung đưa.

var body_col: Color = Color("f58274")
var light_col: Color = Color("ffc2a8")
var trim_col: Color = Color("d9a574")
var ink_col: Color = Color("a8644a")
var glow: float = 0.0
var _t: float = randf() * TAU


func _process(delta: float) -> void:
	_t += delta
	var g: float = 0.5 + 0.5 * sin(_t * 2.4)
	if absf(g - glow) > 0.02:
		glow = g
		queue_redraw()


func _ellipse(c: Vector2, rx: float, ry: float, n: int = 28) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var a: float = TAU * float(i) / float(n)
		pts.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


func _draw() -> void:
	var c := Vector2(0, 58)
	# quầng sáng nhấp nháy
	draw_circle(c, 46.0, Color(1.0, 0.82, 0.55, 0.10 + 0.07 * glow))
	draw_circle(c, 32.0, Color(1.0, 0.86, 0.6, 0.12 + 0.08 * glow))
	# dây treo + nắp trên
	draw_line(Vector2(0, 0), Vector2(0, 24), ink_col, 3.0)
	draw_colored_polygon(_ellipse(Vector2(0, 28), 11.0, 6.0, 16), trim_col)
	# thân đèn
	draw_colored_polygon(_ellipse(c, 21.0, 27.0), body_col)
	draw_colored_polygon(_ellipse(c + Vector2(-5, -6), 11.0, 16.0), light_col)
	draw_colored_polygon(_ellipse(c + Vector2(0, 2), 9.0, 18.0), Color(1.0, 0.93, 0.7, 0.35 + 0.25 * glow))
	# gân đèn
	for k: float in [-0.55, 0.0, 0.55]:
		var pts := PackedVector2Array()
		for i in 13:
			var t: float = float(i) / 12.0
			var y: float = lerpf(-27.0, 27.0, t)
			var w: float = sqrt(maxf(0.0, 1.0 - (y / 27.0) * (y / 27.0))) * 21.0 * k
			pts.append(c + Vector2(w, y))
		draw_polyline(pts, Color(ink_col.r, ink_col.g, ink_col.b, 0.55), 1.6, true)
	draw_polyline(_ellipse(c, 21.0, 27.0, 28) + PackedVector2Array([c + Vector2(21.0, 0)]), ink_col, 2.4, true)
	# nắp dưới + tua rua
	draw_colored_polygon(_ellipse(Vector2(0, 86), 11.0, 6.0, 16), trim_col)
	draw_line(Vector2(0, 90), Vector2(0, 106), Color("ffb347"), 3.0)
	draw_circle(Vector2(0, 108), 4.0, Color("ffb347"))
