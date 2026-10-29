extends PopupBase
## Mục tiêu chương: 6 mục tiêu, cứ 2 mục tiêu = 1 sao. Mỗi sao mở một rương. Đủ 3 sao thì sang chương mới.

const RewardScene := preload("res://scenes/ui/RewardPopup.tscn")

var _stars: Array[TextureRect] = []
var _chest_btn: JuicyButton
var _go_btn: JuicyButton
var _rows: Array[Dictionary] = []
var _info: Label


func _init() -> void:
	title_text = "Mục tiêu chương"
	panel_width = 660.0


func _build(b: VBoxContainer) -> void:
	var g := GameState
	var ch := g.chapter_info()
	var head := UIKit.hbox(12)
	b.add_child(head)
	head.add_child(UIKit.icon(str(ch["thumb"]), 110))
	var hv := UIKit.vbox(2)
	hv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hv)
	hv.add_child(UIKit.label("Chương %d: %s" % [g.chapter + 1, str(ch["name"])], "HeaderLabel", 28))
	var srow := UIKit.hbox(4)
	hv.add_child(srow)
	for i in 3:
		var s := UIKit.icon("star_empty", 52)
		srow.add_child(s)
		_stars.append(s)
	_info = UIKit.label("", "SmallLabel", 19)
	_info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hv.add_child(_info)
	for goal: Dictionary in Progress.goals():
		var card := UIKit.panel("Card")
		b.add_child(card)
		var h := UIKit.hbox(10)
		card.add_child(h)
		h.add_child(UIKit.icon(Progress.goal_icon(goal), 52))
		var v := UIKit.vbox(2)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		h.add_child(v)
		var t := UIKit.label(Progress.goal_text(goal), "", 22)
		t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(t)
		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(0, 22)
		bar.show_percentage = false
		v.add_child(bar)
		var bt := UIKit.label("", "WhiteLabel", 16)
		bt.set_anchors_preset(Control.PRESET_FULL_RECT)
		bt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		bt.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		bar.add_child(bt)
		var tick := UIKit.icon("check", 44)
		h.add_child(tick)
		_rows.append({"goal": goal, "bar": bar, "text": bt, "tick": tick})
	var btns := UIKit.hbox(12)
	btns.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(btns)
	_chest_btn = UIKit.button("Mở rương sao", "GreenButton", "chest_gold", 280)
	_chest_btn.pressed.connect(_claim)
	btns.add_child(_chest_btn)
	_go_btn = UIKit.button("Sang chương mới", "RedButton", "arrow_right", 280)
	_go_btn.pressed.connect(_advance)
	btns.add_child(_go_btn)
	Progress.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	if not is_inside_tree():
		return
	var st := Progress.stars()
	for i in 3:
		_stars[i].texture = Sprites.ui("star" if i < st else "star_empty")
	_info.text = "Hoàn thành %d/%d mục tiêu • Đã nhận %d/3 rương" % [Progress.goals_done(), Progress.goals().size(), Progress.stars_taken()]
	for r in _rows:
		var p := Progress.goal_progress(r["goal"])
		var bar: ProgressBar = r["bar"]
		bar.max_value = p.y
		bar.value = minf(p.x, p.y)
		(r["text"] as Label).text = "%s/%s" % [NumberFormat.fmt(minf(p.x, p.y)), NumberFormat.fmt(p.y)]
		(r["tick"] as Control).modulate.a = 1.0 if p.x >= p.y else 0.15
	_chest_btn.disabled = not Progress.star_claimable()
	_chest_btn.pulse = not _chest_btn.disabled
	_go_btn.visible = not GameState.is_last_chapter()
	_go_btn.disabled = not GameState.can_advance_chapter()
	_go_btn.pulse = not _go_btn.disabled


func _claim() -> void:
	var rewards := Progress.claim_star()
	if rewards.is_empty():
		return
	var p: PopupBase = RewardScene.instantiate()
	p.title_text = "Rương sao %d" % Progress.stars_taken()
	p.set("rewards", rewards)
	UIKit.main.call("open_popup", p)
	_refresh()


func _advance() -> void:
	if not GameState.can_advance_chapter():
		return
	close()
	UIKit.main.call("_select_tab", 3)
