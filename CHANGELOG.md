# Changelog - mt7663-dkms

Semua perubahan, perbaikan bug, dan rilis versi driver MediaTek MT7663/MT7661 SDIO untuk Linux 6.12+ (Amlogic G12A / S905X2 - FiberHome HG680-FJ).

## [1.0.2] - 2026-10-28
### Fixed
- **Amlogic G12A SDIO FIFO Overflow (WASR_TX1_OVER_FLOW)**:
  - Membatasi threshold flush buffer coalescing di \kalDevWriteData\ (\os/linux/hif/sdio/sdio.c\) ke batas host MMC (\host->max_req_size\ = 1536 byte / 3 blok). Mencegah Linux MMC core memecah satu transaksi penulisan port WTDR1 menjadi beberapa CMD53 terpisah saat lalu lintas burst (seperti \dmesg\ via SSH).
- **MTU Clamping (1408 Byte)**:
  - Mengunci default \mtu\ dan batas atas \max_mtu\ interface \wlan0\ ke **1408 byte** di \os/linux/gl_init.c\ (persis arsitektur referensi ZTE B860H V5), menjamin frame individu + descriptor MediaTek tidak melampaui buffer SRAM 1536 byte Amlogic.
- **Packaging & Permissions**:
  - Memperbaiki izin file \/lib/firmware/wifi_mt7661.cfg\ dari executable 0755 menjadi 0644.
  - Menghapus mask error pada \dkms build\ dan \dkms install\ di skrip \postinst\ agar proses build transparan jika gagal.

## [1.0.1] - 2026-10-27
### Fixed
- **SDIO Credit Accounting Leak**:
  - Memperbaiki perhitungan credit halaman di \halTxGetPageCount\ (\os/linux/hif/sdio/hal_api.c\). Mengembalikan 1 credit per frame (SDIO frame-based) alih-alih ~11 halaman PSE, menghentikan kebocoran credit TX yang menguras antrean dan memicu stall FIFO.
- **GTK Rekeying Collision**:
  - Memperbaiki alokasi slot key table WTDR di \mgmt/privacy.c\ (\secPrivacySeekForBcEntry\) agar rotasi KeyId 1 dan KeyId 2 pada WPA2/WPA3 tidak saling menimpa (*assert wsys_i #565* setelah 2,5 menit).
- **HW AMSDU SDIO Overflow**:
  - Menonaktifkan agregasi hardware AMSDU (\.is_support_hw_amsdu = FALSE\) di \chips/mt7663/mt7663.c\ untuk mencegah burst multi-frame melebihi kapasitas SDIO controller Amlogic.

## [1.0.0] - 2026-10-27
### Added
- Rilis baseline porting driver MT7663 / MT7661 SDIO untuk Linux kernel modern 6.12+ (ophub) pada FiberHome HG680-FJ.
- Integrasi firmware patch E2, RAM code, dan konfigurasi optimasi RPS multi-core.
