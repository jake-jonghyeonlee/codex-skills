#!/usr/bin/env python3
"""Scaffold a code-map JSON skeleton for a Python project (stdlib only, ast-based).

This does the mechanical part: file listing, symbol extraction, dependency
edges, and six analysis axes:

  1. External dependencies  — stdlib vs third-party classification
  2. Symbol visibility      — public/private tagging, __all__ detection
  3. Complexity metrics     — function count, avg length, max nesting depth
  4. Coupling data          — depends_on edges (fan-in/fan-out computed at render)
  5. Test mapping           — test files → source module mapping
  6. Compatibility          — Python version / platform from pyproject.toml/setup.cfg

It cannot know what any of it *means* — every "role" field is left as "" for
a human (or the code-map skill) to fill in by actually reading the code.

Usage:
    python3 extract_python_symbols.py /path/to/repo > skeleton.json

Then edit skeleton.json: fill in project.purpose, project.features,
project.stack, project.entry_points, and every "role" string, before
handing it to codemap_dashboard.py.
"""

import argparse
import ast
import configparser
import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".opencode"}

_NESTING_TYPES = (ast.If, ast.For, ast.While, ast.With, ast.Try,
                  ast.AsyncFor, ast.AsyncWith)
if sys.version_info >= (3, 11):
    _NESTING_TYPES = _NESTING_TYPES + (ast.TryStar,)


def _stdlib_names():
    if hasattr(sys, "stdlib_module_names"):
        return sys.stdlib_module_names
    import sysconfig
    names = set(sys.builtin_module_names)
    stdlib_dir = Path(sysconfig.get_paths()["stdlib"])
    if stdlib_dir.is_dir():
        for p in stdlib_dir.iterdir():
            if p.suffix == ".py":
                names.add(p.stem)
            elif p.is_dir() and (p / "__init__.py").exists():
                names.add(p.name)
    return frozenset(names)


def _max_nesting(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _NESTING_TYPES):
            best = max(best, _max_nesting(child, depth + 1))
        else:
            best = max(best, _max_nesting(child, depth))
    return best


def _fn_length(node):
    end = getattr(node, "end_lineno", None)
    return (end - node.lineno + 1) if end else 0


def _is_test_file(rel_path):
    name = Path(rel_path).name
    parts = Path(rel_path).parts
    return (name.startswith("test_") or name.endswith("_test.py")
            or "tests" in parts or "test" in parts)


def module_name_for(path, root):
    rel = path.relative_to(root).with_suffix("")
    parts = rel.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def find_py_files(root):
    return sorted(
        p for p in root.rglob("*.py")
        if not any(part in SKIP_DIRS for part in p.parts)
    )


def extract_file(path, root, module_names, name_to_path, stdlib):
    rel = str(path.relative_to(root))
    src = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(src, filename=rel)
    except SyntaxError as e:
        return {
            "path": rel, "role": "", "depends_on": [], "symbols": [],
            "parse_error": str(e),
        }

    # --- imports: internal deps + external deps ---
    internal_dep_paths = set()
    external_imports = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                resolved = name_to_path.get(alias.name) or name_to_path.get(top)
                if resolved and resolved != rel:
                    internal_dep_paths.add(resolved)
                elif not resolved:
                    external_imports[top] = "stdlib" if top in stdlib else "third_party"
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            resolved = name_to_path.get(node.module) or name_to_path.get(top)
            if resolved and resolved != rel:
                internal_dep_paths.add(resolved)
            elif not resolved and (node.level or 0) == 0:
                external_imports[top] = "stdlib" if top in stdlib else "third_party"

    # --- symbols with visibility + complexity metrics ---
    symbols = []
    has_all = False
    fn_lengths = []
    max_nest = 0
    num_functions = 0
    num_classes = 0

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            num_classes += 1
            vis = "private" if node.name.startswith("_") and not node.name.startswith("__") else "public"
            symbols.append({"name": node.name, "kind": "class", "visibility": vis, "role": ""})
            for sub in node.body:
                if not isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                fl = _fn_length(sub)
                if fl:
                    fn_lengths.append(fl)
                max_nest = max(max_nest, _max_nesting(sub))
                if sub.name.startswith("__") and sub.name != "__init__":
                    continue
                vis = "private" if sub.name.startswith("_") and sub.name != "__init__" else "public"
                symbols.append({
                    "name": f"{node.name}.{sub.name}", "kind": "method",
                    "visibility": vis, "role": "",
                })

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fl = _fn_length(node)
            if fl:
                fn_lengths.append(fl)
            max_nest = max(max_nest, _max_nesting(node))
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            num_functions += 1
            vis = "private" if node.name.startswith("_") else "public"
            symbols.append({"name": node.name, "kind": "function", "visibility": vis, "role": ""})

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "__all__":
                        has_all = True
                    elif target.id.isupper():
                        vis = "private" if target.id.startswith("_") else "public"
                        symbols.append({"name": target.id, "kind": "constant", "visibility": vis, "role": ""})

        elif isinstance(node, ast.AnnAssign) and isinstance(getattr(node, "target", None), ast.Name):
            if node.target.id.isupper():
                symbols.append({"name": node.target.id, "kind": "constant", "visibility": "public", "role": ""})

    avg_fn_len = round(sum(fn_lengths) / len(fn_lengths)) if fn_lengths else 0

    return {
        "path": rel,
        "role": "",
        "loc": len(src.splitlines()),
        "depends_on": sorted(internal_dep_paths),
        "has_all": has_all,
        "metrics": {
            "functions": num_functions,
            "classes": num_classes,
            "avg_fn_length": avg_fn_len,
            "max_nesting": max_nest,
        },
        "symbols": symbols,
        "_external_imports": external_imports,
    }


def _build_import_map(tree, name_to_path, self_path, known_symbols):
    name_refs = {}
    module_refs = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                resolved = name_to_path.get(alias.name) or name_to_path.get(top)
                if resolved and resolved != self_path:
                    module_refs[alias.asname or top] = resolved
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            resolved = name_to_path.get(node.module) or name_to_path.get(top)
            if resolved and resolved != self_path:
                for alias in (node.names or []):
                    if alias.name == "*":
                        for sym in known_symbols.get(resolved, set()):
                            if not sym.startswith("_") and "." not in sym:
                                name_refs[sym] = (resolved, sym)
                    else:
                        name_refs[alias.asname or alias.name] = (resolved, alias.name)

    return name_refs, module_refs


def _find_refs_in_func(func_node, name_refs, module_refs, known_symbols):
    refs = set()

    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and node.id in name_refs:
            path, orig = name_refs[node.id]
            if orig in known_symbols.get(path, set()):
                refs.add(f"{path}::{orig}")

        elif isinstance(node, ast.Attribute):
            val = node.value
            if isinstance(val, ast.Name) and val.id in module_refs:
                path = module_refs[val.id]
                if node.attr in known_symbols.get(path, set()):
                    refs.add(f"{path}::{node.attr}")
            elif isinstance(val, ast.Name) and val.id in name_refs:
                path, orig = name_refs[val.id]
                qualified = f"{orig}.{node.attr}"
                if qualified in known_symbols.get(path, set()):
                    refs.add(f"{path}::{qualified}")
            elif (isinstance(val, ast.Attribute) and
                  isinstance(val.value, ast.Name) and
                  val.value.id in module_refs):
                path = module_refs[val.value.id]
                qualified = f"{val.attr}.{node.attr}"
                if qualified in known_symbols.get(path, set()):
                    refs.add(f"{path}::{qualified}")

    return sorted(refs) if refs else None


def _extract_refs(py_files, root, modules, name_to_path):
    known_symbols = {}
    for m in modules:
        known_symbols[m["path"]] = {s["name"] for s in m.get("symbols", [])}

    for path, m in zip(py_files, modules):
        if "parse_error" in m:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, filename=m["path"])
        except SyntaxError:
            continue

        name_refs, module_refs = _build_import_map(tree, name_to_path, m["path"], known_symbols)
        if not name_refs and not module_refs:
            continue

        sym_by_name = {s["name"]: s for s in m.get("symbols", [])}

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        key = f"{node.name}.{sub.name}"
                        if key in sym_by_name:
                            refs = _find_refs_in_func(sub, name_refs, module_refs, known_symbols)
                            if refs:
                                sym_by_name[key]["refs"] = refs
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in sym_by_name:
                    refs = _find_refs_in_func(node, name_refs, module_refs, known_symbols)
                    if refs:
                        sym_by_name[node.name]["refs"] = refs


def extract_compatibility(root):
    compat = {}

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            if tomllib is not None:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                proj = data.get("project", {})
                if "requires-python" in proj:
                    compat["python_requires"] = proj["requires-python"]
                opt = proj.get("optional-dependencies", {})
                if opt:
                    compat["optional_groups"] = {k: list(v) for k, v in opt.items()}
            else:
                text = pyproject.read_text(encoding="utf-8", errors="replace")
                m = re.search(r'requires-python\s*=\s*"([^"]*)"', text)
                if m:
                    compat["python_requires"] = m.group(1)
        except Exception:
            pass
        if compat:
            compat["source"] = "pyproject.toml"

    if not compat:
        setup_cfg = root / "setup.cfg"
        if setup_cfg.exists():
            try:
                cfg = configparser.ConfigParser()
                cfg.read(str(setup_cfg), encoding="utf-8")
                if cfg.has_option("options", "python_requires"):
                    compat["python_requires"] = cfg.get("options", "python_requires")
                if cfg.has_section("options.extras_require"):
                    compat["optional_groups"] = dict(cfg.items("options.extras_require"))
                if compat:
                    compat["source"] = "setup.cfg"
            except Exception:
                pass

    return compat or None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", help="path to the project root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    py_files = find_py_files(root)
    stdlib = _stdlib_names()

    name_to_path = {}
    for p in py_files:
        name_to_path[module_name_for(p, root)] = str(p.relative_to(root))
    module_names = set(name_to_path)

    modules = [extract_file(p, root, module_names, name_to_path, stdlib) for p in py_files]

    # --- aggregate external deps ---
    all_external = {}
    for m in modules:
        for name, cat in m.pop("_external_imports", {}).items():
            if name not in all_external:
                all_external[name] = {"name": name, "category": cat, "used_by": []}
            all_external[name]["used_by"].append(m["path"])
    external_deps = sorted(all_external.values(), key=lambda x: (x["category"], x["name"]))

    # --- test mapping ---
    test_paths = {m["path"] for m in modules if _is_test_file(m["path"])}
    for m in modules:
        if m["path"] not in test_paths:
            testers = [t["path"] for t in modules
                       if t["path"] in test_paths and m["path"] in (t.get("depends_on") or [])]
            if testers:
                m["tested_by"] = testers

    # --- cross-module refs (second pass) ---
    _extract_refs(py_files, root, modules, name_to_path)

    # --- compatibility ---
    compat = extract_compatibility(root)

    skeleton = {
        "project": {
            "name": root.name,
            "purpose": "",
            "features": [],
            "stack": [],
            "entry_points": [],
            "how_to_run": "",
        },
        "external_deps": external_deps,
        "modules": modules,
    }
    if compat:
        skeleton["compatibility"] = compat

    json.dump(skeleton, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
