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
	panel_width = 660.0
	_selected_review = REVIEWS[randi() % REVIEWS.size()]

func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Nhà Phê Bình Ẩm Thực danh tiếng đã bí mật nếm thử món ăn!", "BodyLabel", 21)
	b.add_child(sub)

	# 1. Khung tranh Thẩm Định Viên
	var center_box := CenterContainer.new()
	center_box.custom_minimum_size = Vector2(0, 140)
	b.add_child(center_box)

	_critic_avatar = Control.new()
	_critic_avatar.custom_minimum_size = Vector2(160, 140)
	_critic_avatar.draw.connect(_draw_critic)
	center_box.add_child(_critic_avatar)

	# 2. Bảng Bài Báo Đánh Giá
	var card := PanelContainer.new()
	card.theme_type_variation = "Card"
	b.add_child(card)

	var card_v := UIKit.vbox(10)
	card.add_child(card_v)

	var critic_title := UIKit.label(str(_selected_review["critic"]), "HeaderLabel", 22)
	critic_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	critic_title.add_theme_color_override("font_color", Color("b45309"))
	card_v.add_child(critic_title)

	# 5 Sao Vàng rực rỡ
	_star_box = UIKit.hbox(8)
	_star_box.alignment = BoxContainer.ALIGNMENT_CENTER
	card_v.add_child(_star_box)
	for i in range(5):
		_star_box.add_child(UIKit.icon("star", 40))

	_review_quote = UIKit.label(str(_selected_review["quote"]), "SmallLabel", 20)
	_review_quote.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_review_quote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_review_quote.add_theme_color_override("font_color", Color("451a03"))
	card_v.add_child(_review_quote)

	# 3. Phần thưởng
	var reward_box := PanelContainer.new()
	reward_box.theme_type_variation = "Highlight"
	b.add_child(reward_box)

	var rh := UIKit.hbox(16)
	rh.alignment = BoxContainer.ALIGNMENT_CENTER
	reward_box.add_child(rh)

	var d_icon := UIKit.icon("diamond", 44)
	rh.add_child(d_icon)

	var r_text := UIKit.label("+%d Kim Cương & Khách Đông Đột Biến (x%s)!" % [int(_selected_review["diamonds"]), str(_selected_review["mult"])], "HeaderLabel", 22)
	r_text.add_theme_color_override("font_color", Color("0284c7"))
	rh.add_child(r_text)

	# 4. Nút Nhận Chứng Nhận
	_claim_btn = UIKit.button("Vinh Danh & Nhận Quà", "GreenButton", "", 360)
	_claim_btn.pressed.connect(_on_claim)
	b.add_child(_claim_btn)

func _process(delta: float) -> void:
	_t += delta * 2.5
	if _critic_avatar:
		_critic_avatar.queue_redraw()

func _draw_critic() -> void:
	var bob := sin(_t) * 3.0
	var c: Vector2 = _critic_avatar.size * 0.5 + Vector2(0, bob)
	
	# Hào quang vàng danh giá
	_critic_avatar.draw_circle(c, 50.0, Color(1, 0.9, 0.6, 0.5))
	
	# Áo dài gấm phê bình gia
	_critic_avatar.draw_circle(c + Vector2(0, 24), 38.0, Color("0284c7"))
	
	# Khuôn mặt râu ria uyên bác
	_critic_avatar.draw_circle(c + Vector2(0, -10), 32.0, Color("fef3c7"))
	
	# Kính tròn tri thức
	_critic_avatar.draw_arc(c + Vector2(-12, -10), 8.0, 0, TAU, 16, Color("78350f"), 2.5)
	_critic_avatar.draw_arc(c + Vector2(12, -10), 8.0, 0, TAU, 16, Color("78350f"), 2.5)
	_critic_avatar.draw_line(c + Vector2(-4, -10), c + Vector2(4, -10), Color("78350f"), 2.5)
	
	# Nụ cười gật gù khen ngợi
	_critic_avatar.draw_arc(c + Vector2(0, 6), 7.0, 0, PI, 12, Color("78350f"), 2.5)
	
	# Râu cằm phúc hậu
	_critic_avatar.draw_colored_polygon(PackedVector2Array([c + Vector2(-6, 12), c + Vector2(6, 12), c + Vector2(0, 22)]), Color("e2e8f0"))
	
	# Khăn xếp xanh trang trọng
	_critic_avatar.draw_arc(c + Vector2(0, -28), 24.0, PI * 0.9, PI * 2.1, 16, Color("0369a1"), 12.0)
	
	# Quạt mo giơ ngón tay cái
	var hand_pos := Vector2(34, -4 + bob)
	_critic_avatar.draw_circle(hand_pos, 10.0, Color("fef3c7"))
	_critic_avatar.draw_line(hand_pos + Vector2(0, -4), hand_pos + Vector2(0, -12), Color("f59e0b"), 4.0)

func _on_claim() -> void:
	# chặn bấm 2 lần trong lúc popup đang mờ dần (từng nhận thưởng 2 lần)
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
