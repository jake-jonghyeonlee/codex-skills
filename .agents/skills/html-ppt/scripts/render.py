#!/usr/bin/env python3
"""html-ppt :: render.py — headless Chrome/Edge screenshot(s) (cross-platform port of render.sh).

Usage:
    python scripts/render.py <html-file>                    # one PNG, slide 1
    python scripts/render.py <html-file> <N>                # N PNGs, slides 1..N, via #/k
    python scripts/render.py <html-file> all                # autodetect .slide count
    python scripts/render.py <html-file> <N> <out-dir>      # custom output dir
Options:
    --size WxH      viewport, default 1920x1080 (use 1242x1660 for 3:4)
    --chrome PATH   explicit browser executable (or set CHROME_PATH)

Requires Google Chrome, Microsoft Edge or Chromium installed locally. No network.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BROWSER_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

SLIDE_RE = re.compile(r'<section[^>]*class="([^"]*\s)?slide(\s[^"]*)?"')


def find_browser(explicit: str | None) -> str:
    if explicit:
        if Path(explicit).is_file():
            return explicit
        sys.exit(f"error: browser not found: {explicit}")
    for c in BROWSER_CANDIDATES:
        if c and Path(c).is_file():
            return c
    for name in ("chrome", "google-chrome", "msedge", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    sys.exit("error: Chrome/Edge not found. Pass --chrome PATH or set CHROME_PATH")


def render_one(browser: str, url: str, target: Path, size: str) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        "--virtual-time-budget=4000",
        f"--window-size={size.replace('x', ',')}",
        f"--screenshot={target}",
        url,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    # Chrome reports success even when it could not write the file; trust only the file.
    ok = target.is_file() and target.stat().st_size > 0
    print(("  ok   " if ok else "  FAIL ") + str(target))
    return ok


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("count", nargs="?", default="1", help="slide count or 'all'")
    ap.add_argument("out", nargs="?", default=None, help="output dir (or .png path when count is 1)")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--chrome", default=None)
    a = ap.parse_args(argv)

    html = Path(a.html).resolve()
    if not html.is_file():
        sys.exit(f"error: {html} not found")
    if not re.fullmatch(r"\d+x\d+", a.size):
        sys.exit("error: --size must look like 1920x1080")
    browser = find_browser(a.chrome)
    stem = html.stem

    if a.count == "all":
        count = len(SLIDE_RE.findall(html.read_text(encoding="utf-8", errors="ignore")))
        if count < 1:
            print('warning: no <section class="slide"> found — rendering 1 page', file=sys.stderr)
            count = 1
    elif a.count.isdigit() and int(a.count) >= 1:
        count = int(a.count)
    else:
        sys.exit(f"error: slide count must be a positive integer or 'all' (got: {a.count})")

    url = html.as_uri()
    failed = 0
    if count == 1:
        if a.out is None:
            target = html.with_suffix(".png")
        elif a.out.lower().endswith(".png"):
            target = Path(a.out)
        else:
            target = Path(a.out) / f"{stem}.png"
        failed += not render_one(browser, url, target, a.size)
    else:
        out_dir = Path(a.out) if a.out else html.parent / f"{stem}-png"
        for i in range(1, count + 1):
            failed += not render_one(browser, f"{url}#/{i}", out_dir / f"{stem}_{i:02d}.png", a.size)

    if failed:
        print(f"error: {failed} of {count} slide(s) were not written from {html}", file=sys.stderr)
        return 1
    print(f"done: rendered {count} slide(s) from {html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
