class_name Juice
extends RefCounted
## Các hiệu ứng "nảy", "rung" dùng chung.


## Nảy: 0.92 -> 1.05 -> 1 (nút bấm, ô giá trị).
static func bounce(node: CanvasItem, strength: float = 1.0) -> void:
	if node == null or not node.is_inside_tree():
		return
	if node is Control:
		var c := node as Control
		c.pivot_offset = c.size * 0.5
	var t := node.create_tween()
	t.tween_property(node, "scale", Vector2.ONE * (1.0 - 0.08 * strength), 0.06)
	t.tween_property(node, "scale", Vector2.ONE * (1.0 + 0.05 * strength), 0.09)
	t.tween_property(node, "scale", Vector2.ONE, 0.08)


## Phóng to rồi về, dùng cho Node2D có scale gốc khác 1.
static func pop(node: Node2D, base: Vector2, amount: float = 0.15) -> void:
	if node == null or not node.is_inside_tree():
		return
	var t := node.create_tween()
	t.tween_property(node, "scale", base * (1.0 + amount), 0.08)
	t.tween_property(node, "scale", base, 0.14).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## Rung nhẹ vị trí (khi mua thành công).
static func shake(node: CanvasItem, power: float = 6.0, time: float = 0.25) -> void:
	if node == null or not node.is_inside_tree():
		return
	var prop := "position"
	var origin: Vector2 = node.get(prop)
	var t := node.create_tween()
	var steps: int = 6
	for i in steps:
		var k: float = 1.0 - float(i) / steps
		var off := Vector2(randf_range(-1, 1), randf_range(-1, 1)) * power * k
		t.tween_property(node, prop, origin + off, time / steps)
	t.tween_property(node, prop, origin, time / steps)
