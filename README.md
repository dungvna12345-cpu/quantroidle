# Quán Trọ Idle

Game idle quản lý quán trọ cho điện thoại, làm bằng **Godot 4.7** (GDScript, renderer Compatibility),
màn hình dọc 720x1280. Game chơi offline hoàn toàn: không quảng cáo, không cần mạng.

## Chạy game
1. Giải nén `QuanTroIdle.zip`.
2. Mở Godot 4.7, chọn **Import**, trỏ tới file `project.godot`.
3. Lần đầu mở, Godot cần vài giây để import ảnh và âm thanh. Xong thì nhấn **F5**.

Trên máy tính: kéo chuột để di chuyển camera, lăn chuột để phóng to/thu nhỏ, click để chạm.
Trên điện thoại: kéo một ngón để di chuyển, chụm hai ngón để phóng to/thu nhỏ.

## Lối chơi
- Khách đi trên đường vào và xếp hàng ngoài cổng. Bồi bàn ra đón và dẫn khách tới bàn.
  Khách gọi món, đầu bếp nấu (có thanh tiến độ trên bếp), bồi bàn mang món ra.
  Khách ăn xong thì ra quầy thu ngân trả tiền rồi đi về.
- Chạm vào khách để phục vụ nhanh hơn. Chạm vào đồng tiền boa trên bàn để nhặt.
- Chạm vào bàn, bếp, quầy hoặc giường để mở popup nâng cấp riêng (có nút Nâng x10).
  Chạm vào ô có ổ khóa để mở thêm bàn hoặc phòng.
- Có 5 tab:
  - **Quán**: cảnh chính, chuyển khu, bản đồ nhỏ, cửa hàng.
  - **Nhân viên**: Đầu bếp, Bồi bàn, Thu ngân, Lễ tân, Quản lý, giờ offline.
  - **Thực đơn**: 10 món ăn Việt.
  - **Mở rộng**: 4 khu, trang trí, tái khởi nghiệp.
  - **Nhiệm vụ**: quà đăng nhập 7 ngày, nhiệm vụ hằng ngày, thành tích.
- Thu nhập offline tính theo tốc độ thu nhập đo thực tế. Mặc định tối đa 2 giờ, nâng được lên 12 giờ.
  Chưa có Quản lý thì nhận 40%, có Quản lý thì nhận 100%.
- **5 chương**: Phố Cổ Hà Nội (x1), Hội An (x4), Sài Gòn (x16), Đà Lạt (x64), Cố Đô Huế (x256).
- **Mỗi chương có đặc trưng riêng** (khai báo ở `data/chapters.json` -> `feature`):
  - Hà Nội, *Phở sáng*: buổi sáng khách gọi đặc sản nhiều hơn, đặc sản bán x2.
  - Hội An, *Đêm hội đèn lồng*: buổi tối giá món +40%, khách đến nhanh hơn.
  - Sài Gòn, *Shipper giao đồ ăn*: shipper ghé cổng, chạm trước khi đi để nhận tiền giao hàng.
  - Đà Lạt, *Sương lạnh*: định kỳ 60 giây món nóng x2, khách kiên nhẫn hơn.
  - Huế, *Ngự yến*: luôn có một đơn tiệc Ngự yến thưởng x4 vàng và thêm kim cương.
- **Giao diện theo chương**: màu tiêu đề popup, khung nổi bật, banner trạng thái đổi theo bảng màu thành phố (`ui`),
  cảnh quán có không khí riêng (`ambience`): lá vàng, đèn lồng, neon, sương, mai vàng.
- **Bản đồ hành trình** ở tab Mở rộng: chạm từng chặng để xem chi tiết. Sang chương mới có màn tổng kết chương cũ.
- **Mục tiêu chương**: mỗi chương có 6 mục tiêu (nút sổ ở thanh trên, hoặc dãy sao dưới tên khu).
  Cứ 2 mục tiêu được 1 sao, mỗi sao mở một rương. Đủ 3 sao thì vào tab Mở rộng, chọn "Lên đường" để sang chương mới.
- **Cây nghiên cứu** (bình tím ở cột phải): dùng Sách nghiên cứu mở 9 nâng cấp vĩnh viễn, chia 3 tầng.
- **Bộ sưu tập đầu bếp** (bộ thẻ ở cột trái): 12 thẻ Thường / Hiếm / Huyền thoại.
  Rút bằng kim cương, trùng thẻ thì thẻ lên cấp.
- **Vòng quay may mắn** (cột trái): mỗi ngày quay miễn phí 1 lần.
  Trúng vàng, kim cương, Sách nghiên cứu, thẻ, x2 thu nhập, rương vàng.
  Quán mới bắt đầu lại từ đầu nhưng giữ kim cương, Danh tiếng và thành tích.
- **24 món Việt.** Mỗi ngày có một **món đặc biệt** bán giá x2.
  Mỗi chương có thêm **món đặc sản** bán giá x1.5: Phở, Bánh mì, Cơm tấm, Lẩu, Bún bò Huế.
- Mỗi chương có **đồ trang trí riêng** và **nhạc nền riêng**.
  Giá nâng cấp tăng theo chương (thấp hơn mức tăng thu nhập), nên chương nào cũng có thứ để phấn đấu.
- **Khách đặc biệt** có huy hiệu trên đầu:
  - khó tính: ít kiên nhẫn, hay để lại tiền boa và boa gấp 3;
  - du lịch: trả x2;
  - khách quen: trả x1.3, cho thêm EXP.
- **Cài đặt**: đổi tên quán, chọn avatar.
- **Hướng dẫn 2 phần**: cơ bản, và các tính năng nâng cao (tự hiện sau phần cơ bản).
- **Chống chỉnh lùi giờ máy**: không tính offline, và khóa quà theo ngày, nếu đồng hồ bị lùi.
- **Tự kiểm tra dữ liệu**: khi mở game, nếu file `data/*.json` lỗi hoặc thiếu ảnh thì game hiện thông báo.
  File lưu được tự nâng lên phiên bản mới.
- **Sự kiện ngẫu nhiên**: Giờ cao điểm, Lễ hội ẩm thực (giá x2), Khách sộp (trả x10), Mưa tiền boa.
- **Đơn đặt tiệc**: phục vụ đủ số phần một món để nhận thưởng lớn.
- Ở chương cuối (Huế), đạt cấp 20 có thể "Mở chuỗi quán mới": chơi lại Huế và nhận thêm Danh tiếng.
  Mỗi điểm Danh tiếng cộng 10% thu nhập vĩnh viễn.

## Cấu trúc
```
autoload/   GameState (tiền, cấp, công thức, signal), SaveManager, AudioManager, NumberFormat
data/       số liệu cân bằng: balance, dishes, staff, areas, decor, quests, shop (JSON)
scenes/     Splash, Main, tabs/, inn/, ui/, fx/   (mỗi đối tượng là một scene có script riêng)
scripts/    mã nguồn tương ứng với scenes/
theme/      main_theme.tres (font Baloo 2, tông kem/nâu, nút tròn, thanh đếm, cột menu)
assets/     sprites/ (SVG + manifest.json chứa điểm neo), ui/, fonts/, audio/
tools/      script Python sinh sprite, theme và âm thanh (Godot bỏ qua thư mục này)
```
- Mọi con số cân bằng nằm trong `data/`. Muốn chỉnh độ khó thì sửa JSON, không cần đụng code.
- Nhân vật và đồ vật đặt trong `Node2D` có `y_sort_enabled`, nhờ vậy che khuất đúng theo chiều sâu.
- Đường đi trong quán dùng waypoint: lưới lối đi cộng với `AStar2D`.
- Giao diện chỉ đọc trạng thái và lắng nghe signal của `GameState`.
- File lưu `user://save.json` có trường `version`. Mỗi lần lưu, bản cũ được chép sang `save_backup.json`.
  Game tự lưu mỗi 10 giây, khi thoát và khi app chạy nền.

## Sinh lại tài nguyên (không bắt buộc)
```
python tools/gen_sprites.py   # sprite SVG + manifest.json + icon.svg
python tools/gen_theme.py     # theme/main_theme.tres
python tools/gen_audio.py     # nhạc + hiệu ứng WAV
```

## Công cụ kiểm thử (tham số đặt sau `--`)
Các chế độ này không ghi đè file lưu thật.
```
godot --path . -- --shots=<thư mục>          # chụp màn hình các tab
godot --path . -- --bench                    # đo FPS với 30 khách cùng lúc
godot --headless --path . -- --autotest=76   # bot tự chơi 10 phút game ở tốc độ x8
godot --headless --path . -- --flows         # bấm qua mọi popup, khu và nút
```

## Xuất file APK Android
1. **Export Template**: trong Godot chọn *Editor → Manage Export Templates → Download and Install*
   (bản 4.7).
2. **JDK 17**: cài OpenJDK 17, ví dụ bản Adoptium Temurin.
3. **Android SDK**: cài Android Studio, hoặc chỉ cài command-line tools rồi chạy lệnh sau:
   ```
   sdkmanager "platform-tools" "build-tools;35.0.0" "platforms;android-35" "cmdline-tools;latest"
   ```
4. Vào *Editor → Editor Settings → Export → Android* và điền:
   - **Java SDK Path**: thư mục JDK 17.
   - **Android SDK Path**: thư mục SDK.
5. **Keystore debug**: Godot 4 thường tự tạo `debug.keystore` khi bạn chọn đường dẫn SDK.
   Nếu không có, tạo bằng lệnh:
   ```
   keytool -keyalg RSA -genkeypair -alias androiddebugkey -keypass android -keystore debug.keystore \
     -storepass android -dname "CN=Android Debug,O=Android,C=US" -validity 9999 -deststoretype pkcs12
   ```
   Sau đó điền vào *Editor Settings → Export → Android → Debug Keystore*
   (user `androiddebugkey`, mật khẩu `android`).
6. Vào *Project → Export…*. Preset **Android** đã có sẵn trong `export_presets.cfg`:
   - arm64 + armv7
   - quyền rung
   - gói `vn.quantro.idle`
   
   Bấm **Export Project**, bỏ chọn *Export With Debug* nếu muốn bản release, rồi lưu thành `QuanTroIdle.apk`.
7. Bản phát hành chính thức: tạo keystore release riêng và điền vào mục *Keystore → Release* của preset.

## Hạn chế đã biết
- Không có hiệu ứng rung trên máy tính, vì đây là tính năng chỉ có trên điện thoại.
- Độ cân bằng được kiểm tra bằng bot tự chơi trong 10 phút đầu. Giai đoạn cuối game (VIP, Tầng trọ,
  tái khởi nghiệp) mới được chạy thử bằng test tự động, chưa có người chơi thật thử lâu dài.
