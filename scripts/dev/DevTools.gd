extends Node
## Công cụ kiểm thử, chỉ chạy khi có tham số sau "--" trên dòng lệnh:
##   --shots=<thư mục>   chụp màn hình các tab rồi thoát
##   --bench             đo FPS với 30 khách cùng lúc
##   --autotest=<giây>   bot tự chơi ở tốc độ x8, in tiến trình mỗi phút game

var main: Node
var _log_t: float = 0.0
var _bot_t: float = 0.0
var _game_t: float = 0.0
var _running_bot: bool = false
var _first_events: Dictionary = {}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	Story.enabled = OS.get_cmdline_user_args().has("--story")
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots"):
			_shots(a.get_slice("=", 1) if a.contains("=") else "user://shots")
		elif a.begins_with("--bench"):
			_bench()
		elif a.begins_with("--flows"):
			_flows()
		elif a.begins_with("--story"):
			_story_test(a.get_slice("=", 1) if a.contains("=") else "user://shots")
		elif a.begins_with("--chapters"):
			_chapters(a.get_slice("=", 1) if a.contains("=") else "user://shots")
		elif a.begins_with("--prestige"):
			_prestige_test()
		elif a.begins_with("--autotest"):
			_autotest(float(a.get_slice("=", 1)) if a.contains("=") else 60.0)


func _wait(sec: float) -> void:
	await get_tree().create_timer(sec, true, false, true).timeout


func _capture(dir: String, file_name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var path := dir.path_join(file_name)
	img.save_png(path)
	print("SHOT ", ProjectSettings.globalize_path(path))


func _close_overlays() -> void:
	if not Story.enabled:
		Story.pending.clear()
	for layer_name in ["tutorial_layer", "popup_layer"]:
		var layer: Control = main.get(layer_name)
		for c in layer.get_children():
			c.queue_free()


## Trạng thái giữa game để ảnh chụp có nội dung thật.
func _demo_state() -> void:
	SaveManager.enabled = false
	var g := GameState
	g.tutorial_done = true
	g.tutorial2_done = true
	g.level = 9
	g.xp = 30
	g.gold = 18450
	g.diamonds = 46
	g.total_customers = 412
	g.lifetime_gold = 52000
	for d: Dictionary in g.dishes:
		if int(d["unlock_level"]) <= g.level:
			g.dish_levels[d["id"]] = 2 + randi() % 6
	g.staff["chef"]["count"] = 2
	g.staff["waiter"]["count"] = 3
	g.staff["waiter"]["level"] = 4
	g.staff["receptionist"]["count"] = 1
	g.manager = true
	var hall: Dictionary = g.areas["hall"]
	for i in 6:
		hall["tables"][i] = [12, 8, 5, 3, 2, 1][i]
	hall["decor"] = {"plant": 2, "lantern": 2, "painting": 1, "rug": 1}
	g.areas["garden"]["unlocked"] = true
	g.areas["garden"]["tables"][2] = 1
	g.areas["garden"]["decor"] = {"lantern": 2, "plant": 1}
	g.add_daily("serve", 34)
	g.add_daily("upgrade", 5)
	for id: String in g.areas:
		g.notify_area(id)
	g.notify_state()
	g.add_gold(0.0)
	g.add_diamonds(0)
	g.add_xp(0.0)


func _shots(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	_demo_state()
	_close_overlays()
	var world: InnWorld = main.get("world")
	world.show_area("hall", true)
	world.zoom_level = 0.85
	world.camera.position = world.current().position + Iso.to_world(Vector2(4.6, 4.8))
	world.call("_apply_camera")
	await _wait(9.0)
	await _capture(dir, "01_quan_sanh_an.png")
	for i in range(1, 5):
		main.call("_select_tab", i, true)
		await _wait(0.8)
		await _capture(dir, "0%d_tab_%d.png" % [i + 1, i])
	main.call("_select_tab", 0, true)
	main.call("go_to_area", "garden")
	await _wait(8.0)
	await _capture(dir, "06_san_vuon.png")
	main.call("_on_object_tapped", "garden", "table", 0)
	await _wait(0.8)
	await _capture(dir, "07_popup_nang_cap.png")
	_close_overlays()
	main.call("_on_level_up", 10, [{"icon": "dish_banh_xeo", "text": "Món mới: Bánh xèo"}])
	await _wait(1.2)
	await _capture(dir, "08_len_cap.png")
	_close_overlays()
	Progress.research_points = 12
	Progress.buy_research("income")
	Progress.buy_research("income")
	Progress.buy_research("cook")
	Progress.pull_free(8)
	var k := 9
	for fn in ["open_goals", "open_research", "open_collection", "open_wheel"]:
		main.call(fn)
		await _wait(1.0)
		await _capture(dir, "%02d_%s.png" % [k, fn.substr(5)])
		_close_overlays()
		await _wait(0.3)
		k += 1
	main.call("go_to_area", "hall")
	await _wait(1.5)
	await _capture(dir, "13_man_chinh.png")
	# cận cảnh, ban đêm, công trường
	world.zoom_level = 1.3
	world.camera.position = world.current().position + Iso.to_world(Vector2(5, 4))
	world.call("_apply_camera")
	await _wait(1.0)
	await _capture(dir, "14_can_canh.png")
	g.day_t = g.bal("day_cycle_seconds", 480) * 0.75
	await _wait(1.0)
	await _capture(dir, "15_ban_dem.png")
	g.day_t = 60.0
	g.areas["hall"]["wings"] = {"side": Time.get_unix_time_from_system() + 30.0}
	g.notify_area("hall")
	world.zoom_level = 0.75
	world.camera.position = world.current().position + Iso.to_world(Vector2(12, 4))
	world.call("_apply_camera")
	await _wait(1.5)
	await _capture(dir, "16_cong_truong.png")
	get_tree().quit()


## Bấm qua mọi popup và luồng chính để bắt lỗi khi chạy.
func _flows() -> void:
	var g := GameState
	_close_overlays()
	g.tutorial_done = true
	g.add_gold(5000000.0)
	g.add_diamonds(500)
	g.add_xp(2000.0)
	print("FLOWS cấp=", g.level)
	await _wait(0.3)
	_close_overlays()
	await _wait(0.3)
	var popups: Control = main.get("popup_layer")
	# mở khóa mọi khu, vào từng khu, mở popup của từng loại vật
	for ad: Dictionary in g.areas_data:
		var id: String = ad["id"]
		g.unlock_area(id)
		main.call("go_to_area", id)
		await _wait(0.8)
		var kinds: Array = ["table", "kitchen", "cashier"] if ad["kind"] == "dining" else ["room", "reception"]
		for k: String in kinds:
			for idx in [0, 3]:
				main.call("_on_object_tapped", id, k, idx)
				await _wait(0.3)
				for p in popups.get_children():
					if p.has_method("_buy"):
						for i in 2:
							p.call("_buy", [1, 10][i])
					p.call("close")
				await _wait(0.3)
		var a: InnArea = (main.get("world") as InnWorld).current()
		for i in 12:
			a.spawn_customer()
		for c in a.customers:
			a.tap(c.position + Vector2(0, -40))
		for t in a.tables:
			t.add_tip(10.0)
			a.tap(t.position + t.tip_sprite.position)
		await _wait(3.0)
	# các tab: bấm mọi nút
	for i in range(1, 5):
		main.call("_select_tab", i, true)
		await _wait(0.4)
		_press_all(main.get("tabs")[i])
		await _wait(0.4)
	_close_overlays()
	main.call("_select_tab", 0, true)
	# popup phụ
	main.call("open_shop")
	await _wait(0.4)
	for p in popups.get_children():
		_press_all(p)
	await _wait(0.4)
	_close_overlays()
	main.call("open_settings")
	await _wait(0.4)
	_close_overlays()
	g.pending_offline = 1234.0
	g.pending_offline_seconds = 3700.0
	main.call("open_popup", load("res://scenes/ui/OfflinePopup.tscn").instantiate())
	await _wait(0.4)
	for p in popups.get_children():
		if p.has_method("_claim"):
			p.call("_claim", true)
	await _wait(0.6)
	# sự kiện + đơn đặt tiệc
	main.call("go_to_area", "hall")
	await _wait(0.8)
	for ev in ["rush", "festival", "rich", "tip_rain"]:
		g.start_event(ev)
		await _wait(1.5)
	var hall: InnArea = (main.get("world") as InnWorld).current()
	for c in hall.customers:
		hall.tap(c.position + Vector2(0, -40))
	for t in hall.tables:
		if t.tip_value > 0.0:
			hall.tap(t.position + t.tip_sprite.position)
	for o: Dictionary in g.orders:
		o["have"] = o["need"]
	main.call("open_orders")
	await _wait(0.5)
	for p in popups.get_children():
		for i in 3:
			p.call("_claim", i)
		p.call("_skip", 0)
	await _wait(0.5)
	_close_overlays()
	print("FLOWS sự_kiện=%s đơn_xong=%d món_đặc_biệt=%s" % [g.current_event.get("id", ""), int(g.daily.get("progress", {}).get("order", 0)), g.daily_special()])
	# tiến trình: sao chương, nghiên cứu, thẻ, vòng quay
	var pr := Progress
	pr.research_points = 40
	for r: Dictionary in pr.research_data:
		for k in 3:
			pr.buy_research(str(r["id"]))
	pr.pull_free(15)
	g.add_diamonds(400)
	for fn in ["open_goals", "open_research", "open_collection", "open_wheel"]:
		main.call(fn)
		await _wait(0.6)
		for p in popups.get_children():
			if p.has_method("_claim"):
				p.call("_claim")
			if p.has_method("_spin"):
				p.call("_spin")
				await _wait(4.2)
			if p.has_method("_pull"):
				p.call("_pull", 10)
		await _wait(0.8)
		_close_overlays()
		await _wait(0.3)
	print("FLOWS tiến_trình: sao=%d đã_nhận=%d mục_tiêu=%d sách=%d nghiên_cứu=%d thẻ=%d bonus_thu_nhập=%s" % [
		pr.stars(), pr.stars_taken(), pr.goals_done(), pr.research_points, pr.research_total(), pr.cards_owned(), pr.bonus("income")])
	main.call("start_tutorial")
	await _wait(0.5)
	for e in ["tap_customer", "popup_object", "tab_menu", "tab_staff"]:
		g.fire_tutorial(e)
		await _wait(0.2)
	_close_overlays()
	print("FLOWS vàng=%s kim_cương=%d khách=%d cấp=%d" % [NumberFormat.fmt(g.gold), g.diamonds, g.total_customers, g.level])
	print("FLOWS prestige: can=%s gain=%d" % [g.can_prestige(), g.prestige_gain()])
	await _wait(0.5)
	get_tree().quit()


## Tái khởi nghiệp rồi đặt lại toàn bộ (cả hai đều nạp lại cảnh).
func _prestige_test() -> void:
	var g := GameState
	g.tutorial_done = true
	g.add_gold(1.0e8)
	g.add_xp(1.0e6)
	await _wait(0.5)
	print("PRESTIGE trước: cấp=%d danh_tiếng=%d gain=%d" % [g.level, g.reputation, g.prestige_gain()])
	g.do_prestige()
	await get_tree().create_timer(2.0, true, false, true).timeout
	print("PRESTIGE sau: cấp=%d vàng=%s danh_tiếng=%d hệ_số=%s" % [g.level, NumberFormat.fmt(g.gold), g.reputation, g.income_mult()])
	g.reset_everything()
	await get_tree().create_timer(2.0, true, false, true).timeout
	print("RESET sau: cấp=%d danh_tiếng=%d" % [g.level, g.reputation])
	get_tree().quit()


## Đi qua cả 5 chương: chụp quán của mỗi chương rồi sang chương sau (cảnh được nạp lại).
func _chapters(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	var g := GameState
	g.tutorial_done = true
	await _wait(1.0)
	_close_overlays()
	await _wait(5.0)
	await _capture(dir, "chuong_%d.png" % (g.chapter + 1))
	print("CHAPTER %d %s cấp=%d hệ_số=%s vàng=%s" % [g.chapter + 1, g.chapter_info()["name"], g.level, g.income_mult(), NumberFormat.fmt(g.gold)])
	if g.is_last_chapter():
		main.call("_select_tab", 3, true)
		await _wait(0.8)
		await _capture(dir, "hanh_trinh.png")
		get_tree().quit()
		return
	g.add_xp(1.0e7)
	_complete_goals()
	await _wait(0.3)
	_close_overlays()
	print("CHAPTER sao=%d có_thể_sang=%s" % [Progress.stars(), g.can_advance_chapter()])
	g.advance_chapter()


## Hoàn thành mọi mục tiêu chương hiện tại (chỉ dùng khi kiểm thử).
func _complete_goals() -> void:
	var g := GameState
	g.run_customers = 999999
	g.run_gold = 1.0e18
	for d: String in g.dish_levels:
		g.dish_levels[d] = 50
	for id: String in g.staff:
		g.staff[id]["count"] = int(g.staff_data[id]["max_count"])
	for id: String in g.areas:
		var a: Dictionary = g.areas[id]
		a["unlocked"] = true
		for i in (a["tables"] as Array).size():
			a["tables"][i] = maxi(1, int(a["tables"][i]))
		for i in (a["rooms"] as Array).size():
			a["rooms"][i] = maxi(1, int(a["rooms"][i]))
		for k: String in g.decor_data:
			a["decor"][k] = g.decor_max(id, k)


## Kiểm tra cốt truyện: cảnh mở đầu, thử thách của Phát, khách quen, lời nói của khách.
func _story_test(dir: String) -> void:
	DirAccess.make_dir_recursive_absolute(dir)
	var g := GameState
	var popups: Control = main.get("popup_layer")
	await _wait(2.5)
	await _capture(dir, "s1_intro.png")
	for i in 3:
		_click_dialog(popups)
		await _wait(0.15)
	await _wait(1.2)
	await _capture(dir, "s2_phat.png")
	for i in 30:
		_click_dialog(popups)
		await _wait(0.05)
	await _wait(1.0)
	_close_overlays()
	g.tutorial_done = true
	g.tutorial2_done = true
	print("STORY intro_seen=%s tutorial_layer=%d" % [Story.seen.get("intro", false), (main.get("tutorial_layer") as Control).get_child_count()])
	_close_overlays()
	# đạt 1 sao -> cảnh sao 1 -> Phát thách đấu
	g.add_xp(5000.0)
	_complete_goals_partial()
	for k in 40:
		await _wait(0.3)
		for i in 10:
			_click_dialog(popups)
		if not Story.challenge.is_empty():
			break
	print("STORY thử_thách=", Story.challenge)
	await _wait(1.0)
	await _capture(dir, "s3_thu_thach.png")
	g.add_gold(1.0e9, true)
	g.run_gold += 1.0e9
	await _wait(1.5)
	await _capture(dir, "s4_thang.png")
	for i in 20:
		_click_dialog(popups)
		await _wait(0.05)
	await _wait(1.0)
	await _capture(dir, "s5_thuong.png")
	print("STORY thắng=%s phần_thưởng_popup=%d" % [Story.challenge_won, popups.get_child_count()])
	_close_overlays()
	# khách quen + lời nói
	var a: InnArea = (main.get("world") as InnWorld).current()
	for i in 6:
		a.spawn_customer()
	for c in a.customers:
		c.say(Story.chatter("queue"))
	Story.serve_regular("ong_ba")
	Story.serve_regular("ong_ba")
	Story.serve_regular("ong_ba")
	await _wait(1.0)
	await _capture(dir, "s6_khach_quen.png")
	print("STORY thân_thiết=", Story.friendship, " chờ=", Story.pending)
	get_tree().quit()


func _click_dialog(popups: Control) -> void:
	for p in popups.get_children():
		if p.has_method("_next"):
			var ev := InputEventMouseButton.new()
			ev.button_index = MOUSE_BUTTON_LEFT
			ev.pressed = true
			p.call("_gui_input", ev)


func _complete_goals_partial() -> void:
	var g := GameState
	g.run_customers = 500
	g.staff["waiter"]["count"] = 4
	g.areas["garden"]["unlocked"] = true


func _press_all(n: Node) -> void:
	for c in n.find_children("*", "BaseButton", true, false):
		var b := c as BaseButton
		if b.visible and not b.disabled and b is JuicyButton:
			b.pressed.emit()


func _bench() -> void:
	SaveManager.enabled = false
	_close_overlays()
	GameState.tutorial_done = true
	var a: InnArea = (main.get("world") as InnWorld).current()
	for i in 30:
		a.spawn_customer()
	await _wait(2.0)
	var samples: Array[float] = []
	for i in 10:
		await _wait(0.5)
		samples.append(Engine.get_frames_per_second())
	var total: float = 0.0
	var low: float = 9999.0
	for s in samples:
		total += s
		low = minf(low, s)
	print("BENCH customers=%d avg_fps=%.1f min_fps=%.1f" % [a.customers.size(), total / samples.size(), low])
	get_tree().quit()


func _autotest(seconds: float) -> void:
	# --chapter=N: chơi thử từ chương N (nạp lại cảnh một lần)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--chapter="):
			var want: int = int(arg.get_slice("=", 1)) - 1
			if GameState.chapter != want:
				GameState.chapter = want
				GameState.new_game(true)
				GameState.tutorial_done = true
				GameState.tutorial2_done = true
				GameState.world_reset.emit()
				return
	GameState.tutorial2_done = true
	GameState.tutorial_done = true
	_close_overlays()
	Engine.time_scale = 8.0
	_running_bot = true
	print("AUTOTEST bắt đầu: %s giây thực = %s giây game" % [seconds, seconds * 8.0])
	await _wait(seconds)
	_running_bot = false
	Engine.time_scale = 1.0
	_report()
	print("AUTOTEST các mốc: ", _first_events)
	get_tree().quit()


func _process(delta: float) -> void:
	if not _running_bot:
		return
	_game_t += delta
	_log_t += delta
	_bot_t += delta
	if _bot_t >= 0.5:
		_bot_t = 0.0
		_bot_step()
	if _log_t >= 60.0:
		_log_t = 0.0
		_report()


func _report() -> void:
	var g := GameState
	var opened: Array[String] = []
	for id: String in g.areas:
		if g.area_unlocked(id):
			opened.append(id)
	print("ch%d t=%4ds cấp=%d sao=%d vàng=%s khách=%d tốc_độ=%s/s món=%d bồi=%d bếp=%d khu=%s" % [
		g.chapter + 1, int(_game_t), g.level, Progress.stars(), NumberFormat.fmt(g.gold), g.total_customers, NumberFormat.fmt_dec(g.measured_rate),
		g.unlocked_dishes().size(), g.staff_count("waiter"), g.staff_count("chef"), ",".join(opened)])


func _mark(ev: String) -> void:
	if not _first_events.has(ev):
		_first_events[ev] = int(_game_t)


## Bot đơn giản: mua thứ rẻ nhất đang mua được.
func _bot_step() -> void:
	var g := GameState
	g.claim_login()
	for q: Dictionary in g.quest_data["daily"]:
		g.claim_daily(q)
	for a: Dictionary in g.quest_data["achievements"]:
		g.claim_achievement(a)
	var best_cost: float = INF
	var best: Callable = Callable()
	var best_name: String = ""
	var options: Array = []
	for ad: Dictionary in g.areas_data:
		var id: String = ad["id"]
		if not g.area_unlocked(id):
			if g.level >= int(ad["unlock_level"]):
				options.append([g.area_unlock_cost(id), g.unlock_area.bind(id), "area_" + id])
			continue
		if ad["kind"] == "dining":
			var tl: Array = g.areas[id]["tables"]
			for i in tl.size():
				if int(tl[i]) == 0 and g.table_slot_open(id, i):
					options.append([g.table_unlock_cost(id), g.unlock_table.bind(id, i), "table"])
					break
			for i in tl.size():
				if int(tl[i]) > 0:
					options.append([g.table_upgrade_cost(id, i), g.upgrade_table.bind(id, i, 1), "table_up"])
			options.append([g.kitchen_upgrade_cost(id), g.upgrade_kitchen.bind(id, 1), "kitchen"])
			for w: Dictionary in g.wings(id):
				if not g.wing_unlocked(id, str(w["id"])) and g.level >= int(w["unlock_level"]):
					options.append([g.wing_cost(id, str(w["id"])), g.unlock_wing.bind(id, str(w["id"])), "wing_" + str(w["id"])])
		else:
			var rl: Array = g.areas[id]["rooms"]
			for i in rl.size():
				if int(rl[i]) == 0:
					options.append([g.room_unlock_cost(id), g.unlock_room.bind(id, i), "room"])
					break
	for dish: String in g.unlocked_dishes():
		options.append([g.dish_upgrade_cost(dish), g.upgrade_dish.bind(dish, 1), "dish"])
	for sid in ["chef", "waiter", "cashier", "receptionist"]:
		if g.staff_unlocked(sid):
			if g.staff_count(sid) < int(g.staff_data[sid]["max_count"]):
				options.append([g.hire_cost(sid) * 0.8, g.hire.bind(sid), "hire_" + sid])
			if g.staff_count(sid) > 0:
				options.append([g.staff_upgrade_cost(sid), g.upgrade_staff.bind(sid, 1), "staff_up"])
	if not g.manager and g.staff_unlocked("manager"):
		options.append([g.manager_cost(), g.hire_manager, "manager"])
	for o: Array in options:
		if float(o[0]) < best_cost:
			best_cost = float(o[0])
			best = o[1]
			best_name = o[2]
	if best.is_valid() and g.can_afford(best_cost):
		if best.call():
			_mark(best_name)
	_mark("level_%d" % g.level)
