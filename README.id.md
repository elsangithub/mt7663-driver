<p align="right">
  <a href="README.md">English</a> | <b>Bahasa Indonesia</b>
</p>

# Driver Wi-Fi MediaTek MT7663 / MT7661 SDIO untuk TV Box Amlogic (Armbian Ophub)

[![Release](https://img.shields.io/github/v/release/elsangithub/mt7663-driver?color=blue&label=release)](https://github.com/elsangithub/mt7663-driver/releases)
[![Build & Release](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml/badge.svg)](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml)
[![DKMS Ready](https://img.shields.io/badge/DKMS-Automated_Build-brightgreen.svg)](https://github.com/elsangithub/mt7663-driver)
[![License: GPL-2.0](https://img.shields.io/badge/License-GPL_2.0-blue.svg)](https://opensource.org/licenses/GPL-2.0)

Driver kernel Linux *out-of-tree* berkinerja tinggi yang telah di-*patch* khusus untuk modul **MediaTek MT7663 / MT7661** (AMPAK MT7661RSN, SDIO ID `037A:7663` / `037A:7603`) dual-band 802.11a/b/g/n/ac.

Dioptimalkan secara khusus untuk mengatasi batasan arsitektur pengontrol SDIO Amlogic G12A (S905X2), dan telah diuji serta divalidasi langsung secara fisik pada perangkat **FiberHome HG680-FJ**.

> [!NOTE]
> **Lingkungan yang Telah Teruji & Tervalidasi:**
> Driver ini telah diuji dan diverifikasi secara langsung pada rilis **Armbian by Ophub** berikut:
> - **Debian 12 (Bookworm)** dengan kernel **`6.18.56-ophub`**
> - **Debian 13 (Trixie)** dengan kernel **`6.12.112-ophub`**
> - **Debian 12 (Bookworm)** dengan kernel **`5.10.272-ophub`** *(dengan DTB Universal `dtbfix/meson-g12a-hg680-fj-uni.dtb`)*
>
> Rilis Ophub memuat penyesuaian khusus pada Device Tree (DTB) dan subsistem clock/daya untuk TV box Amlogic.

> [!WARNING]
> **Pernyataan Kompatibilitas untuk Versi Kernel Lain:**
> Meskipun arsitektur DKMS memungkinkan kompilasi otomatis pada versi Linux lainnya, **tetap ada kemungkinan driver belum cocok 100%** dengan rilis kernel yang belum pernah kami uji (misalnya kernel *mainline vanilla*, kernel non-LTS, atau rilis kernel masa depan yang mengubah struktur API jaringan internal Linux). Jika Anda menemukan kegagalan kompilasi atau masalah saat dijalankan di versi kernel lain, silakan buat laporan kendala di menu *GitHub Issues* dengan melampirkan log `uname -a` dan `dmesg`.

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

> [!NOTE]
> **Dukungan Kernel: Linux 6.x & Linux 5.10 (dengan Patch DTB Universal)**
> - **Linux 6.x+ (Direkomendasikan, contoh: 6.6 / 6.12 / 6.18)**: Didukung langsung secara *out-of-the-box* dengan DTB bawaan Ophub.
> - **Linux 5.10 LTS (contoh: 5.10.272-ophub)**: Didukung penuh! Pada DTB bawaan Ophub, *reference clock* 32.768 KHz belum memiliki binding `amlogic,meson-g12a-ee-pwm`. Cukup pasang patch DTB universal kami ([`dtbfix/meson-g12a-hg680-fj-uni.dtb`](dtbfix/meson-g12a-hg680-fj-uni.dtb)), dan Wi-Fi akan langsung terdeteksi serta bekerja mulus di Kernel 5.10!

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
# Unduh paket rilis resmi terbaru (v1.0.8)
wget https://github.com/elsangithub/mt7663-driver/releases/download/v1.0.8/mt7663-dkms_1.0.8_all.deb

# Pasang paket (DKMS akan otomatis mengompilasi modul untuk kernel aktif dalam ~15-20 detik)
sudo dpkg -i mt7663-dkms_1.0.8_all.deb
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
# Hubungkan ke SSID Wi-Fi
sudo nmcli dev wifi connect "NAMA_SSID_ANDA" password "PASSWORD_WIFI"

# Flush cache penyimpanan agar profil NetworkManager langsung tersimpan permanen
sync
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

## 🔥 Fitur Baru v1.0.8: Mode Hotspot / SoftAP 5 GHz (`ap0`)

Driver versi 1.0.8 menghadirkan antarmuka virtual terisolasi **`ap0`** untuk difungsikan sebagai **Hotspot Wi-Fi 5 GHz berkecepatan tinggi** (802.11ac VHT80) yang meneruskan koneksi internet kabel (`eth0`) ke perangkat nirkabel (smartphone, laptop, dll.).

> [!IMPORTANT]
> **Zero Regression pada Mode Client (`wlan0`):**
> - Antarmuka utama **`wlan0` tetap murni dalam mode Client (STA) 100%** dan dikelola oleh NetworkManager.
> - Antarmuka **`ap0` diatur sebagai unmanaged** (`/etc/NetworkManager/conf.d/99-mt7663-unmanaged-ap0.conf`) sehingga NetworkManager tidak akan menginterupsi hotspot.
> - **Secara default saat boot, hotspot TIDAK menyala sendiri** kecuali Anda mengaktifkan layanannya. Pengguna yang hanya ingin memakai STB sebagai klien Wi-Fi tidak akan terpengaruh sama sekali.

### Menyalakan Hotspot Secara Instan (Turnkey CLI):
1. **Pasang paket pendukung**:
   ```bash
   sudo apt update && sudo apt install -y hostapd dnsmasq
   ```
2. **Jalankan Hotspot**:
   ```bash
   sudo mt7663-hotspot start
   ```
   *(Hotspot otomatis memancarkan SSID `HG680_5G_VHT80` dengan sandi `password123` di Channel 36 5 GHz, menetapkan IP `192.168.4.1` dengan MTU 1408, dan mengaktifkan NAT Masquerade ke `eth0`).*

3. **Periksa Status & Perangkat yang Terhubung**:
   ```bash
   sudo mt7663-hotspot status
   ```

4. **Menghentikan Hotspot**:
   ```bash
   sudo mt7663-hotspot stop
   ```

### Menjalankan Hotspot Otomatis Saat Boot (Opsional):
Jika Anda ingin STB otomatis berfungsi sebagai Hotspot setiap kali dinyalakan:
```bash
sudo systemctl enable mt7663-hotspot
```
*(Untuk mematikannya kembali dan kembali ke murni Client: `sudo systemctl disable --now mt7663-hotspot`)*

### Panduan Mengganti Nama SSID, Sandi, & Channel 5 GHz Hotspot:

1. **Buka file konfigurasi hostapd dengan editor nano:**
   ```bash
   sudo nano /etc/hostapd/hostapd-mt7663.conf
   ```

2. **Ubah parameter sesuai kebutuhan Anda:**
   - **Nama WiFi (SSID):**
     ```ini
     ssid=Nama_Hotspot_Baru_Anda
     ```
   - **Kata Sandi (Minimal 8 karakter):**
     ```ini
     wpa_passphrase=SandiRahasia123
     ```
   - **Channel Frekuensi 5 GHz (Bandwidth 80 MHz / VHT80):**
     ```ini
     channel=36
     vht_oper_centr_freq_seg0_idx=42
     ```
     > [!TIP]
     > **Tabel Referensi Channel 5 GHz (80 MHz):**
     > - **Pita Bawah (UNII-1: Channel 36, 40, 44, atau 48):**
     >   Gunakan `channel=36` (atau 40/44/48) dan pastikan `vht_oper_centr_freq_seg0_idx=42`.
     > - **Pita Atas (UNII-3: Channel 149, 153, 157, atau 161):**
     >   Gunakan `channel=149` (atau 153/157/161) dan ubah menjadi `vht_oper_centr_freq_seg0_idx=155`.

3. **Simpan dan Terapkan:**
   - Tekan **`Ctrl + O`** lalu **`Enter`** untuk menyimpan, kemudian tekan **`Ctrl + X`** untuk keluar dari nano.
   - Terapkan perubahan dengan memuat ulang hotspot:
     ```bash
     sudo mt7663-hotspot restart
     ```
   - Periksa status apakah sudah aktif kembali:
     ```bash
     sudo mt7663-hotspot status
     ```

---

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
1. **Mengatasi Kartu MicroSD Sama Sekali Tidak Terdeteksi**:
   Pada banyak unit FiberHome HG680-FJ yang menggunakan DTB bawaan asli, kartu MicroSD yang dicolokkan sering kali **sama sekali tidak terdeteksi oleh sistem** (tidak muncul di `lsblk` atau `fdisk -l`, dan tidak ada partisi `/dev/mmcblk1` yang terbentuk). Hal ini terjadi karena DTB bawaan memaksakan negosiasi voltase I/O 1.8V yang tidak didukung hardware serta pin GPIO deteksi kartu yang mengambang (*floating*). File DTB fixed ini langsung menuntaskan masalah tersebut sehingga kartu MicroSD yang sebelumnya tidak terbaca bisa langsung terdeteksi dan di-mount secara normal.
2. **Voltage Sag Akibat Transmisi Wi-Fi & False Card Removal**:
   Saat Wi-Fi bekerja dengan beban tinggi (misalnya saat speedtest atau unduhan besar), terjadi lonjakan arus cepat yang memicu penurunan tegangan tipis (*voltage sag*) pada jalur daya 3.3V bersama di board STB. DTB bawaan menggunakan saklar mekanis pendeteksi kartu (`cd-gpios = <0x2f 0x2f 0x01>`) yang membaca penurunan tegangan sesaat ini sebagai kartu dicabut (`mmc1: card aaaa removed`). Jika sistem operasi berjalan dari MicroSD, hal ini langsung memicu **Read-Only Filesystem / Kernel Panic Crash**.
3. **Error I/O Sektor 0**:
   DTB bawaan mengizinkan frekuensi hingga 200 MHz (`max-frequency = <0xbebc200>`). Jalur tembaga PCB slot MicroSD HG680-FJ yang tidak berpelindung tidak stabil pada 200 MHz, menyebabkan CRC corrupt pada kartu MicroSD SDXC modern.
4. **Ketidakcocokan Voltase I/O**:
   DTB bawaan mengarahkan jalur sinyal `vqmmc-supply` ke 1.8V (`VDDAO_1V8`), padahal slot fisik HG680-FJ terkunci permanen pada 3.3V.

### Apa yang Diubah oleh `dtbfix/meson-g12a-hg680-fj-uni.dtb`?
- Menghapus saklar mekanis `cd-gpios` dan menggantinya dengan flag `non-removable;` (mengunci MicroSD sebagai media permanen anti-lepas seperti halnya eMMC internal; 100% kebal terhadap noise listrik dan *voltage sag* Wi-Fi).
- Mengunci `max-frequency` pada frekuensi stabil **50 MHz** (`0x2faf080` / standar High-Speed).
- Mengunci `vqmmc-supply` pada tegangan 3.3V (`VDDAO_3V3`).

### Cara Memasang DTB Fixed Ini:
File biner DTB siap pakai telah disediakan di dalam repositori pada direktori [`dtbfix/meson-g12a-hg680-fj-uni.dtb`](dtbfix/meson-g12a-hg680-fj-uni.dtb) dan juga dapat diunduh langsung dari [GitHub Releases](https://github.com/elsangithub/mt7663-driver/releases). Anda dapat memilih salah satu metode di bawah ini:

#### Metode A: Unduh Langsung & Timpa (Paling Cepat & Praktis)
Unduh DTB Universal langsung dari rilis resmi dan timpa DTB lama:
```bash
# 1. Cadangkan (backup) file DTB asli
sudo cp /boot/dtb/amlogic/meson-g12a-hg680-fj.dtb /boot/dtb/amlogic/meson-g12a-hg680-fj.dtb.bak

# 2. Unduh dan pasang DTB Universal langsung dari rilis resmi
sudo wget -O /boot/dtb/amlogic/meson-g12a-hg680-fj.dtb https://github.com/elsangithub/mt7663-driver/releases/download/v1.0.7/meson-g12a-hg680-fj-uni.dtb

# 3. Reboot STB
sudo reboot
```
*(Bagi yang meng-clone repositori git secara lokal, Anda juga bisa memakai perintah lokal: `sudo cp dtbfix/meson-g12a-hg680-fj-uni.dtb /boot/dtb/amlogic/meson-g12a-hg680-fj.dtb`)*

#### Metode B: Mengubah Path DTB di `uEnv.txt`
Unduh file DTB fixed dengan nama aslinya, lalu arahkan konfigurasi boot ke file tersebut:
```bash
# 1. Unduh file DTB fixed ke direktori boot
sudo wget -O /boot/dtb/amlogic/meson-g12a-hg680-fj-uni.dtb https://github.com/elsangithub/mt7663-driver/releases/download/v1.0.7/meson-g12a-hg680-fj-uni.dtb

# 2. Buka file konfigurasi boot
sudo nano /boot/uEnv.txt
```
Arahkan baris `FDT=` ke nama file DTB fixed:
```ini
FDT=/dtb/amlogic/meson-g12a-hg680-fj-uni.dtb
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

## 🔄 Pemakaian Saat Berganti Versi Kernel

Jika Anda memperbarui atau berganti versi kernel di TV box Anda:

1. Pastikan direktori header kernel aktif tersedia:
   ```bash
   ls -d /usr/src/linux-headers-$(uname -r)
   ```
2. Jalankan salah satu perintah berikut untuk membangun ulang driver untuk kernel baru Anda (~15-20 detik):
   - **Opsi 1: Pasang Ulang Paket .deb (Paling Mudah)**
     ```bash
     sudo dpkg -i mt7663-dkms_1.0.7_all.deb
     ```
   - **Opsi 2: Pemicu Otomatis via DKMS**
     ```bash
     sudo dkms autoinstall
     ```
   - **Opsi 3: Konfigurasi Ulang Paket**
     ```bash
     sudo dpkg-reconfigure mt7663-dkms
     ```
3. Lakukan reboot untuk memuat modul baru dan menginisialisasi hardware:
   ```bash
   sudo reboot
   ```

---

## 📄 License
GPL-2.0 / MediaTek Proprietary Base.

---

## 🤝 Credits & Acknowledgments
- **MediaTek Inc.**: Arsitektur chipset orisinal dan baseline driver.
- **[junglon/mt7668-driver](https://github.com/junglon/mt7668-driver)**: Referensi berharga serta wawasan implementasi driver wireless MediaTek untuk platform Amlogic.
- **Ophub & Armbian Community**: Kernel Linux kustom dan perkakas build untuk TV box Amlogic.
- **Van der Decken**: Maintainer dan developer.
