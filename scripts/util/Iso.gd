class_name Iso
extends RefCounted
## Phép chiếu isometric 2:1. Một ô = 128 x 64 đơn vị thế giới.

const HALF_W := 64.0
const HALF_H := 32.0


static func to_world(g: Vector2) -> Vector2:
	return Vector2((g.x - g.y) * HALF_W, (g.x + g.y) * HALF_H)


static func to_grid(p: Vector2) -> Vector2:
	var a: float = p.x / HALF_W
	var b: float = p.y / HALF_H
	return Vector2((a + b) * 0.5, (b - a) * 0.5)
