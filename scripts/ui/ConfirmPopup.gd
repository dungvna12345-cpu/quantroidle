extends PopupBase
## Hộp thoại xác nhận Có / Không.

signal answered(yes: bool)

var message: String = ""
var yes_text: String = "Đồng ý"
var no_text: String = "Hủy"
var yes_variation: String = "GreenButton"


func _build(b: VBoxContainer) -> void:
	b.add_child(centered_label(message, "", 26))
	var row := UIKit.hbox(16)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	b.add_child(row)
	var no := UIKit.button(no_text, "", "", 200)
	no.pressed.connect(_answer.bind(false))
	row.add_child(no)
	var yes := UIKit.button(yes_text, yes_variation, "", 220)
	yes.pressed.connect(_answer.bind(true))
	row.add_child(yes)


func _answer(yes: bool) -> void:
	answered.emit(yes)
	close()
