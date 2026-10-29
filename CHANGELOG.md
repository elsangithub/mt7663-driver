# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2026-10-29
### Added
- **Full Linux Kernel 5.10 LTS Support**: Expanded native compatibility to include Linux Kernel 5.10 LTS (e.g. `5.10.272-ophub`) on FiberHome HG680-FJ.
- **Universal DTB Collection (`dtbfix/`)**: Bundled pre-compiled Device Tree blobs (`meson-g12a-hg680-fj-uni.dtb`, `fixed.dtb`, `ori.dtb`) to provide seamless 32kHz reference clocking and MicroSD hardware stability across both Kernel 5.10 and Kernel 6.x.
- **Dynamic Cross-Kernel Toolchain Alignment**: Enhanced `debian/postinst` self-healing logic to conditionally inspect header sources for `symsearch.c`, enabling automatic, zero-intervention `modpost` rebuilding across both Kernel 5.x and Kernel 6.x under Debian 12 Bookworm.

### Fixed
- **Pre-installation Kernel Guard**: Replaced obsolete Kernel < 6.0 warning in `debian/preinst` with informative guidance directing Kernel 5.x users to the universal DTB.
- **DTC Audio Routing Escape Bug**: Resolved string-splitting octal escape sequence glitch (`Lineout\x08U2`) in Device Tree compilation, ensuring 100% clean ALSA DAPM routing without `axg-sound-card` warnings in `dmesg`.

## [1.0.6] - 2026-10-29
### Added
- **RF Power Calibration Firmware (`TxPwrLimit_MT76x3.dat`)**: Bundled regulatory transmit power calibration tables directly into `/lib/firmware/`, ensuring optimal linear Power Amplifier (PA) operation for 256-QAM (MCS 8/9) without saturation, distortion, or missing firmware errors in `dmesg`.
- **Automatic Boot Module Loading (`/etc/modules-load.d/wlan_mt7663_sdio.conf`)**: Integrated automatic module configuration into the `.deb` package to ensure `wlan_mt7663_sdio` starts seamlessly on clean OS burns without requiring manual configuration.
- **Self-Healing Toolchain Alignment**: Integrated runtime detection and instant GCC rebuilding of kernel header host tools (`modpost`) in `postinst` to automatically resolve GLIBC mismatches (e.g. Debian 12 Bookworm GLIBC 2.36 vs Ophub GLIBC 2.38+) without triggering Kbuild `syncconfig` or deleting `autoconf.h`.

### Changed
- **Comprehensive In-Tree Driver Neutralization**: Enhanced `/etc/modprobe.d/blacklist-mt7663-bluetooth.conf` with `install <module> /bin/true` overrides for all conflicting in-tree drivers (`mt7663s`, `mt76_sdio`, `mt7663_usb_sdio_common`, `mt7615_common`, `mt76_connac_lib`, `mt76`, `btmtksdio`, `btmtk`), completely preventing udev alias race conditions and device lockups on boot across Linux 6.12 and 6.18+.
- **Unified Packaging Architecture**: Centralized all runtime files and scripts exclusively inside `/root/mt7663-driver` with zero external dependencies.

## [1.0.5] - 2026-10-28
### Added
- **Linux 6.18+ Modern Kernel Support**: Added backward/forward compatibility bridge for Linux 6.18+ timer subsystem modernization (`timer_delete_sync()`, `timer_delete()`, and `container_of` from_timer mapping) alongside `FB_EVENT_BLANK` fallback, while maintaining 100% native compatibility with Linux 6.12 LTS.
- **Pre-installation Kernel Guard (`preinst`)**: Automatically detects running kernel during package installation (`dpkg -i`) and warns if running on Kernel < 6.0, detailing FiberHome HG680-FJ's hardware DTB dependency on `meson-g12-pwm-v2`.
- **Makefile Kernel Architecture Check**: Emits diagnostic compile-time warning if targeting Kernel < 6.0.
- **Kernel Focus Realignment**: Shifted project focus and roadmap exclusively to modern 6.x series (Linux 6.12+ LTS & 6.18+ LTS).

### Changed
- **Silent Production Logging**: Completely silenced all development debug messages (`[scan-start]`, `[scan-set-ch]`, `[wlanoidSetAddKey]`, `[wlan-ack]`, `[wlan-cfg]`, and `[wlan-bufbin]`), eliminating red error text and log spam in `dmesg`.
- **Clean Kernel Dmesg**: Driver is now whisper-quiet and zero-spam in production kernel environments.
- **Version Leap**: Skipped v1.0.4 directly to v1.0.5 per project release schedule.

## [1.0.3] - 2026-10-28
### Added
- **Native SMP CPU Affinity**: Thread workers `rx_thread` and `hif_thread` in `os/linux/gl_kal.c` dynamically bind to online CPUs excluding CPU0 (`set_cpus_allowed_ptr`), ensuring packet and SDIO bus processing never contend with system timers or OS scheduler on CPU0.
- **Udev Instant IRQ Mapping**: Replaced external systemd service with instantaneous `99-wlan-performance.rules` udev trigger, dynamically setting `ffe03000.mmc` SDIO IRQ SMP affinity to CPU 2,3 upon network device registration with zero race conditions.
- **802.11ac High-Throughput Aggregation**: Enabled `AmsduInAmpduTx 1` and `VhtAmsduInAmpduTx 1` in `wifi_mt7661.cfg` to allow multi-MSDU packing per AMPDU over 5GHz radio.
- **VHT Beamforming & RX Diversity**: Enabled `StaVHTBfee 1` (Explicit VHT Beamformee) and `StbcRx 1` (Space-Time Block Coding) in firmware configuration for enhanced SNR and signal reception from multi-antenna routers.
- **HIF Processing Loop Expansion**: Doubled `HifTxLoop` to 32 and `OsTxLoop` to 16 for higher batch processing under sustained network load.

### Removed
- Redundant `wlan-tune.service` systemd unit file (now completely handled natively by udev).

## [1.0.2] - 2026-10-28
### Added
- Comprehensive `CHANGELOG.md` for formal semantic version tracking.
- Coalescing buffer flush clamping to MMC host `max_req_size` (1536B) in `kalDevWriteData` (`os/linux/hif/sdio/sdio.c`).
- Hard netdev MTU lock to 1408 in `os/linux/gl_init.c` to prevent multi-CMD53 splitting by core MMC under Amlogic G12A SRAM constraints.

### Fixed
- Fixed `wifi_mt7661.cfg` file permissions to standard read-only 0644.
- Completely eliminated `WASR_TX1_OVER_FLOW` and host controller FIFO lockups during high-volume bursts.

## [1.0.1] - 2026-10-27
### Fixed
- Fixed credit allocation leak in `halTxGetPageCount` (`os/linux/hif/sdio/hal_api.c`).
- Stabilized SDIO bus polling and interrupt acknowledge routines.

## [1.0.0] - 2026-10-25
### Added
- Initial port of MediaTek MT7663/MT7661 driver for Linux 6.12+ (Armbian).
