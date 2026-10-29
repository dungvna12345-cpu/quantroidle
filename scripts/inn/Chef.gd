class_name Chef
extends Walker
## Đầu bếp: nấu ở bếp lò của mình, nấu xong mang món ra quầy chuyển món rồi quay lại.

enum S { IDLE, COOKING, TO_PASS, RETURN }

var kitchen: Kitchen
var stove_index: int = 0
var home: Vector2 = Vector2.ZERO
var pass_spot: Vector2 = Vector2.ZERO
var state: S = S.IDLE
var order: Dictionary = {}
var dish_sprite: Sprite2D
var _cook_t: float = 0.0


func _ready() -> void:
	set_sprite("chef")
	speed = GameState.bal("walk_speed", 2.6) * 1.2 * (1.0 + Progress.bonus("walk"))
	dish_sprite = Sprite2D.new()
	dish_sprite.z_index = 5
	dish_sprite.visible = false
	add_child(dish_sprite)
	arrived.connect(_on_arrived)


func is_free() -> bool:
	return state == S.IDLE and not moving


func start_cooking(o: Dictionary) -> void:
	order = o
	state = S.COOKING
	_cook_t = 0.0


func _process(delta: float) -> void:
	super(delta)
	if state == S.COOKING:
		# hoạt ảnh đảo chảo: nhún + lắc liên tục
		_cook_t += delta
		body.position.y = -absf(sin(_cook_t * 9.0)) * 4.0
		body.rotation = sin(_cook_t * 6.0) * 0.08
	if dish_sprite.visible:
		dish_sprite.position = Vector2(20.0 * facing, -62.0) + body.position


## Kitchen gọi khi nấu xong.
func finish_cooking() -> void:
	state = S.TO_PASS
	Sprites.apply(dish_sprite, "dish_" + str(order["dish"]))
	dish_sprite.scale = Vector2(0.24, 0.24)
	dish_sprite.visible = true
	# Hiệu ứng tung chảo nảy đĩa nóng hổi
	dish_sprite.position = Vector2(20.0 * facing, -86.0) + body.position
	create_tween().tween_property(dish_sprite, "position:y", -62.0 + body.position.y, 0.16).set_trans(Tween.TRANS_BOUNCE)
	if randf() < 0.35:
		say("Nóng hổi vừa thổi vừa ăn!")
	walk_to(pass_spot)


func _on_arrived() -> void:
	match state:
		S.TO_PASS:
			dish_sprite.visible = false
			kitchen.dish_delivered_to_pass(order)
			order = {}
			state = S.RETURN
			walk_to(home)
		S.RETURN:
			state = S.IDLE
			facing = 1.0
