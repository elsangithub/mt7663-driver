# FiberHome HG680-FJ Device Tree (DTB) Collection

Direktori ini berisi 3 varian file Device Tree Blob (`.dtb`) untuk FiberHome HG680-FJ (Amlogic S905X2 / G12A) di Armbian Ophub:

---

## ???? Perbandingan 3 Varian DTB / Comparison Table

| File | Target Kernel | MicroSD Clock | Card Detect | SDIO Wi-Fi 32kHz Clock | Status & Rekomendasi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`meson-g12a-hg680-fj-ori.dtb`** | Linux 6.x | 104 MHz (SDR104) | GPIO (`cd-gpios`) | `amlogic,meson-g12-pwm-v2` | Asli bawaan pabrik Ophub. Rentan freeze/corrupt pada kartu MicroSD tertentu. |
| **`meson-g12a-hg680-fj-fixed.dtb`** | Linux 6.x | 50 MHz | `non-removable` | `amlogic,meson-g12-pwm-v2` | Patch stabilitas MicroSD. Sangat stabil untuk booting dari kartu TF pada Kernel 6.x. |
| **`meson-g12a-hg680-fj-uni.dtb`** | **Linux 5.10 & 6.x** | 50 MHz | `non-removable` | **Universal** (`meson-g12a-ee-pwm` + `meson-g12-pwm-v2`) | **Sangat direkomendasikan!** Stabil untuk MicroSD dan mendukung Wi-Fi di Kernel 5.10 LTS maupun Kernel 6.x. |

---

## ???? Checksum SHA256

```text
8a55a85bc3676fc350cc09418d4945e516f53a172a6130a9339d556a71e8ec4a  meson-g12a-hg680-fj-ori.dtb
5689deafc728165fd9549e1880c2981fab943574037928e24815c9b42ffaec57  meson-g12a-hg680-fj-fixed.dtb
a9796296036147ea10733c14406c3701f029de3d9bd0ebbe4a4eefee2e796b3b  meson-g12a-hg680-fj-uni.dtb
```

---

## ???? Cara Pemasangan / How to Apply

Pilih salah satu file DTB yang Anda inginkan, lalu salin ke `/boot/dtb/amlogic/`:

```bash
# Contoh menggunakan DTB Universal (direkomendasikan):
sudo cp dtbfix/meson-g12a-hg680-fj-uni.dtb /boot/dtb/amlogic/

# Edit konfigurasi boot uEnv.txt:
sudo nano /boot/uEnv.txt
# Ubah baris FDT menjadi:
# FDT=/dtb/amlogic/meson-g12a-hg680-fj-uni.dtb

sudo reboot
```

