class_name Room
extends Node2D
## Phòng trọ (giường). Khách vào ngủ, hết giờ thì trả tiền phòng.

var area: InnArea
var index: int = 0
var grid: Vector2 = Vector2.ZERO
var body: Sprite2D
var zzz: Sprite2D
var lock_icon: Sprite2D
var price_label: Label
var bar: WorldBar
var guest: Customer = null
var reserved: bool = false
var sleep_left: float = 0.0
var sleep_total: float = 1.0
var _t: float = 0.0


func setup(a: InnArea, i: int, g: Vector2) -> void:
	area = a
	index = i
	grid = g
	position = Iso.to_world(g)
	body = Sprites.make("bed")
	add_child(body)
	zzz = Sprites.make("bubble_zzz")
	zzz.position = Vector2(10, -70)
	zzz.z_index = 30
	zzz.visible = false
	add_child(zzz)
	bar = WorldBar.new()
	bar.position = Vector2(0, -20)
	bar.visible = false
	add_child(bar)
	lock_icon = Sprite2D.new()
	lock_icon.texture = Sprites.ui("lock")
	lock_icon.scale = Vector2(0.42, 0.42)
	lock_icon.position = Vector2(0, -66)
	lock_icon.z_index = 25
	add_child(lock_icon)
	price_label = Label.new()
	price_label.theme_type_variation = "WhiteLabel"
	price_label.add_theme_font_size_override("font_size", 22)
	price_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	price_label.size = Vector2(140, 30)
	price_label.position = Vector2(-70, -44)
	price_label.z_index = 25
	price_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(price_label)
	refresh()


func unlocked() -> bool:
	return GameState.room_level(area.area_id, index) > 0


func is_free() -> bool:
	return unlocked() and guest == null and not reserved


func approach_grid() -> Vector2:
	return grid + Vector2(0.0, 0.62)


func slot_open() -> bool:
	return GameState.bed_slot_open(area.area_id, index)


func refresh() -> void:
	visible = slot_open()
	var on := unlocked()
	body.modulate = Color.WHITE if on else Color(1, 1, 1, 0.35)
	lock_icon.visible = not on
	price_label.visible = not on
	if not on:
		price_label.text = NumberFormat.fmt(GameState.room_unlock_cost(area.area_id))


func start_sleep(c: Customer) -> void:
	guest = c
	reserved = false
	var t: float = float(GameState.area_info(area.area_id)["room"]["sleep_time"])
	sleep_total = t
	sleep_left = t
	zzz.visible = true
	bar.visible = true
	Juice.pop(zzz, Vector2(Sprites.SCALE, Sprites.SCALE), 0.3)


func _process(delta: float) -> void:
	_t += delta
	if not unlocked():
		lock_icon.position.y = -66.0 + sin(_t * 3.0) * 3.0
	if guest != null:
		var rate: float = GameState.bal("tap_rush_mult", 2.0) if guest.rushed else 1.0
		sleep_left -= delta * rate
		bar.ratio = 1.0 - sleep_left / sleep_total
		zzz.position.y = -70.0 + sin(_t * 2.0) * 4.0
		if sleep_left <= 0.0:
			var g := guest
			guest = null
			zzz.visible = false
			bar.visible = false
			area.guest_woke(self, g)


func hit_rect() -> Rect2:
	return Rect2(position + Vector2(-64, -70), Vector2(128, 96))
