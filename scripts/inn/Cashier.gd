class_name Cashier
extends Node2D
## Quầy thu ngân: tính tiền cho khách đứng đầu hàng.

signal paid(c: Customer)

var area: InnArea
var grid: Vector2 = Vector2.ZERO
var counter: Sprite2D
var person: Sprite2D
var bar: WorldBar
var current: Customer = null
var _left: float = 0.0
var _total: float = 1.0
var _t: float = 0.0


func setup(a: InnArea, g: Vector2, person_sprite: String) -> void:
	area = a
	grid = g
	position = Iso.to_world(g)
	counter = Sprites.make("cashier_counter")
	add_child(counter)
	# nhân viên đứng sau quầy là node riêng để y-sort đúng
	person = Sprites.make(person_sprite)
	person.position = Iso.to_world(g + Vector2(-0.72, 0.0))
	area.objects.add_child(person)
	bar = WorldBar.new()
	bar.position = Vector2(0, -132)
	bar.fill_color = Color("ffd34d")
	bar.visible = false
	add_child(bar)


func pay_spot(k: int) -> Vector2:
	return grid + Vector2(0.85, 0.7 * k)


func busy() -> bool:
	return current != null


func begin(c: Customer) -> void:
	current = c
	_total = GameState.pay_time(area.area_id)
	_left = _total
	bar.visible = true


func _process(delta: float) -> void:
	_t += delta
	if current == null:
		person.rotation = 0.0
		return
	if not is_instance_valid(current):
		current = null
		bar.visible = false
		return
	var rate: float = GameState.bal("tap_rush_mult", 2.0) if current.rushed else 1.0
	_left -= delta * rate
	bar.ratio = 1.0 - _left / _total
	person.rotation = sin(_t * 10.0) * 0.04
	if _left <= 0.0:
		var c := current
		current = null
		bar.visible = false
		person.rotation = 0.0
		var py := person.position.y
		var pt := create_tween()
		pt.tween_property(person, "position:y", py + 3.5, 0.08)
		pt.tween_property(person, "position:y", py, 0.12)
		paid.emit(c)


func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-70, -110), Vector2(140, 130))
