class_name Customer
extends Walker
## Khách: đi đường -> xếp hàng -> được dẫn vào bàn -> gọi món -> ăn -> trả tiền -> về.
## Khách trọ: đi đường -> xếp hàng -> vào phòng ngủ -> trả tiền phòng -> về.

enum S { ROAD, QUEUE, CALLED, WALK_IN, ORDER, EAT, WAIT_PAY, TO_PAY, PAY_QUEUE, PAYING, LEAVE, TO_BED, SLEEP }

var area: InnArea
var state: S = S.ROAD
var base_sprite: String = "cust_1"
var dish_id: String = ""
var table: int = -1
var room: int = -1
var queue_index: int = -1
var pay_index: int = -1
var wait_t: float = 0.0
var eat_left: float = 0.0
var eat_total: float = 1.0
var rushed: bool = false
var golden: bool = false   # khách sộp trong sự kiện: trả gấp 10
var ctype: String = "normal"   # normal / picky / tourist / regular
var regular_id: String = ""      # khách quen có tên (cốt truyện)
var bar: WorldBar
var _glow: Sprite2D
var _eat_anim_t: float = 0.0


func _ready() -> void:
	speed = GameState.bal("walk_speed", 2.6) * (1.0 + Progress.bonus("walk"))
	set_sprite(base_sprite)
	bar = WorldBar.new()
	bar.position = Vector2(0, -102)
	bar.visible = false
	add_child(bar)
	arrived.connect(_on_arrived)
	if not regular_id.is_empty():
		var tag := Label.new()
		tag.text = str(Story.character(regular_id)["name"])
		tag.theme_type_variation = "WhiteLabel"
		tag.add_theme_font_size_override("font_size", 18)
		tag.add_theme_color_override("font_color", Color("ffe27a"))
		tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		tag.size = Vector2(160, 26)
		tag.position = Vector2(-80, -128)
		tag.z_index = 29
		tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(tag)
	if ctype == "wealth":
		golden = true
		body.modulate = Color(1.35, 1.2, 0.4)
		_glow = Sprite2D.new()
		_glow.texture = Sprites.ui("sparkle")
		_glow.scale = Vector2(0.65, 0.65)
		_glow.position = Vector2(0, -60)
		_glow.modulate = Color(1, 0.85, 0.2, 0.85)
		_glow.z_index = -1
		add_child(_glow)
		var tag := Label.new()
		tag.text = "THẦN TÀI"
		tag.theme_type_variation = "WhiteLabel"
		tag.add_theme_font_size_override("font_size", 18)
		tag.add_theme_color_override("font_color", Color("ffd700"))
		tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		tag.size = Vector2(160, 26)
		tag.position = Vector2(-80, -128)
		tag.z_index = 29
		tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(tag)
	elif ctype == "critic":
		var tag := Label.new()
		tag.text = "PHÊ BÌNH VIÊN"
		tag.theme_type_variation = "WhiteLabel"
		tag.add_theme_font_size_override("font_size", 18)
		tag.add_theme_color_override("font_color", Color("ff8f7a"))
		tag.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		tag.size = Vector2(180, 26)
		tag.position = Vector2(-90, -128)
		tag.z_index = 29
		tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(tag)
	elif ctype != "normal":
		var badge := Sprite2D.new()
		badge.texture = Sprites.ui("badge_" + ctype)
		badge.scale = Vector2(0.3, 0.3)
		badge.position = Vector2(-26, -96)
		badge.z_index = 29
		add_child(badge)
	if golden and ctype != "wealth":
		body.modulate = Color(1.25, 1.05, 0.45)
		_glow = Sprite2D.new()
		_glow.texture = Sprites.ui("sparkle")
		_glow.scale = Vector2(0.55, 0.55)
		_glow.position = Vector2(0, -60)
		_glow.modulate = Color(1, 0.9, 0.3, 0.7)
		_glow.z_index = -1
		add_child(_glow)


func set_state(s: S) -> void:
	state = s
	wait_t = 0.0
	_eat_anim_t = 0.0


func _process(delta: float) -> void:
	super(delta)
	if _glow:
		_glow.rotation += delta * 1.5
		_glow.visible = visible
	match state:
		S.QUEUE, S.CALLED:
			wait_t += delta
			var p: float = GameState.patience() * (0.5 if ctype == "picky" else 1.0)
			_mood(wait_t / p)
			if not moving:
				body.rotation = sin(wait_t * 3.2) * 0.04
			# hết kiên nhẫn thì bỏ về (có Quản lý thì khách không bỏ đi)
			if state == S.QUEUE and wait_t >= p and not GameState.manager and not rushed:
				area.customer_gave_up(self)
		S.ORDER:
			wait_t += delta
			if wait_t > GameState.patience() * 1.2:
				show_bubble("face_angry")
			elif wait_t > GameState.patience() * 0.8:
				show_bubble("face_neutral")
		S.EAT:
			var rate: float = GameState.bal("tap_rush_mult", 2.0) if rushed else 1.0
			eat_left -= delta * rate
			bar.ratio = 1.0 - eat_left / eat_total
			_eat_anim_t += delta * (10.0 if rushed else 6.0)
			# Nhịp gật đầu ăn ngon lành (chibi eating bob)
			var chew: float = absf(sin(_eat_anim_t))
			body.position.y = -chew * 4.0
			body.rotation = sin(_eat_anim_t * 0.5) * 0.04
			if eat_left <= 0.0:
				bar.visible = false
				body.position.y = 0.0
				body.rotation = 0.0
				var jt := create_tween()
				jt.tween_property(body, "position:y", -14.0, 0.12).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
				jt.tween_property(body, "position:y", 0.0, 0.14).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
				show_bubble("face_heart" if randf() < 0.65 else "face_happy")
				area.customer_finished_eating(self)


## Cảm xúc khi chờ: 😊 -> 😐 -> 😠
func _mood(r: float) -> void:
	if r < 0.25:
		show_bubble("")
	elif r < 0.55:
		show_bubble("face_happy")
	elif r < 0.8:
		show_bubble("face_neutral")
	else:
		show_bubble("face_angry")


func sit(on: bool) -> void:
	set_sprite(base_sprite + "_sit" if on else base_sprite)
	if on:
		facing = 1.0


func start_eat(t: float) -> void:
	set_state(S.EAT)
	eat_total = maxf(0.2, t)
	eat_left = eat_total
	bar.ratio = 0.0
	bar.visible = true
	show_bubble("")


## Người chơi chạm vào khách: phục vụ nhanh hơn kèm biểu cảm dễ thương.
func rush() -> bool:
	if rushed or state in [S.LEAVE, S.PAYING, S.SLEEP]:
		return false
	rushed = true
	speed_mult = 1.6
	wait_t = 0.0
	show_bubble("face_heart")
	# Bouncy squish & stretch khi chạm
	var orig_s := body.scale
	var bt := create_tween()
	bt.tween_property(body, "scale", Vector2(orig_s.x * 1.25, orig_s.y * 0.75), 0.08)
	bt.tween_property(body, "scale", Vector2(orig_s.x * 0.88, orig_s.y * 1.18), 0.12)
	bt.tween_property(body, "scale", orig_s, 0.1)
	modulate = Color(1.3, 1.25, 1.05)
	var t := create_tween()
	t.tween_property(self, "modulate", Color.WHITE, 0.5)
	if ctype == "wealth":
		var bonus: int = int(GameState.income_rate() * 8.0) + 88
		GameState.add_gold(bonus)
		say("Tấn tài tấn lộc! Quán trọ đại phát!")
	elif ctype == "critic":
		say("Món ăn rất vừa vị, phong thái 5 sao!")
	else:
		var cute_shouts := ["Ngon quá!", "Tuyệt cú mèo!", "Phục vụ 10 điểm!", "Thơm nức mũi!", "Tuyệt đỉnh!"]
		if randf() < 0.45:
			say(cute_shouts[randi() % cute_shouts.size()])
	get_tree().create_timer(1.2).timeout.connect(_clear_heart)
	return true


func _clear_heart() -> void:
	if not is_instance_valid(self):
		return
	if bubble_kind() == "face_heart" and state != S.LEAVE:
		if state == S.ORDER:
			show_bubble("bubble", "dish_" + dish_id)
		else:
			show_bubble("")


func _on_arrived() -> void:
	match state:
		S.ROAD:
			set_state(S.QUEUE)
		S.WALK_IN:
			area.customer_seated(self)
		S.TO_PAY:
			set_state(S.PAY_QUEUE)
		S.TO_BED:
			area.guest_in_bed(self)
		S.LEAVE:
			area.customer_left(self)
