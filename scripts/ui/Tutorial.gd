extends Control
## Hướng dẫn chơi lần đầu (6 bước) + hướng dẫn tính năng nâng cao (6 bước), có bàn tay chỉ vào chỗ cần bấm.
## Bước có "event" tự hoàn thành khi người chơi làm đúng; luôn có nút Bỏ qua.

signal finished

const STEPS := [
	{"text": "Chào mừng đến Quán Trọ! Khách đi vào, bồi bàn dẫn tới bàn, đầu bếp nấu món, thu ngân tính tiền.", "target": "", "event": ""},
	{"text": "Chạm vào khách đang xếp hàng ngoài cổng để phục vụ nhanh hơn!", "target": "customer", "event": "tap_customer"},
	{"text": "Chạm vào bàn ăn để xem chỉ số và nâng cấp. Bàn có ổ khóa thì mở thêm bàn mới.", "target": "table", "event": "popup_object"},
	{"text": "Mở tab Thực đơn để nâng cấp món ăn, tăng giá bán.", "target": "tab_2", "event": "tab_menu"},
	{"text": "Tab Nhân viên: thuê thêm bồi bàn và đầu bếp để phục vụ nhanh hơn.", "target": "tab_1", "event": "tab_staff"},
	{"text": "Làm nhiệm vụ để nhận kim cương. Chúc quán đông khách!", "target": "tab_4", "event": ""},
]
const FEATURE_STEPS := [
	{"text": "Mỗi chương có 6 mục tiêu. Cứ 2 mục tiêu = 1 sao, mỗi sao mở một rương. Đủ 3 sao thì sang quán ở thành phố mới!", "target": "goals", "event": ""},
	{"text": "Đơn đặt tiệc: phục vụ đủ số phần món khách đặt để nhận thưởng lớn.", "target": "orders", "event": ""},
	{"text": "Nghiên cứu: dùng Sách mở nâng cấp vĩnh viễn, giữ lại qua mọi chương.", "target": "research", "event": ""},
	{"text": "Vòng quay may mắn: mỗi ngày quay miễn phí 1 lần!", "target": "wheel", "event": ""},
	{"text": "Bộ sưu tập đầu bếp nổi tiếng: rút thẻ bằng kim cương, mỗi thẻ cộng chỉ số cho quán.", "target": "cards", "event": ""},
	{"text": "Khách có huy hiệu: mặt đỏ là khó tính (boa đậm), máy ảnh là khách du lịch (trả x2), tim vàng là khách quen. Chúc quán phát đạt!", "target": "", "event": ""},
]
const HAND_TIP := Vector2(48, 6)

var feature_mode: bool = false
var steps: Array = []

var step: int = 0
var _panel: PanelContainer
var _text: Label
var _counter: Label
var _next: JuicyButton
var _hand: TextureRect
var _t: float = 0.0
var _step_t: float = 0.0


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel = UIKit.panel("Card")
	_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_panel.offset_left = -330
	_panel.offset_right = 330
	_panel.offset_top = 200
	_panel.offset_bottom = 380
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_panel)
	var row := UIKit.hbox(12)
	_panel.add_child(row)
	var face := TextureRect.new()
	face.texture = Sprites.tex("manager")
	face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	face.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	face.custom_minimum_size = Vector2(96, 130)
	row.add_child(face)
	var v := UIKit.vbox(8)
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(v)
	_counter = UIKit.label("", "SmallLabel", 18)
	v.add_child(_counter)
	_text = UIKit.label("", "", 24)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(480, 0)
	v.add_child(_text)
	var btns := UIKit.hbox(10)
	btns.alignment = BoxContainer.ALIGNMENT_END
	v.add_child(btns)
	var skip := UIKit.button("Bỏ qua", "", "", 150)
	skip.custom_minimum_size = Vector2(150, 54)
	skip.pressed.connect(_finish)
	btns.add_child(skip)
	_next = UIKit.button("Tiếp", "GreenButton", "", 150)
	_next.custom_minimum_size = Vector2(150, 54)
	_next.pressed.connect(_advance)
	btns.add_child(_next)
	_hand = TextureRect.new()
	_hand.texture = Sprites.ui("hand")
	_hand.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_hand.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_hand.size = Vector2(96, 96)
	_hand.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hand)
	steps = FEATURE_STEPS if feature_mode else STEPS
	GameState.tutorial_event.connect(_on_event)
	_show()


func _show() -> void:
	if step >= steps.size():
		_finish()
		return
	var s: Dictionary = steps[step]
	_text.text = str(s["text"])
	_counter.text = "Hướng dẫn %d/%d" % [step + 1, steps.size()]
	_next.text = "Xong" if step == steps.size() - 1 else "Tiếp"
	_next.visible = str(s["event"]).is_empty()
	_step_t = 0.0
	Juice.bounce(_panel, 0.6)


func _on_event(id: String) -> void:
	if step < steps.size() and str(steps[step]["event"]) == id:
		_advance()


func _advance() -> void:
	step += 1
	AudioManager.play("pop")
	_show()


func _process(delta: float) -> void:
	_t += delta
	_step_t += delta
	# bước cần thao tác: sau 8 giây vẫn cho bấm Tiếp để không bị kẹt
	if step < steps.size() and not _next.visible and _step_t > 8.0:
		_next.visible = true
	var target: String = str(steps[mini(step, steps.size() - 1)]["target"])
	var p: Vector2 = Vector2(-1, -1)
	if not target.is_empty() and UIKit.main:
		p = UIKit.main.call("tutorial_target", target)
	_hand.visible = p.x >= 0.0
	if _hand.visible:
		var bob: float = absf(sin(_t * 4.0)) * 16.0
		_hand.position = p - HAND_TIP + Vector2(0, bob)


func _finish() -> void:
	if feature_mode:
		GameState.tutorial2_done = true
	else:
		GameState.tutorial_done = true
		if not GameState.tutorial2_done and UIKit.main:
			UIKit.main.call_deferred("start_tutorial", true)
	finished.emit()
	queue_free()
