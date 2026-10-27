#!/usr/bin/env python3
"""html-ppt :: new_deck.py — scaffold a new deck from a template (cross-platform port of new-deck.sh).

Usage:
    python scripts/new_deck.py <name> [output-parent-dir] [-t <template>]

Creates <parent>/<name>/index.html with the asset references rewritten so they
resolve from wherever the deck actually lands — at any depth, inside the skill
tree or outside it. Then verifies that every local href/src/url() reference in
the generated files resolves to a real file.

    <output-parent-dir>  absolute, or relative to the current directory.
                         Defaults to <skill>/examples.
    -t, --template       "deck" (default), a full-deck name (e.g. pitch-deck),
                         a single-page name (e.g. arch-diagram), or a path to
                         any .html file / full-deck directory.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent.parent  # skill root

ASSET_REF = re.compile(r"""(["'(])(\.\./)*assets/""")
LOCAL_REF = re.compile(r"""(?:href|src)=(?:"([^"]*)"|'([^']*)')|url\(([^)]*)\)""")


def resolve_template(arg: str) -> Path | None:
    cand = Path(arg)
    if cand.exists():
        return cand.resolve()
    if arg == "deck" and (HERE / "templates" / "deck.html").is_file():
        return HERE / "templates" / "deck.html"
    if (HERE / "templates" / "full-decks" / arg).is_dir():
        return HERE / "templates" / "full-decks" / arg
    if (HERE / "templates" / "single-page" / f"{arg}.html").is_file():
        return HERE / "templates" / "single-page" / f"{arg}.html"
    if (HERE / "templates" / arg).is_file():
        return HERE / "templates" / arg
    return None


def rel_prefix(target: Path, base: Path) -> str:
    """Relative path from base (deck dir) to target (skill root), POSIX separators for HTML.
    Falls back to an absolute file path when the two live on different Windows drives."""
    try:
        rel = os.path.relpath(target, base)
    except ValueError:  # different drive letters: no relative path exists
        return target.as_uri()
    return PurePosixPath(*Path(rel).parts).as_posix() if rel != "." else "."


def rewrite_assets(path: Path, prefix: str) -> None:
    text = path.read_text(encoding="utf-8")
    new = ASSET_REF.sub(lambda m: f"{m.group(1)}{prefix}/assets/", text)
    if new != text:
        path.write_text(new, encoding="utf-8")


def local_refs(path: Path) -> set[str]:
    refs: set[str] = set()
    for m in LOCAL_REF.finditer(path.read_text(encoding="utf-8", errors="ignore")):
        ref = next(g for g in m.groups() if g is not None).strip().strip("\"'")
        ref = re.split(r"[?#]", ref, maxsplit=1)[0]
        if not ref or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^//", ref):
            continue
        refs.add(ref)
    return refs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("parent", nargs="?", default=None)
    ap.add_argument("-t", "--template", default="deck")
    a = ap.parse_args(argv)

    template = resolve_template(a.template)
    if template is None:
        full = sorted(p.name for p in (HERE / "templates" / "full-decks").glob("*") if p.is_dir())
        print(f"error: no template named '{a.template}'", file=sys.stderr)
        print(f"  full-decks:  {' '.join(full)}", file=sys.stderr)
        print(f"  single-page: see {HERE / 'templates' / 'single-page'}", file=sys.stderr)
        return 1

    parent = (HERE / "examples") if a.parent is None else Path(a.parent).resolve()
    out_dir = parent / a.name
    if out_dir.exists():
        print(f"error: {out_dir} already exists", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True)
    out_dir = out_dir.resolve()

    prefix = rel_prefix(HERE, out_dir)
    if template.is_dir():
        shutil.copytree(template, out_dir, dirs_exist_ok=True)
        files = [p for p in out_dir.rglob("*") if p.suffix in {".html", ".css", ".js"}]
    else:
        shutil.copy2(template, out_dir / "index.html")
        files = [out_dir / "index.html"]
    for f in files:
        rewrite_assets(f, prefix)

    if not (out_dir / "index.html").is_file():
        print(f"error: template produced no index.html in {out_dir}", file=sys.stderr)
        return 1

    missing = 0
    checked = 0
    for f in files:
        for ref in local_refs(f):
            checked += 1
            target = (f.parent / ref).resolve()
            if not target.exists():
                missing += 1
                print(f"  missing: {f.relative_to(out_dir)} -> {ref}", file=sys.stderr)
    if missing:
        print(f"error: {missing} of {checked} local reference(s) do not resolve", file=sys.stderr)
        return 1
    print(f"created {out_dir / 'index.html'} (asset prefix: {prefix}/assets/, {checked} references verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
