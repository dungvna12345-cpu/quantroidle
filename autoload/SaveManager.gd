extends Node
## Lưu / tải game dạng JSON. Có bản dự phòng khi file chính bị hỏng.

const SAVE_PATH := "user://save.json"
const BACKUP_PATH := "user://save_backup.json"

var _timer: float = 0.0
var loaded_from: String = ""   # "save", "backup" hoặc "" (game mới)
var enabled: bool = true       # tắt khi chạy công cụ kiểm thử để không ghi đè file lưu thật


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots") or a.begins_with("--bench") or a.begins_with("--autotest") 				or a.begins_with("--flows") or a.begins_with("--prestige") or a.begins_with("--chapters") or a.begins_with("--story"):
			enabled = false
	if enabled:
		load_game()


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= GameState.bal("autosave_seconds", 10):
		_timer = 0.0
		save_game()


func _notification(what: int) -> void:
	# lưu khi thoát, khi app chạy nền hoặc mất focus
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_APPLICATION_PAUSED \
			or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		save_game()


func save_game() -> void:
	if not enabled:
		return
	var data: Dictionary = GameState.to_dict()
	data["saved_at"] = Time.get_unix_time_from_system()
	data["progress"] = Progress.to_dict()
	data["story"] = Story.to_dict()
	var text := JSON.stringify(data, "\t")
	# bản lưu cũ còn đọc được thì chép sang file dự phòng trước khi ghi đè
	if FileAccess.file_exists(SAVE_PATH):
		var old := FileAccess.get_file_as_string(SAVE_PATH)
		if _parse(old) != null:
			_write(BACKUP_PATH, old)
	_write(SAVE_PATH, text)


func _write(path: String, text: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_warning("Không ghi được " + path)
		return
	f.store_string(text)
	f.close()


func _parse(text: String) -> Variant:
	if text.is_empty():
		return null
	var json := JSON.new()
	if json.parse(text) != OK:
		return null
	var d: Variant = json.data
	if d is Dictionary and (d as Dictionary).has("version"):
		return d
	return null


func _read(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	return _parse(FileAccess.get_file_as_string(path))


func load_game() -> void:
	var d: Variant = _read(SAVE_PATH)
	loaded_from = "save"
	if d == null:
		d = _read(BACKUP_PATH)
		loaded_from = "backup"
		if d != null:
			push_warning("File lưu hỏng, dùng bản dự phòng")
	if d == null:
		loaded_from = ""
		GameState.new_game()
		return
	var data: Dictionary = d
	GameState.from_dict(data)
	var pr: Variant = data.get("progress", {})
	if pr is Dictionary:
		Progress.from_dict(pr)
	var sd: Variant = data.get("story", {})
	if sd is Dictionary:
		Story.from_dict(sd)
	# tính thu nhập offline (chờ người chơi bấm Nhận trong popup)
	var now := Time.get_unix_time_from_system()
	var away: float = maxf(0.0, now - float(data.get("saved_at", now)))
	# đồng hồ bị chỉnh lùi so với lần chơi trước -> không tính offline
	if now + 300.0 < GameState.max_time_seen:
		away = 0.0
	GameState.max_time_seen = maxf(GameState.max_time_seen, now)
	if away >= GameState.bal("offline_min_seconds", 30):
		var earned := GameState.compute_offline(away)
		if earned > 0.0:
			GameState.pending_offline += earned
			GameState.pending_offline_seconds += away


## Xóa toàn bộ dữ liệu (đã hỏi xác nhận 2 lần ở popup Cài đặt).
func delete_all() -> void:
	for p in [SAVE_PATH, BACKUP_PATH]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(p))
	Progress.reset()
	Story.reset()
	GameState.reset_everything()
	save_game()
