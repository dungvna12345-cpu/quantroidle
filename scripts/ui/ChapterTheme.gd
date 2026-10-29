class_name ChapterTheme
extends RefCounted
## Bảng màu giao diện theo chương (data/chapters.json -> "ui"): tiêu đề popup, khung nổi bật,
## banner trạng thái, chữ tiêu đề mục. Sửa trực tiếp theme của project nên mọi control cập nhật ngay.

# Màu gốc của theme (Phố Cổ) dùng khi chương không khai báo "ui".
const DEFAULT := {
	"header": "#f08a76", "header_dark": "#c95f4c", "accent": "#d06a52",
	"soft": "#fff1b8", "soft_border": "#f2a541", "banner": "#6f9d6c", "banner_dark": "#4e774c",
}


static func palette(chapter_index: int = -1) -> Dictionary:
	var out: Dictionary = DEFAULT.duplicate()
	var ui: Variant = GameState.chapter_info(chapter_index).get("ui", {})
	if ui is Dictionary:
		for k: String in ui:
			out[k] = ui[k]
	return out


static func color(key: String, chapter_index: int = -1) -> Color:
	return Color(str(palette(chapter_index).get(key, DEFAULT.get(key, "#ffffff"))))


## Màu nhấn của chương hiện tại (tiêu đề mục, chữ nổi bật).
static func accent() -> Color:
	return color("accent")


## Áp bảng màu của chương hiện tại lên theme project.
static func apply() -> void:
	var th := ThemeDB.get_project_theme()
	if th == null:
		return
	var p := palette()
	_tint(th, "PopupHeader", Color(str(p["header"])), Color(str(p["header_dark"])))
	_tint(th, "Highlight", Color(str(p["soft"])), Color(str(p["soft_border"])))
	_tint(th, "StatusBanner", Color(str(p["banner"])), Color(str(p["banner_dark"])))
	th.set_color("font_color", "HeaderLabel", Color(str(p["accent"])))


static func _tint(th: Theme, type_name: String, bg: Color, border: Color) -> void:
	var sb := th.get_stylebox("panel", type_name) as StyleBoxFlat
	if sb == null:
		return
	sb.bg_color = bg
	sb.border_color = border
