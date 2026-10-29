class_name FortuneStickPopup
extends PopupBase
## Xin Xăm Quán Trọ / Rút Quẻ Cầu May:
## Lắc ống tre xin quẻ cát tường nhận phúc lộc vàng và kim cương!

var _cylinder_icon: Label
var _draw_btn: JuicyButton
var _card_panel: PanelContainer
var _result_title: Label
var _result_desc: Label
var _reward_label: Label
var _is_shaking: bool = false
var _drawn: bool = false

const FORTUNES := [
	{
		"title": "🏮 QUẺ ĐẠI CÁT: KIM NGÂN ĐẦY NHÀ",
		"desc": "Hôm nay quán trọ tài lộc hanh thông, buôn may bán đắt, vàng ròng chảy vào như nước!",
		"gold_mult": 40.0,
		"diamonds": 2,
		"fever": 25.0,
		"color": "facc15"
	},
	{
		"title": "✨ QUẺ THƯỢNG CÁT: KHÁCH QUÝ ĐẬM TÌNH",
		"desc": "Khách thập phương tấp nập tìm đến, tiếng lành đồn xa khắp ba miền đất nước!",
		"gold_mult": 25.0,
		"diamonds": 3,
		"fever": 15.0,
		"color": "fb923c"
	},
	{
		"title": "🍲 QUẺ TRUNG CÁT: BẾP LỬA HỒNG HÀO",
		"desc": "Hương thơm nức nở, nồi niêu reo vui, đầu bếp trổ tài chiêu đãi thực khách!",
		"gold_mult": 20.0,
		"diamonds": 1,
		"fever": 10.0,
		"color": "38bdf8"
	},
	{
		"title": "🎋 QUẺ AN KHANG: PHƯỚC LỘC TOÀN GIA",
		"desc": "Quán trọ ấm êm, nhân viên đồng lòng, khách trọ mến thương lưu luyến không rời.",
		"gold_mult": 15.0,
		"diamonds": 2,
		"fever": 8.0,
		"color": "4ade80"
	}
]


func _init() -> void:
	title_text = "Xin Xăm Quán Trọ"
	panel_width = 650.0


func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Lắc ống xăm đầu ngày để cầu tài lộc và may mắn!", "BodyLabel", 22)
	b.add_child(sub)

	# Ống xăm biểu tượng
	var cbox := CenterContainer.new()
	cbox.custom_minimum_size = Vector2(0, 130)
	b.add_child(cbox)

	_cylinder_icon = Label.new()
	_cylinder_icon.text = "🎋"
	_cylinder_icon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_cylinder_icon.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_cylinder_icon.add_theme_font_size_override("font_size", 90)
	_cylinder_icon.pivot_offset = Vector2(45, 50)
	cbox.add_child(_cylinder_icon)

	# Khung quẻ xăm hiển thị kết quả
	_card_panel = PanelContainer.new()
	_card_panel.custom_minimum_size = Vector2(0, 160)
	_card_panel.modulate.a = 0.0
	b.add_child(_card_panel)

	var cv := UIKit.vbox(10)
	_card_panel.add_child(cv)

	_result_title = UIKit.label("", "HeaderLabel", 24)
	_result_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cv.add_child(_result_title)

	_result_desc = UIKit.label("", "BodyLabel", 19)
	_result_desc.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_result_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cv.add_child(_result_desc)

	_reward_label = UIKit.label("", "GreenLabel", 20)
	_reward_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cv.add_child(_reward_label)

	_draw_btn = UIKit.button("🎋 LẮC ỐNG XĂM NGAY!", "RedButton", "", 320)
	_draw_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_draw_btn.pressed.connect(_on_draw_pressed)
	b.add_child(_draw_btn)


func _on_draw_pressed() -> void:
	if _drawn:
		close()
		return
	if _is_shaking:
		return
	_is_shaking = true
	_draw_btn.disabled = true

	# Lắc ống xăm
	AudioManager.play("bell", 0.1)
	var st := create_tween()
	for i in 6:
		st.tween_property(_cylinder_icon, "rotation", 0.25 if i % 2 == 0 else -0.25, 0.08)
	st.tween_property(_cylinder_icon, "rotation", 0.0, 0.08)
	st.tween_callback(_reveal_fortune)


func _reveal_fortune() -> void:
	_drawn = true
	_is_shaking = false
	_draw_btn.disabled = false

	var f: Dictionary = FORTUNES[randi() % FORTUNES.size()]

	_result_title.text = str(f["title"])
	_result_title.modulate = Color(str(f["color"]))
	_result_desc.text = str(f["desc"])

	var bonus_gold := maxf(388.0, GameState.income_rate() * float(f["gold_mult"]))
	var dias: int = int(f["diamonds"])
	var fever_dur: float = float(f["fever"])

	GameState.add_gold(bonus_gold)
	GameState.add_diamonds(dias)
	GameState.start_fever(fever_dur)

	_reward_label.text = "Phần Thưởng: +%s Vàng • +%d 💎 • Giờ Vàng %ds!" % [
		NumberFormat.fmt(bonus_gold), dias, int(fever_dur)
	]

	AudioManager.play("levelup", 0.15)
	Juice.bounce(_card_panel, 1.2)

	var fade := create_tween()
	fade.tween_property(_card_panel, "modulate:a", 1.0, 0.25)

	_draw_btn.text = "TẠ TƠN THẦN LINH ✨"

	if UIKit.main:
		for i in 8:
			UIKit.main.call("sparkle_at", _draw_btn.global_position + Vector2(randf_range(-120, 120), randf_range(-60, 20)))
