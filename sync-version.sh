#!/usr/bin/env python3
"""
MediaTek MT7663 Driver Release Version Synchronization Script
Atomically synchronizes version strings across dkms.conf, debian packaging, build scripts, and READMEs.
"""

import sys
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

def get_current_version():
    dkms_path = REPO_ROOT / "dkms.conf"
    if dkms_path.exists():
        with open(dkms_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\s*PACKAGE_VERSION="([^"]+)"', line)
                if m:
                    return m.group(1)
    return None

def update_file(path, pattern, replacement):
    if not path.exists():
        return False
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    new_content, count = re.subn(pattern, replacement, content)
    if count > 0:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False

def main():
    target_ver = sys.argv[1] if len(sys.argv) > 1 else None
    if not target_ver:
        target_ver = get_current_version()
    
    if not target_ver:
        print("[ERROR] No target version specified and unable to detect from dkms.conf.", file=sys.stderr)
        print("Usage: ./sync-version.sh <version> (e.g. ./sync-version.sh 1.0.12)", file=sys.stderr)
        sys.exit(1)

    target_ver = target_ver.lstrip("v")
    print("=" * 65)
    print(f" Synchronizing MT7663 Release Version -> v{target_ver}")
    print("=" * 65)

    # 1. dkms.conf
    dkms_file = REPO_ROOT / "dkms.conf"
    if update_file(dkms_file, r'PACKAGE_VERSION="[^"]+"', f'PACKAGE_VERSION="{target_ver}"'):
        print(f" [OK] dkms.conf -> PACKAGE_VERSION=\"{target_ver}\"")

    # 2. debian/control
    ctrl_file = REPO_ROOT / "debian" / "control"
    if update_file(ctrl_file, r'(?m)^Version:\s*.+$', f'Version: {target_ver}'):
        print(f" [OK] debian/control -> Version: {target_ver}")

    # 3. debian/postinst & debian/prerm
    postinst_file = REPO_ROOT / "debian" / "postinst"
    if update_file(postinst_file, r'(?m)^VERSION="[^"]+"', f'VERSION="{target_ver}"'):
        print(f" [OK] debian/postinst -> VERSION=\"{target_ver}\"")

    prerm_file = REPO_ROOT / "debian" / "prerm"
    if update_file(prerm_file, r'(?m)^VERSION="[^"]+"', f'VERSION="{target_ver}"'):
        print(f" [OK] debian/prerm -> VERSION=\"{target_ver}\"")

    # 4. build-deb.sh
    build_file = REPO_ROOT / "build-deb.sh"
    if update_file(build_file, r'DEFAULT_VERSION:-[0-9.]+', f'DEFAULT_VERSION:-{target_ver}'):
        print(f" [OK] build-deb.sh -> DEFAULT_VERSION:-{target_ver}")

    # 5. README.md & README.id.md
    for readme_name in ["README.md", "README.id.md"]:
        readme_path = REPO_ROOT / readme_name
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                text = f.read()

            # Package download link
            text = re.sub(
                r'(releases/download/)v[0-9.]+(?:-[a-zA-Z0-9.]+)?/mt7663-dkms_[0-9.]+(?:-[a-zA-Z0-9.]+)?_all\.deb',
                rf'\g<1>v{target_ver}/mt7663-dkms_{target_ver}_all.deb',
                text
            )
            # DTB download link (non-capturing prerelease group, capturing filename group)
            text = re.sub(
                r'(releases/download/)v[0-9.]+(?:-[a-zA-Z0-9.]+)?/(meson-g12a-hg680-fj[^\s()]+\.dtb)',
                rf'\g<1>v{target_ver}/\2',
                text
            )
            # dpkg command
            text = re.sub(
                r'mt7663-dkms_[0-9.]+(?:-[a-zA-Z0-9.]+)?_all\.deb',
                f'mt7663-dkms_{target_ver}_all.deb',
                text
            )
            # Header version indicator
            text = re.sub(
                r'\(v[0-9.]+(?:-[a-zA-Z0-9.]+)?\)',
                f'(v{target_ver})',
                text
            )

            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f" [OK] {readme_name} -> synchronized to v{target_ver}")

    print("=" * 65)
    print(" Synchronization complete! Verification:")
    print(f" - dkms.conf:        PACKAGE_VERSION=\"{get_current_version()}\"")
    print("=" * 65)

if __name__ == "__main__":
    main()
