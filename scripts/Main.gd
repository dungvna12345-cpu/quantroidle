extends Node
## Khung chính: thanh trên (Vàng, Kim cương, Cấp quán + EXP, Cài đặt), vùng nội dung 5 tab,
## thanh tab dưới, lớp hiệu ứng, popup, hướng dẫn. Giao tiếp với logic qua signal của GameState.

const TAB_SCENES: Array[PackedScene] = [
	preload("res://scenes/tabs/InnTab.tscn"),
	preload("res://scenes/tabs/StaffTab.tscn"),
	preload("res://scenes/tabs/MenuTab.tscn"),
	preload("res://scenes/tabs/ExpandTab.tscn"),
	preload("res://scenes/tabs/QuestTab.tscn"),
]
const TAB_NAMES: Array[String] = ["Quán", "Nhân viên", "Thực đơn", "Mở rộng", "Nhiệm vụ"]
const TAB_ICONS: Array[String] = ["icon_customers", "icon_staff", "icon_pot", "icon_plant", "icon_basket"]
## thứ tự hiển thị ở thanh dưới: Thực đơn, Nhân viên, [Quán], Mở rộng, Nhiệm vụ
const NAV_ORDER: Array[int] = [2, 1, 0, 3, 4]
const TAB_EVENTS: Array[String] = ["tab_inn", "tab_staff", "tab_menu", "tab_expand", "tab_quest"]

const ChapterThemeScript := preload("res://scripts/ui/ChapterTheme.gd")
const OfflineScene := preload("res://scenes/ui/OfflinePopup.tscn")
const LevelUpScene := preload("res://scenes/ui/LevelUpPopup.tscn")
const SettingsScene := preload("res://scenes/ui/SettingsPopup.tscn")
const ObjectScene := preload("res://scenes/ui/ObjectPopup.tscn")
const ShopScene := preload("res://scenes/ui/ShopPopup.tscn")
const OrdersScene := preload("res://scenes/ui/OrdersPopup.tscn")
const ChapterScene := preload("res://scenes/ui/ChapterPopup.tscn")
const GoalsScene := preload("res://scenes/ui/GoalsPopup.tscn")
const ResearchScene := preload("res://scenes/ui/ResearchPopup.tscn")
const CollectionScene := preload("res://scenes/ui/CollectionPopup.tscn")
const WheelScene := preload("res://scenes/ui/WheelPopup.tscn")
const DialogueScene := preload("res://scenes/ui/DialoguePopup.tscn")
const RewardScene := preload("res://scenes/ui/RewardPopup.tscn")
const TutorialScene := preload("res://scenes/ui/Tutorial.tscn")
const ResourcePillScene := preload("res://scenes/ui/ResourcePill.tscn")
const CoinFlyScene := preload("res://scenes/fx/CoinFly.tscn")
const SparkleScene := preload("res://scenes/fx/Sparkle.tscn")
const FloatingTextScene := preload("res://scenes/fx/FloatingText.tscn")
const CookingMiniGameScript := preload("res://scripts/ui/CookingMiniGame.gd")
const FortuneStickScript := preload("res://scripts/ui/FortuneStickPopup.gd")
const GuestbookScript := preload("res://scripts/ui/GuestbookPopup.gd")
const MysteryChestScript := preload("res://scripts/ui/MysteryChestPopup.gd")
const PetPopupScript := preload("res://scripts/ui/PetPopup.gd")
const FoodCriticScript := preload("res://scripts/ui/FoodCriticPopup.gd")
const FortuneStormScript := preload("res://scripts/ui/FortuneStormPopup.gd")

const TOP_H := 86.0
const TAB_H := 148.0

@onready var world: InnWorld = $World
@onready var root: Control = $UI/Root

var gold_pill: ResourcePill
var avatar_button: JuicyButton
var diamond_pill: ResourcePill
var level_num: Label
var exp_bar: ProgressBar
var content: Control
var tabs: Array[Control] = []
var tab_buttons: Array[JuicyButton] = []
var tab_labels: Array[Label] = []
var home_nav_btn: JuicyButton
var menu_nav_btn: JuicyButton
var expand_nav_btn: JuicyButton
var staff_nav_btn: JuicyButton
var quest_nav_btn: JuicyButton
var center_nav_btn: JuicyButton
var settings_nav_btn: JuicyButton
var nav_fade: TextureRect
var quest_badge: PanelContainer
var quest_badge_label: Label
var current_tab: int = -1
var popup_layer: Control
var tutorial_layer: Control
var fx_layer: Control
var toast_layer: Control
var fade: ColorRect

var _safe_top: float = 0.0
var _safe_bottom: float = 0.0
var _levelup_queue: Array[Dictionary] = []
var _toast: PanelContainer
var _switching: bool = false


func _ready() -> void:
	UIKit.main = self
	# bảng màu giao diện theo chương (scene được nạp lại mỗi khi sang chương)
	ChapterThemeScript.apply()
	_compute_safe_area()
	_build_content()
	_build_top_bar()
	_build_tab_bar()
	_build_layers()
	GameState.gold_changed.connect(_on_gold)
	GameState.diamonds_changed.connect(_on_diamonds)
	GameState.exp_changed.connect(_on_exp)
	GameState.leveled_up.connect(_on_level_up)
	GameState.coin_fx.connect(_on_coin_fx)
	GameState.toast.connect(show_toast)
	GameState.purchased.connect(_on_purchased)
	GameState.world_reset.connect(_on_world_reset)
	GameState.event_started.connect(_on_event_started)
	GameState.combo_hit.connect(_on_combo)
	world.object_tapped.connect(_on_object_tapped)
	gold_pill.set_target(GameState.gold, true)
	diamond_pill.set_target(GameState.diamonds, true)
	_on_exp(GameState.xp, GameState.exp_needed())
	_select_tab(0, true)
	# hiện dần từ màn khởi động
	fade.color.a = 1.0
	create_tween().tween_property(fade, "color:a", 0.0, 0.4)
	_startup.call_deferred()
	_start_dev_tools()


func _compute_safe_area() -> void:
	if not OS.has_feature("mobile"):
		return
	var safe: Rect2i = DisplayServer.get_display_safe_area()
	var screen: Vector2i = DisplayServer.screen_get_size()
	if screen.y <= 0:
		return
	var vs: Vector2 = root.get_viewport_rect().size
	var k: float = vs.y / float(screen.y)
	_safe_top = maxf(0.0, safe.position.y * k)
	_safe_bottom = maxf(0.0, (screen.y - safe.end.y) * k)


func _startup() -> void:
	AudioManager.set_chapter_music(str(GameState.chapter_info().get("id", "")))
	var errs := GameState.validate_data()
	if not errs.is_empty():
		var c: PopupBase = load("res://scenes/ui/ConfirmPopup.tscn").instantiate()
		c.title_text = "Lỗi dữ liệu game"
		c.set("message", "\n".join(errs.slice(0, 6)))
		c.set("yes_text", "Đã hiểu")
		open_popup(c)
	if GameState.just_advanced:
		GameState.just_advanced = false
		open_popup(ChapterScene.instantiate())
	if GameState.pending_offline > 0.0:
		open_popup(OfflineScene.instantiate())
	# cảnh mở đầu chạy trước, hướng dẫn bắt đầu khi cảnh mở đầu xong
	if not GameState.tutorial_done and Story.seen.get("intro", false):
		start_tutorial()
	elif GameState.tutorial_done and not GameState.tutorial2_done and Story.seen.get("intro", false):
		start_tutorial(true)


# =====================================================================
# Dựng giao diện
# =====================================================================

func _build_top_bar() -> void:
	var top := Control.new()
	top.name = "TopBar"
	top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top.offset_top = 4.0 + _safe_top
	top.offset_bottom = TOP_H + _safe_top
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(top)

	# 1. Avatar tròn (viền gỗ mộc sang trọng)
	var av := UIKit.button("", "IconButton", "avatar")
	av.icon = Sprites.ui(GameState.avatar)
	avatar_button = av
	av.add_theme_constant_override("icon_max_width", 72)
	av.position = Vector2(8, 4)
	av.size = Vector2(72, 72)
	av.custom_minimum_size = Vector2(72, 72)
	av.pressed.connect(open_settings)
	top.add_child(av)

	# 2. Level Badge gắn liền kề avatar
	var lv_pill := PanelContainer.new()
	lv_pill.theme_type_variation = "LevelPill"
	lv_pill.position = Vector2(86, 10)
	lv_pill.size = Vector2(120, 44)
	lv_pill.custom_minimum_size = Vector2(120, 44)
	top.add_child(lv_pill)
	var lvh := UIKit.hbox(4)
	lvh.alignment = BoxContainer.ALIGNMENT_CENTER
	lv_pill.add_child(lvh)
	var star := UIKit.icon("star", 24)
	star.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	lvh.add_child(star)
	level_num = UIKit.label("CẤP %d" % GameState.level, "ResourceLabel", 18)
	level_num.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	lvh.add_child(level_num)

	# Thanh EXP nhỏ gọn dưới capsule cấp
	exp_bar = ProgressBar.new()
	exp_bar.theme_type_variation = "ExpBar"
	exp_bar.position = Vector2(88, 58)
	exp_bar.size = Vector2(116, 8)
	exp_bar.show_percentage = false
	exp_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(exp_bar)

	# 3. Gold Pill [ 🪙 122M (+) ]
	gold_pill = ResourcePillScene.instantiate()
	gold_pill.icon_id = "coin"
	gold_pill.position = Vector2(244, 8)
	gold_pill.size = Vector2(220, 56)
	gold_pill.custom_minimum_size = Vector2(220, 56)
	gold_pill.plus_pressed.connect(open_shop)
	top.add_child(gold_pill)

	# 4. Diamond Pill [ 💎 1,250 (+) ]
	diamond_pill = ResourcePillScene.instantiate()
	diamond_pill.icon_id = "diamond"
	diamond_pill.position = Vector2(476, 8)
	diamond_pill.size = Vector2(192, 56)
	diamond_pill.custom_minimum_size = Vector2(192, 56)
	diamond_pill.plus_pressed.connect(open_shop)
	top.add_child(diamond_pill)

	# 5. Dải trạng thái đặc biệt (chỉ hiện khi có giờ vàng / sự kiện)
	var status_box := PanelContainer.new()
	status_box.name = "StatusBanner"
	status_box.theme_type_variation = "StatusBanner"
	status_box.set_anchors_preset(Control.PRESET_CENTER_TOP)
	status_box.offset_left = -170
	status_box.offset_right = 170
	status_box.offset_top = 70
	status_box.offset_bottom = 106
	status_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	status_box.visible = false
	top.add_child(status_box)
	var stat_lbl := UIKit.label("", "StatusLabel", 16)
	stat_lbl.name = "StatusLabel"
	stat_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	stat_lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	status_box.add_child(stat_lbl)


func _build_content() -> void:
	content = Control.new()
	content.set_anchors_preset(Control.PRESET_FULL_RECT)
	content.offset_top = TOP_H + _safe_top
	content.offset_bottom = -(TAB_H + _safe_bottom - 20.0)
	content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(content)
	for scene in TAB_SCENES:
		var t: Control = scene.instantiate()
		t.visible = false
		content.add_child(t)
		tabs.append(t)


func _build_tab_bar() -> void:
	# Dải nền mờ bảo vệ nội dung
	var grad := Gradient.new()
	grad.set_color(0, Color(0.24, 0.13, 0.08, 0.0))
	grad.set_color(1, Color(0.24, 0.13, 0.08, 0.85))
	var gt := GradientTexture2D.new()
	gt.gradient = grad
	gt.fill_from = Vector2(0.5, 0.0)
	gt.fill_to = Vector2(0.5, 0.6)
	gt.width = 8
	gt.height = 128
	nav_fade = TextureRect.new()
	nav_fade.texture = gt
	nav_fade.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	nav_fade.stretch_mode = TextureRect.STRETCH_SCALE
	nav_fade.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	nav_fade.offset_top = -(TAB_H + _safe_bottom + 40.0)
	nav_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	nav_fade.visible = false
	root.add_child(nav_fade)

	# Đế gỗ thanh điều hướng
	var dock_bg := PanelContainer.new()
	dock_bg.theme_type_variation = "NavBar"
	dock_bg.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	dock_bg.offset_top = -(TAB_H + _safe_bottom - 16.0)
	dock_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(dock_bg)

	# Hàng 5 Tab chính
	var bar := HBoxContainer.new()
	bar.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bar.offset_top = -(TAB_H + _safe_bottom)
	bar.offset_bottom = -(8.0 + _safe_bottom)
	bar.alignment = BoxContainer.ALIGNMENT_CENTER
	bar.add_theme_constant_override("separation", 6)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bar)

	# 1. QUÁN (Tab 0)
	home_nav_btn = _build_nav_card("tab_inn", "QUÁN", _on_tab_pressed.bind(0))
	bar.add_child(home_nav_btn)

	# 2. THỰC ĐƠN (Tab 2)
	menu_nav_btn = _build_nav_card("tab_menu", "THỰC ĐƠN", _on_tab_pressed.bind(2))
	bar.add_child(menu_nav_btn)

	# 3. MỞ RỘNG (Tab 3)
	expand_nav_btn = _build_nav_card("tab_expand", "MỞ RỘNG", _on_tab_pressed.bind(3))
	bar.add_child(expand_nav_btn)

	# 4. NHÂN VIÊN (Tab 1)
	staff_nav_btn = _build_nav_card("tab_staff", "NHÂN VIÊN", _on_tab_pressed.bind(1))
	bar.add_child(staff_nav_btn)

	# 5. NHIỆM VỤ (Tab 4)
	quest_nav_btn = _build_nav_card("tab_quest", "NHIỆM VỤ", _on_tab_pressed.bind(4))
	bar.add_child(quest_nav_btn)

	# Mảng quản lý tab cho hệ thống hướng dẫn & logic game
	tab_buttons.resize(5)
	tab_buttons[0] = home_nav_btn
	tab_buttons[1] = staff_nav_btn
	tab_buttons[2] = menu_nav_btn
	tab_buttons[3] = expand_nav_btn
	tab_buttons[4] = quest_nav_btn

	# Huy hiệu chấm đỏ báo nhiệm vụ nhận thưởng
	quest_badge = UIKit.panel("Badge")
	quest_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	quest_badge_label = UIKit.label("0", "WhiteLabel", 15)
	quest_badge.add_child(quest_badge_label)
	quest_nav_btn.add_child(quest_badge)
	quest_badge.position = Vector2(88, 4)

	# Nút nổi "GIỜ VÀNG" (Fever / Rush)
	center_nav_btn = JuicyButton.new()
	center_nav_btn.name = "FeverButton"
	center_nav_btn.custom_minimum_size = Vector2(80, 80)
	center_nav_btn.size = Vector2(80, 80)
	center_nav_btn.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	center_nav_btn.offset_left = -96
	center_nav_btn.offset_right = -16
	center_nav_btn.offset_top = -(TAB_H + _safe_bottom + 80.0)
	center_nav_btn.offset_bottom = -(TAB_H + _safe_bottom)
	center_nav_btn.pressed.connect(_on_center_button_pressed)
	root.add_child(center_nav_btn)

	var fvb := UIKit.vbox(1)
	fvb.set_anchors_preset(Control.PRESET_FULL_RECT)
	fvb.alignment = BoxContainer.ALIGNMENT_CENTER
	fvb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center_nav_btn.add_child(fvb)

	var fic := TextureRect.new()
	fic.texture = Sprites.ui("dish_pho")
	fic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	fic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	fic.custom_minimum_size = Vector2(40, 40)
	fvb.add_child(fic)

	var flb := UIKit.label("GIỜ VÀNG", "WhiteLabel", 12)
	flb.add_theme_constant_override("outline_size", 4)
	flb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	fvb.add_child(flb)
	_style_nav_center(center_nav_btn)


func _build_nav_card(icon_id: String, text: String, on_click: Callable) -> JuicyButton:
	var b := JuicyButton.new()
	b.custom_minimum_size = Vector2(132, 94)
	b.size_flags_vertical = Control.SIZE_SHRINK_END
	b.pressed.connect(on_click)
	var vb := UIKit.vbox(2)
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	vb.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(vb)
	var ic := TextureRect.new()
	ic.name = "Icon"
	ic.texture = Sprites.ui(icon_id)
	ic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	ic.custom_minimum_size = Vector2(42, 42)
	vb.add_child(ic)
	var lb := UIKit.label(text, "NavLabel", 14)
	lb.name = "Label"
	lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(lb)
	_style_nav_card(b, false)
	return b


func _style_nav_card(b: Button, sel: bool) -> void:
	if b == null:
		return
	if sel:
		var st := StyleBoxFlat.new()
		st.bg_color = Color("991b1b")
		st.border_color = Color("f59e0b")
		st.set_border_width_all(2)
		st.border_width_bottom = 5
		st.set_corner_radius_all(18)
		st.shadow_color = Color(0.96, 0.62, 0.04, 0.35)
		st.shadow_size = 6
		st.shadow_offset = Vector2(0, 1)
		st.content_margin_top = 6.0
		st.content_margin_bottom = 6.0
		st.content_margin_left = 6.0
		st.content_margin_right = 6.0
		for st_name in ["normal", "hover", "pressed", "disabled"]:
			b.add_theme_stylebox_override(st_name, st)
	else:
		for st_name in ["normal", "hover", "pressed", "disabled"]:
			b.add_theme_stylebox_override(st_name, StyleBoxEmpty.new())
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	var lb: Label = b.find_child("Label", true, false)
	if lb:
		lb.add_theme_color_override("font_color", Color("fffdf0") if sel else Color("e0cdb6"))
		lb.add_theme_color_override("font_outline_color", Color("450a0a") if sel else Color("140702"))
		lb.add_theme_constant_override("outline_size", 5 if sel else 3)
	var ic: TextureRect = b.find_child("Icon", true, false)
	if ic:
		ic.modulate = Color(1.0, 1.0, 1.0) if sel else Color(0.88, 0.82, 0.76)


func _style_nav_center(b: Button) -> void:
	if b == null:
		return
	for st_name in ["normal", "hover", "pressed", "disabled"]:
		var st := StyleBoxTexture.new()
		st.texture = Sprites.ui("nav_circle_coral")
		st.content_margin_top = 4.0
		st.content_margin_bottom = 8.0
		b.add_theme_stylebox_override(st_name, st)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())


func _on_center_button_pressed() -> void:
	AudioManager.play("bell")
	Juice.bounce(center_nav_btn, 1.25)
	if current_tab != 0:
		_select_tab(0)
		return
	var a := world.current()
	if a and a.has_method("cheer_all"):
		a.cheer_all()
	GameState.start_fever(25.0)
	sparkle_at(center_nav_btn.global_position)
	GameState.show_toast("GIỜ VÀNG BÙNG NỔ! PHỤC VỤ THẦN TỐC x3!", "bolt")


func _build_layers() -> void:
	popup_layer = _full_layer()
	tutorial_layer = _full_layer()
	fx_layer = _full_layer()
	toast_layer = _full_layer()
	fade = ColorRect.new()
	fade.color = Color(0.12, 0.07, 0.04, 0.0)
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(fade)


func _full_layer() -> Control:
	var c := Control.new()
	c.set_anchors_preset(Control.PRESET_FULL_RECT)
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(c)
	return c


# =====================================================================
# Tab
# =====================================================================

func _on_tab_pressed(i: int) -> void:
	_select_tab(i)


func _select_tab(i: int, instant: bool = false) -> void:
	if i == current_tab:
		return
	var prev := current_tab
	current_tab = i
	for k in tabs.size():
		tabs[k].visible = k == i
	var t := tabs[i]
	if t.has_method("on_shown"):
		t.call("on_shown")
	if not instant:
		# trượt + mờ dần khi chuyển tab
		var dir: float = 1.0 if i > prev else -1.0
		t.position.x = 60.0 * dir
		t.modulate.a = 0.0
		var tw := t.create_tween().set_parallel(true)
		tw.tween_property(t, "position:x", 0.0, 0.22).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tw.tween_property(t, "modulate:a", 1.0, 0.18)
		AudioManager.play("whoosh")
	nav_fade.visible = i != 0
	_style_nav_card(home_nav_btn, i == 0)
	_style_nav_card(menu_nav_btn, i == 2)
	_style_nav_card(expand_nav_btn, i == 3)
	_style_nav_card(staff_nav_btn, i == 1)
	_style_nav_card(quest_nav_btn, i == 4)
	if i >= 0 and i < tab_buttons.size() and tab_buttons[i]:
		Juice.bounce(tab_buttons[i], 1.1)
	GameState.fire_tutorial(TAB_EVENTS[i])


# =====================================================================
# Cập nhật
# =====================================================================

func _process(_delta: float) -> void:
	world.input_enabled = current_tab == 0 and popup_layer.get_child_count() == 0 and not _switching
	if center_nav_btn:
		center_nav_btn.visible = current_tab == 0
	# cốt truyện: hiện cảnh chờ khi màn hình rảnh (không có popup / hướng dẫn)
	if Story.has_pending() and popup_layer.get_child_count() == 0 and tutorial_layer.get_child_count() == 0 \
			and not _switching:
		_play_scene(Story.pop_pending())
	var n: int = GameState.quests_claimable_count()
	quest_badge.visible = n > 0
	quest_badge_label.text = str(n)
	_update_status_banner()


func _update_status_banner() -> void:
	var status_box: Control = root.find_child("StatusBanner", true, false)
	var stat_lbl: Label = root.find_child("StatusLabel", true, false)
	if not stat_lbl or not status_box:
		return
	if GameState.is_fever():
		status_box.visible = true
		stat_lbl.text = "🔥 GIỜ VÀNG BÙNG NỔ! THU NHẬP x3 (%ds)" % int(ceil(GameState.fever_left()))
	elif not GameState.current_event.is_empty():
		status_box.visible = true
		stat_lbl.text = "🏮 SỰ KIỆN: " + str(GameState.current_event.get("name", "ĐANG DIỄN RA")).to_upper()
	else:
		status_box.visible = false


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		# nút Back Android: đóng popup trên cùng hoặc về tab Quán
		var n := popup_layer.get_child_count()
		if n > 0:
			var p := popup_layer.get_child(n - 1)
			if p is PopupBase and (p as PopupBase).closable:
				(p as PopupBase).close()
		elif current_tab != 0:
			_select_tab(0)


func _on_gold(v: float) -> void:
	gold_pill.set_target(v)


func _on_diamonds(v: int) -> void:
	diamond_pill.set_target(v)
	Juice.bounce(diamond_pill.icon_rect, 1.2)


func _on_exp(xp: float, need: float) -> void:
	exp_bar.max_value = need
	exp_bar.value = xp
	level_num.text = "CẤP %d" % GameState.level


func _on_level_up(lv: int, unlocks: Array) -> void:
	_levelup_queue.append({"level": lv, "unlocks": unlocks})
	Juice.bounce(level_num, 2.0)
	if not _has_popup("LevelUp"):
		_show_next_levelup()


func _show_next_levelup() -> void:
	if _levelup_queue.is_empty():
		return
	var d: Dictionary = _levelup_queue.pop_front()
	var p: PopupBase = LevelUpScene.instantiate()
	p.name = "LevelUp"
	p.set("new_level", int(d["level"]))
	p.set("unlocks", d["unlocks"])
	p.closed.connect(_show_next_levelup)
	open_popup(p)


func _has_popup(pname: String) -> bool:
	for c in popup_layer.get_children():
		if str(c.name).begins_with(pname):
			return true
	return false


func _on_purchased(_kind: String) -> void:
	AudioManager.play("purchase")
	AudioManager.vibrate(30)
	Juice.bounce(gold_pill, 0.8)


## Combo chạm khách: chữ "Combo xN!" to dần, màu nóng dần, tiếng cao dần.
func _on_combo(n: int, world_pos: Vector2) -> void:
	if n < 2 or current_tab != 0:
		return
	var sp := world.global_to_screen(world_pos)
	var ft: Label = FloatingTextScene.instantiate()
	ft.set("start", sp + Vector2(0, -40))
	ft.set("color", Color("ffe27a").lerp(Color("ff4500"), clampf(n / 15.0, 0.0, 1.0)))
	ft.text = "Combo x%d!" % n
	ft.add_theme_font_size_override("font_size", 34 + mini(n, 15) * 2)
	fx_layer.add_child(ft)
	# Âm thanh nốt nhạc thăng hoa theo thang âm ngũ cung
	var pitches := [1.0, 1.12, 1.26, 1.34, 1.5, 1.68, 1.88, 2.15]
	var p_idx: int = (n - 2) % pitches.size()
	AudioManager.play_pitch("pop", pitches[p_idx])
	if n % 5 == 0:
		AudioManager.vibrate(40)
		sparkle_at(sp)
		AudioManager.play("levelup", 0.08)
	if n >= 10 and not GameState.is_fever():
		GameState.show_toast("ĐẠI TIỆC CUNG ĐÌNH! TOÀN QUÁN THU NHẬP x3!", "bolt")
		GameState.start_fever(18.0)
		AudioManager.play("legendary")
		AudioManager.vibrate(60)
		for i in 12:
			sparkle_at(sp + Vector2(randf_range(-120, 120), randf_range(-140, 40)))
	elif n == 20 or n == 30:
		GameState.show_toast("RỒNG VÀNG GIÁNG THẾ! COMBO x%d!" % n, "bolt")
		var rate: float = GameState.income_rate()
		GameState.add_gold(rate * 15.0 + 888.0)
		AudioManager.play("legendary")
		for i in 16:
			sparkle_at(sp + Vector2(randf_range(-160, 160), randf_range(-180, 60)))


func _on_event_started(_ev: Dictionary) -> void:
	AudioManager.play("levelup")
	AudioManager.vibrate(40)


func _on_world_reset() -> void:
	SaveManager.save_game()
	get_tree().reload_current_scene()


func _on_object_tapped(area_id: String, kind: String, index: int) -> void:
	var p: PopupBase = ObjectScene.instantiate()
	p.set("area_id", area_id)
	p.set("kind", kind)
	p.set("index", index)
	open_popup(p)


# =====================================================================
# API cho các tab / popup
# =====================================================================

func _play_scene(id: String) -> void:
	if id.is_empty():
		return
	if current_tab != 0:
		_select_tab(0, true)
	var d: Control = DialogueScene.instantiate()
	d.set("scene_id", id)
	d.set("lines", Story.scene_lines(id))
	d.connect("finished", _on_scene_finished)
	open_popup(d)


func _on_scene_finished(id: String) -> void:
	Story.scene_finished(id)
	if id == "intro":
		if not GameState.tutorial_done:
			start_tutorial.call_deferred()
		elif not GameState.tutorial2_done:
			start_tutorial.call_deferred(true)
	if (id.ends_with("_win") or id.begins_with("reg:")) and not Story.last_rewards.is_empty():
		var p: PopupBase = RewardScene.instantiate()
		p.title_text = "Phần thưởng!"
		p.set("rewards", Story.last_rewards)
		Story.last_rewards = []
		open_popup.call_deferred(p)


func open_popup(p: Control) -> void:
	popup_layer.add_child(p)


func open_settings() -> void:
	open_popup(SettingsScene.instantiate())


func open_shop() -> void:
	open_popup(ShopScene.instantiate())


func open_orders() -> void:
	open_popup(OrdersScene.instantiate())


func open_goals() -> void:
	open_popup(GoalsScene.instantiate())


func open_research() -> void:
	open_popup(ResearchScene.instantiate())


func open_collection() -> void:
	open_popup(CollectionScene.instantiate())


func open_wheel() -> void:
	open_popup(WheelScene.instantiate())


func open_cooking() -> void:
	open_popup(CookingMiniGameScript.new())


func open_fortune() -> void:
	open_popup(FortuneStickScript.new())


func open_guestbook() -> void:
	open_popup(GuestbookScript.new())


func open_mystery_chest() -> void:
	open_popup(MysteryChestScript.new())


func open_pet() -> void:
	open_popup(PetPopupScript.new())


func open_food_critic() -> void:
	open_popup(FoodCriticScript.new())


func open_fortune_storm() -> void:
	open_popup(FortuneStormScript.new())


func start_tutorial(features: bool = false) -> void:
	for c in tutorial_layer.get_children():
		c.queue_free()
	_select_tab(0)
	var t: Control = TutorialScene.instantiate()
	t.set("feature_mode", features)
	tutorial_layer.add_child(t)


func refresh_avatar() -> void:
	avatar_button.icon = Sprites.ui(GameState.avatar)


## Chuyển khu có hiệu ứng mờ dần.
func go_to_area(id: String) -> void:
	if _switching:
		return
	if id == GameState.current_area:
		_select_tab(0)
		return
	_switching = true
	AudioManager.play("whoosh")
	var t := create_tween()
	t.tween_property(fade, "color:a", 1.0, 0.2)
	t.tween_callback(func() -> void:
		GameState.set_current_area(id)
		world.show_area(id)
		_select_tab(0, true)
	)
	t.tween_property(fade, "color:a", 0.0, 0.3)
	t.tween_callback(func() -> void: _switching = false)


func show_toast(text: String, icon_id: String = "") -> void:
	if _toast and is_instance_valid(_toast):
		_toast.queue_free()
	_toast = UIKit.panel("Toast")
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := UIKit.hbox(12)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	_toast.add_child(row)
	if not icon_id.is_empty():
		row.add_child(UIKit.icon(icon_id, 44))
	var l := UIKit.label(text, "WhiteLabel", 24)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	# chữ dài thì xuống dòng thay vì tràn ra ngoài màn hình
	var max_w: float = (root.get_viewport_rect().size.x if root else 720.0) - 120.0 - (56.0 if not icon_id.is_empty() else 0.0)
	var font := l.get_theme_font("font")
	if font and font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x > max_w:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size.x = max_w
	row.add_child(l)
	toast_layer.add_child(_toast)
	_toast.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_toast.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_toast.offset_top = TOP_H + _safe_top + 110.0
	_toast.modulate.a = 0.0
	var tw := _toast.create_tween()
	tw.tween_property(_toast, "modulate:a", 1.0, 0.15)
	tw.tween_interval(1.6)
	tw.tween_property(_toast, "modulate:a", 0.0, 0.3)
	tw.tween_callback(_toast.queue_free)


func sparkle_at(screen_pos: Vector2) -> void:
	var s: Node2D = SparkleScene.instantiate()
	s.position = screen_pos
	fx_layer.add_child(s)


## Lấp lánh tại một điểm trong thế giới (toạ độ global của cảnh quán).
func sparkle_at_world(world_pos: Vector2) -> void:
	sparkle_at(world.global_to_screen(world_pos))


## Nhiều đốm lấp lánh toả quanh một điểm màn hình.
func burst_sparkles(screen_pos: Vector2, count: int) -> void:
	for i in mini(count, 12):
		sparkle_at(screen_pos + Vector2(randf_range(-60.0, 60.0), randf_range(-60.0, 60.0)))


## Đồng vàng bay toả từ một điểm màn hình lên ô vàng.
func burst_coins(screen_pos: Vector2, count: int, _amount: float) -> void:
	for i in count:
		_spawn_coin(screen_pos, i * 0.05)


func _spawn_coin(from: Vector2, delay: float) -> void:
	if fx_layer.get_child_count() > 60:
		return
	var c: CoinFly = CoinFlyScene.instantiate()
	c.from = from
	c.to = gold_pill.icon_center()
	c.delay = delay
	c.landed.connect(_on_coin_landed)
	fx_layer.add_child(c)


func _on_coin_landed() -> void:
	gold_pill.bump()
	AudioManager.play("coin", 0.1, 0.06)


func _on_coin_fx(world_pos: Vector2, amount: float) -> void:
	if current_tab != 0:
		gold_pill.bump()
		return
	var sp := world.global_to_screen(world_pos)
	var vs := root.get_viewport_rect().size
	if sp.x < -50 or sp.y < -50 or sp.x > vs.x + 50 or sp.y > vs.y + 50:
		gold_pill.bump()
		return
	var n: int = clampi(2 + int(log(maxf(amount, 1.0)) / log(8.0)), 2, 7)
	if GameState.is_fever():
		n = clampi(n + 3, 5, 10)
	for i in n:
		var jitter := Vector2(randf_range(-18, 18), randf_range(-12, 12))
		_spawn_coin(sp + jitter, i * 0.045)
	var ft: Label = FloatingTextScene.instantiate()
	ft.set("start", sp + Vector2(0, -20))
	ft.text = "+" + NumberFormat.fmt(amount)
	fx_layer.add_child(ft)


## Vị trí màn hình cho bàn tay hướng dẫn. (-1, -1) = không có.
func tutorial_target(target: String) -> Vector2:
	var none := Vector2(-1, -1)
	if target in ["goals", "orders", "research", "wheel", "cards", "menu", "upgrade", "events", "shop"]:
		if current_tab != 0 or popup_layer.get_child_count() > 0:
			return none
		return tabs[0].call("button_center", target)
	if target.begins_with("tab_"):
		var i: int = int(target.substr(4))
		if i == 2:
			return tabs[0].call("button_center", "menu")
		if i == 3:
			return tabs[0].call("button_center", "upgrade")
		if i >= 0 and i < tab_buttons.size() and tab_buttons[i] != null:
			var r := tab_buttons[i].get_global_rect()
			return Vector2(r.get_center().x, r.position.y + 30)
		return none
	if current_tab != 0 or popup_layer.get_child_count() > 0:
		return none
	var a := world.current()
	if a == null:
		return none
	match target:
		"customer":
			var c := a.first_queue_customer()
			if c == null:
				return none
			return world.global_to_screen(a.to_global(c.position + Vector2(0, -40)))
		"table":
			return world.global_to_screen(a.to_global(a.first_table_pos() + Vector2(0, -40)))
	return none


# =====================================================================
# Công cụ kiểm thử (chỉ bật khi chạy với tham số dòng lệnh)
# =====================================================================

func _start_dev_tools() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--shots") or a.begins_with("--bench") or a.begins_with("--autotest") 				or a.begins_with("--flows") or a.begins_with("--prestige") or a.begins_with("--chapters") or a.begins_with("--story"):
			var dev: Node = load("res://scripts/dev/DevTools.gd").new()
			dev.set("main", self)
			add_child(dev)
			return
