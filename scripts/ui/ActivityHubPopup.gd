class_name ActivityHubPopup
extends PopupBase
## Trung tâm Phúc Lợi & Hoạt Động: gộp tất cả 8 minigame, vòng quay, rút quẻ,
## bão tài lộc, thi nấu ăn, thú cưng, giám khảo và bộ sưu tập vào một giao diện
## chợ hội truyền thống ấm cúng, sang trọng, không làm rác màn hình chính.

var _items: Array[Dictionary] = [
	{
		"id": "wheel",
		"icon": "icon_wheel",
		"title": "Vòng Quay May Mắn",
		"desc": "Quay thưởng vàng, ngọc & quà tặng mỗi ngày.",
		"action_text": "QUAY",
		"method": "open_wheel",
		"badge_check": func() -> bool: return Progress.free_spin()
	},
	{
		"id": "fortune",
		"icon": "gift",
		"title": "Rút Quẻ Đầu Năm",
		"desc": "Xin xăm may mắn, giải quẻ nhận lộc nhân đôi.",
		"action_text": "XIN XĂM",
		"method": "open_fortune",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "storm",
		"icon": "gold_bag",
		"title": "Bão Tài Lộc",
		"desc": "Hứng mưa tiền vàng rơi ngập tràn sân quán.",
		"action_text": "HỨNG LỘC",
		"method": "open_fortune_storm",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "chest",
		"icon": "chest_gold",
		"title": "Rương Thần Bí",
		"desc": "Mở rương kho báu ngẫu nhiên nhận bội thu tài lộc.",
		"action_text": "MỞ RƯƠNG",
		"method": "open_mystery_chest",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "cooking",
		"icon": "icon_plate",
		"title": "Thi Nấu Ăn",
		"desc": "Thử tài khéo tay nhặt nguyên liệu canh chuẩn lửa.",
		"action_text": "THỬ TÀI",
		"method": "open_cooking",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "pet",
		"icon": "icon_staff",
		"title": "Mèo Chiêu Tài",
		"desc": "Vuốt ve, chăm sóc mèo cưng để nhận tiền boa.",
		"action_text": "CHĂM SÓC",
		"method": "open_pet",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "critic",
		"icon": "icon_trophy",
		"title": "Giám Khảo Ẩm Thực",
		"desc": "Mời thực khách sành ăn chấm điểm món quán.",
		"action_text": "CHẤM ĐIỂM",
		"method": "open_food_critic",
		"badge_check": func() -> bool: return true
	},
	{
		"id": "cards",
		"icon": "icon_cards",
		"title": "Sổ Sưu Tập Thẻ",
		"desc": "Bộ sưu tập thẻ ẩm thực tinh hoa và khách quý.",
		"action_text": "XEM SỔ",
		"method": "open_collection",
		"badge_check": func() -> bool: return false
	},
]


func _ready() -> void:
	title_text = "Phúc Lợi & Hoạt Động"
	panel_width = 660.0
	super()


func _build(b: VBoxContainer) -> void:
	var sub := UIKit.label("Tham gia các hoạt động vui nhộn để nhận thưởng dồi dào!", "SmallLabel", 18)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.add_child(sub)

	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(0, 520)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	b.add_child(sc)

	var list := UIKit.vbox(10)
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(list)

	for item in _items:
		var card := _build_activity_card(item)
		list.add_child(card)


func _build_activity_card(info: Dictionary) -> PanelContainer:
	var card := PanelContainer.new()
	card.theme_type_variation = "Card"
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var row := UIKit.hbox(12)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	card.add_child(row)

	# Icon tròn viền gỗ vàng
	var icon_box := PanelContainer.new()
	var isb := StyleBoxFlat.new()
	isb.bg_color = Color("fff2d6")
	isb.set_corner_radius_all(20)
	isb.border_color = Color("dfb678")
	isb.set_border_width_all(2)
	isb.set_content_margin_all(8)
	icon_box.add_theme_stylebox_override("panel", isb)
	row.add_child(icon_box)

	var ic := TextureRect.new()
	ic.texture = Sprites.ui(str(info["icon"]))
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.custom_minimum_size = Vector2(52, 52)
	icon_box.add_child(ic)

	# Thông tin chữ
	var vb := UIKit.vbox(2)
	vb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(vb)

	var title_row := UIKit.hbox(6)
	vb.add_child(title_row)

	var t_lbl := UIKit.label(str(info["title"]), "HeaderLabel", 22)
	t_lbl.add_theme_color_override("font_color", Color("4a2810"))
	title_row.add_child(t_lbl)

	var has_badge: bool = false
	if info.has("badge_check") and info["badge_check"] is Callable:
		has_badge = bool(info["badge_check"].call())

	if has_badge and str(info["id"]) == "wheel":
		var b_pill := PanelContainer.new()
		b_pill.theme_type_variation = "Badge"
		var bl := UIKit.label("MIỄN PHÍ", "WhiteLabel", 14)
		b_pill.add_child(bl)
		title_row.add_child(b_pill)

	var d_lbl := UIKit.label(str(info["desc"]), "SmallLabel", 16)
	d_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(d_lbl)

	# Nút hành động
	var btn := UIKit.button(str(info["action_text"]), "GreenButton" if has_badge else "Button", "", 120)
	btn.custom_minimum_size = Vector2(120, 52)
	btn.add_theme_font_size_override("font_size", 18)
	btn.pressed.connect(func() -> void:
		close()
		if UIKit.main and UIKit.main.has_method(str(info["method"])):
			UIKit.main.call(str(info["method"]))
	)
	row.add_child(btn)

	return card


## Trả về tổng số hoạt động đang có quà hoặc sẵn sàng
static func count_ready() -> int:
	var cnt := 0
	if Progress.free_spin():
		cnt += 1
	if GameState.login_claimable():
		cnt += 1
	# Có thể có thêm các lượt miễn phí khác
	cnt += 1 # luôn có mini-game giải trí sẵn sàng
	return cnt
