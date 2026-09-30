"""Builds the .nvda-addon package from the addon folder.

Usage: python build.py
Writes NVDAAnnounceYears-<version>.nvda-addon next to this script.
"""
import re
import zipfile
from pathlib import Path

root = Path(__file__).parent
addonDir = root / "addon"
manifest = (addonDir / "manifest.ini").read_text(encoding="utf-8")
name = re.search(r"^name\s*=\s*(\S+)", manifest, re.M).group(1)
version = re.search(r"^version\s*=\s*(\S+)", manifest, re.M).group(1)
outPath = root / f"{name}-{version}.nvda-addon"

with zipfile.ZipFile(outPath, "w", zipfile.ZIP_DEFLATED) as z:
	for path in sorted(addonDir.rglob("*")):
		if path.is_dir() or "__pycache__" in path.parts or path.suffix == ".pyc":
			continue
		z.write(path, path.relative_to(addonDir).as_posix())
print(outPath.name)
