extends SceneTree

func _init():
    var main_scene = load('res://scenes/Main.tscn')
    var main = main_scene.instantiate()
    root.add_child(main)
    # process a few frames
    for i in range(5):
        await process_frame
    var img = root.get_texture().get_image()
    if img:
        print('Image captured! Size: ', img.get_size(), ' format: ', img.get_format())
        var buf = img.save_jpg_to_buffer(0.8)
        print('Buffer length: ', buf.size())
        var f = FileAccess.open('tools/godot_internal_frame.jpg', FileAccess.WRITE)
        f.store_buffer(buf)
        f.close()
    else:
        print('Image is null')
    quit()
