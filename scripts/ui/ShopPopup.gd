extends PopupBase
## Cửa hàng kim cương (không dùng tiền thật): x2 thu nhập, gọi khách hàng loạt, túi vàng.

var _cards: Array[UpgradeCard] = []
var _diamond_label: Label
var _boost_label: Label


func _init() -> void:
	title_text = "Cửa hàng"
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	var top := UIKit.hbox(8)
	top.alignment = BoxContainer.ALIGNMENT_CENTER
	top.add_child(UIKit.icon("diamond", 44))
	_diamond_label = UIKit.label("", "HeaderLabel")
	top.add_child(_diamond_label)
	b.add_child(top)
	_boost_label = centered_label("", "GreenLabel")
	b.add_child(_boost_label)
	for item: Dictionary in GameState.shop_data:
		var c := UpgradeCard.new()
		c.setup(Sprites.ui(str(item["icon"])), str(item["name"]), 1)
		c.action.connect(_buy.bind(item, c))
		b.add_child(c)
		_cards.append(c)
	b.add_child(centered_label("Nhận kim cương từ nhiệm vụ, thành tích, quà đăng nhập và khi lên cấp.", "SmallLabel", 19))
	_refresh()


func _process(_delta: float) -> void:
	if GameState.boost_active():
		_boost_label.text = "Đang x2 thu nhập: còn " + NumberFormat.fmt_clock(GameState.boost_left())
	else:
		_boost_label.text = ""


func _refresh() -> void:
	_diamond_label.text = str(GameState.diamonds)
	for i in _cards.size():
		var item: Dictionary = GameState.shop_data[i]
		var desc: String = str(item["desc"])
		if str(item["type"]) == "gold":
			desc += "\n= " + NumberFormat.fmt(GameState.shop_gold_amount(item)) + " vàng"
		_cards[i].set_info("", desc)
		var cost: int = int(item["cost"])
		_cards[i].set_button(0, str(cost), GameState.diamonds >= cost, "BlueButton", "diamond", false)


func _buy(_idx: int, item: Dictionary, card: UpgradeCard) -> void:
	if GameState.shop_buy(item):
		Juice.shake(card, 6.0)
		if UIKit.main:
			UIKit.main.call("sparkle_at", card.buttons[0].get_global_rect().get_center())
	_refresh()
