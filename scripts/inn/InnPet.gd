class_name InnPet
extends Walker
## Mèo Chiêu Tài của Quán Trọ: lững thững dạo chơi giữa các bàn, ngủ cuộn tròn,
## vẫy đuôi mừng khách. Khi chạm vào: nhảy mừng, kêu meo meo và ban tặng vàng/kim cương!

var area: InnArea
var _state: String = "idle" # idle / walk / sleep
var _action_timer: float = 3.0
var _pet_count: int = 0
var _tail_angle: float = 0.0
var pet_body: Node2D
var pet_tail: Node2D


func _init() -> void:
	super()
	# Tạo hình thú cưng Mèo Chiêu Tài Chibi vẽ mượt mà
	pet_body = Node2D.new()
	add_child(pet_body)
	pet_body.draw.connect(_draw_cat)
	# Ẩn body sprite mặc định của Walker, dùng pet_body
	body.visible = false


var _tip_timer: float = 8.0


func setup(a: InnArea) -> void:
	area = a
	speed = 1.4
	_pick_new_action()


func _process(delta: float) -> void:
	super(delta)
	_tail_angle += delta * (8.0 if moving else 3.5)
	pet_body.queue_redraw()

	if GameState.pet_level >= 3:
		_tip_timer -= delta
		if _tip_timer <= 0.0:
			_tip_timer = 14.0
			_auto_collect_tips()

	if moving:
		return
	_action_timer -= delta
	if _action_timer <= 0.0:
		_pick_new_action()


func _auto_collect_tips() -> void:
	if area == null or not is_instance_valid(area):
		return
	var count: int = 0
	for t in area.tables:
		if t.tip_value > 0.0:
			count += 1
			t.collect_tip()
	if count > 0:
		say("Meo! Đã gom tiền boa giúp sen! 🐾")
		show_bubble("face_heart")
		Juice.bounce(self, 1.25)
		AudioManager.play("coin", 0.1)


func _pick_new_action() -> void:
	if area == null or not is_instance_valid(area):
		return
	var r := randf()
	if r < 0.45 and not area.aisle_cols.is_empty() and not area.aisle_rows.is_empty():
		_state = "walk"
		show_bubble("")
		var gx: float = float(area.aisle_cols[randi() % area.aisle_cols.size()])
		var gy: float = float(area.aisle_rows[randi() % area.aisle_rows.size()])
		walk_to(Vector2(gx, gy))
		_action_timer = randf_range(8.0, 14.0)
	elif r < 0.75:
		_state = "sleep"
		show_bubble("bubble_zzz")
		_action_timer = randf_range(5.0, 9.0)
	else:
		_state = "idle"
		show_bubble("face_heart" if randf() < 0.5 else "")
		_action_timer = randf_range(4.0, 7.0)


## Khi người chơi chạm vuốt ve mèo
func pet_interaction() -> void:
	_pet_count += 1
	_state = "idle"
	_action_timer = 5.0
	show_bubble("face_heart")
	Juice.bounce(self, 1.35)
	AudioManager.play("coin", 0.15)
	AudioManager.play("legendary", 0.1)
	if UIKit.main and UIKit.main.has_method("open_pet") and randf() < 0.35:
		UIKit.main.call_deferred("open_pet")

	var bonus: float = maxf(88.0, GameState.income_rate() * 12.0)
	GameState.add_gold(bonus)

	var meows := ["Meo meo~ 🐾", "Gừ gừ... sướng quá!", "Meo! Chúc quán phát tài!", "Meo meo nựng thích ghê!"]
	say(meows[randi() % meows.size()])

	GameState.pet_xp += 25.0
	var req_xp: float = float(GameState.pet_level * 100)
	if GameState.pet_xp >= req_xp and GameState.pet_level < 5:
		GameState.pet_level += 1
		GameState.pet_xp = 0.0
		AudioManager.play("levelup", 0.15)
		var perks := [
			"",
			"Mèo được tặng Nón Lá Tre Chibi! 👒",
			"Mở khóa Kỹ năng Tự Gom Tiền Boa! 💰",
			"Mở khóa Giác Quan Báo Động Bắt Trộm! 🚨",
			"Mở khóa Hào Quang Vàng: +15% Doanh Thu Toàn Quán! ✨"
		]
		GameState.show_toast("MÈO LÊN CẤP %d! %s" % [GameState.pet_level, perks[GameState.pet_level - 1]])
	else:
		if _pet_count % 5 == 0:
			GameState.add_diamonds(1)
			GameState.show_toast("Mèo Chiêu Tài tặng bạn +1 Kim Cương! 💎")
		else:
			GameState.show_toast("+%s Vàng từ Mèo Chiêu Tài!" % NumberFormat.fmt(bonus))

	if UIKit.main:
		UIKit.main.call("sparkle_at", global_position + Vector2(0, -40))


## Vẽ mèo tam thể chibi tròn xoe siêu đáng yêu
func _draw_cat() -> void:
	var flip: float = facing
	var c := Vector2(0, -18)

	# 1. Đuôi mèo ngoe nguẩy
	var tail_rad: float = sin(_tail_angle) * 0.35
	var tail_pts := PackedVector2Array()
	var t_base := c + Vector2(-14 * flip, 4)
	tail_pts.append(t_base)
	tail_pts.append(t_base + Vector2(-10 * flip + sin(tail_rad) * 6, -10 + cos(tail_rad) * 4))
	tail_pts.append(t_base + Vector2(-18 * flip + sin(tail_rad) * 12, -20))
	pet_body.draw_polyline(tail_pts, Color("e07a3f"), 5.0, true)
	pet_body.draw_circle(tail_pts[2], 3.0, Color("3d2c25"))

	# 2. Chân mèo (bước đi khi moving)
	var step_y: float = sin(_tail_angle * 1.5) * 3.0 if moving else 0.0
	pet_body.draw_circle(c + Vector2(-9 * flip, 14 + step_y), 5.0, Color("fdf6eb"))
	pet_body.draw_circle(c + Vector2(9 * flip, 14 - step_y), 5.0, Color("fdf6eb"))

	# 3. Thân mèo hình bầu tròn ấm áp
	pet_body.draw_colored_polygon(_ellipse(c + Vector2(0, 4), 16.0, 13.0), Color("fdf6eb"))
	# Đốm cam tam thể bên phải
	pet_body.draw_colored_polygon(_ellipse(c + Vector2(7 * flip, 2), 7.0, 9.0), Color("e07a3f"))
	# Đốm nâu sôcôla bên trái
	pet_body.draw_colored_polygon(_ellipse(c + Vector2(-8 * flip, 5), 6.0, 7.0), Color("3d2c25"))

	# 4. Đầu mèo tròn vo
	var head_c := c + Vector2(4 * flip, -10)
	pet_body.draw_colored_polygon(_ellipse(head_c, 13.0, 11.0), Color("fdf6eb"))
	pet_body.draw_colored_polygon(_ellipse(head_c + Vector2(5 * flip, -3), 6.0, 6.0), Color("e07a3f"))

	# 5. Tai mèo tam giác
	var ear_l := PackedVector2Array([head_c + Vector2(-9 * flip, -6), head_c + Vector2(-11 * flip, -17), head_c + Vector2(-2 * flip, -10)])
	var ear_r := PackedVector2Array([head_c + Vector2(2 * flip, -10), head_c + Vector2(9 * flip, -17), head_c + Vector2(10 * flip, -6)])
	pet_body.draw_colored_polygon(ear_l, Color("3d2c25"))
	pet_body.draw_colored_polygon(ear_r, Color("e07a3f"))
	pet_body.draw_circle(head_c + Vector2(-7 * flip, -10), 3.0, Color("fca5a5"))
	pet_body.draw_circle(head_c + Vector2(6 * flip, -10), 3.0, Color("fca5a5"))

	# 6. Mắt nhắm tít cười hạnh phúc hoặc mắt đen long lanh
	if _state == "sleep":
		pet_body.draw_line(head_c + Vector2(-2 * flip, -2), head_c + Vector2(2 * flip, -2), Color("3d2c25"), 2.0)
		pet_body.draw_line(head_c + Vector2(5 * flip, -2), head_c + Vector2(9 * flip, -2), Color("3d2c25"), 2.0)
	else:
		pet_body.draw_circle(head_c + Vector2(0 * flip, -2), 2.2, Color("221815"))
		pet_body.draw_circle(head_c + Vector2(7 * flip, -2), 2.2, Color("221815"))
		pet_body.draw_circle(head_c + Vector2(1 * flip, -3), 0.8, Color.WHITE)
		pet_body.draw_circle(head_c + Vector2(8 * flip, -3), 0.8, Color.WHITE)

	# 7. Mũi hồng + ria mép
	pet_body.draw_circle(head_c + Vector2(3.5 * flip, 1), 1.5, Color("f472b6"))
	pet_body.draw_line(head_c + Vector2(-2 * flip, 1), head_c + Vector2(-9 * flip, 0), Color("8c7569"), 1.2)
	pet_body.draw_line(head_c + Vector2(-2 * flip, 3), head_c + Vector2(-9 * flip, 4), Color("8c7569"), 1.2)
	pet_body.draw_line(head_c + Vector2(9 * flip, 1), head_c + Vector2(16 * flip, 0), Color("8c7569"), 1.2)
	pet_body.draw_line(head_c + Vector2(9 * flip, 3), head_c + Vector2(16 * flip, 4), Color("8c7569"), 1.2)

	# 8. Vòng cổ đỏ & Chuông vàng chiêu tài
	pet_body.draw_line(head_c + Vector2(-4 * flip, 7), head_c + Vector2(6 * flip, 7), Color("e11d48"), 3.0)
	pet_body.draw_circle(head_c + Vector2(1 * flip, 9), 3.2, Color("facc15"))
	pet_body.draw_circle(head_c + Vector2(1 * flip, 9), 1.0, Color("78350f"))

	# 9. Nón Lá Tre Chibi (Khi Cấp Thân Thiết >= 2)
	if GameState.pet_level >= 2:
		var hat_c := head_c + Vector2(0, -14)
		var hat_pts := PackedVector2Array([
			hat_c + Vector2(-15 * flip, 4),
			hat_c + Vector2(0, -12),
			hat_c + Vector2(15 * flip, 4)
		])
		pet_body.draw_colored_polygon(hat_pts, Color("fef08a")) # Nón lá vàng tre
		pet_body.draw_polyline(hat_pts, Color("ca8a04"), 2.0, true)
		pet_body.draw_line(hat_c + Vector2(-10 * flip, 4), head_c + Vector2(1 * flip, 8), Color("ef4444"), 1.6)
		pet_body.draw_line(hat_c + Vector2(10 * flip, 4), head_c + Vector2(1 * flip, 8), Color("ef4444"), 1.6)

	# 10. Hào quang vàng Thần Tài (Khi Cấp Thân Thiết == 5)
	if GameState.pet_level >= 5:
		var aura_r: float = 24.0 + sin(_tail_angle * 1.5) * 3.0
		pet_body.draw_arc(c, aura_r, 0, TAU, 24, Color(1.0, 0.84, 0.0, 0.45), 3.0)


func _ellipse(pos: Vector2, rx: float, ry: float, n: int = 20) -> PackedVector2Array:
	var pts := PackedVector2Array()
	for i in n:
		var a: float = TAU * float(i) / float(n)
		pts.append(pos + Vector2(cos(a) * rx, sin(a) * ry))
	return pts


func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-36, -50), Vector2(72, 60))
