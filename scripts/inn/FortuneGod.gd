class_name FortuneGod
extends Walker
## Thần Tài Giá Đáo:
## Xuất hiện dọc lối đi với hào quang vàng rực rỡ, phát lộc cho quán trọ.
## Khi người chơi chạm vào Thần Tài, kích hoạt Minigame "MƯA LÌ XÌ THẦN TÀI"!

signal tapped

var area: Node2D
var _active: bool = true
var _t: float = 0.0
var _custom_draw: Node2D

func _init() -> void:
	super()
	body.visible = false # Vẽ riêng bằng custom draw
	_custom_draw = Node2D.new()
	_custom_draw.draw.connect(_draw_fortune_god)
	add_child(_custom_draw)
	speed = 1.3

func _ready() -> void:
	show_bubble("sparkle")

func hit_rect() -> Rect2:
	return Rect2(position.x - 50, position.y - 130, 100, 140)

func interact() -> void:
	if not _active:
		return
	_active = false
	moving = false
	AudioManager.play("legendary")
	AudioManager.play("levelup", 0.15)
	AudioManager.vibrate(50)
	show_bubble("face_heart")
	say("ĐẠI CÁT ĐẠI LỢI! Thần Tài ban phước lành! 🧧✨")
	
	# Nhún nhảy chào phúc
	var tw := create_tween()
	tw.tween_property(self, "scale", Vector2(1.25, 1.25), 0.15)
	tw.tween_property(self, "scale", Vector2.ONE, 0.15)
	tw.tween_callback(func():
		tapped.emit()
		# đi tiếp ra khỏi đường để `arrived` giải phóng node, Thần Tài mới mới xuất hiện lại được
		moving = path.size() > 0
	)


func is_active() -> bool:
	return _active

func _process(delta: float) -> void:
	super(delta)
	_t += delta * 3.5
	if _custom_draw:
		_custom_draw.queue_redraw()

func _draw_fortune_god() -> void:
	var flip: float = facing
	var bob := sin(_t) * 3.0
	var c := Vector2(0, -32 + bob)

	# 1. Hào quang vàng Thần Tài xoay vòng
	var aura_rad := 38.0 + sin(_t * 1.5) * 4.0
	_custom_draw.draw_circle(c, aura_rad, Color(1.0, 0.85, 0.2, 0.35))
	_custom_draw.draw_arc(c, aura_rad + 4.0, 0, TAU, 24, Color(1.0, 0.9, 0.4, 0.5), 2.5)

	# 2. Áo gấm đỏ Thần Tài (Long bào đỏ viền vàng)
	var robe_pts := PackedVector2Array([
		c + Vector2(-18 * flip, 14),
		c + Vector2(-24 * flip, 38),
		c + Vector2(24 * flip, 38),
		c + Vector2(18 * flip, 14)
	])
	_custom_draw.draw_colored_polygon(robe_pts, Color("dc2626")) # Đỏ rực
	_custom_draw.draw_line(c + Vector2(-24 * flip, 38), c + Vector2(24 * flip, 38), Color("facc15"), 4.0) # Viền vàng
	_custom_draw.draw_line(c + Vector2(0, 14), c + Vector2(0, 38), Color("facc15"), 3.0)

	# Thắt lưng ngọc bích
	_custom_draw.draw_line(c + Vector2(-16 * flip, 22), c + Vector2(16 * flip, 22), Color("15803d"), 5.0)
	_custom_draw.draw_circle(c + Vector2(0, 22), 4.5, Color("facc15"))

	# 3. Đầu & Khuôn mặt phúc hậu
	var head_c := c + Vector2(0, -10)
	_custom_draw.draw_circle(head_c, 18.0, Color("fef3c7"))

	# Má hồng phúc hậu
	_custom_draw.draw_circle(head_c + Vector2(-10 * flip, 3), 4.5, Color(1.0, 0.6, 0.6, 0.6))
	_custom_draw.draw_circle(head_c + Vector2(10 * flip, 3), 4.5, Color(1.0, 0.6, 0.6, 0.6))

	# Mắt cười tít hình trăng khuyết
	_custom_draw.draw_arc(head_c + Vector2(-7 * flip, -2), 4.5, PI * 1.1, PI * 1.9, 8, Color("451a03"), 2.5)
	_custom_draw.draw_arc(head_c + Vector2(7 * flip, -2), 4.5, PI * 1.1, PI * 1.9, 8, Color("451a03"), 2.5)

	# Miệng cười tươi rói
	_custom_draw.draw_arc(head_c + Vector2(0, 5), 5.5, 0, PI, 10, Color("b91c1c"), 2.5)

	# Râu dài trắng như cước
	var beard_pts := PackedVector2Array([
		head_c + Vector2(-8 * flip, 8),
		head_c + Vector2(8 * flip, 8),
		head_c + Vector2(0, 26)
	])
	_custom_draw.draw_colored_polygon(beard_pts, Color("f8fafc"))

	# 4. Mũ Cánh Chuồn Thần Tài
	var hat_c := head_c + Vector2(0, -16)
	var hat_box := PackedVector2Array([
		hat_c + Vector2(-16 * flip, 6),
		hat_c + Vector2(-12 * flip, -14),
		hat_c + Vector2(12 * flip, -14),
		hat_c + Vector2(16 * flip, 6)
	])
	_custom_draw.draw_colored_polygon(hat_box, Color("1e1b4b")) # Đen nhung quan trạng
	_custom_draw.draw_circle(hat_c + Vector2(0, -4), 5.0, Color("facc15")) # Ngọc vàng giữa mũ

	# Hai cánh chuồn vươn dài hai bên
	_custom_draw.draw_line(hat_c + Vector2(-12 * flip, -4), hat_c + Vector2(-36 * flip, -6), Color("1e1b4b"), 6.0)
	_custom_draw.draw_circle(hat_c + Vector2(-36 * flip, -6), 5.0, Color("facc15"))
	_custom_draw.draw_line(hat_c + Vector2(12 * flip, -4), hat_c + Vector2(36 * flip, -6), Color("1e1b4b"), 6.0)
	_custom_draw.draw_circle(hat_c + Vector2(36 * flip, -6), 5.0, Color("facc15"))

	# 5. Tay cầm Kim Nguyên Bảo (Thỏi vàng lấp lánh)
	var ingot_c := c + Vector2(18 * flip, 10)
	_custom_draw.draw_circle(ingot_c, 8.0, Color("facc15"))
	_custom_draw.draw_line(ingot_c + Vector2(-10, 0), ingot_c + Vector2(10, 0), Color("eab308"), 4.0)
	_custom_draw.draw_circle(ingot_c + Vector2(0, -4), 4.5, Color("fef08a"))

	# Tay còn lại cầm cuốn thư "PHÚC"
	var scroll_c := c + Vector2(-18 * flip, 12)
	_custom_draw.draw_rect(Rect2(scroll_c.x - 6, scroll_c.y - 12, 12, 24), Color("b91c1c"))
	_custom_draw.draw_rect(Rect2(scroll_c.x - 7, scroll_c.y - 14, 14, 4), Color("facc15"))
	_custom_draw.draw_rect(Rect2(scroll_c.x - 7, scroll_c.y + 10, 14, 4), Color("facc15"))
