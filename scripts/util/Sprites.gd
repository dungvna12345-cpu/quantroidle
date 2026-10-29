class_name Sprites
extends RefCounted
## Tạo Sprite2D từ ảnh SVG trong assets/sprites, đặt điểm neo theo manifest.json.
## Ảnh vẽ ở 2x nên mặc định scale 0.5.

const DIR := "res://assets/sprites/"
const UI_DIR := "res://assets/ui/"
const SCALE := 0.5

static var _manifest: Dictionary = {}
static var _cache: Dictionary = {}


static func _ensure_manifest() -> void:
	if not _manifest.is_empty():
		return
	var f := FileAccess.open(DIR + "manifest.json", FileAccess.READ)
	if f == null:
		push_error("Thiếu assets/sprites/manifest.json")
		return
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if parsed is Dictionary:
		_manifest = parsed


static func tex(id: String) -> Texture2D:
	if _cache.has(id):
		return _cache[id]
	var path := DIR + id + ".svg"
	if not ResourceLoader.exists(path):
		path = UI_DIR + id + ".svg"
	if not ResourceLoader.exists(path):
		if id.begins_with("dish_"):
			path = DIR + "dish_pho.svg"
		elif id.begins_with("badge_"):
			path = UI_DIR + "badge_regular.svg"
		else:
			path = UI_DIR + "coin.svg"
	var t: Texture2D = load(path) as Texture2D
	_cache[id] = t
	return t


static func ui(id: String) -> Texture2D:
	var key := "ui:" + id
	if _cache.has(key):
		return _cache[key]
	var path := UI_DIR + id + ".svg"
	if not ResourceLoader.exists(path):
		path = DIR + id + ".svg"
	if not ResourceLoader.exists(path):
		if id.begins_with("dish_"):
			path = DIR + "dish_pho.svg"
		elif id.begins_with("badge_"):
			path = UI_DIR + "badge_regular.svg"
		else:
			path = UI_DIR + "coin.svg"
	var t: Texture2D = load(path) as Texture2D
	_cache[key] = t
	return t


static func clear_cache() -> void:
	_cache.clear()


static func anchor(id: String) -> Vector2:
	_ensure_manifest()
	var m: Array = _manifest.get(id, [])
	if m.size() >= 4:
		return Vector2(float(m[2]), float(m[3]))
	return Vector2.ZERO


static func make(id: String) -> Sprite2D:
	var s := Sprite2D.new()
	apply(s, id)
	return s


## Gán ảnh cho sprite có sẵn, giữ hướng lật (scale.x âm).
static func apply(s: Sprite2D, id: String) -> void:
	s.texture = tex(id)
	s.centered = false
	s.offset = -anchor(id)
	var flip: float = -1.0 if s.scale.x < 0.0 else 1.0
	s.scale = Vector2(SCALE * flip, SCALE)
