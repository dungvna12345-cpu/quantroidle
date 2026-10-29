extends PopupBase
## Cài đặt: nhạc, âm thanh, rung, xóa dữ liệu (hỏi xác nhận 2 lần).

const ConfirmScene := preload("res://scenes/ui/ConfirmPopup.tscn")


func _init() -> void:
	title_text = "Cài đặt"


const AVATARS: Array[String] = ["avatar", "cust_1", "cust_2", "cust_4", "cust_5", "chef", "manager"]


func _build(b: VBoxContainer) -> void:
	# tên quán + avatar chủ quán
	var name_row := UIKit.hbox(10)
	name_row.add_child(UIKit.label("Tên quán:", "", 26))
	var edit := LineEdit.new()
	edit.text = GameState.owner_name
	edit.max_length = 18
	edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	edit.add_theme_font_size_override("font_size", 26)
	edit.text_changed.connect(func(t: String) -> void:
		GameState.owner_name = t.strip_edges() if not t.strip_edges().is_empty() else "Quán Trọ"
		GameState.notify_state()
	)
	name_row.add_child(edit)
	b.add_child(name_row)
	var av_row := UIKit.hbox(6)
	av_row.alignment = BoxContainer.ALIGNMENT_CENTER
	for a in AVATARS:
		var btn := UIKit.button("", "IconButton", "")
		btn.icon = Sprites.ui(a)
		btn.expand_icon = true
		btn.custom_minimum_size = Vector2(76, 76)
		btn.modulate = Color.WHITE if a == GameState.avatar else Color(1, 1, 1, 0.45)
		btn.pressed.connect(_pick_avatar.bind(a, av_row, btn))
		av_row.add_child(btn)
	b.add_child(av_row)
	b.add_child(HSeparator.new())
	_toggle_row(b, "music", "Nhạc nền", "music")
	_toggle_row(b, "sound", "Âm thanh", "sfx")
	_toggle_row(b, "vibrate", "Rung", "vibrate")
	b.add_child(HSeparator.new())
	var stats := "Danh tiếng: %d (+%d%% thu nhập)\nTổng khách đã phục vụ: %s\nTổng vàng kiếm được: %s" % [
		GameState.reputation, int(GameState.reputation * GameState.bal("prestige_bonus", 0.1) * 100.0),
		NumberFormat.fmt(GameState.total_customers), NumberFormat.fmt(GameState.lifetime_gold)]
	b.add_child(centered_label(stats, "SmallLabel"))
	var tut := UIKit.button("Xem lại hướng dẫn", "BlueButton", "info", 360)
	tut.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	tut.pressed.connect(_replay_tutorial)
	b.add_child(tut)
	var del := UIKit.button("Xóa dữ liệu", "RedButton", "trash", 360)
	del.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	del.pressed.connect(_ask_delete_1)
	b.add_child(del)
	b.add_child(centered_label("Quán Trọ Idle • phiên bản 1.0", "SmallLabel", 18))


func _toggle_row(b: VBoxContainer, icon_id: String, text: String, key: String) -> void:
	var row := UIKit.hbox(14)
	row.add_child(UIKit.icon(icon_id, 52))
	var l := UIKit.label(text, "", 28)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(l)
	var cb := CheckButton.new()
	cb.button_pressed = bool(GameState.settings.get(key, true))
	cb.focus_mode = Control.FOCUS_NONE
	cb.text = "Bật" if cb.button_pressed else "Tắt"
	cb.toggled.connect(func(on: bool) -> void:
		GameState.set_setting(key, on)
		cb.text = "Bật" if on else "Tắt"
		AudioManager.play("click")
	)
	row.add_child(cb)
	b.add_child(row)


func _pick_avatar(a: String, row: HBoxContainer, picked: Button) -> void:
	GameState.avatar = a
	for c in row.get_children():
		(c as Control).modulate = Color(1, 1, 1, 0.45)
	picked.modulate = Color.WHITE
	if UIKit.main:
		UIKit.main.call("refresh_avatar")


func _replay_tutorial() -> void:
	close()
	if UIKit.main:
		UIKit.main.call("start_tutorial")


func _ask_delete_1() -> void:
	var c: PopupBase = ConfirmScene.instantiate()
	c.title_text = "Xóa dữ liệu?"
	c.set("message", "Toàn bộ tiến trình sẽ bị xóa vĩnh viễn.\nBạn có chắc không?")
	c.set("yes_text", "Xóa")
	c.set("yes_variation", "RedButton")
	c.connect("answered", func(yes: bool) -> void:
		if yes:
			_ask_delete_2()
	)
	UIKit.main.call("open_popup", c)


func _ask_delete_2() -> void:
	var c: PopupBase = ConfirmScene.instantiate()
	c.title_text = "Xác nhận lần 2"
	c.set("message", "Đây là lần hỏi cuối cùng.\nXóa hết và chơi lại từ đầu?")
	c.set("yes_text", "Xóa hết")
	c.set("yes_variation", "RedButton")
	c.connect("answered", func(yes: bool) -> void:
		if yes:
			close()
			SaveManager.delete_all()
	)
	UIKit.main.call("open_popup", c)
