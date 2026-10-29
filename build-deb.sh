#!/bin/bash
set -e

PACKAGE=mt7663-dkms
# Otomatis deteksi versi dari dkms.conf sebagai Single Source of Truth
DEFAULT_VERSION=$(grep -E "^[[:space:]]*PACKAGE_VERSION=" dkms.conf 2>/dev/null | cut -d'"' -f2)
VERSION=${1:-${DEFAULT_VERSION:-1.0.7}}
TARGET_DEB="${PACKAGE}_${VERSION}_all.deb"

# Proteksi Version Lock: Mencegah rebuild pada versi yang sudah dirilis/dikunci
if [ "$FORCE_REBUILD" != "1" ] && [ -f "$TARGET_DEB" ]; then
    if git rev-parse -q --verify "refs/tags/v${VERSION}" >/dev/null 2>&1; then
        echo "======================================================================="
        echo "  [VERSION LOCKED] Rilis v${VERSION} (${TARGET_DEB}) sudah dikunci!"
        echo "  Versi yang sudah dirilis resmi tidak boleh di-build ulang sembarangan."
        echo "  Silakan naikkan versi (bump version) untuk membuat rilis baru."
        echo "  (Gunakan FORCE_REBUILD=1 ./build-deb.sh jika sengaja ingin menimpa)"
        echo "======================================================================="
        exit 0
    fi
fi

BUILD_DIR=/tmp/${PACKAGE}_build
SRC_DIR=${BUILD_DIR}/usr/src/mt7663-${VERSION}

echo "Building Debian package for Release v${VERSION} (${TARGET_DEB})..."

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

dpkg-deb --build ${BUILD_DIR} ${TARGET_DEB}
rm -rf ${BUILD_DIR}

echo "Package created successfully: ${TARGET_DEB}"
