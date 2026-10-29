class_name FoodCriticPopup
extends PopupBase
## Popup Nhà Phê Bình Ẩm Thực Ghé Thăm (Food Critic Review)
## Trao chứng nhận 5 sao Michelin Phố Cổ, thưởng Kim Cương và kích hoạt Làn Sóng Khách Nườm Nượp!

var _star_box: HBoxContainer
var _review_quote: Label
var _reward_label: Label
var _claimed: bool = false
var _claim_btn: JuicyButton
var _critic_avatar: Control
var _t: float = 0.0

const REVIEWS := [
	{
		"critic": "Bác Sáu Sành Ăn - Báo Ẩm Thực Ba Miền",
		"quote": "“Nước dùng phở ninh từ xương tủy thơm nức mùi hoa hồi, thảo quả. Bánh phở mướt mềm, thịt bò thơm ngọt. Xứng danh Đệ Nhất Phố Cổ!”",
		"stars": 5,
		"diamonds": 35,
		"mult": 3.0
	},
	{
		"critic": "Đầu Bếp Cung Đình - Hoàng Gia Hội",
		"quote": "“Nem rán giòn rụm bên ngoài, đậm đà béo ngậy bên trong. Cách nêm nếm gia truyền này khiến ta nhớ mãi phong vị ngự thiện năm nào!”",
		"stars": 5,
		"diamonds": 30,
		"mult": 3.0
	},
	{
		"critic": "Ký Giả Phương Xa - Tạp Chí Lữ Khách",
		"quote": "“Quán trọ không chỉ có món ăn trác tuyệt mà không gian sân vườn hoa đào, tiếng nhạc du dương khiến thực khách đắm say quên lối về.”",
		"stars": 5,
		"diamonds": 25,
		"mult": 2.5
	}
]

var _selected_review: Dictionary

func _init() -> void:
	title_text = "Thẩm Định Ẩm Thực"
	panel_width = 620.0
	_selected_review = REVIEWS[randi() % REVIEWS.size()]

func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Nhà Phê Bình Ẩm Thực danh tiếng đã bí mật nếm thử món ăn!", "SmallLabel", 18)
	b.add_child(sub)

	# 1. Chân dung Thẩm Định Viên (Nhân vật VIP phong thái đĩnh đạc)
	var center_box := CenterContainer.new()
	center_box.custom_minimum_size = Vector2(0, 130)
	b.add_child(center_box)

	var frame_box := PanelContainer.new()
	frame_box.theme_type_variation = "Highlight"
	frame_box.custom_minimum_size = Vector2(110, 110)
	center_box.add_child(frame_box)

	var avatar_rect := TextureRect.new()
	avatar_rect.texture = Sprites.tex("cust_vip")
	avatar_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	avatar_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	avatar_rect.custom_minimum_size = Vector2(96, 96)
	frame_box.add_child(avatar_rect)

	# Hiệu ứng thở nhẹ cho avatar
	var tw := avatar_rect.create_tween().set_loops()
	tw.tween_property(avatar_rect, "scale", Vector2(1.04, 1.04), 1.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(avatar_rect, "scale", Vector2(1.0, 1.0), 1.2).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)

	# 2. Bảng Bài Báo Đánh Giá (Nền giấy ngà cổ truyền)
	var card := PanelContainer.new()
	card.theme_type_variation = "Card"
	b.add_child(card)

	var card_v := UIKit.vbox(8)
	card.add_child(card_v)

	var critic_title := UIKit.label(str(_selected_review["critic"]), "HeaderLabel", 22)
	critic_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card_v.add_child(critic_title)

	# 5 Sao Vàng rực rỡ
	_star_box = UIKit.hbox(8)
	_star_box.alignment = BoxContainer.ALIGNMENT_CENTER
	card_v.add_child(_star_box)
	for i in range(5):
		_star_box.add_child(UIKit.icon("star", 36))

	_review_quote = UIKit.label(str(_selected_review["quote"]), "SmallLabel", 18)
	_review_quote.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_review_quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_review_quote.add_theme_color_override("font_color", Color("451a03"))
	card_v.add_child(_review_quote)

	# 3. Phần thưởng
	var reward_box := PanelContainer.new()
	reward_box.theme_type_variation = "Highlight"
	b.add_child(reward_box)

	var rh := UIKit.hbox(12)
	rh.alignment = BoxContainer.ALIGNMENT_CENTER
	reward_box.add_child(rh)

	var d_icon := UIKit.icon("diamond", 38)
	rh.add_child(d_icon)

	var r_text := UIKit.label("+%d Kim Cương & Khách Đông Đột Biến (x%s)!" % [int(_selected_review["diamonds"]), str(_selected_review["mult"])], "HeaderLabel", 20)
	r_text.add_theme_color_override("font_color", Color("0369a1"))
	rh.add_child(r_text)

	# 4. Nút Nhận Chứng Nhận
	_claim_btn = UIKit.button("Vinh Danh & Nhận Quà", "Button", "", 360)
	_claim_btn.pressed.connect(_on_claim)
	b.add_child(_claim_btn)

func _on_claim() -> void:
	if _claimed or _closing:
		return
	_claimed = true
	AudioManager.play("legendary")
	AudioManager.play("levelup", 0.2)
	
	var gems: int = int(_selected_review["diamonds"])
	GameState.add_diamonds(gems)
	
	var bonus_gold: float = maxf(100000.0, GameState.income_rate() * 60.0)
	GameState.add_gold(bonus_gold)
	
	GameState.show_toast("Bài báo ẩm thực đã đăng tải! Lượng khách kéo đến nườm nượp (+%d KC)!" % gems, "star")
	GameState.trigger_rush(18)
	
	if UIKit.main:
		UIKit.main.call("burst_sparkles", panel.get_global_rect().get_center(), 22)
		UIKit.main.call("burst_coins", panel.get_global_rect().get_center(), 14, bonus_gold)
		
	close()
