extends Node
## StreamService: Cung cấp luồng hình ảnh 35+ FPS và nhận sự kiện cảm ứng trực tiếp qua TCP loopback

const PORT: int = 8999
const FPS_INTERVAL: float = 0.030 # ~33 FPS
const JPEG_QUALITY: float = 0.72

var _server: TCPServer
var _clients: Array[StreamPeerTCP] = []
var _timer: float = 0.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_server = TCPServer.new()
	var err := _server.listen(PORT, "127.0.0.1")
	if err == OK:
		print("[StreamService] Sẵn sàng tại 127.0.0.1:", PORT)
	else:
		push_warning("[StreamService] Không thể mở cổng: " + str(err))

func _process(delta: float) -> void:
	if not _server or not _server.is_listening():
		return
		
	# Chấp nhận kết nối mới
	while _server.is_connection_available():
		var peer := _server.take_connection()
		if peer:
			peer.set_no_delay(true)
			peer.big_endian = false
			_clients.append(peer)
			print("[StreamService] Phone streamer đã kết nối!")

	# Dọn dẹp client ngắt kết nối và đọc input
	var active_clients: Array[StreamPeerTCP] = []
	for client in _clients:
		client.poll()
		var status := client.get_status()
		if status == StreamPeerTCP.STATUS_CONNECTED:
			active_clients.append(client)
			_read_inputs(client)
		elif status == StreamPeerTCP.STATUS_ERROR:
			pass
	_clients = active_clients

	# Gửi khung hình mới
	if _clients.is_empty():
		return

	_timer += delta
	if _timer >= FPS_INTERVAL:
		_timer = 0.0
		_broadcast_frame()

func _read_inputs(peer: StreamPeerTCP) -> void:
	# Format gói tin touch từ Python:
	# [type: uint8 (1=down, 2=up, 3=move)] [x: float32] [y: float32] -> 9 bytes
	while peer.get_available_bytes() >= 9:
		var event_type := peer.get_u8()
		var x := peer.get_float()
		var y := peer.get_float()
		
		var vp := get_viewport()
		if not vp:
			continue
			
		var v_size := vp.get_visible_rect().size
		var v_pos := Vector2(x * v_size.x, y * v_size.y)
		
		var win := get_window()
		var win_size: Vector2 = Vector2(win.size) if win else Vector2(450, 800)
		var win_pos := Vector2(x * win_size.x, y * win_size.y)
		
		if event_type == 1: # DOWN
			var mev := InputEventMouseButton.new()
			mev.button_index = MOUSE_BUTTON_LEFT
			mev.pressed = true
			mev.position = win_pos
			mev.global_position = win_pos
			Input.parse_input_event(mev)
			
			var tev := InputEventScreenTouch.new()
			tev.index = 0
			tev.pressed = true
			tev.position = win_pos
			Input.parse_input_event(tev)
		elif event_type == 2: # UP
			var mev := InputEventMouseButton.new()
			mev.button_index = MOUSE_BUTTON_LEFT
			mev.pressed = false
			mev.position = win_pos
			mev.global_position = win_pos
			Input.parse_input_event(mev)
			
			var tev := InputEventScreenTouch.new()
			tev.index = 0
			tev.pressed = false
			tev.position = win_pos
			Input.parse_input_event(tev)
		elif event_type == 3: # MOVE
			var mev := InputEventMouseMotion.new()
			mev.button_mask = MOUSE_BUTTON_MASK_LEFT
			mev.position = win_pos
			mev.global_position = win_pos
			Input.parse_input_event(mev)
			
			var dev := InputEventScreenDrag.new()
			dev.index = 0
			dev.position = v_pos
			vp.push_input(dev)

func _broadcast_frame() -> void:
	var vp := get_viewport()
	if not vp:
		return
	var tex := vp.get_texture()
	if not tex:
		return
	var img := tex.get_image()
	if not img or img.is_empty():
		return
		
	var buf := img.save_jpg_to_buffer(JPEG_QUALITY)
	var sz := buf.size()
	if sz == 0:
		return
		
	for client in _clients:
		client.put_u32(sz)
		client.put_data(buf)
