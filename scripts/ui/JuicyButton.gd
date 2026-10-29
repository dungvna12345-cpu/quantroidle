class_name JuicyButton
extends Button
## Nút bấm có hiệu ứng nảy (0.92 -> 1.05 -> 1), tiếng click và nhấp nháy nhẹ khi đủ tiền.

var sound: String = "click"
var pulse: bool = false:
	set(v):
		pulse = v
		set_process(v)
		if not v:
			self_modulate = Color.WHITE

var _t: float = 0.0
var _tween: Tween


func _ready() -> void:
	focus_mode = Control.FOCUS_NONE
	pivot_offset = size * 0.5
	resized.connect(_on_resized)
	button_down.connect(_on_down)
	button_up.connect(_on_up)
	set_process(pulse)


func _on_resized() -> void:
	pivot_offset = size * 0.5


func _on_down() -> void:
	_kill()
	_tween = create_tween()
	_tween.tween_property(self, "scale", Vector2.ONE * 0.92, 0.06)


func _on_up() -> void:
	_kill()
	_tween = create_tween()
	_tween.tween_property(self, "scale", Vector2.ONE * 1.05, 0.08)
	_tween.tween_property(self, "scale", Vector2.ONE, 0.08)
	if not sound.is_empty():
		AudioManager.play(sound)


func _kill() -> void:
	if _tween and _tween.is_valid():
		_tween.kill()


func _process(delta: float) -> void:
	if disabled:
		self_modulate = Color.WHITE
		return
	_t += delta
	var k: float = 0.5 + 0.5 * sin(_t * 5.0)
	self_modulate = Color.WHITE.lerp(Color(1.16, 1.16, 1.04), k)
