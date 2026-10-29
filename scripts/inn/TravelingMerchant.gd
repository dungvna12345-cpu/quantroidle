class_name TravelingMerchant
extends Walker
## Thương buôn phương xa gánh rương kho báu ghé thăm quán trọ.
## Người chơi chạm vào để mở mini-game 3 Rương Thần Bí.

signal tapped

var area: Node2D
var _sparkle_t: float = 0.0
var _active: bool = true

func _ready() -> void:
	speed = 1.6
	set_sprite("customer_tourist")
	body.modulate = Color(1.2, 1.15, 0.7)
	
	# Đèn lồng / Hào quang rực rỡ
	var aura := Sprite2D.new()
	aura.texture = Sprites.ui("sparkle")
	aura.scale = Vector2(0.8, 0.8)
	aura.position = Vector2(0, -65)
	aura.modulate = Color(1.0, 0.85, 0.2, 0.8)
	aura.z_index = -1
	add_child(aura)
	
	# Nhãn danh hiệu Thương Buôn
	var tag := Label.new()
	tag.text = "THƯƠNG BUÔN"
	tag.theme_type_variation = "WhiteLabel"
	tag.add_theme_font_size_override("font_size", 18)
	tag.add_theme_color_override("font_color", Color("ffd700"))
	tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tag.size = Vector2(180, 26)
	tag.position = Vector2(-90, -128)
	tag.z_index = 29
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tag)
	
	show_bubble("gift")

func hit_rect() -> Rect2:
	return Rect2(position.x - 45, position.y - 120, 90, 130)

func interact() -> void:
	if not _active:
		return
	_active = false
	AudioManager.play("chest_open")
	AudioManager.vibrate(30)
	show_bubble("face_heart")
	say("Đại phúc lâm môn! Hãy chọn rương báu vật!")
	tapped.emit()
	
	# Nhún nhảy vui mừng rồi tiếp tục đi
	var jt := create_tween()
	jt.tween_property(body, "scale", Vector2(1.25, 0.8), 0.1)
	jt.tween_property(body, "scale", Vector2(0.9, 1.2), 0.12)
	jt.tween_property(body, "scale", Vector2.ONE, 0.1)

func _process(delta: float) -> void:
	super(delta)
	_sparkle_t += delta
	if _sparkle_t >= 1.2:
		_sparkle_t = 0.0
		if _active and randf() < 0.4:
			say("Rương quý phương xa đây!")
