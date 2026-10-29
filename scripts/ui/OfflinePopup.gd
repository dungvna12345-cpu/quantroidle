extends PopupBase
## Popup "Chào mừng trở lại": thời gian vắng mặt, vàng kiếm được, nút Nhận / Nhận x2 (tốn kim cương).


var _rays: TextureRect


func _init() -> void:
	title_text = "Chào mừng trở lại!"
	closable = false


func _build(b: VBoxContainer) -> void:
	if ResourceLoader.exists("res://assets/ui/rays.svg"):
		_rays = TextureRect.new()
		_rays.texture = Sprites.ui("rays")
		_rays.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		_rays.size = Vector2(900, 900)
		_rays.pivot_offset = _rays.size * 0.5
		_rays.modulate = Color(1, 0.88, 0.5, 0.7)
		_rays.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(_rays)
		move_child(_rays, 1)
	var away: float = GameState.pending_offline_seconds
	var capped: float = minf(away, GameState.offline_cap_hours() * 3600.0)
	b.add_child(centered_label("Bạn đã vắng mặt %s." % NumberFormat.fmt_time(away), "", 26))
	var who: String = "Quản lý đã trông quán giúp bạn!" if GameState.manager else "Quán vẫn mở cửa khi bạn đi vắng."
	b.add_child(centered_label(who, "SmallLabel"))
	var box := UIKit.panel("Highlight")
	b.add_child(box)
	var row := UIKit.hbox(10)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_child(row)
	row.add_child(UIKit.icon("coin", 72))
	var amount := UIKit.label("+" + NumberFormat.fmt(GameState.pending_offline), "", 54)
	amount.add_theme_color_override("font_color", Color("d98a12"))
	amount.add_theme_color_override("font_outline_color", Color("3a2416"))
	amount.add_theme_constant_override("outline_size", 4)
	row.add_child(amount)
	var note := "Tính %s (tối đa %d giờ)" % [NumberFormat.fmt_time(capped), GameState.offline_cap_hours()]
	if not GameState.manager:
		note += " • Thuê Quản lý để nhận 100%"
	b.add_child(centered_label(note, "SmallLabel", 19))
	var btns := UIKit.hbox(14)
	btns.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(btns)
	var take := UIKit.button("Nhận", "GreenButton", "", 220)
	take.pressed.connect(_claim.bind(false))
	btns.add_child(take)
	var cost: int = int(GameState.bal("offline_x2_diamonds", 5))
	var dbl := UIKit.button("Nhận x2  (%d)" % cost, "BlueButton", "diamond", 260)
	dbl.disabled = GameState.diamonds < cost
	dbl.pulse = not dbl.disabled
	dbl.pressed.connect(_claim.bind(true))
	btns.add_child(dbl)


func _process(delta: float) -> void:
	if _rays:
		_rays.position = get_viewport_rect().size * 0.5 - _rays.size * 0.5
		_rays.rotation += delta * 0.2


func _claim(double: bool) -> void:
	var amount: float = GameState.pending_offline * (2.0 if double else 1.0)
	if GameState.claim_offline(double):
		AudioManager.play("purchase")
		if UIKit.main:
			UIKit.main.call("burst_coins", panel.get_global_rect().get_center(), 8, amount)
		close()
