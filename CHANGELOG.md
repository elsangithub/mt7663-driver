# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2026-10-28
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
