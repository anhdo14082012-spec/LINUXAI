# GROM LINUX — Build file .iso

Đóng gói toàn bộ shell + power daemon + AI runtime thành một file
`.iso` có thể boot bằng USB hoặc chạy trong VM.

## Vì sao cần WSL để build trên Windows

Build ISO Linux (rootfs, kernel, bootloader, squashfs) phải dùng công
cụ Linux: `live-build`, `debootstrap`, `xorriso`. Windows không chạy
được các công cụ này trực tiếp, nên `build-iso.bat` chỉ là **launcher**:
nó gọi WSL để chạy `build-iso.sh` thật sự bên trong môi trường Linux.

## Cách nhanh nhất: build trên GitHub Actions

Không cần WSL hay máy Linux. Đẩy repo lên GitHub, vào **Actions → Build
GROM LINUX ISO → Run workflow**. Workflow (`.github/workflows/build-iso.yml`)
build bên trong container Debian bookworm và xuất file `grom-linux.iso`
ở mục Artifacts. Đẩy tag `v*` để tự tạo Release. Hai cách bên dưới
(Windows/WSL, Linux) vẫn dùng được nếu muốn build trên máy mình.

## Yêu cầu (khi build trên máy local)

- Windows 10/11 với **WSL2** + **Ubuntu** đã cài
  (nếu chưa có: mở PowerShell quyền Admin, chạy `wsl --install -d Ubuntu`,
  khởi động lại máy, tạo user khi được hỏi lần đầu)
- Khoảng **10-15GB dung lượng trống** trong WSL (ổ `~/` của Ubuntu,
  không phải ổ C: Windows)
- Kết nối mạng ổn định (tải gói + debootstrap)

## Cách build

**Trên Windows:** double-click `build-iso.bat`, hoặc chạy từ CMD:

```cmd
build-iso.bat
```

Script sẽ tự:
1. Kiểm tra WSL có sẵn
2. Chuyển đường dẫn thư mục dự án sang path WSL
3. Gọi `sudo bash build-iso.sh` bên trong WSL

**Trên Linux (hoặc trực tiếp trong WSL):**

```bash
cd iso-build
sudo bash build-iso.sh
```

Quá trình mất khoảng **15-40 phút** tùy máy và tốc độ mạng (debootstrap
tải toàn bộ base system Debian về rồi cài thêm các gói GROM LINUX).

## Kết quả

File ISO nằm tại:

```
iso-build/output/grom-linux.iso
```

**Tài khoản demo trong bản live:** `grom` / `grom` — đổi mật khẩu ngay
nếu bạn cài lên đĩa thật hoặc chia sẻ ISO cho người khác.

## Thử ISO trong máy ảo (khuyên dùng trước khi ghi USB)

Dùng QEMU (có sẵn nếu làm theo phần trước của dự án):

```bash
qemu-system-x86_64 -cdrom iso-build/output/grom-linux.iso -m 4096 -enable-kvm
```

Hoặc mở trực tiếp bằng VirtualBox / VMware.

## Ghi ra USB để boot máy thật

**Trên Linux/WSL:**
```bash
sudo dd if=iso-build/output/grom-linux.iso of=/dev/sdX bs=4M status=progress
# /dev/sdX là USB, kiểm tra kỹ bằng `lsblk` trước khi chạy — dd ghi đè toàn bộ USB
```

**Trên Windows:** dùng [Rufus](https://rufus.ie) — chọn file `grom-linux.iso`, chọn USB, Start.

## Build lại sau khi sửa code

ISO đóng gói **bản copy** của `shell/`, `power/`, `ai/` tại thời điểm
build — sửa code xong, chạy lại `build-iso.bat`/`build-iso.sh` là đủ,
không cần sửa gì trong `iso-build/`.

## Tùy chỉnh

- **Đổi danh sách gói cài sẵn:** sửa `config/package-lists/grom.list.chroot`
  (file này được `build-iso.sh` tạo lại mỗi lần chạy — nếu muốn sửa cố định,
  sửa trực tiếp trong `build-iso.sh`)
- **Đổi tên/nhãn ISO:** sửa các tham số `--iso-application`, `--iso-volume`
  trong `build-iso.sh`
- **Thêm gói AI vào sẵn trong ISO** (thay vì cài sau khi boot): thêm bước
  gọi `ai/setup-local-ai.sh` vào hook `0100-grom-setup.hook.chroot` —
  lưu ý sẽ làm ISO nặng thêm vài GB vì chứa sẵn model.
