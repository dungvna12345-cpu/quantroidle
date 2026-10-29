class_name ResourcePill
extends Control
## Ô đếm vàng / kim cương: thanh nâu trong mờ, icon to đè mép trái, nút "+" xanh nhỏ.
## Số chạy tăng dần tới giá trị thật (không nhảy cóc).

signal plus_pressed

var icon_rect: TextureRect
var value_label: Label
var plus_button: JuicyButton
var target: float = 0.0
var shown: float = 0.0
var icon_id: String = "coin"
var show_plus: bool = true


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if custom_minimum_size == Vector2.ZERO:
		custom_minimum_size = Vector2(200, 64)
	var bar := PanelContainer.new()
	bar.theme_type_variation = "CounterBar"
	bar.set_anchors_preset(Control.PRESET_FULL_RECT)
	bar.offset_left = 26
	bar.offset_top = 10
	bar.offset_bottom = -6
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bar)
	value_label = UIKit.label("0", "ResourceLabel", 26)
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	value_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	bar.add_child(value_label)
	icon_rect = UIKit.icon(icon_id, 64)
	icon_rect.position = Vector2(0, 0)
	icon_rect.size = Vector2(64, 64)
	add_child(icon_rect)
	if show_plus:
		plus_button = UIKit.button("", "IconButton", "plus_green")
		plus_button.custom_minimum_size = Vector2(34, 34)
		plus_button.size = Vector2(34, 34)
		plus_button.position = Vector2(38, 36)
		plus_button.add_theme_constant_override("icon_max_width", 34)
		plus_button.pressed.connect(func() -> void: plus_pressed.emit())
		add_child(plus_button)
	_render()


func set_target(v: float, instant: bool = false) -> void:
	target = v
	if instant:
		shown = v
		_render()


func _process(delta: float) -> void:
	if is_equal_approx(shown, target):
		return
	# tiến dần về giá trị thật, luôn có bước tối thiểu để không kéo dài mãi
	var diff: float = target - shown
	var step: float = diff * minf(1.0, delta * 7.0)
	if absf(step) < 1.0:
		step = signf(diff) * minf(absf(diff), maxf(1.0, absf(diff) * delta * 20.0))
	shown += step
	if absf(target - shown) < 0.5:
		shown = target
	_render()


func _render() -> void:
	if value_label:
		value_label.text = NumberFormat.fmt(shown)


func icon_center() -> Vector2:
	return icon_rect.get_global_rect().get_center()


func bump() -> void:
	Juice.bounce(icon_rect, 1.4)
