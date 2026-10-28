#!/bin/bash
set -e

PACKAGE=mt7663-dkms
VERSION=1.0.2
BUILD_DIR=/tmp/${PACKAGE}_build
SRC_DIR=${BUILD_DIR}/usr/src/mt7663-${VERSION}

echo "Building Debian package for ${PACKAGE}_${VERSION}..."

rm -rf ${BUILD_DIR}
mkdir -p ${SRC_DIR}
mkdir -p ${BUILD_DIR}/DEBIAN
mkdir -p ${BUILD_DIR}/etc/modprobe.d
mkdir -p ${BUILD_DIR}/etc/systemd/system
mkdir -p ${BUILD_DIR}/etc/udev/rules.d
mkdir -p ${BUILD_DIR}/etc/sysctl.d
mkdir -p ${BUILD_DIR}/lib/firmware

# Copy source tree to /usr/src/mt7663-${VERSION} for DKMS
rsync -a --exclude=".git" --exclude="system" --exclude="*.o" --exclude="*.ko" --exclude="*.mod" --exclude="*.mod.c" --exclude="*.cmd" --exclude="*.deb" ./ ${SRC_DIR}/

# Copy system configurations, services, rules, and firmware
cp system/etc/modprobe.d/blacklist-mt7663-bluetooth.conf ${BUILD_DIR}/etc/modprobe.d/
cp system/etc/systemd/system/* ${BUILD_DIR}/etc/systemd/system/
cp system/etc/udev/rules.d/* ${BUILD_DIR}/etc/udev/rules.d/
cp system/etc/sysctl.d/* ${BUILD_DIR}/etc/sysctl.d/
cp system/lib/firmware/* ${BUILD_DIR}/lib/firmware/
chmod 644 ${BUILD_DIR}/lib/firmware/*

cat << 'CTRL' > ${BUILD_DIR}/DEBIAN/control
Package: mt7663-dkms
Version: 1.0.2
Architecture: all
Maintainer: Van der Decken <root@hermes>
Depends: dkms, build-essential
Section: kernel
Priority: optional
Description: MediaTek MT7663 SDIO Wi-Fi driver module (DKMS)
 Patched high-performance Linux driver for MediaTek MT7663 SDIO Wi-Fi,
 tuned for Linux 6.12+ with multi-core RPS, IRQ affinity, and underflow fast-path.
CTRL

cat << 'POST' > ${BUILD_DIR}/DEBIAN/postinst
#!/bin/sh
set -e

echo "Registering mt7663 (1.0.2) with DKMS..."
dkms remove -m mt7663 -v 1.0.2 --all 2>/dev/null || true
dkms add -m mt7663 -v 1.0.2 || true
dkms build -m mt7663 -v 1.0.2 || true
dkms install -m mt7663 -v 1.0.2 || true

echo "Configuring automatic kernel module loading..."
echo wlan_mt7663_sdio > /etc/modules-load.d/wlan_mt7663_sdio.conf
depmod -a
modprobe wlan_mt7663_sdio 2>/dev/null || true

# Apply sysctl and udev performance rules
sysctl -p /etc/sysctl.d/99-wifi-throughput.conf 2>/dev/null || true
udevadm control --reload-rules 2>/dev/null || true
udevadm trigger 2>/dev/null || true

# Enable services
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload 2>/dev/null || true
    systemctl enable mt7663-shutdown.service 2>/dev/null || true
    systemctl enable wlan-tune.service 2>/dev/null || true
    systemctl restart wlan-tune.service 2>/dev/null || true
fi
POST
chmod 755 ${BUILD_DIR}/DEBIAN/postinst

cat << 'PRE' > ${BUILD_DIR}/DEBIAN/prerm
#!/bin/sh
set -e

echo "Removing mt7663 (1.0.2) from DKMS..."
ip link set wlan0 down 2>/dev/null || true
modprobe -r wlan_mt7663_sdio 2>/dev/null || true
dkms remove -m mt7663 -v 1.0.2 --all 2>/dev/null || true
rm -f /etc/modules-load.d/wlan_mt7663_sdio.conf

if [ -d /run/systemd/system ]; then
    systemctl disable mt7663-shutdown.service 2>/dev/null || true
    systemctl disable wlan-tune.service 2>/dev/null || true
    systemctl daemon-reload 2>/dev/null || true
fi
PRE
chmod 755 ${BUILD_DIR}/DEBIAN/prerm

dpkg-deb --build ${BUILD_DIR} ${PACKAGE}_${VERSION}_all.deb
rm -rf ${BUILD_DIR}

echo "Package created successfully: ${PACKAGE}_${VERSION}_all.deb"
