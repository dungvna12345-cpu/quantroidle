class_name Waiter
extends Walker
## Bồi bàn: ra cửa đón khách và dẫn vào bàn, lấy món ở bếp mang ra bàn.

enum S { IDLE, TO_DOOR, LEADING, TO_PICKUP, CARRYING }

var area: InnArea
var state: S = S.IDLE
var task: Dictionary = {}
var post_offset: Vector2 = Vector2.ZERO
var dish_sprite: Sprite2D


func _ready() -> void:
	set_sprite("waiter")
	dish_sprite = Sprite2D.new()
	dish_sprite.z_index = 5
	dish_sprite.visible = false
	add_child(dish_sprite)
	arrived.connect(_on_arrived)
	_update_speed()


func _update_speed() -> void:
	speed = GameState.bal("waiter_speed", 3.2) * GameState.staff_speed("waiter") * (1.0 + Progress.bonus("walk"))


func is_free() -> bool:
	return state == S.IDLE


func go_seat(cust: Customer, table_i: int) -> void:
	_update_speed()
	task = {"cust": cust, "table": table_i}
	state = S.TO_DOOR
	walk(area.path_to(grid, "door"))


func go_deliver(order: Dictionary) -> void:
	_update_speed()
	task = order
	state = S.TO_PICKUP
	walk(area.path_to(grid, "pickup"))


func go_home() -> void:
	state = S.IDLE
	task = {}
	var p := area.path_to(grid, "post")
	p.append(area.point_pos("post") + post_offset)
	walk(p)


func _process(delta: float) -> void:
	super(delta)
	if dish_sprite.visible:
		# món nằm trên khay, nhấp nhô theo nhịp bước chân
		var bob: float = sin(_bob_t) * 2.5 if moving else 0.0
		dish_sprite.position = Vector2(26.0 * facing, -60.0 + bob) + body.position


func _on_arrived() -> void:
	match state:
		S.TO_DOOR:
			if area.start_lead(self, task):
				state = S.LEADING
				walk(area.path_to(grid, "serve_%d" % int(task["table"])))
			else:
				go_home()
		S.LEADING:
			go_home()
		S.TO_PICKUP:
			area.take_dish(task)
			set_sprite("waiter_tray")
			Sprites.apply(dish_sprite, "dish_" + str(task["dish"]))
			dish_sprite.scale = Vector2(0.24, 0.24)
			dish_sprite.visible = true
			state = S.CARRYING
			walk(area.path_to(grid, "serve_%d" % int(task["table"])))
		S.CARRYING:
			# cúi chào duyên dáng khi đặt món
			var t := create_tween()
			t.tween_property(body, "rotation", 0.25 * facing, 0.12)
			t.tween_property(body, "rotation", 0.0, 0.18)
			dish_sprite.visible = false
			set_sprite("waiter")
			area.deliver(task)
			show_bubble("face_happy")
			get_tree().create_timer(0.9).timeout.connect(func():
				if is_instance_valid(self) and bubble_kind() == "face_happy":
					show_bubble(""))
			go_home()
