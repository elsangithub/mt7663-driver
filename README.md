<p align="right">
  <b>English</b> | <a href="README.id.md">Bahasa Indonesia</a>
</p>

# MediaTek MT7663 / MT7661 SDIO Wi-Fi Driver for Amlogic TV Boxes (Armbian Ophub)

[![Release](https://img.shields.io/github/v/release/elsangithub/mt7663-driver?color=blue&label=release)](https://github.com/elsangithub/mt7663-driver/releases)
[![Build & Release](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml/badge.svg)](https://github.com/elsangithub/mt7663-driver/actions/workflows/release.yml)
[![DKMS Ready](https://img.shields.io/badge/DKMS-Automated_Build-brightgreen.svg)](https://github.com/elsangithub/mt7663-driver)
[![License: GPL-2.0](https://img.shields.io/badge/License-GPL_2.0-blue.svg)](https://opensource.org/licenses/GPL-2.0)

Patched, high-performance out-of-tree Linux kernel driver for the **MediaTek MT7663 / MT7661** (AMPAK MT7661RSN, SDIO ID `037A:7663` / `037A:7603`) dual-band 802.11a/b/g/n/ac combo module.

Tuned specifically for Amlogic SoC hardware constraints (S905X2 / G12A, S905X3 / SM1, S905W2, etc.), tested and physically verified on the **FiberHome HG680-FJ**.

> [!NOTE]
> **Verified Environments:**
> This driver has been specifically tested and validated on the following **Armbian by Ophub** releases:
> - **Debian 12 (Bookworm)** with kernel **`6.18.56-ophub`**
> - **Debian 13 (Trixie)** with kernel **`6.12.112-ophub`**
>
> Ophub builds incorporate specific device tree (DTB) and power/clock tree patches for Amlogic TV boxes.

> [!WARNING]
> **Compatibility Disclaimer for Other Kernel Versions:**
> While DKMS enables automatic compilation on other Linux versions, **there is always a possibility of incompatibility** with untested kernel releases (e.g., mainline vanilla kernels, older 5.x trees, or newer kernel versions with modified internal network APIs). If you encounter build or runtime errors on other versions, please open a GitHub Issue with your `uname -a` and `dmesg` logs.

---

## 🔍 Hardware Compatibility & FiberHome HG680-FJ Chipset Variants

The **FiberHome HG680-FJ** (Amlogic S905X2 / G12A) TV box was shipped by the factory with **two different internal Wi-Fi module variants** depending on the production batch:

| Hardware Variant | Physical Module | Internal Core Chipset | Required Linux Driver |
| :--- | :--- | :--- | :--- |
| **Variant A** | MediaTek MT7668 | MediaTek MT7668 | Built-in in-tree Linux kernel driver (`mt7668u` / `mt7668`) |
| **Variant B** | AMPAK MT7661RSN | **MediaTek MT7663** (`037A:7663`) | **This DKMS Driver Package (`mt7663-dkms`)** |

- **MT7668 Units**: Supported out-of-the-box by standard modern Linux kernels.
- **AMPAK MT7661RSN (MT7663) Units**: **Not supported** by standard in-tree kernel drivers (no Wi-Fi interface appears or hardware fails to initialize). This repository was created specifically to enable full, stable, high-performance Dual-Band (2.4 GHz & 5 GHz) connectivity on these units.
- **Safe Coexistence**: This driver uses an isolated firmware configuration file (`/lib/firmware/wifi_mt7661.cfg`), ensuring that shared disk images between MT7668 and MT7663 units will not conflict.

### How to Check Your Unit's Chipset Variant:
Run the following command on your TV box terminal:
```bash
cat /sys/bus/sdio/devices/*/device 2>/dev/null || cat /sys/bus/sdio/devices/*/vendor 2>/dev/null
```
If the output shows vendor `0x037a` and device `0x7663` or `0x7603`, your board is equipped with the **AMPAK MT7661RSN (MT7663)** module and requires this driver.

> [!CAUTION]
> **Legacy Kernel 5.x (5.10 / 5.15) is NOT supported on FiberHome HG680-FJ!**
> The HG680-FJ Device Tree (`meson-g12a-hg680-fj.dtb`) requires `amlogic,meson-g12-pwm-v2` to supply the 32.768 KHz SDIO reference clock. This driver is only present in Linux 6.x+ kernels. On Kernel 5.x, SDIO hardware power and clock remain uninitialized, preventing Wi-Fi hardware detection.

---

## 🚀 Key Highlights & Verified Benchmarks (FiberHome HG680-FJ)

- **Pure Standalone Wi-Fi**: 100% stable operation with Ethernet cable disconnected (`eth0` down).
- **Dual-Band 2.4 GHz & 5 GHz**: Full 802.11n 2x2 MIMO on 2.4 GHz (up to 62+ Mbps TCP) and 802.11ac VHT on 5 GHz (up to 73+ Mbps TCP, 3.2 ms latency, 0.0% packet loss).
- **Amlogic G12A SRAM Burst Protection**: Resolves the infamous `WASR_TX1_OVER_FLOW` and SDIO FIFO stalls caused by Amlogic's 1536-byte single-request hardware constraint (`amlogic,dram-access-quirk`).
- **Native SMP Multi-Core CPU Affinity**: Kernel worker threads (`rx_thread`, `hif_thread`, `main_thread`) automatically bind to CPUs 1, 2, and 3 (`set_cpus_allowed_ptr`), completely offloading packet and bus processing from CPU0.
- **Instant Udev Hardware IRQ Routing**: SDIO interrupt line (`ffe03000.mmc`) is mapped automatically to CPU 2 and 3 on device registration, keeping system timers on CPU0 responsive without jitter.
- **Zero-Hang Warm Reboots**: Clean SDIO bus shutdown sequence via `mt7663-shutdown.service` and `mmc-pwrseq` hardware reset pin pulsing ensures 100% reliable detection across soft reboots (`sudo reboot`).

---

## 📦 Installation Instructions (Armbian Ophub)

> [!IMPORTANT]
> **Do NOT run `apt install linux-headers-$(uname -r)` on Armbian Ophub!**
> Standard Debian/Ubuntu repositories do not host custom Ophub kernels. On Armbian Ophub, kernel headers are **already pre-installed** in `/usr/src/linux-headers-$(uname -r)`.

### Step 1: Install Required Build Tools & DKMS
```bash
sudo apt update
sudo apt install -y dkms build-essential wget
```

### Step 2: Verify Kernel Headers are Present
```bash
ls -d /usr/src/linux-headers-$(uname -r)
```
*(If the folder appears, your system is 100% ready for DKMS).*

### Step 3: Download & Install the Debian Package (.deb)
```bash
# Download the latest verified release package (v1.0.6)
wget https://github.com/elsangithub/mt7663-driver/releases/download/v1.0.6/mt7663-dkms_1.0.6_all.deb

# Install package (DKMS will compile the module for your active kernel in ~15-20s)
sudo dpkg -i mt7663-dkms_1.0.6_all.deb
```

### Step 4: Reboot
```bash
sudo reboot
```

---

## 📶 Connecting & Verifying Wi-Fi

### Connect to Wi-Fi via Terminal:
```bash
sudo nmcli dev wifi connect "YOUR_SSID" password "YOUR_PASSWORD"
```

### Verify Connection & Physical Link Rate:
```bash
iw dev wlan0 link
```
*Expected output (5 GHz band)*:
- `SSID: YOUR_5G_SSID`
- `freq: 5180.0` (Channel 36) or `5785.0` (Channel 157)
- `signal: -38 dBm` to `-50 dBm`
- `tx bitrate: 156.0 MBit/s` (or higher)

### Verify Multi-Core Interrupt Offloading:
```bash
grep -E "CPU|mmc" /proc/interrupts
```
*SDIO interrupts (`ffe03000.mmc`) accumulate heavily on **CPU2/CPU3**, leaving **CPU0** unburdened!*

---

## 🗑️ Clean Uninstallation

If you ever wish to remove this driver and restore your system, the package includes automated cleanup routines (`prerm` and `postrm`) that leave no orphan configurations behind.

### Option 1: Remove Driver (Package Only)
Unregisters and removes the DKMS module:
```bash
sudo dpkg -r mt7663-dkms
```

### Option 2: Complete Purge (Recommended)
Removes the package, compiled DKMS modules, udev rules, sysctl tuning, shutdown service, and firmware configurations:
```bash
sudo apt purge -y mt7663-dkms
```

#### What Gets Cleaned Up Automatically?
1. Shuts down the Wi-Fi network interface (`ip link set dev wlan0 down`).
2. Unloads the kernel module (`rmmod wlan_mt7663_sdio`).
3. Removes DKMS registration and binaries from `/var/lib/dkms/mt7663-dkms/`.
4. Removes auto-load configuration from `/etc/modules-load.d/wlan_mt7663_sdio.conf`.
5. Stops, disables, and deletes `/etc/systemd/system/mt7663-shutdown.service`.
6. Deletes udev IRQ routing rule `/etc/udev/rules.d/99-wlan-performance.rules`.
7. Deletes TCP buffer tuning `/etc/sysctl.d/99-wifi-throughput.conf`.

---

## 🛠️ Architecture & Under-the-Hood Fixes

| Component | Root Cause in Stock Driver | Solution in This Package |
| :--- | :--- | :--- |
| **Amlogic SDIO Burst** | Host `max_req_size = 1536` due to `amlogic,dram-access-quirk`. Driver buffered 4096B, triggering multi-CMD53 splitting and `WASR_TX1_OVER_FLOW`. | Clamped coalescing buffer flush in `kalDevWriteData` (`sdio.c`) to `host->max_req_size` (1536B) and enforced netdev MTU to 1408. |
| **CPU0 Bottleneck** | ARM GICv2 routes all SPI interrupts to CPU0 by default; MediaTek's internal affinity code relied on proprietary Android kernel APIs (`mt_sched_setaffinity`). | Replaced with standard Linux kernel `set_cpus_allowed_ptr()` in `gl_kal.c` to bind `rx_thread` and `hif_thread` to CPUs 1-3. |
| **Hardware IRQ Routing** | Race conditions during early boot systemd timing. | Integrated dynamic trigger into `/usr/lib/udev/wlan-irq-tune.sh` via `99-wlan-performance.rules`. |
| **PMTU Packet Drops** | Asymmetric MTU (1408 local vs 1500 remote) caused silent packet blackholes when path discovery was disabled (`tcp_mtu_probing = 0`). | Automated `net.ipv4.tcp_mtu_probing = 1` and `tcp_moderate_rcvbuf = 1` in `/etc/sysctl.d/99-wifi-throughput.conf` (0.0% packet loss). |
| **802.11ac Performance** | Stock configuration defaulted aggregation and beamforming to disabled. | Enabled `AmsduInAmpduTx 1`, `VhtAmsduInAmpduTx 1`, `StaVHTBfee 1` (Beamforming), `StbcRx 1`, and doubled processing loops (`HifTxLoop 32`, `OsTxLoop 16`). |
| **Warm Reboot Reliability** | Always-on power rails on TV boxes leave MT7663 state machine active after SoC reset, leading to CMD5 probe timeout (error -110). | Integrated `mt7663-shutdown.service` to unbind host MMC controller prior to reset, triggering clean hardware reset sequence. |

---

## 🔄 Using Across Kernel Upgrades

This package uses **DKMS (Dynamic Kernel Module Support)**:
- When upgrading or switching Ophub kernels on your TV box, ensure you install the matching `linux-headers-<version>-ophub_*.deb` package.
- DKMS will automatically rebuild the kernel module for the new kernel version during boot or package trigger.

---

## 📄 License
GPL-2.0 / MediaTek Proprietary Base.

---

## 🤝 Credits & Acknowledgments
- **MediaTek Inc.**: Original chipset architecture and driver baseline.
- **[junglon/mt7668-driver](https://github.com/junglon/mt7668-driver)**: Invaluable reference implementation and insights on MediaTek wireless drivers for Amlogic platforms.
- **Ophub & Armbian Community**: Custom Linux kernels and build tooling for Amlogic TV boxes.
- **Van der Decken**: Maintainer and developer.
