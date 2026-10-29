class_name GuestbookPopup
extends PopupBase
## Sổ Tay Thực Khách & Drama Quán Trọ:
## Mở khóa câu chuyện, tính cách độc đáo của từng vị khách quen và nhận quà Kim Cương!

var _scroll: ScrollContainer
var _vbox: VBoxContainer


func _init() -> void:
	title_text = "Sổ Tay Thực Khách"
	panel_width = 680.0


func _build(b: VBoxContainer) -> void:
	var sub := centered_label("Khám phá bí mật & kết thân với các vị khách để nhận quà Kim Cương!", "BodyLabel", 20)
	b.add_child(sub)

	_scroll = ScrollContainer.new()
	_scroll.custom_minimum_size = Vector2(0, 680)
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	b.add_child(_scroll)

	_vbox = UIKit.vbox(14)
	_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scroll.add_child(_vbox)

	_refresh_list()


func _refresh_list() -> void:
	for c in _vbox.get_children():
		c.queue_free()

	for g: Dictionary in GameState.guests_data:
		var card := PanelContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.theme_type_variation = "Card"
		_vbox.add_child(card)

		var h := UIKit.hbox(14)
		card.add_child(h)

		# Ảnh chân dung khách
		var ava := TextureRect.new()
		ava.texture = Sprites.tex(str(g.get("avatar", "customer_regular")))
		ava.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		ava.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		ava.custom_minimum_size = Vector2(85, 100)
		h.add_child(ava)

		# Cột thông tin
		var info_v := UIKit.vbox(3)
		info_v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(info_v)

		# Tên khách + Món yêu thích
		var name_row := UIKit.hbox(8)
		info_v.add_child(name_row)
		var name_l := UIKit.label(str(g.get("name")), "HeaderLabel", 21)
		name_row.add_child(name_l)

		var fav_l := UIKit.label("Món ruột: " + str(g.get("fav_dish")), "SmallLabel", 16)
		fav_l.modulate = Color("e07a3f")
		info_v.add_child(fav_l)

		# Câu nói cửa miệng
		var quote_l := UIKit.label("“" + str(g.get("quote")) + "”", "SideLabel", 16)
		quote_l.modulate = Color("a8a29e")
		quote_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info_v.add_child(quote_l)

		# Tiểu sử ngắn
		var story_l := UIKit.label(str(g.get("story")), "BodyLabel", 17)
		story_l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		info_v.add_child(story_l)

		# Đặc quyền kết thân
		var perk_l := UIKit.label("Đặc quyền: " + str(g.get("perk")), "GreenLabel", 16)
		info_v.add_child(perk_l)

		# Tiến độ kết thân
		var gid: String = str(g.get("id"))
		var req: int = int(g.get("milestone", 10))
		var cur: int = mini(GameState.total_customers, req)
		var dias: int = int(g.get("reward_diamonds", 5))

		var act_row := UIKit.hbox(10)
		info_v.add_child(act_row)

		var prog_l := UIKit.label("Thân thiết: %d/%d khách" % [cur, req], "SmallLabel", 16)
		prog_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		act_row.add_child(prog_l)

		var btn: JuicyButton
		if GameState.guest_claimed.has(gid):
			btn = UIKit.button("ĐÃ NHẬN", "BlueButton", "check", 140)
			btn.disabled = true
		elif cur >= req:
			btn = UIKit.button("NHẬN  %d" % dias, "GreenButton", "diamond", 150)
			btn.pressed.connect(_claim.bind(gid, dias))
		else:
			btn = UIKit.button("CHƯA ĐẠT", "RedButton", "", 140)
			btn.disabled = true
		act_row.add_child(btn)


func _claim(gid: String, dias: int) -> void:
	GameState.guest_claimed[gid] = true
	GameState.add_diamonds(dias)
	AudioManager.play("levelup", 0.15)
	AudioManager.play("coin", 0.1)
	GameState.show_toast("ĐÃ KẾT THÂN! Nhận +%d Kim Cương!" % dias, "diamond")
	SaveManager.save_game()
	if UIKit.main:
		for i in 8:
			UIKit.main.call("sparkle_at", global_position + Vector2(randf_range(-100, 100), randf_range(-60, 60)))
	_refresh_list()
