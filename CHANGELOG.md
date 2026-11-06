# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.12] - 2026-11-07

### Fixed
- **Multi-Kernel Compatibility for DFS Radar CAC Event (`cfg80211_cac_event`)**:
  - Corrected preprocessor guard in `os/linux/gl_p2p_kal.c` to `#if KERNEL_VERSION(6, 12, 0) <= CFG80211_VERSION_CODE`.
  - Resolves fatal compilation failure `error: too many arguments to function 'cfg80211_cac_event'` on Linux kernels 6.1 through 6.11 (such as Debian 12 standard 6.1, Linux 6.6 LTS, and Ubuntu 24.04 6.8), while preserving 5-argument MLO signature compatibility for Linux 6.12+.

## [1.0.11] - 2026-11-03

### Fixed
- **Universal SDIO Controller Device Matching (`ffe03000*`)**:
  - Updated `mt7663-shutdown.service` to dynamically discover and unbind `/sys/bus/platform/drivers/meson-gx-mmc/ffe03000*` using wildcard matching.
  - Simplified IRQ affinity matching in `wlan-irq-tune.sh` to pattern `/ffe03000/`.
  - Ensures seamless operation across kernel versions and DTB variants regardless of whether the platform bus device is named `ffe03000.mmc` or `ffe03000.sd`.
- **UsrMerge Packaging Compliance (`build-deb.sh`)**:
  - Relocated firmware installation destination from `./lib/firmware/` to `./usr/lib/firmware/` in `build-deb.sh`.
  - Prevents `dpkg -x` extraction from converting `/lib` into a physical directory, which broke the mandatory `/lib -> usr/lib` symlink on modern Debian/Armbian systems and caused fatal `run-init: can't execute '/sbin/init': No such file or directory` kernel panics.
- **Multi-Kernel Compatibility for Station Update (`cfg80211_new_sta` & `cfg80211_del_sta`)**:
  - Corrected kernel version preprocessor guard in `os/linux/gl_p2p_kal.c` to `#if (CFG80211_VERSION_CODE >= KERNEL_VERSION(6, 14, 0))`.
  - Fixes fatal kernel oops and `main_thread` crash when stations associate on Linux 5.10 LTS and 6.12 LTS (`6.12.114-ophub`), while preserving upstream `struct wireless_dev *` signature compatibility for Linux 6.18+.
- **`cfg80211_ops` Callback Signatures (`os/linux/gl_cfg80211.c` & `os/linux/include/gl_cfg80211.h`)**:
  - Restored standard `struct net_device *ndev` parameter type across `add_key`, `get_key`, `del_key`, `set_default_mgmt_key`, `get_station`, `change_station`, `add_station`, and `del_station`.
  - Eliminates bogus pointer dereferencing (`wdev->netdev`) and fixes `errno=11` failures during hostapd station flag updates.
- **WPA2/WPA3 Data-Plane Queue Unlocking (`fgIsTxKeyReady`)**:
  - Explicitly mark station transmission as allowed (`fgIsTxKeyReady = TRUE`) and update station queue record (`qmUpdateStaRec`) upon `NL80211_STA_FLAG_AUTHORIZED` and pairwise key installation in `mtk_cfg_change_station` and `mtk_p2p_cfg80211_add_key`.
  - Resolves client loop where device connected to Wi-Fi but showed "terhubung tanpa internet" due to blocked data queues.
- **Global Station Record Lookup Fallback (`nicEventAddPkeyDone` & `nicRxProcessEventPacket`)**:
  - Added fallback search via `cnmGetAnyStaRecByAddress` to prevent BSS index mismatch on virtual interface `ap0` from dropping key completion events.

## [1.0.10] - 2026-11-03

### Release
- Version alignment release maintaining full parity with v1.0.8 codebase.

## [1.0.8] - 2026-10-31

### Changed
- **Decoupled Architecture (Pure Kernel DKMS Driver)**:
  - Decoupled the WSGI Web UI dashboard, Python runtime files, hotspot daemon, and routing scripts out of `mt7663-dkms` into the standalone companion package: [**`mt7663-router-webui`**](https://github.com/elsangithub/mt7663-router-webui).
  - Reduced `mt7663-dkms` package dependencies strictly to `dkms (>= 2.1.0.0)` and `build-essential`. Zero background daemons, zero external dependencies, and minimal memory footprint.
- **Modular Kernel Parameter (`ap_mode`)**:
  - Added kernel module parameter `ap_mode` via `module_param(ap_mode, int, 0644)` in `os/linux/gl_init.c`:
    - `ap_mode=0` (default): Pure Wi-Fi Client mode (`wlan0` only). Highly stable, lightweight, and ideal for standard desktop/server operations.
    - `ap_mode=1`: Dynamically instantiates the dedicated virtual interface `ap0` alongside `wlan0` for Dual-Band Concurrent (DBDC) SoftAP Hotspot & Repeater operations when paired with `mt7663-router-webui`.

### Added
- **Modern Linux 6.7+ & 6.18+ (Ophub) cfg80211 wdev Compatibility**:
  - Updated `kalP2PGOStationUpdate` in `os/linux/gl_p2p_kal.c` to pass `struct wireless_dev *wdev` to `cfg80211_new_sta()` and `cfg80211_del_sta()` for kernels >= 6.7.0, preventing kernel oops during station association.
- **WPA2/WPA3 Key Handshake Exception Patch (`wlanoidSetAddKey`)**:
  - Adjusted key index bitmask in `common/wlan_oid.c` to permit `IS_AUTHENTICATOR` (`BIT(28)`), eliminating key handshake drops during AP encryption setup.
- **TX1 Overflow Fast-Path Interrupt Recovery**:
  - Added immediate interrupt acknowledgement for `WASR_TX1_OVER_FLOW` in `nic/nic.c`, preventing SDIO bus stalls and dmesg log floods under heavy bidirectional network saturation.
- **State Machine Null-Pointer Guards (`ais_fsm.c`)**:
  - Protected 6 AIS FSM event transitions against null pointer dereference (`prAdapter->prAisBssInfo != NULL`), eliminating kernel panics during rapid interface state transitions.

## [1.0.8-rc4] - 2026-10-31
### Added
- **Pre-Decoupling Turnkey Router Web UI Prototype**:
  - Early monolithic test integrating Python 3 + `bottle.py` Web UI and routing scripts into driver package (subsequently decoupled into standalone `mt7663-router-webui` in rc5).
  - Dynamic dual-interface NAT masquerading and source-based policy routing testing.

## [1.0.8-rc3] - 2026-10-31
### Fixed
- **Hotspot Client Discovery in Status Command**: Enhanced `/usr/sbin/mt7663-hotspot status` to accurately detect, deduplicate, and display connected client stations with their hostname, IP address, MAC, and ARP reachability state by reading active `dnsmasq` DHCP leases and `ip neigh` tables instead of relying on MediaTek's unpopulated `iw dev ap0 station dump`.
- **Automated Release Notes & Native CLI Pipeline**: Transitioned CI/CD release workflow to native GitHub CLI (`gh release create`) with automated changelog extraction directly from `CHANGELOG.md` for seamless atomic release asset publishing.

## [1.0.8-rc1] - 2026-10-30
### Added
- **Dual-Band 5 GHz 802.11ac SoftAP / Hotspot Mode Support (`ap0`)**: Added high-performance Wi-Fi Hotspot mode operating on a dedicated virtual interface (`ap0`) alongside pure Client (`wlan0`) mode without interference or regression.
- **Turnkey Hotspot Utility & Service (`mt7663-hotspot`)**: Integrated hotspot CLI tool (`/usr/sbin/mt7663-hotspot`), systemd service (`mt7663-hotspot.service`), and hostapd configuration template (`/etc/hostapd/hostapd-mt7663.conf`) with automatic IP gateway setup, DHCP Option 26 (MTU 1408), and NAT Masquerade packet routing.
- **NetworkManager AP Isolation (`99-mt7663-unmanaged-ap0.conf`)**: Bundled NetworkManager rule designating `ap0` as unmanaged so NetworkManager leaves AP operations solely to `hostapd` while continuing to manage `wlan0` client mode smoothly.

### Fixed
- **Linux >= 6.7 cfg80211 Association Kernel Oops**: Updated `kalP2PGOStationUpdate` in `os/linux/gl_p2p_kal.c` to pass `struct wireless_dev *wdev` instead of `net_device` to `cfg80211_new_sta()` and `cfg80211_del_sta()`, resolving kernel crashes upon client station association.
- **Amlogic SDIO Buffer Overflow & Firmware Assert (`wsys_i #565`)**: Enforced hardware-safe MTU of 1408 (`mtu = 1408`, `max_mtu = 1408`) across all dynamic AP/P2P interfaces in `gl_p2p_cfg80211.c` and `gl_p2p.c`, preventing Ethernet frame overflow on Amlogic Meson G12A (`max_req_size = 1536`).
- **TX1 Overflow Fast-Path Interrupt Handling**: Added immediate acknowledgement and clearing of `WASR_TX1_OVER_FLOW` in `nic/nic.c` to prevent interrupt storms and maintain stable hardware communication.
- **P2P Station Flag Error (errno=11)**: Updated `mtk_cfg_change_station` in `os/linux/gl_cfg80211.c` to cleanly return success for AP interfaces, eliminating hostapd station flag failure warnings.

## [1.0.7] - 2026-10-29
### Added
- **Full Linux Kernel 5.10 LTS Support**: Expanded native compatibility to include Linux Kernel 5.10 LTS (e.g. `5.10.272-ophub`) on FiberHome HG680-FJ.
