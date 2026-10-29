extends PopupBase
## Mini-game 3 Rương Thần Bí của Thương Buôn Phương Xa.
## Người chơi chọn 1 trong 3 chiếc rương sơn mài để nhận thưởng lớn.

const SunRaysScript := preload("res://scripts/ui/SunRays.gd")

class ChestCard extends Control:
	signal selected(card: ChestCard)
	
	var chest_id: int = 0
	var title: String = ""
	var reward_type: String = "gold" # gold / diamond / boost
	var reward_amount: int = 0
	var reward_desc: String = ""
	var is_open: bool = false
	var is_chosen: bool = false
	
	var chest_icon: String = "chest_gold"
	var box_panel: PanelContainer
	var icon_box: Control
	var title_label: Label
	var reward_label: Label
	var rays_node: Node2D
	var glow_fx: TextureRect
	
	func _init(id: int, p_title: String, p_icon: String, p_type: String, p_amount: int, p_desc: String) -> void:
		chest_id = id
		title = p_title
		chest_icon = p_icon
		reward_type = p_type
		reward_amount = p_amount
		reward_desc = p_desc
		custom_minimum_size = Vector2(160, 240)
		size = Vector2(160, 240)

	func _ready() -> void:
		box_panel = UIKit.panel("Card")
		box_panel.set_anchors_preset(Control.PRESET_FULL_RECT)
		add_child(box_panel)
		
		var vb := UIKit.vbox(8)
		vb.set_anchors_preset(Control.PRESET_FULL_RECT)
		vb.alignment = BoxContainer.ALIGNMENT_CENTER
		box_panel.add_child(vb)
		
		icon_box = Control.new()
		icon_box.custom_minimum_size = Vector2(120, 110)
		vb.add_child(icon_box)
		
		rays_node = SunRaysScript.new()
		rays_node.position = Vector2(60, 55)
		rays_node.radius = 80.0
		rays_node.visible = false
		icon_box.add_child(rays_node)
		
		glow_fx = TextureRect.new()
		glow_fx.texture = Sprites.ui(chest_icon)
		glow_fx.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		glow_fx.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		glow_fx.size = Vector2(90, 90)
		glow_fx.position = Vector2(15, 10)
		icon_box.add_child(glow_fx)
		
		title_label = UIKit.label(title, "SideLabel", 15)
		title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vb.add_child(title_label)
		
		reward_label = UIKit.label("CHƯA MỞ", "SmallLabel", 13)
		reward_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		reward_label.add_theme_color_override("font_color", Color("ffd700"))
		vb.add_child(reward_label)
		
		var btn := JuicyButton.new()
		btn.theme_type_variation = "FlatButton"
		btn.set_anchors_preset(Control.PRESET_FULL_RECT)
		btn.pressed.connect(_on_pressed)
		add_child(btn)

	func _on_pressed() -> void:
		if not is_open:
			selected.emit(self)

	func reveal(chosen: bool) -> void:
		is_open = true
		is_chosen = chosen
		if chosen:
			box_panel.theme_type_variation = "Highlight"
			rays_node.visible = true
			glow_fx.modulate = Color(1.3, 1.2, 0.4)
			Juice.bounce(icon_box, 1.25)
		else:
			modulate = Color(0.7, 0.7, 0.7, 0.8)
			
		match reward_type:
			"gold":
				glow_fx.texture = Sprites.ui("coin")
				reward_label.text = "+%s Vàng" % NumberFormat.fmt(reward_amount)
			"diamond":
				glow_fx.texture = Sprites.ui("diamond")
				reward_label.text = "+%d Kim Cương" % reward_amount
			"boost":
				glow_fx.texture = Sprites.ui("bolt")
				reward_label.text = "Tăng Tốc x2"

var _chests: Array[ChestCard] = []
var _has_chosen: bool = false
var _claim_btn: JuicyButton
var _chosen_reward: Dictionary = {}

func _init() -> void:
	title_text = "RƯƠNG THẦN BÍ"

func _build(b: VBoxContainer) -> void:
	b.add_child(centered_label("Thương buôn mang tới 3 chiếc rương chứa cổ vật quý giá.\nHãy chọn 1 chiếc rương để thử vận may của bạn!", "SmallLabel", 18))
	
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 14)
	b.add_child(row)
	
	var rate: float = GameState.income_rate()
	var gold_val: int = int(maxf(100000.0, rate * 120.0))
	
	var rewards := [
		{"type": "gold", "amount": gold_val, "desc": "Kho Báu Tiền Vàng"},
		{"type": "diamond", "amount": 25, "desc": "Túi Kim Cương Hoàng Gia"},
		{"type": "boost", "amount": 180, "desc": "Buff Tăng Tốc x2 (180s)"}
	]
	rewards.shuffle()
	
	var titles := ["Rương Sơn Mài", "Rương Hoàng Kim", "Rương Bạc Quý"]
	var icons := ["chest_wood", "chest_gold", "chest_silver"]
	
	for i in 3:
		var r: Dictionary = rewards[i]
		var c := ChestCard.new(i, titles[i], icons[i], r["type"], r["amount"], r["desc"])
		c.selected.connect(_on_chest_selected)
		row.add_child(c)
		_chests.append(c)
		
	_claim_btn = UIKit.button("CHỌN 1 RƯƠNG ĐỂ MỞ", "GreenButton", "", 320)
	_claim_btn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_claim_btn.disabled = true
	_claim_btn.pressed.connect(_on_claim)
	b.add_child(_claim_btn)

func _on_chest_selected(card: ChestCard) -> void:
	if _has_chosen:
		return
	_has_chosen = true
	AudioManager.play("chest_open")
	AudioManager.play("legendary")
	AudioManager.vibrate(50)
	
	_chosen_reward = {
		"type": card.reward_type,
		"amount": card.reward_amount,
		"desc": card.reward_desc
	}
	
	for c in _chests:
		c.reveal(c == card)
		
	# Trao thưởng
	match card.reward_type:
		"gold":
			GameState.add_gold(card.reward_amount)
			_claim_btn.text = "NHẬN %s VÀNG" % NumberFormat.fmt(card.reward_amount)
		"diamond":
			GameState.add_diamonds(card.reward_amount)
			_claim_btn.text = "NHẬN %d KIM CƯƠNG" % card.reward_amount
		"boost":
			GameState.activate_boost(float(card.reward_amount))
			_claim_btn.text = "KÍCH HOẠT TĂNG TỐC x2"
			
	_claim_btn.disabled = false
	_claim_btn.pulse = true

func _on_claim() -> void:
	close()
