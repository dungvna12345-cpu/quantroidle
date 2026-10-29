extends Node
## Nhạc nền lặp vô tận + hiệu ứng âm thanh (có pool để phát chồng nhau) + rung.

const AUDIO_DIR := "res://assets/audio/"
const SFX_NAMES: Array[String] = ["coin", "click", "purchase", "levelup", "whoosh", "pop",
	"sizzle", "chest_open", "card_flip", "legendary", "spin_tick"]
const POOL_SIZE := 8

var _music: AudioStreamPlayer
var _pool: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _last_play: Dictionary = {}
var _next: int = 0
var _headless: bool = false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_headless = DisplayServer.get_name() == "headless"
	for n in SFX_NAMES:
		if not ResourceLoader.exists(AUDIO_DIR + n + ".wav"):
			continue
		var s: AudioStream = load(AUDIO_DIR + n + ".wav")
		if s:
			_streams[n] = s
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.volume_db = -4.0
		add_child(p)
		_pool.append(p)
	_music = AudioStreamPlayer.new()
	_music.stream = load(AUDIO_DIR + "music_loop.wav")
	_music.volume_db = -9.0
	# phát lại khi hết bài -> lặp vô tận
	_music.finished.connect(_on_music_finished)
	add_child(_music)
	GameState.settings_changed.connect(_apply_settings)
	_apply_settings()
	# tự xử lý thoát: dừng âm thanh vài khung hình trước khi tắt để không rò rỉ tài nguyên
	get_tree().auto_accept_quit = false


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_shutdown()


func _shutdown() -> void:
	_stop_all()
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	get_tree().quit()


func _stop_all() -> void:
	_music.stop()
	_music.stream = null
	for p in _pool:
		p.stop()
		p.stream = null


func _exit_tree() -> void:
	_stop_all()
	_streams.clear()
	Sprites.clear_cache()


## Đổi nhạc nền theo chương (music_<id>.wav), không có thì dùng nhạc mặc định.
func set_chapter_music(chapter_id: String) -> void:
	var path := AUDIO_DIR + "music_" + chapter_id + ".wav"
	if not ResourceLoader.exists(path):
		path = AUDIO_DIR + "music_loop.wav"
	var s: AudioStream = load(path)
	if _music.stream == s:
		return
	var was_playing := _music.playing
	_music.stop()
	_music.stream = s
	if was_playing or (GameState.settings.get("music", true) and not _headless):
		_music.play()


func _on_music_finished() -> void:
	if GameState.settings.get("music", true):
		_music.play()


func _apply_settings() -> void:
	# chạy headless (kiểm thử tự động) thì không phát nhạc
	if _headless:
		return
	var on: bool = GameState.settings.get("music", true)
	if on and not _music.playing:
		_music.play()
	elif not on and _music.playing:
		_music.stop()


## Phát hiệu ứng. min_gap: chống phát dồn dập (vd. tiếng xu).
func play(sfx_name: String, pitch_jitter: float = 0.0, min_gap: float = 0.05) -> void:
	if _headless or not GameState.settings.get("sfx", true) or not _streams.has(sfx_name):
		return
	var now: float = Time.get_ticks_msec() / 1000.0
	if now - float(_last_play.get(sfx_name, -10.0)) < min_gap:
		return
	_last_play[sfx_name] = now
	var p: AudioStreamPlayer = _pool[_next]
	_next = (_next + 1) % POOL_SIZE
	p.stream = _streams[sfx_name]
	p.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	p.play()


## Phát hiệu ứng với cao độ cho trước (combo càng cao tiếng càng cao).
func play_pitch(sfx_name: String, pitch: float) -> void:
	if _headless or not GameState.settings.get("sfx", true) or not _streams.has(sfx_name):
		return
	var p: AudioStreamPlayer = _pool[_next]
	_next = (_next + 1) % POOL_SIZE
	p.stream = _streams[sfx_name]
	p.pitch_scale = pitch
	p.play()


func vibrate(ms: int = 35) -> void:
	if GameState.settings.get("vibrate", true):
		Input.vibrate_handheld(ms)
