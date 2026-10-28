#!/bin/bash
set -e

PACKAGE=mt7663-dkms
VERSION=1.0.5
BUILD_DIR=/tmp/${PACKAGE}_build
SRC_DIR=${BUILD_DIR}/usr/src/mt7663-${VERSION}

echo "Building Debian package for ${PACKAGE}_${VERSION}..."

rm -rf ${BUILD_DIR}
mkdir -p ${SRC_DIR}
mkdir -p ${BUILD_DIR}/DEBIAN

# 1. Copy pure driver source code directly to /usr/src/mt7663-${VERSION} (no junk)
cp -a chips common include mgmt nic os prealloc Makefile Kconfig dkms.conf CHANGELOG.md README.md ${SRC_DIR}/

# 2. Copy ALL system integration files at once from unified system/ directory
cp -a system/* ${BUILD_DIR}/
chmod 644 ${BUILD_DIR}/lib/firmware/*
chmod 755 ${BUILD_DIR}/usr/lib/udev/wlan-irq-tune.sh

cat << CTRL > ${BUILD_DIR}/DEBIAN/control
Package: mt7663-dkms
Version: ${VERSION}
Architecture: all
Maintainer: Van der Decken <root@hermes>
Depends: dkms, build-essential
Section: kernel
Priority: optional
Description: MediaTek MT7663 SDIO Wi-Fi driver module (DKMS)
 Patched high-performance Linux driver for MediaTek MT7663 SDIO Wi-Fi,
 tuned for Linux 6.12+ / 6.18+ with native SMP CPU affinity, udev instant IRQ mapping,
 and 802.11ac A-MSDU/Beamforming throughput boost.
CTRL

cat << 'PREINST' > ${BUILD_DIR}/DEBIAN/preinst
#!/bin/sh
set -e

KERNEL_MAJOR=$(uname -r | cut -d. -f1)
if [ "$KERNEL_MAJOR" -lt 6 ] 2>/dev/null; then
    echo "======================================================================="
    echo "  [PERINGATAN] Kernel $(uname -r) TIDAK DIDUKUNG di FiberHome HG680-FJ!"
    echo "  Device Tree HG680-FJ membutuhkan driver 'meson-g12-pwm-v2' yang"
    echo "  hanya tersedia pada Kernel Linux 6.x ke atas (rekomendasi: 6.12 / 6.18+)."
    echo "  Pada Kernel 5.x, clock SDIO tidak aktif sehingga Wi-Fi tidak terdeteksi."
    echo "  Silakan gunakan kernel 6.x: armbian-update -k 6.12"
    echo "======================================================================="
fi
exit 0
PREINST
chmod 755 ${BUILD_DIR}/DEBIAN/preinst

cat << POST > ${BUILD_DIR}/DEBIAN/postinst
#!/bin/sh
set -e

# Detect existing registrations dynamically
OLD_VERSIONS=\$(dkms status -m mt7663 2>/dev/null | awk -F'[/,]' '{print \$2}' | sort -u)

if [ -n "\$OLD_VERSIONS" ]; then
    for VER in \$OLD_VERSIONS; do
        if [ "\$VER" != "${VERSION}" ]; then
            echo "Terdeteksi driver mt7663 versi lama (\$VER), mencopot versi lama..."
            dkms remove -m mt7663 -v "\$VER" --all 2>/dev/null || true
        fi
    done
else
    echo "Instalasi bersih terdeteksi (belum ada versi lama di sistem)."
fi

echo "Registering mt7663 (${VERSION}) with DKMS..."
dkms remove -m mt7663 -v ${VERSION} --all 2>/dev/null || true
dkms add -m mt7663 -v ${VERSION}

# Check if kernel header host tools (modpost) match system glibc, self-heal if needed
KERNEL_BUILD_DIR="/lib/modules/\$(uname -r)/build"
MODPOST_BIN="\${KERNEL_BUILD_DIR}/scripts/mod/modpost"
if [ -d "\$KERNEL_BUILD_DIR" ]; then
    if [ -f "\$MODPOST_BIN" ] && ! "\$MODPOST_BIN" -h >/dev/null 2>&1; then
        echo "Menyelaraskan toolchain header kernel (rebuilding modpost untuk glibc lokal)..."
        make -C "\$KERNEL_BUILD_DIR" scripts >/dev/null 2>&1 || true
    fi
fi

dkms build -m mt7663 -v ${VERSION}
dkms install -m mt7663 -v ${VERSION}

echo "Configuring automatic kernel module loading..."
echo wlan_mt7663_sdio > /etc/modules-load.d/wlan_mt7663_sdio.conf
depmod -a
modprobe wlan_mt7663_sdio 2>/dev/null || true

# Apply sysctl and udev performance rules
sysctl -p /etc/sysctl.d/99-wifi-throughput.conf 2>/dev/null || true
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true
/usr/lib/udev/wlan-irq-tune.sh 2>/dev/null || true

# Clean up old external service if present
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload 2>/dev/null || true
    systemctl stop wlan-tune.service 2>/dev/null || true
    systemctl disable wlan-tune.service 2>/dev/null || true
    rm -f /etc/systemd/system/wlan-tune.service 2>/dev/null || true
    systemctl enable mt7663-shutdown.service 2>/dev/null || true
fi
POST
chmod 755 ${BUILD_DIR}/DEBIAN/postinst

cat << PRERM > ${BUILD_DIR}/DEBIAN/prerm
#!/bin/sh
set -e

echo "Removing mt7663 (${VERSION}) from DKMS..."
ip link set wlan0 down 2>/dev/null || true
modprobe -r wlan_mt7663_sdio 2>/dev/null || true
dkms remove -m mt7663 -v ${VERSION} --all 2>/dev/null || true
rm -f /etc/modules-load.d/wlan_mt7663_sdio.conf

if [ -d /run/systemd/system ]; then
    systemctl disable mt7663-shutdown.service 2>/dev/null || true
    systemctl daemon-reload 2>/dev/null || true
fi
PRERM
chmod 755 ${BUILD_DIR}/DEBIAN/prerm

dpkg-deb --build ${BUILD_DIR} ${PACKAGE}_${VERSION}_all.deb
rm -rf ${BUILD_DIR}

echo "Package created successfully: ${PACKAGE}_${VERSION}_all.deb"
