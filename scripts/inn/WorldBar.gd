class_name WorldBar
extends Node2D
## Thanh tiến độ nhỏ trong cảnh (trên bếp lò, trên khách đang ăn, trên quầy thu ngân).

var bar_width: float = 64.0
var bar_height: float = 13.0
var fill_color: Color = Color("7bd35b")
var ratio: float = 0.0:
	set(v):
		ratio = clampf(v, 0.0, 1.0)
		queue_redraw()

var _bg: StyleBoxFlat
var _fg: StyleBoxFlat


func _ready() -> void:
	z_index = 40
	_bg = StyleBoxFlat.new()
	_bg.bg_color = Color(0.23, 0.14, 0.09, 0.85)
	_bg.set_corner_radius_all(7)
	_bg.border_color = Color("3a2416")
	_bg.set_border_width_all(2)
	_fg = StyleBoxFlat.new()
	_fg.bg_color = fill_color
	_fg.set_corner_radius_all(5)
	_fg.border_color = fill_color.darkened(0.3)
	_fg.border_width_bottom = 3


func _draw() -> void:
	var r := Rect2(-bar_width * 0.5, -bar_height * 0.5, bar_width, bar_height)
	draw_style_box(_bg, r)
	if ratio > 0.01:
		var inner := r.grow(-2.0)
		inner.size.x = maxf(inner.size.y, inner.size.x * ratio)
		draw_style_box(_fg, inner)
