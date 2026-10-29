class_name TabBase
extends Control
## Lớp cơ sở cho các tab: làm mới nội dung khi trạng thái game thay đổi (giới hạn tần suất).

var _dirty: bool = true
var _cooldown: float = 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build()
	GameState.gold_changed.connect(_mark)
	GameState.diamonds_changed.connect(_mark)
	GameState.state_changed.connect(_mark)
	GameState.quests_changed.connect(_mark)
	GameState.current_area_changed.connect(_mark)
	GameState.area_changed.connect(_mark)
	GameState.orders_changed.connect(_mark)
	Progress.changed.connect(_mark)
	_refresh()


func _mark(_a: Variant = null) -> void:
	_dirty = true


func _process(delta: float) -> void:
	_cooldown -= delta
	if _dirty and visible and _cooldown <= 0.0:
		_dirty = false
		_cooldown = 0.2
		_refresh()


## Gọi khi tab được mở.
func on_shown() -> void:
	_dirty = false
	_refresh()


func _build() -> void:
	pass


func _refresh() -> void:
	pass


func _sparkle(c: Control) -> void:
	if UIKit.main and c:
		UIKit.main.call("sparkle_at", c.get_global_rect().get_center())
