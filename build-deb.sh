#!/bin/bash
set -e

PACKAGE=mt7663-dkms
VERSION=${1:-1.0.6}
BUILD_DIR=/tmp/${PACKAGE}_build
SRC_DIR=${BUILD_DIR}/usr/src/mt7663-${VERSION}

echo "Building Debian package for ${PACKAGE}_${VERSION}..."

rm -rf ${BUILD_DIR}
mkdir -p ${SRC_DIR}
mkdir -p ${BUILD_DIR}/DEBIAN

# 1. Copy pure driver source code directly to /usr/src/mt7663-${VERSION} (no junk)
cp -a chips common include mgmt nic os prealloc Makefile Kconfig dkms.conf CHANGELOG.md README.md ${SRC_DIR}/
sed -i "s/PACKAGE_VERSION=\".*\"/PACKAGE_VERSION=\"${VERSION}\"/" ${SRC_DIR}/dkms.conf
find ${SRC_DIR} -type f \( -name "*.o" -o -name "*.o.d" -o -name "*.cmd" -o -name "*.ko" -o -name "*.mod*" \) -delete

# 2. Copy ALL system integration files at once from unified system/ directory
cp -a system/* ${BUILD_DIR}/
chmod 644 ${BUILD_DIR}/lib/firmware/*
chmod 755 ${BUILD_DIR}/usr/lib/udev/wlan-irq-tune.sh

# 3. Copy Debian package control scripts from debian/ directory
cp -a debian/* ${BUILD_DIR}/DEBIAN/
sed -i "s/^Version:.*/Version: ${VERSION}/" ${BUILD_DIR}/DEBIAN/control
sed -i "s/VERSION=\".*\"/VERSION=\"${VERSION}\"/" ${BUILD_DIR}/DEBIAN/postinst ${BUILD_DIR}/DEBIAN/prerm
chmod 755 ${BUILD_DIR}/DEBIAN/preinst ${BUILD_DIR}/DEBIAN/postinst ${BUILD_DIR}/DEBIAN/prerm

dpkg-deb --build ${BUILD_DIR} ${PACKAGE}_${VERSION}_all.deb
rm -rf ${BUILD_DIR}

echo "Package created successfully: ${PACKAGE}_${VERSION}_all.deb"
