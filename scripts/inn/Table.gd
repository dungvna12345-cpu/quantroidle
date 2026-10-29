class_name Table
extends Node2D
## Bàn ăn + ghế. Khi chưa mở khóa hiện ổ khóa kèm giá. Có thể có đồng tiền boa để nhặt.

const SEAT_OFFSET := Vector2(-0.45, -0.45)

var area: InnArea
var index: int = 0
var grid: Vector2 = Vector2.ZERO
var body: Sprite2D
var chair: Sprite2D
var lock_icon: Sprite2D
var price_label: Label
var tip_sprite: Sprite2D
var plate: Sprite2D
var tip_value: float = 0.0
var _tip_age: float = 0.0
var _tier: int = -1
var _t: float = 0.0


func setup(a: InnArea, i: int, g: Vector2) -> void:
	area = a
	index = i
	grid = g
	position = Iso.to_world(g)
	body = Sprite2D.new()
	add_child(body)
	# ghế là node riêng trong lớp y-sort để khách ngồi vẽ đè lên ghế
	chair = Sprite2D.new()
	chair.position = Iso.to_world(g + SEAT_OFFSET) + Vector2(0, -1)
	area.objects.add_child(chair)
	plate = Sprite2D.new()
	plate.visible = false
	plate.z_index = 2
	add_child(plate)
	tip_sprite = Sprites.make("coin")
	tip_sprite.scale = Vector2(0.28, 0.28)
	tip_sprite.z_index = 25
	tip_sprite.visible = false
	add_child(tip_sprite)
	lock_icon = Sprite2D.new()
	lock_icon.texture = Sprites.ui("lock")
	lock_icon.scale = Vector2(0.42, 0.42)
	lock_icon.position = Vector2(0, -62)
	lock_icon.z_index = 25
	add_child(lock_icon)
	price_label = Label.new()
	price_label.theme_type_variation = "WhiteLabel"
	price_label.add_theme_font_size_override("font_size", 22)
	price_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	price_label.size = Vector2(140, 30)
	price_label.position = Vector2(-70, -40)
	price_label.z_index = 25
	price_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(price_label)
	refresh()


func seat_grid() -> Vector2:
	return grid + SEAT_OFFSET


func serve_grid() -> Vector2:
	return grid + Vector2(0.62, 0.05)


func unlocked() -> bool:
	return GameState.table_level(area.area_id, index) > 0


func slot_open() -> bool:
	return GameState.table_slot_open(area.area_id, index)


func refresh() -> void:
	visible = slot_open()
	chair.visible = visible
	var on := unlocked()
	var tier: int = GameState.table_tier(area.area_id, index) if on else 1
	if tier != _tier:
		if _tier > 0:
			Juice.pop(body, Vector2(Sprites.SCALE, Sprites.SCALE), 0.2)
		_tier = tier
		Sprites.apply(body, "table_%d" % tier)
		Sprites.apply(chair, "chair_%d" % tier)
	body.modulate = Color.WHITE if on else Color(1, 1, 1, 0.35)
	chair.modulate = body.modulate
	lock_icon.visible = not on
	price_label.visible = not on
	if not on:
		price_label.text = NumberFormat.fmt(GameState.table_unlock_cost(area.area_id))


func show_dish(dish_id: String) -> void:
	if dish_id.is_empty():
		plate.visible = false
		return
	Sprites.apply(plate, "dish_" + dish_id)
	plate.scale = Vector2(0.26, 0.26)
	plate.position = Vector2(4, -44)
	plate.visible = true


func add_tip(v: float) -> void:
	tip_value += v
	_tip_age = 0.0
	tip_sprite.visible = true
	Juice.pop(tip_sprite, Vector2(0.28, 0.28), 0.4)


## Nhặt tiền boa. Trả về true nếu có tiền.
func collect_tip() -> bool:
	if tip_value <= 0.0:
		return false
	GameState.earn(tip_value, area.to_global(position + tip_sprite.position), area.visible)
	tip_value = 0.0
	tip_sprite.visible = false
	GameState.tips_collected += 1
	GameState.add_daily("tip", 1)
	AudioManager.play("coin", 0.1)
	return true


func _process(delta: float) -> void:
	_t += delta
	if not unlocked():
		lock_icon.position.y = -62.0 + sin(_t * 3.0) * 3.0
	if tip_value > 0.0:
		_tip_age += delta
		tip_sprite.position = Vector2(-22, -58 + sin(_t * 4.0) * 4.0)
		# Quản lý tự nhặt tiền boa sau vài giây
		if GameState.manager and _tip_age >= GameState.bal("tip_auto_collect", 5.0):
			collect_tip()


func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-58, -80), Vector2(116, 100))


func tip_hit_rect() -> Rect2:
	return Rect2(position + tip_sprite.position - Vector2(30, 30), Vector2(60, 60))
