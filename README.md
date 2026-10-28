# MediaTek MT7663 / MT7661 SDIO Wi-Fi Driver for Linux (Kernel 5.10 - 6.12+ LTS)
### High-Performance Standalone Wi-Fi for Amlogic TV Boxes (Armbian / Ophub)

Patched, high-performance out-of-tree Linux kernel driver for the **MediaTek MT7663 / MT7661** (AMPAK MT7661RSN, SDIO ID `037A:7663` / `037A:7603`) dual-band 802.11a/b/g/n/ac combo module.

Tuned specifically for Amlogic SoC hardware constraints (S905X2 / G12A, S905X3 / SM1, S905W2, etc.), tested and validated on the **FiberHome HG680-FJ** running **Armbian Ophub** across Linux kernels **5.10.x, 5.15.x, 6.1.x, and 6.12.x LTS**.

---

## ???? Key Highlights & Verified Benchmarks (FiberHome HG680-FJ)

- **Pure Standalone Wi-Fi**: 100% stable operation with Ethernet cable disconnected (`eth0` down).
- **Dual-Band 2.4 GHz & 5 GHz**: Full 802.11n 2x2 MIMO on 2.4 GHz (up to 62 Mbps TCP) and 802.11ac VHT on 5 GHz (up to 73+ Mbps TCP, 3.2 ms latency, 0.0% packet loss).
- **Amlogic G12A SRAM Burst Protection**: Resolves the infamous `WASR_TX1_OVER_FLOW` and SDIO FIFO stalls caused by Amlogic's 1536-byte single-request hardware constraint (`amlogic,dram-access-quirk`).
- **Native SMP Multi-Core CPU Affinity**: Kernel worker threads (`rx_thread`, `hif_thread`, `main_thread`) automatically bind to CPUs 1, 2, and 3 (`set_cpus_allowed_ptr`), completely offloading packet and bus processing from CPU0.
- **Instant Udev Hardware IRQ Routing**: SDIO interrupt line (`ffe03000.mmc`) is mapped automatically to CPU 2 and 3 on device registration, keeping system timers on CPU0 responsive without jitter.
- **Zero-Hang Warm Reboots**: Clean SDIO bus shutdown sequence via `mt7663-shutdown.service` and `mmc-pwrseq` hardware reset pin pulsing ensures 100% reliable detection across soft reboots (`sudo reboot`).
- **Coexistence with MT7668**: Uses dedicated `/lib/firmware/wifi_mt7661.cfg` so MT7668 and MT7663 units can share identical root filesystems without configuration conflicts.

---

## ???? Installation Instructions (Armbian Ophub)

> [!IMPORTANT]
> **Do NOT run `apt install linux-headers-$(uname -r)` on Armbian Ophub!**
> Standard Debian/Ubuntu repositories do not host custom Ophub kernels. On Armbian Ophub, kernel headers are **already pre-installed** in `/usr/src/linux-headers-$(uname -r)`.

### Step 1: Install Required Build Tools & DKMS
Only install standard packages from apt (headers are already on your system):
```bash
sudo apt update
sudo apt install -y dkms build-essential wget
```

### Step 2: Verify Kernel Headers are Present
Run this quick check to confirm Ophub's pre-installed headers:
```bash
ls -d /usr/src/linux-headers-$(uname -r)
```
*(If the folder appears, your system is 100% ready for DKMS).*

### Step 3: Download & Install the Debian Package (.deb)
```bash
# Download the latest release package (v1.0.5)
wget https://github.com/<your-username>/mt7663-driver/releases/download/v1.0.5/mt7663-dkms_1.0.5_all.deb

# Install package (DKMS will compile the module for your active kernel in ~15-20s)
sudo dpkg -i mt7663-dkms_1.0.5_all.deb
```

### Step 4: Reboot
```bash
sudo reboot
```

---

## ???? Using Across Different Kernels (e.g. Linux 5.10.x-ophub, 5.15.x, 6.1.x)

This package uses **DKMS (Dynamic Kernel Module Support)** and includes universal kernel compatibility shims:

- **Switching Kernels via Ophub**:
  When installing a new Ophub kernel (e.g., switching to `5.10.261-ophub`), ensure you install all three matching deb packages provided by Ophub:
  1. `linux-image-<version>-ophub_*.deb`
  2. `linux-dtb-<version>-ophub_*.deb`
  3. `linux-headers-<version>-ophub_*.deb`  *(Essential for DKMS)*

- **Automatic DKMS Rebuild**:
  Once the new kernel boots, simply run:
  ```bash
  sudo dpkg -i mt7663-dkms_1.0.5_all.deb
  ```
  DKMS detects the new kernel version and compiles a dedicated binary module tailored for that exact kernel release.

---

## ???? Connecting & Verifying Wi-Fi

### Connect to Wi-Fi via Terminal:
```bash
# Connect to your Wi-Fi SSID
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
*Notice that SDIO interrupts (`ffe03000.mmc`) accumulate heavily on **CPU2**, leaving **CPU0** completely unburdened!*

### Test Network Speed & Latency:
```bash
speedtest
```

---

## ??????? Architecture & Under-the-Hood Fixes

| Component | Root Cause in Stock Driver | Solution in v1.0.5 |
| :--- | :--- | :--- |
| **Amlogic SDIO Burst** | Host `max_req_size = 1536` due to `amlogic,dram-access-quirk`. Driver buffered 4096B, triggering multi-CMD53 splitting and `WASR_TX1_OVER_FLOW`. | Clamped coalescing buffer flush in `kalDevWriteData` (`sdio.c`) to `host->max_req_size` (1536B) and enforced netdev MTU to 1408. |
| **CPU0 Bottleneck** | ARM GICv2 routes all SPI interrupts to CPU0 by default; MediaTek's internal affinity code relied on proprietary Android kernel APIs (`mt_sched_setaffinity`). | Replaced with standard Linux kernel `set_cpus_allowed_ptr()` in `gl_kal.c` to bind `rx_thread` and `hif_thread` to CPUs 1-3. |
| **Hardware IRQ Routing** | Manual or fragile systemd unit timing races during early boot. | Integrated instantaneous dynamic trigger into `/usr/lib/udev/wlan-irq-tune.sh` via `99-wlan-performance.rules`. |
| **PMTU Packet Drops** | Asymmetric MTU (1408 local vs 1500 remote) caused silent packet blackholes when path discovery was disabled (`tcp_mtu_probing = 0`). | Automated `net.ipv4.tcp_mtu_probing = 1` and `tcp_moderate_rcvbuf = 1` in `/etc/sysctl.d/99-wifi-throughput.conf` to achieve 0.0% packet loss. |
| **802.11ac Performance** | Stock `wifi_mt7661.cfg` defaulted aggregation and beamforming to disabled. | Enabled `AmsduInAmpduTx 1`, `VhtAmsduInAmpduTx 1`, `StaVHTBfee 1` (Beamforming), `StbcRx 1`, and doubled processing loops (`HifTxLoop 32`, `OsTxLoop 16`). |
| **Warm Reboot Reliability** | Always-on power rails on TV boxes leave MT7663 state machine active after SoC reset, leading to CMD5 probe timeout (error -110). | Integrated `mt7663-shutdown.service` to unbind host MMC controller prior to reset, triggering clean hardware reset sequence. |

---

## ??????? Rollback Checkpoint

If you ever need to revert to the previous milestone release (**v1.0.2**):
```bash
# Revert instantly using local backup
sudo dpkg -i /root/mt7663-dkms_1.0.2_all.deb
```
*(Git repository is also permanently tagged at `v1.0.2` on commit `e9b5ee0`).*

---

## ???? License
GPL-2.0 / MediaTek Proprietary Base.

---

## ???? Credits & Acknowledgments
- **MediaTek Inc.**: Original chipset architecture and driver baseline.
- **Ophub & Armbian Community**: Linux kernels for Amlogic TV boxes.
- **Antigravity**: Development, reverse engineering, and performance optimization.

