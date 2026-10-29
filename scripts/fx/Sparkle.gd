class_name Sparkle
extends CPUParticles2D
## Hạt lấp lánh bung ra khi nâng cấp thành công. Tự huỷ khi xong.


func _ready() -> void:
	texture = Sprites.ui("sparkle")
	amount = 24
	lifetime = 0.8
	one_shot = true
	explosiveness = 0.9
	spread = 180.0
	gravity = Vector2(0, 160)
	initial_velocity_min = 120.0
	initial_velocity_max = 280.0
	angular_velocity_min = -300.0
	angular_velocity_max = 300.0
	scale_amount_min = 0.1
	scale_amount_max = 0.26
	var grad := Gradient.new()
	grad.set_color(0, Color(1.0, 0.95, 0.5, 1.0))
	grad.set_color(1, Color(1.0, 0.8, 0.3, 0.0))
	color_ramp = grad
	emitting = true
	finished.connect(queue_free)
