<p align="right">
  <a href="README.md">English</a> | <b>Bahasa Indonesia</b>
</p>

# Driver Wi-Fi MediaTek MT7663 / MT7661 SDIO untuk TV Box Amlogic (Armbian Ophub)

[![Release](https://img.shields.io/github/v/release/elsangithub/mt7663-driver?color=blue&label=release)](https://github.com/elsangithub/mt7663-driver/releases)
[![Build & Release](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml/badge.svg)](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml)
[![DKMS Ready](https://img.shields.io/badge/DKMS-Automated_Build-brightgreen.svg)](https://github.com/elsangithub/mt7663-driver)
[![License: GPL-2.0](https://img.shields.io/badge/License-GPL_2.0-blue.svg)](https://opensource.org/licenses/GPL-2.0)

Driver kernel Linux *out-of-tree* berkinerja tinggi yang telah di-*patch* khusus untuk modul **MediaTek MT7663 / MT7661** (AMPAK MT7661RSN, SDIO ID `037A:7663` / `037A:7603`) dual-band 802.11a/b/g/n/ac.

Dioptimalkan secara khusus untuk mengatasi batasan arsitektur Amlogic SoC (S905X2 / G12A, S905X3 / SM1, S905W2, dll.), dan telah diuji serta divalidasi langsung secara fisik pada perangkat **FiberHome HG680-FJ**.

> [!NOTE]
> **Lingkungan yang Telah Teruji & Tervalidasi:**
> Driver ini telah diuji dan diverifikasi secara langsung pada rilis **Armbian by Ophub** berikut:
> - **Debian 12 (Bookworm)** dengan kernel **`6.18.56-ophub`**
> - **Debian 13 (Trixie)** dengan kernel **`6.12.112-ophub`**
>
> Rilis Ophub memuat penyesuaian khusus pada Device Tree (DTB) dan subsistem clock/daya untuk TV box Amlogic.

> [!WARNING]
> **Pernyataan Kompatibilitas untuk Versi Kernel Lain:**
> Meskipun arsitektur DKMS memungkinkan kompilasi otomatis pada versi Linux lainnya, **tetap ada kemungkinan driver belum cocok 100%** dengan rilis kernel yang belum pernah kami uji (misalnya kernel *mainline vanilla*, kernel 5.x lawas, atau kernel masa depan yang mengubah struktur API jaringan internal Linux). Jika Anda menemukan kegagalan kompilasi atau masalah saat dijalankan di versi kernel lain, silakan buat laporan kendala di menu *GitHub Issues* dengan melampirkan log `uname -a` dan `dmesg`.

---

## 🔍 Kompatibilitas Hardware & Varian Chipset FiberHome HG680-FJ

Perangkat STB **FiberHome HG680-FJ** (Amlogic S905X2 / G12A) di pasaran beredar dengan **dua varian modul Wi-Fi internal** tergantung batch produksi pabrik:

| Varian Hardware | Modul Fisik | Core Chipset Internal | Driver Linux yang Digunakan |
| :--- | :--- | :--- | :--- |
| **Varian A** | MediaTek MT7668 | MediaTek MT7668 | Driver terpisah untuk MT7668 (contoh: [junglon/mt7668-driver](https://github.com/junglon/mt7668-driver)) |
| **Varian B** | AMPAK MT7661RSN | **MediaTek MT7663** (`037A:7663`) | **Driver DKMS ini (`mt7663-dkms`)** |

- **Unit MT7668**: Membutuhkan solusi driver terpisah khusus chipset MT7668 (seperti driver komunitas oleh junglon). Paket ini tidak ditujukan untuk modul MT7668.
- **Unit AMPAK MT7661RSN (MT7663)**: Membutuhkan paket DKMS ini (`mt7663-dkms`) agar hardware SDIO dapat diinisialisasi dan menyediakan konektivitas Dual-Band (2.4 GHz & 5 GHz) secara penuh.
- **Koeksistensi Bersih**: Driver ini menggunakan file konfigurasi firmware terisolasi (`/lib/firmware/wifi_mt7661.cfg`), sehingga jika Anda menggunakan satu image sistem yang sama untuk unit MT7668 dan MT7663, konfigurasi keduanya tidak akan saling bentrok.

### Cara Memeriksa Varian Chipset di STB Anda:
Jalankan perintah berikut di terminal STB:
```bash
cat /sys/bus/sdio/devices/*/device 2>/dev/null || cat /sys/bus/sdio/devices/*/vendor 2>/dev/null
```
Jika terminal menampilkan vendor `0x037a` dan device `0x7663` atau `0x7603`, maka unit Anda menggunakan modul **AMPAK MT7661RSN (MT7663)** dan memerlukan driver ini.

> [!CAUTION]
> **Kernel Lawas 5.x (5.10 / 5.15) TIDAK didukung pada FiberHome HG680-FJ!**
> Device Tree HG680-FJ (`meson-g12a-hg680-fj.dtb`) memerlukan driver `amlogic,meson-g12-pwm-v2` untuk menyuplai *reference clock* SDIO 32.768 KHz. Driver clock ini hanya tersedia di kernel Linux 6.x+. Pada Kernel 5.x, daya dan clock SDIO tetap mati sehingga modul Wi-Fi tidak dapat dideteksi oleh hardware.

---

## 🚀 Fitur Unggulan & Hasil Pengujian (FiberHome HG680-FJ)

- **Pure Standalone Wi-Fi**: 100% stabil beroperasi mandiri tanpa perlu kabel LAN terhubung (`eth0` down).
- **Dual-Band 2.4 GHz & 5 GHz**: Mendukung 802.11n 2x2 MIMO di 2.4 GHz (hingga 62+ Mbps TCP) dan 802.11ac VHT di 5 GHz (hingga 73+ Mbps TCP, latensi 3.2 ms, 0.0% packet loss).
- **Amlogic G12A SRAM Burst Protection**: Mengatasi crash `WASR_TX1_OVER_FLOW` dan SDIO FIFO stall akibat batasan hardware Amlogic buffer 1536-byte (`amlogic,dram-access-quirk`).
- **SMP Multi-Core CPU Affinity**: Kernel worker thread (`rx_thread`, `hif_thread`, `main_thread`) dialokasikan otomatis ke CPU 1, 2, dan 3 (`set_cpus_allowed_ptr`), membebaskan CPU0 dari beban pemrosesan paket jaringan.
- **Dynamic Hardware IRQ Routing**: Interupsi SDIO (`ffe03000.mmc`) diarahkan otomatis ke CPU 2 dan 3 saat registrasi perangkat via udev rule, menjaga timer sistem di CPU0 tetap responsif tanpa jitter.
- **Zero-Hang Warm Reboot**: Integrasi `mt7663-shutdown.service` memutus controller MMC sebelum sistem shutdown, menjamin deteksi hardware tetap 100% mulus saat restart (`sudo reboot`).

---

## 📦 Panduan Instalasi (Armbian Ophub)

> [!IMPORTANT]
> **JANGAN menjalankan `apt install linux-headers-$(uname -r)` di Armbian Ophub!**
> Repositori standar Debian/Ubuntu tidak menyediakan kernel custom Ophub. Di Armbian Ophub, header kernel **sudah terpasang otomatis** di direktori `/usr/src/linux-headers-$(uname -r)`.

### Langkah 1: Pasang Paket Pendukung Build & DKMS
```bash
sudo apt update
sudo apt install -y dkms build-essential wget
```

### Langkah 2: Verifikasi Keberadaan Kernel Headers
```bash
ls -d /usr/src/linux-headers-$(uname -r)
```
*(Jika direktori muncul, sistem Anda siap 100% untuk kompilasi DKMS).*

### Langkah 3: Unduh & Pasang Paket Debian (.deb)
```bash
# Unduh paket rilis resmi terbaru (v1.0.6)
wget https://github.com/elsangithub/mt7663-driver/releases/download/v1.0.6/mt7663-dkms_1.0.6_all.deb

# Pasang paket (DKMS akan otomatis mengompilasi modul untuk kernel aktif dalam ~15-20 detik)
sudo dpkg -i mt7663-dkms_1.0.6_all.deb
```

### Langkah 4: Muat Driver atau Reboot
Driver langsung aktif setelah instalasi. Untuk memastikan semua layanan tersinkronisasi sempurna:
```bash
sudo reboot
```

---

## 📶 Menghubungkan & Memverifikasi Wi-Fi

### Langkah 1: Pindai Jaringan Wi-Fi yang Tersedia:
```bash
nmcli device wifi list
```

### Langkah 2: Hubungkan ke Jaringan Wi-Fi via Terminal:
```bash
sudo nmcli dev wifi connect "NAMA_SSID_ANDA" password "PASSWORD_WIFI"
```

### Langkah 3: Periksa Status Koneksi & Kecepatan Link Fisik:
```bash
iw dev wlan0 link
```
*Contoh output (Frekuensi 5 GHz)*:
- `SSID: NAMA_SSID_ANDA`
- `freq: 5180.0` (Channel 36) atau `5785.0` (Channel 157)
- `signal: -38 dBm` hingga `-50 dBm`
- `tx bitrate: 156.0 MBit/s` (atau lebih tinggi)

### Verifikasi Distribusi IRQ Multi-Core:
```bash
grep -E "CPU|mmc" /proc/interrupts
```
*Interupsi SDIO (`ffe03000.mmc`) akan terdistribusi ke **CPU2/CPU3**, menjaga **CPU0** tetap bebas beban.*

---

## 🗑️ Cara Hapus Bersih (Clean Uninstallation)

Jika Anda ingin mencopot pemasangan driver ini dan mengembalikan sistem ke kondisi semula, paket ini dilengkapi dengan script pembersih otomatis (`prerm` dan `postrm`) yang memastikan tidak ada sisa konfigurasi yang tertinggal.

### Opsi 1: Menghapus Driver (Remove Package)
Menonaktifkan dan menghapus modul DKMS dari sistem:
```bash
sudo dpkg -r mt7663-dkms
```

### Opsi 2: Hapus Bersih Total Termasuk Seluruh Konfigurasi (Purge - Direkomendasikan)
Menghapus paket, modul DKMS terkompilasi, aturan udev tuning, konfigurasi sysctl, service shutdown, serta file konfigurasi firmware:
```bash
sudo apt purge -y mt7663-dkms
```

#### Apa yang Dibersihkan Secara Otomatis Saat Penghapusan?
1. Menghentikan interface Wi-Fi (`ip link set dev wlan0 down`).
2. Meng-*unload* module kernel dari memori RAM (`rmmod wlan_mt7663_sdio`).
3. Menghapus pendaftaran DKMS dan binari modul yang terkompilasi dari direktori `/var/lib/dkms/mt7663-dkms/`.
4. Menghapus file *auto-load* modul di `/etc/modules-load.d/wlan_mt7663_sdio.conf`.
5. Menonaktifkan dan menghapus *systemd shutdown unit* `/etc/systemd/system/mt7663-shutdown.service`.
6. Menghapus script dan aturan IRQ udev `/etc/udev/rules.d/99-wlan-performance.rules`.
7. Menghapus parameter kernel TCP buffer di `/etc/sysctl.d/99-wifi-throughput.conf`.

---

## ⚡ Patch Hardware Opsional: DTB Penstabil MicroSD (HG680-FJ)

> [!TIP]
> **Cakupan Penggunaan**: Patch ini bersifat **sepenuhnya opsional** dan berlaku untuk **SEMUA unit FiberHome HG680-FJ** (baik yang menggunakan modul Wi-Fi **MT7668** maupun **MT7663**). Patch ini sangat direkomendasikan terutama jika Anda menjalankan Armbian yang di-*boot* dari **kartu MicroSD** (`/dev/mmcblk1`).

### Mengapa Patch DTB Ini Diperlukan?
1. **Voltage Sag Akibat Transmisi Wi-Fi & False Card Removal**:
   Saat Wi-Fi bekerja dengan beban tinggi (misalnya saat speedtest atau unduhan besar), terjadi lonjakan arus cepat yang memicu penurunan tegangan tipis (*voltage sag*) pada jalur daya 3.3V bersama di board STB. DTB bawaan menggunakan saklar mekanis pendeteksi kartu (`cd-gpios = <0x2f 0x2f 0x01>`) yang membaca penurunan tegangan sesaat ini sebagai kartu dicabut (`mmc1: card aaaa removed`). Jika sistem operasi berjalan dari MicroSD, hal ini langsung memicu **Read-Only Filesystem / Kernel Panic Crash**.
2. **Error I/O Sektor 0**:
   DTB bawaan mengizinkan frekuensi hingga 200 MHz (`max-frequency = <0xbebc200>`). Jalur tembaga PCB slot MicroSD HG680-FJ yang tidak berpelindung tidak stabil pada 200 MHz, menyebabkan CRC corrupt pada kartu MicroSD SDXC modern.
3. **Ketidakcocokan Voltase I/O**:
   DTB bawaan mengarahkan jalur sinyal `vqmmc-supply` ke 1.8V (`VDDAO_1V8`), padahal slot fisik HG680-FJ terkunci permanen pada 3.3V.

### Apa yang Diubah oleh `dtbfix/meson-g12a-hg680-fj-fixed.dtb`?
- Menghapus saklar mekanis `cd-gpios` dan menggantinya dengan flag `non-removable;` (mengunci MicroSD sebagai media permanen anti-lepas seperti halnya eMMC internal; 100% kebal terhadap noise listrik dan *voltage sag* Wi-Fi).
- Mengunci `max-frequency` pada frekuensi stabil **50 MHz** (`0x2faf080` / standar High-Speed).
- Mengunci `vqmmc-supply` pada tegangan 3.3V (`VDDAO_3V3`).

### Cara Memasang DTB Fixed Ini:
File biner DTB siap pakai telah disediakan di dalam repositori pada direktori [`dtbfix/meson-g12a-hg680-fj-fixed.dtb`](dtbfix/meson-g12a-hg680-fj-fixed.dtb):

```bash
# 1. Salin file DTB fixed ke direktori boot DTB Armbian Anda
sudo cp dtbfix/meson-g12a-hg680-fj-fixed.dtb /boot/dtb/amlogic/

# 2. Buka file konfigurasi boot
sudo nano /boot/uEnv.txt
```
Cari baris `FDT=` dan arahkan ke file DTB yang baru:
```ini
FDT=/dtb/amlogic/meson-g12a-hg680-fj-fixed.dtb
```
Simpan dan keluar (`Ctrl + O`, `Enter`, `Ctrl + X`), kemudian restart STB:
```bash
sudo reboot
```

---

## 🛠️ Rangkuman Arsitektur & Perbaikan Masalah

| Komponen | Penyebab pada Driver Bawaan | Solusi di Driver Ini |
| :--- | :--- | :--- |
| **Amlogic SDIO Burst** | Host `max_req_size = 1536` karena `amlogic,dram-access-quirk`. Driver menampung 4096B sehingga memicu split CMD53 dan error `WASR_TX1_OVER_FLOW`. | Coalescing buffer dibatasi ke `host->max_req_size` (1536B) di `kalDevWriteData` (`sdio.c`) dan netdev MTU disesuaikan ke 1408. |
| **CPU0 Bottleneck** | ARM GICv2 mengarahkan semua interupsi SPI ke CPU0; kode afinitas MediaTek lama memakai API proprietary Android (`mt_sched_setaffinity`). | Diganti dengan API standar Linux kernel `set_cpus_allowed_ptr()` di `gl_kal.c` untuk mengikat `rx_thread` dan `hif_thread` ke CPU 1-3. |
| **Hardware IRQ Routing** | Race condition pada timing eksekusi systemd saat early boot. | Diintegrasikan ke script udev `/usr/lib/udev/wlan-irq-tune.sh` via `99-wlan-performance.rules` yang terpicu tepat saat MMC terdaftar. |
| **PMTU Packet Drops** | MTU asimetris (1408 lokal vs 1500 remote) memicu packet blackhole jika PMTU probing mati (`tcp_mtu_probing = 0`). | Otomatisasi `net.ipv4.tcp_mtu_probing = 1` dan `tcp_moderate_rcvbuf = 1` di `/etc/sysctl.d/99-wifi-throughput.conf` (0.0% packet loss). |
| **802.11ac Performance** | Konfigurasi default mematikan agregasi frame dan beamforming. | Mengaktifkan `AmsduInAmpduTx 1`, `VhtAmsduInAmpduTx 1`, `StaVHTBfee 1` (Beamforming), `StbcRx 1`, dan meningkatkan throughput loop (`HifTxLoop 32`, `OsTxLoop 16`). |
| **Warm Reboot Reliability** | Power rail STB selalu aktif membuat state machine chip MT7663 tidak ter-reset saat reboot, memicu timeout CMD5 (error -110). | Menambahkan `mt7663-shutdown.service` untuk unbind host MMC sebelum shutdown, memicu reset sequence hardware yang bersih. |

---

## 🔄 Pemakaian Saat Upgrade Kernel (Kernel Upgrades)

Paket ini dirancang menggunakan standar **DKMS (Dynamic Kernel Module Support)**:
- Saat Anda melakukan update atau pergantian kernel Ophub di TV box, pastikan menginstal paket `linux-headers-<versi>-ophub_*.deb` yang sesuai.
- DKMS akan secara otomatis mengompilasi ulang modul driver untuk kernel baru tersebut saat boot atau trigger paket tanpa perlu kompilasi manual.

---

## 📄 License
GPL-2.0 / MediaTek Proprietary Base.

---

## 🤝 Credits & Acknowledgments
- **MediaTek Inc.**: Arsitektur chipset orisinal dan baseline driver.
- **[junglon/mt7668-driver](https://github.com/junglon/mt7668-driver)**: Referensi berharga serta wawasan implementasi driver wireless MediaTek untuk platform Amlogic.
- **Ophub & Armbian Community**: Kernel Linux kustom dan perkakas build untuk TV box Amlogic.
- **Van der Decken**: Maintainer dan developer.
