class_name SneakyThief
extends Walker
## Chuột Nhắt Tinh Nghịch / Kẻ Trộm Vặt:
## Lẻn vào quán trọ vác theo bao vàng, chạy dọc các lối đi.
## Người chơi phải chạm 3 lần để bắt trộm trước khi trộm thoát!

signal caught(thief: SneakyThief)
signal escaped(thief: SneakyThief)

var area: InnArea
var hp: int = 3
var max_hp: int = 3
var escape_timer: float = 15.0
var _anim_t: float = 0.0
var _defeated: bool = false
var body_draw: Node2D

func _init() -> void:
	super()
	body_draw = Node2D.new()
	add_child(body_draw)
	body_draw.draw.connect(_draw_thief)
	body.visible = false # ẩn walker sprite mặc định
	arrived.connect(_on_arrived)


func setup(a: InnArea, start_grid: Vector2, target_grid: Vector2) -> void:
	area = a
	speed = 1.6
	place(start_grid)
	walk_to(target_grid)
	show_bubble("face_neutral")
	AudioManager.play("bell", 0.1)


func _process(delta: float) -> void:
	if _defeated:
		return
	super(delta)
	_anim_t += delta * (12.0 if moving else 4.0)
	body_draw.queue_redraw()

	escape_timer -= delta
	if escape_timer <= 0.0 and not _defeated:
		_escape()


func hit() -> bool:
	if _defeated or hp <= 0:
		return false
	hp -= 1
	AudioManager.play_pitch("pop", 1.4 + (3 - hp) * 0.2)
	AudioManager.play("coin", 0.1)
	Juice.bounce(self, 1.3)
	speed += 0.4 # Chạy nhanh hơn khi bị phát hiện!

	# Rơi tiền xu tức thì
	var drop_gold := maxf(50.0, GameState.income_rate() * 5.0)
	GameState.add_gold(drop_gold)
	if UIKit.main:
		UIKit.main.call("sparkle_at_world", global_position + Vector2(0, -30))

	if hp > 0:
		var squeaks := ["Chít chít! Bị lộ rồi!", "Đừng đuổi theo tôi!", "Bao vàng của tôiii!", "Chạy đằng trời!"]
		say(squeaks[randi() % squeaks.size()])
		show_bubble("face_angry")
	else:
		_defeat()
	return true


func _defeat() -> void:
	_defeated = true
	moving = false
	show_bubble("face_heart")
	say("Đầu hàng! Trả lại vàng nè!")
	AudioManager.play("levelup", 0.1)

	var bonus_gold := maxf(388.0, GameState.income_rate() * 45.0)
	GameState.add_gold(bonus_gold)
	GameState.add_diamonds(2)
	GameState.show_toast("ĐÃ BẮT ĐƯỢC CHUỘT NHẮT! +%s Vàng & +2 Kim Cương!" % NumberFormat.fmt(bonus_gold), "gold_bag")

	if UIKit.main:
		for i in 8:
			UIKit.main.call("sparkle_at_world", global_position + Vector2(randf_range(-40, 40), randf_range(-60, 10)))

	var dt := create_tween()
	dt.tween_property(self, "scale", Vector2(1.3, 1.3), 0.15)
	dt.tween_property(self, "modulate:a", 0.0, 0.35)
	dt.tween_callback(queue_free)
	caught.emit(self)


func _escape() -> void:
	_defeated = true
	GameState.show_toast("Chuột nhắt đã lẻn vào bóng tối tẩu thoát!", "gold_bag")
	var et := create_tween()
	et.tween_property(self, "modulate:a", 0.0, 0.3)
	et.tween_callback(queue_free)
	escaped.emit(self)


func _on_arrived() -> void:
	if not _defeated:
		_escape()


func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-36, -55), Vector2(72, 65))


## Vẽ Chibi Chuột Nhắt siêu ngộ nghĩnh vác bao vàng
func _draw_thief() -> void:
	var flip: float = facing
	var c := Vector2(0, -18)
	var bob := sin(_anim_t) * 2.5

	# 1. Bao tải vàng lớn sau lưng
	var sack_pos := c + Vector2(-14 * flip, -2 + bob)
	body_draw.draw_colored_polygon(_ellipse(sack_pos, 13.0, 15.0), Color("8d5b38")) # Bao vải gai
	body_draw.draw_colored_polygon(_ellipse(sack_pos + Vector2(2 * flip, -10), 6.0, 5.0), Color("facc15")) # Vàng lộ ra
	body_draw.draw_line(sack_pos + Vector2(-4 * flip, -8), sack_pos + Vector2(4 * flip, -6), Color("54331d"), 3.0)

	# 2. Đuôi chuột dài ngoe nguẩy
	var tail_pts := PackedVector2Array()
	tail_pts.append(c + Vector2(-16 * flip, 6 + bob))
	tail_pts.append(c + Vector2(-24 * flip, 2 + bob + sin(_anim_t * 0.8) * 6))
	tail_pts.append(c + Vector2(-30 * flip, -4 + bob + cos(_anim_t * 0.8) * 8))
	body_draw.draw_polyline(tail_pts, Color("e5a3a3"), 3.0, true)

	# 3. Chân chuột
	var step := cos(_anim_t) * 3.0 if moving else 0.0
	body_draw.draw_circle(c + Vector2(-7 * flip, 13 + step), 4.0, Color("fca5a5"))
	body_draw.draw_circle(c + Vector2(7 * flip, 13 - step), 4.0, Color("fca5a5"))

	# 4. Thân chuột lông xám
	body_draw.draw_colored_polygon(_ellipse(c + Vector2(0, 3 + bob), 14.0, 12.0), Color("71717a"))
	body_draw.draw_colored_polygon(_ellipse(c + Vector2(2 * flip, 5 + bob), 8.0, 9.0), Color("f4f4f5")) # Bụng trắng

	# 5. Đầu chuột + mõm nhọn
	var head_c := c + Vector2(6 * flip, -8 + bob)
	body_draw.draw_colored_polygon(_ellipse(head_c, 11.0, 9.0), Color("71717a"))

	# Tai to tròn
	body_draw.draw_circle(head_c + Vector2(-7 * flip, -8), 6.0, Color("71717a"))
	body_draw.draw_circle(head_c + Vector2(-7 * flip, -8), 4.0, Color("fca5a5"))
	body_draw.draw_circle(head_c + Vector2(4 * flip, -9), 6.0, Color("71717a"))
	body_draw.draw_circle(head_c + Vector2(4 * flip, -9), 4.0, Color("fca5a5"))

	# Mặt nạ trộm màu đen (Zorro bandit mask)
	var mask_l := head_c + Vector2(-2 * flip, -2)
	var mask_r := head_c + Vector2(8 * flip, -2)
	body_draw.draw_line(mask_l + Vector2(-4 * flip, 0), mask_r + Vector2(4 * flip, 0), Color("18181b"), 5.0)

	# Mắt lén lút
	body_draw.draw_circle(head_c + Vector2(0 * flip, -2), 2.2, Color.WHITE)
	body_draw.draw_circle(head_c + Vector2(6 * flip, -2), 2.2, Color.WHITE)
	body_draw.draw_circle(head_c + Vector2(1 * flip, -2), 1.2, Color.BLACK)
	body_draw.draw_circle(head_c + Vector2(7 * flip, -2), 1.2, Color.BLACK)

	# Mũi hồng + Ria chuột
	body_draw.draw_circle(head_c + Vector2(9 * flip, 2), 2.0, Color("f43f5e"))
	body_draw.draw_line(head_c + Vector2(5 * flip, 2), head_c + Vector2(-3 * flip, 0), Color("27272a"), 1.2)
	body_draw.draw_line(head_c + Vector2(5 * flip, 3), head_c + Vector2(-3 * flip, 5), Color("27272a"), 1.2)
	body_draw.draw_line(head_c + Vector2(9 * flip, 2), head_c + Vector2(17 * flip, 0), Color("27272a"), 1.2)
	body_draw.draw_line(head_c + Vector2(9 * flip, 3), head_c + Vector2(17 * flip, 5), Color("27272a"), 1.2)

	# Thanh máu chuột trên đầu (3 vạch tròn)
	var hp_y := head_c.y - 18
	for i in max_hp:
		var dot_x := (i - 1) * 8
		var col := Color("ef4444") if i < hp else Color("52525b")
		body_draw.draw_circle(Vector2(dot_x, hp_y), 3.0, col)


func _ellipse(pos: Vector2, rx: float, ry: float, n: int = 16) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var a: float = TAU * float(i) / float(n)
		pts.append(pos + Vector2(cos(a) * rx, sin(a) * ry))
	return pts
