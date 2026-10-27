#!/usr/bin/env python3
"""Verify the agent-skills environment: Python packages, skill folders (.agents/skills required,
optional/skills reported), bundled assets without external URLs, and the local Chrome/Edge
headless PDF path. Read-only except for files written under a temp dir.

Run inside .venv-skills:  python -I scripts/verify_skills.py [--chrome PATH] [--strict]
Exit code 0 = all required checks passed; 1 = a required check failed.
Optional checks (optional/skills packages, Chrome PDF, ppt-master integrity) are reported
but only fail when --strict is given.
"""
from __future__ import annotations

import argparse
import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents" / "skills"
OPTIONAL_SKILLS = ROOT / "optional" / "skills"

# module name -> skills that need it (required: .agents/skills)
REQUIRED_MODULES = {
    "PIL": "archscribe",
    "numpy": "matplotlib, archscribe",
    "svg.path": "archscribe",
    "matplotlib": "matplotlib",
    "pymupdf": "html-to-pdf",
    "websocket": "html-to-pdf",
    "reportlab": "pdf",
    "pdfplumber": "pdf",
    "pypdf": "pdf",
    "hypothesis": "property-based-testing",
}
# optional/skills dependencies (reported; fail only with --strict)
OPTIONAL_MODULES = {
    "yaml": "ppt-master",
    "pptx": "ppt-master",
    "xlsxwriter": "ppt-master",
    "pathops": "ppt-master",
    "uharfbuzz": "ppt-master",
    "polars": "polars",
}

# external asset references that would break on an air-gapped host
EXTERNAL_ASSET = re.compile(r'(?:src|href)=["\']https?://', re.I)
ASSET_SUFFIXES = {".html", ".css", ".js", ".py"}

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
]

TEST_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>verify</title>
<style>body{font-family:"Segoe UI","Malgun Gothic",sans-serif;margin:40px}h1{color:#2f6fdb}</style>
</head><body><h1>agent-skills verify</h1><p>한글 렌더링 확인 — self-contained HTML, no network.</p></body></html>"""


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).is_file() else None
    for c in BROWSER_CANDIDATES:
        if c and Path(c).is_file():
            return c
    for name in ("chrome", "google-chrome", "msedge", "chromium"):
        found = shutil.which(name)
        if found:
            return found
    return None


def check_modules(modules: dict[str, str]) -> list[tuple[str, bool, str]]:
    rows = []
    for mod, users in modules.items():
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, "__version__", getattr(m, "version", ""))
            rows.append((f"import {mod}", True, f"{ver} ({users})"))
        except Exception as exc:  # noqa: BLE001 - report any import failure
            rows.append((f"import {mod}", False, f"{type(exc).__name__}: {exc} ({users})"))
    return rows


def check_skill_folders(skills: Path, label: str) -> list[tuple[str, bool, str]]:
    rows = []
    if not skills.is_dir():
        return [(f"{label} dir", False, f"{skills} missing")]
    names: dict[str, Path] = {}
    for skill_md in sorted(skills.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        name = ""
        if text.startswith("---"):
            for line in text.split("\n")[1:40]:
                if line.startswith("---"):
                    break
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("\"'")
        ok = bool(name)
        dup = name in names
        names.setdefault(name, skill_md.parent)
        rows.append((f"{label} {skill_md.parent.name}", ok and not dup,
                     "duplicate name" if dup else (f"name={name}" if ok else "missing name: frontmatter")))
    return rows


def check_offline_assets(skills: Path) -> tuple[str, bool, str]:
    """No <script src>/<link href>/src= pointing at http(s) inside bundled HTML/CSS/JS/Python."""
    hits = []
    for f in skills.rglob("*"):
        if f.suffix not in ASSET_SUFFIXES or not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if EXTERNAL_ASSET.search(text):
            hits.append(str(f.relative_to(ROOT)))
    return ("offline assets", not hits, "no external src/href" if not hits else ", ".join(hits[:5]))


def check_ppt_master_guard(python: str) -> tuple[str, bool, str] | None:
    guard = OPTIONAL_SKILLS / "ppt-master" / "scripts" / "attribution_guard.py"
    if not guard.is_file():
        return None
    r = subprocess.run([python, "-I", str(guard)], capture_output=True, text=True, check=False)
    return ("ppt-master attribution_guard", r.returncode == 0, (r.stdout + r.stderr).strip()[-200:] or "ok")


def check_chrome_pdf(browser: str | None) -> tuple[str, bool, str]:
    if not browser:
        return ("chrome headless pdf", False, "Chrome/Edge not found (set CHROME_PATH or pass --chrome)")
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "verify.html"
        pdf = Path(tmp) / "verify.pdf"
        html.write_text(TEST_HTML, encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
               f"--print-to-pdf={pdf}", html.as_uri()]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        except subprocess.TimeoutExpired:
            return ("chrome headless pdf", False, f"timeout: {browser}")
        if pdf.is_file() and pdf.stat().st_size > 0:
            return ("chrome headless pdf", True, f"{pdf.stat().st_size} bytes via {browser}")
        return ("chrome headless pdf", False, f"no PDF written by {browser} (policy or sandbox?)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chrome", default=None)
    ap.add_argument("--strict", action="store_true", help="optional checks also fail the run")
    a = ap.parse_args(argv)

    required = [("python 3.12", sys.version_info[:2] == (3, 12), sys.version.split()[0])]
    required += check_modules(REQUIRED_MODULES)
    required += check_skill_folders(SKILLS, "skill")
    required.append(check_offline_assets(SKILLS))
    optional = check_modules(OPTIONAL_MODULES)
    optional += check_skill_folders(OPTIONAL_SKILLS, "optional")
    optional.append(check_chrome_pdf(find_browser(a.chrome)))
    guard = check_ppt_master_guard(sys.executable)
    if guard:
        optional.append(guard)

    width = max(len(r[0]) for r in required + optional)
    print("required")
    for name, ok, note in required:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {note}")
    print("optional")
    for name, ok, note in optional:
        print(f"  [{'PASS' if ok else 'WARN'}] {name.ljust(width)}  {note}")

    failed = [r for r in required if not r[1]]
    if a.strict:
        failed += [r for r in optional if not r[1]]
    print(f"\n{'OK' if not failed else 'FAILED'}: {len(failed)} failing check(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
