extends Control
## Màn khởi động: logo, thanh tải. Nạp sẵn ảnh rồi mờ dần sang màn chính.

const MAIN_SCENE := "res://scenes/Main.tscn"
const MIN_TIME := 0.6
const TIPS: Array[String] = [
	"Mẹo: chạm vào khách đang chờ để phục vụ nhanh hơn!",
	"Mẹo: thuê Quản lý để quán tự kinh doanh khi bạn vắng mặt.",
	"Mẹo: trang trí quán giúp khách kéo đến đông hơn.",
	"Mẹo: nhặt đồng tiền boa khách để lại trên bàn.",
]

var _bar: ProgressBar
var _logo: TextureRect
var _fade: ColorRect
var _t: float = 0.0
var _done: bool = false
var _queue: Array[String] = []
var _index: int = 0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := TextureRect.new()
	var grad := Gradient.new()
	grad.set_color(0, Color("ffe7a8"))
	grad.set_color(1, Color("f6a85a"))
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill_from = Vector2(0.5, 0.0)
	gt.fill_to = Vector2(0.5, 1.0)
	gt.width = 16
	gt.height = 256
	bg.texture = gt
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var center := VBoxContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 18)
	add_child(center)
	_logo = TextureRect.new()
	_logo.texture = load("res://assets/ui/logo_full.png")
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.custom_minimum_size = Vector2(0, 520)
	center.add_child(_logo)
	var sub := UIKit.label("Kinh doanh quán trọ phố cổ", "", 30)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_color_override("font_color", Color("8a4a1c"))
	center.add_child(sub)
	var bottom := UIKit.margin(90, 0, 90, 120)
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.grow_vertical = Control.GROW_DIRECTION_BEGIN
	add_child(bottom)
	var bv := UIKit.vbox(12)
	bottom.add_child(bv)
	_bar = ProgressBar.new()
	_bar.custom_minimum_size = Vector2(0, 34)
	_bar.show_percentage = false
	bv.add_child(_bar)
	var tip := UIKit.label(TIPS[randi() % TIPS.size()], "", 22)
	tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tip.add_theme_color_override("font_color", Color("6b3a16"))
	bv.add_child(tip)
	_fade = ColorRect.new()
	_fade.color = Color(0.12, 0.07, 0.04, 0.0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fade)
	# danh sách ảnh cần nạp trước (đọc từ manifest)
	var f := FileAccess.open(Sprites.DIR + "manifest.json", FileAccess.READ)
	if f:
		var m: Variant = JSON.parse_string(f.get_as_text())
		if m is Dictionary:
			for k: String in m:
				_queue.append(k)


func _process(delta: float) -> void:
	_t += delta
	_logo.pivot_offset = _logo.size * 0.5
	_logo.scale = Vector2.ONE * (1.0 + sin(_t * 3.0) * 0.03)
	if _done:
		_bar.value = lerpf(_bar.value, 100.0, minf(1.0, delta * 8.0))
		return
	# nạp dần vài ảnh mỗi khung hình -> thanh tải chạy theo tiến độ thật
	var budget: int = 6
	while budget > 0 and _index < _queue.size():
		Sprites.tex(_queue[_index])
		_index += 1
		budget -= 1
	var p: float = float(_index) / float(maxi(1, _queue.size()))
	_bar.value = lerpf(_bar.value, minf(p, _t / MIN_TIME) * 100.0, minf(1.0, delta * 8.0))
	if _index >= _queue.size() and _t >= MIN_TIME:
		_done = true
		var scene: PackedScene = load(MAIN_SCENE)
		var tw := create_tween()
		tw.tween_property(_fade, "color:a", 1.0, 0.3)
		tw.tween_callback(func() -> void: get_tree().change_scene_to_packed(scene))
