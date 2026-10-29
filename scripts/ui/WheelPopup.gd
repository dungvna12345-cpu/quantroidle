extends PopupBase
## Vòng quay may mắn: mỗi ngày 1 lượt miễn phí, quay thêm tốn kim cương.
## Bánh xe vẽ bằng code (8 ô màu + icon), quay chậm dần rồi dừng đúng ô trúng.

const RewardScene := preload("res://scenes/ui/RewardPopup.tscn")


## Bánh xe: tự vẽ các ô quạt và icon phần thưởng.
class WheelView extends Control:
	var segments: Array = []
	var icons: Array[Texture2D] = []
	var font: Font

	func _ready() -> void:
		for s: Dictionary in segments:
			icons.append(Sprites.ui(str(s["icon"])))
		font = get_theme_default_font()

	func _draw() -> void:
		var c := size * 0.5
		var r: float = minf(size.x, size.y) * 0.5 - 6.0
		var n: int = segments.size()
		var seg: float = TAU / n
		draw_circle(c, r + 6.0, Color("6b4128"))
		for i in n:
			var a0: float = -PI / 2.0 + i * seg
			var pts := PackedVector2Array([c])
			for k in 17:
				var a: float = a0 + seg * k / 16.0
				pts.append(c + Vector2(cos(a), sin(a)) * r)
			draw_colored_polygon(pts, Color(str(segments[i]["color"])))
			draw_line(c, c + Vector2(cos(a0), sin(a0)) * r, Color(1, 1, 1, 0.9), 3.0, true)
			# icon + chữ ở giữa ô
			var mid: float = a0 + seg * 0.5
			var p := c + Vector2(cos(mid), sin(mid)) * r * 0.64
			draw_set_transform(p, mid + PI / 2.0, Vector2.ONE)
			draw_texture_rect(icons[i], Rect2(-28, -40, 56, 56), false)
			draw_string_outline(font, Vector2(-50, 36), str(segments[i]["label"]), HORIZONTAL_ALIGNMENT_CENTER, 100, 20, 6,
				Color("6b4128"))
			draw_string(font, Vector2(-50, 36), str(segments[i]["label"]), HORIZONTAL_ALIGNMENT_CENTER, 100, 20, Color.WHITE)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		draw_circle(c, 34.0, Color("6b4128"))
		draw_circle(c, 28.0, Color("ffc93c"))


## Kim chỉ màu đỏ phía trên bánh xe.
class Pointer extends Control:
	func _draw() -> void:
		var w: float = size.x
		var pts := PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w * 0.5, size.y)])
		draw_colored_polygon(pts, Color("e8414f"))
		pts.append(pts[0])
		draw_polyline(pts, Color("6b4128"), 4.0, true)


var _wheel: WheelView
var _spin_btn: JuicyButton
var _spinning: bool = false
var _last_seg: int = 0


func _init() -> void:
	title_text = "Vòng quay may mắn"


func _build(b: VBoxContainer) -> void:
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(0, 520)
	b.add_child(holder)
	_wheel = WheelView.new()
	_wheel.segments = Progress.wheel_data["segments"]
	_wheel.set_anchors_preset(Control.PRESET_CENTER)
	_wheel.offset_left = -240
	_wheel.offset_right = 240
	_wheel.offset_top = -240
	_wheel.offset_bottom = 240
	_wheel.pivot_offset = Vector2(240, 240)
	holder.add_child(_wheel)
	var ptr := Pointer.new()
	ptr.set_anchors_preset(Control.PRESET_CENTER_TOP)
	ptr.offset_left = -22
	ptr.offset_right = 22
	ptr.offset_top = -6
	ptr.offset_bottom = 44
	holder.add_child(ptr)
	_spin_btn = UIKit.button("", "GreenButton", "", 340)
	_spin_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_spin_btn.pressed.connect(_spin)
	b.add_child(_spin_btn)
	b.add_child(centered_label("Mỗi ngày quay miễn phí 1 lần. Phần thưởng: vàng, kim cương, Sách nghiên cứu, thẻ đầu bếp, x2 thu nhập, rương vàng.", "SmallLabel", 18))
	_refresh()


func _process(_delta: float) -> void:
	if not _spinning:
		return
	var seg: float = TAU / maxi(1, _wheel.segments.size())
	var k: int = floori(_wheel.rotation / seg)
	if k != _last_seg:
		_last_seg = k
		AudioManager.play("spin_tick", 0.05, 0.03)


func _refresh() -> void:
	if Progress.free_spin():
		_spin_btn.text = "QUAY MIỄN PHÍ"
		_spin_btn.icon = null
		_spin_btn.disabled = false
	else:
		var cost: int = int(Progress.wheel_data.get("spin_cost", 10))
		_spin_btn.text = "Quay  %d" % cost
		_spin_btn.icon = Sprites.ui("diamond")
		_spin_btn.disabled = GameState.diamonds < cost
	_spin_btn.pulse = not _spin_btn.disabled
	_spin_btn.disabled = _spin_btn.disabled or _spinning


func _spin() -> void:
	if _spinning:
		return
	var res := Progress.spin()
	if res.is_empty():
		return
	_spinning = true
	_refresh()
	var n: int = _wheel.segments.size()
	var seg: float = TAU / n
	var idx: int = int(res["index"])
	# xoay sao cho tâm ô trúng nằm ngay dưới kim (phía trên)
	var base: float = _wheel.rotation - fposmod(_wheel.rotation, TAU)
	var target: float = base + TAU * 6.0 + (TAU - (idx + 0.5) * seg) + randf_range(-0.3, 0.3) * seg
	AudioManager.play("whoosh")
	var t := create_tween()
	t.tween_property(_wheel, "rotation", target, 3.6).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	t.tween_callback(_done.bind(res["rewards"]))


func _done(rewards: Array) -> void:
	_spinning = false
	_refresh()
	AudioManager.play("levelup")
	var p: PopupBase = RewardScene.instantiate()
	p.title_text = "Trúng thưởng!"
	p.set("rewards", rewards)
	UIKit.main.call("open_popup", p)
