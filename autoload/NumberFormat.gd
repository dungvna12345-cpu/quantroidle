extends Node
## Định dạng số lớn (1.2K, 3.4M, 5.6B, 7.8T, rồi aa, ab...) và thời gian tiếng Việt.

const SUFFIX: Array[String] = ["", "K", "M", "B", "T"]


func fmt(n: float) -> String:
	if is_nan(n) or is_inf(n):
		return "∞"
	if n < 0.0:
		return "-" + fmt(-n)
	if n < 1000.0:
		return str(int(floor(n)))
	var tier: int = int(floor(log(n) / log(1000.0)))
	var scaled: float = n / pow(1000.0, tier)
	# hiển thị dùng floor nên không bao giờ làm tròn lên; chỉ cần sửa sai số log() ở đúng mốc 1000^k
	if scaled >= 1000.0:
		scaled /= 1000.0
		tier += 1
	var text: String
	if scaled >= 100.0:
		text = str(int(floor(scaled)))
	else:
		text = ("%.1f" % (floor(scaled * 10.0) / 10.0)).trim_suffix(".0")
	return text + _suffix(tier)


func _suffix(tier: int) -> String:
	if tier < SUFFIX.size():
		return SUFFIX[tier]
	# sau T là aa, ab, ... az, ba, ...
	var k: int = tier - SUFFIX.size()
	var first: int = floori(k / 26.0) % 26
	var second: int = k % 26
	return char(97 + first) + char(97 + second)


## Số có phần thập phân cho giá trị nhỏ (vd. tốc độ 1.25).
func fmt_dec(n: float) -> String:
	if n < 100.0:
		return ("%.1f" % n).trim_suffix(".0")
	return fmt(n)


## "2 giờ 5 phút", "3 phút 20 giây", "45 giây".
func fmt_time(seconds: float) -> String:
	var s: int = int(max(0.0, seconds))
	var h: int = floori(s / 3600.0)
	var m: int = floori((s % 3600) / 60.0)
	var sec: int = s % 60
	if h > 0:
		return "%d giờ %d phút" % [h, m]
	if m > 0:
		return "%d phút %d giây" % [m, sec]
	return "%d giây" % sec


## Đồng hồ đếm ngược dạng 01:23:45 / 12:05.
func fmt_clock(seconds: float) -> String:
	var s: int = int(max(0.0, seconds))
	var h: int = floori(s / 3600.0)
	var m: int = floori((s % 3600) / 60.0)
	var sec: int = s % 60
	if h > 0:
		return "%02d:%02d:%02d" % [h, m, sec]
	return "%02d:%02d" % [m, sec]
