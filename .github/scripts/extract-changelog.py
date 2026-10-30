#!/usr/bin/env python3
import sys
import os
import re

version = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('VERSION', '')
if version.startswith('v'):
    version = version[1:]

changelog_path = 'CHANGELOG.md'
if not os.path.exists(changelog_path):
    print(f"### Release v{version}\n")
    sys.exit(0)

text = open(changelog_path, 'r', encoding='utf-8').read()

# 1. Try exact version match
pattern = r'## \[' + re.escape(version) + r'\][^\n]*\n(.*?)(?=\n## \[|\Z)'
m = re.search(pattern, text, re.DOTALL)

# 2. Fallback to base version (e.g. 1.0.8 for 1.0.8-rc1)
if not m:
    base_version = re.split(r'[-~]', version)[0]
    pattern = r'## \[' + re.escape(base_version) + r'\][^\n]*\n(.*?)(?=\n## \[|\Z)'
    m = re.search(pattern, text, re.DOTALL)

if m:
    print(f"### Changes in v{version}:\n\n" + m.group(1).strip() + "\n")
else:
    print(f"### Release v{version}\n")
