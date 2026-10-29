[English](README.md) | [Bahasa Indonesia](README.id.md)

# FiberHome HG680-FJ Device Tree (DTB) Collection

This directory contains 3 Device Tree Blob (`.dtb`) variants for FiberHome HG680-FJ (Amlogic S905X2 / G12A) running Armbian Ophub:

---

## 📊 DTB Variant Comparison Table

| File | Target Kernel | MicroSD Clock | Card Detect | SDIO Wi-Fi 32kHz Clock | Notes & Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`meson-g12a-hg680-fj-ori.dtb`** | Linux 6.x | 104 MHz (SDR104) | GPIO (`cd-gpios`) | `amlogic,meson-g12-pwm-v2` | Stock Ophub DTB. Prone to detection failure on certain MicroSD cards. |
| **`meson-g12a-hg680-fj-fixed.dtb`** | Linux 6.x | 50 MHz | `non-removable` | `amlogic,meson-g12-pwm-v2` | MicroSD stability patch. Highly stable for TF card booting on Kernel 6.x. |
| **`meson-g12a-hg680-fj-uni.dtb`** | **Linux 5.10 & 6.x** | 50 MHz | `non-removable` | **Universal** (`meson-g12a-ee-pwm` + `meson-g12-pwm-v2`) | **Highly recommended!** Stable MicroSD timing and enables Wi-Fi on both Kernel 5.10 LTS and Kernel 6.x. |

---

## 🔑 SHA256 Checksums

```text
8a55a85bc3676fc350cc09418d4945e516f53a172a6130a9339d556a71e8ec4a  meson-g12a-hg680-fj-ori.dtb
5689deafc728165fd9549e1880c2981fab943574037928e24815c9b42ffaec57  meson-g12a-hg680-fj-fixed.dtb
1af098f3f49f1adbe19b686921ee16a75e2301ca542324efc7a33ba24d2ba166  meson-g12a-hg680-fj-uni.dtb
```

---

## 📖 Usage Guide

Select your preferred DTB file and copy it to your boot partition:

```bash
# Example using Universal DTB (recommended):
sudo cp dtbfix/meson-g12a-hg680-fj-uni.dtb /boot/dtb/amlogic/

# Edit your boot environment file uEnv.txt:
sudo nano /boot/uEnv.txt
# Update the FDT line to:
# FDT=/dtb/amlogic/meson-g12a-hg680-fj-uni.dtb

sudo reboot
```
