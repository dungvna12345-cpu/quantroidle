extends PopupBase
## Chúc mừng sang chương mới: ảnh quán mới, thành phố, hệ số thu nhập.

var _t: float = 0.0


func _init() -> void:
	title_text = "CHƯƠNG MỚI!"
	closable = false


func _build(b: VBoxContainer) -> void:
	var g := GameState
	var info := g.chapter_info()
	var pic := TextureRect.new()
	pic.texture = Sprites.ui(str(info["thumb"]))
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	pic.custom_minimum_size = Vector2(0, 240)
	b.add_child(pic)
	b.add_child(centered_label("Chương %d: %s" % [g.chapter + 1, str(info["name"])], "HeaderLabel", 34))
	b.add_child(centered_label(str(info["desc"]), "", 24))
	var box := UIKit.panel("Highlight")
	b.add_child(box)
	var v := UIKit.vbox(2)
	box.add_child(v)
	var l1 := centered_label("Thu nhập mọi món x%d" % int(info["income_mult"]), "GreenLabel", 28)
	v.add_child(l1)
	v.add_child(centered_label("Danh tiếng: %d (+%d%% thu nhập) • +20 kim cương" % [
		g.reputation, int(g.reputation * g.bal("prestige_bonus", 0.1) * 100.0)], "SmallLabel", 20))
	var ok := UIKit.button("Khai trương!", "GreenButton", "", 320)
	ok.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	ok.pressed.connect(close)
	b.add_child(ok)
	AudioManager.play("levelup")
	AudioManager.vibrate(80)


func _process(delta: float) -> void:
	_t += delta
	if _t > 0.35 and UIKit.main:
		_t = 0.0
		var vs := get_viewport_rect().size
		UIKit.main.call("sparkle_at", Vector2(randf_range(0.15, 0.85) * vs.x, randf_range(0.15, 0.45) * vs.y))
