#!/usr/bin/env python3
"""Project JSON -> self-contained HTML "code map" dashboard.

This is a comprehension tool, not an audit tool: no findings, no severity,
no bug-hunting. It answers "what does this code do and how is it put
together" for someone encountering an unfamiliar repo, read-only.

Usage:
    python3 codemap_dashboard.py project.json -o codemap.html
    python3 codemap_dashboard.py --example > project.json

No dependencies beyond the standard library. The output HTML embeds its
data, CSS and JS inline (no CDN, no fetch()) so it opens correctly from a
plain `file://` path -- e.g. after being carried into a closed network via
git. The dependency diagram is hand-drawn SVG computed in-browser from
`depends_on` edges -- no charting library.

Project JSON schema:

{
  "project": {
    "name": "my-project",
    "purpose": "1-2 paragraphs: what this project does, for someone who has never seen it",
    "features": ["one line per user-facing feature/capability"],
    "stack": [
      "Python 3.11",
      {"name": "pygame", "note": "rendering + input"}
    ],
    "entry_points": ["main.py"],
    "how_to_run": "python3 main.py"
  },
  "external_deps": [
    {"name": "pygame", "category": "third_party", "used_by": ["main.py"]}
  ],
  "compatibility": {
    "python_requires": ">=3.8",
    "platforms": [],
    "optional_groups": {"dev": ["pytest"]},
    "source": "pyproject.toml"
  },
  "modules": [
    {
      "path": "game.py",
      "role": "one or more sentences: this module's responsibility",
      "loc": 145,
      "depends_on": ["board.py", "tetromino.py"],
      "has_all": false,
      "metrics": {
        "functions": 3,
        "classes": 1,
        "avg_fn_length": 12,
        "max_nesting": 2
      },
      "tested_by": ["test_game.py"],
      "symbols": [
        {"name": "Game", "kind": "class", "visibility": "public", "role": "one line"},
        {"name": "Game.rotate", "kind": "method", "visibility": "public", "role": "..."},
        {"name": "Game._move", "kind": "method", "visibility": "private", "role": "..."}
      ]
    }
  ]
}
"""

import argparse
import json
import sys

REQUIRED_MODULE_FIELDS = ["path", "role"]


def validate(data):
    errors = []
    project = data.get("project", {})
    if not project.get("name"):
        errors.append("project.name is missing")
    if not project.get("purpose"):
        errors.append("project.purpose is missing")

    for i, s in enumerate(project.get("stack", [])):
        if isinstance(s, dict) and not s.get("name"):
            errors.append(f"project.stack[{i}] is an object but missing 'name'")
        elif not isinstance(s, (str, dict)):
            errors.append(f"project.stack[{i}] must be a string or {{name, note}} object")

    modules = data.get("modules")
    if not isinstance(modules, list):
        errors.append("modules must be a list")
        modules = []

    known_paths = {m.get("path") for m in modules if isinstance(m, dict)}

    for i, m in enumerate(modules):
        for f in REQUIRED_MODULE_FIELDS:
            if not m.get(f):
                errors.append(f"modules[{i}].{f} is missing")
        for dep in m.get("depends_on", []):
            if dep not in known_paths:
                errors.append(f"modules[{i}].depends_on references unknown module '{dep}'")
        for j, sym in enumerate(m.get("symbols", [])):
            if not sym.get("name"):
                errors.append(f"modules[{i}].symbols[{j}].name is missing")

    if errors:
        raise ValueError("invalid project JSON:\n  - " + "\n  - ".join(errors))


EXAMPLE_DATA = {
    "project": {
        "name": "my-project",
        "purpose": "이 프로젝트가 무엇을 하는지, 처음 보는 사람 기준으로 1~2문단.",
        "features": ["사용자 관점에서 이 프로젝트가 하는 일, 한 줄씩"],
        "stack": [{"name": "Python 3.11", "note": "표준 라이브러리만 사용"}],
        "entry_points": ["main.py"],
        "how_to_run": "python3 main.py",
    },
    "external_deps": [
        {"name": "requests", "category": "third_party", "used_by": ["main.py"]},
    ],
    "compatibility": {
        "python_requires": ">=3.8",
        "source": "pyproject.toml",
    },
    "modules": [
        {
            "path": "src/example.py",
            "role": "이 모듈의 책임을 한두 문장으로.",
            "loc": 42,
            "depends_on": [],
            "has_all": False,
            "metrics": {"functions": 2, "classes": 1, "avg_fn_length": 10, "max_nesting": 2},
            "tested_by": ["tests/test_example.py"],
            "symbols": [
                {"name": "ExampleClass", "kind": "class", "visibility": "public", "role": "한 줄 설명"},
                {"name": "ExampleClass.run", "kind": "method", "visibility": "public", "role": "한 줄 설명"},
            ],
        }
    ],
}


def render(data):
    json_blob = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return (
        HTML_TEMPLATE
        .replace("__PROJECT_NAME__", data["project"]["name"])
        .replace("__CODEMAP_DATA_JSON__", json_blob)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", help="project JSON file ('-' for stdin)")
    parser.add_argument("-o", "--output", help="output HTML path (default: <project>-codemap.html)")
    parser.add_argument("--example", action="store_true", help="print an example project JSON to stdout and exit")
    args = parser.parse_args()

    if args.example:
        json.dump(EXAMPLE_DATA, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    if not args.input:
        parser.error("input is required unless --example is given")

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    try:
        data = json.loads(raw)
        validate(data)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or f"{data['project']['name']}-codemap.html"
    html = render(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {output_path}")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PROJECT_NAME__ — 코드 맵</title>
<style>
  :root {
    --bg: #f3f4f7;
    --bg-card: #ffffff;
    --bg-subtle: #eef0f3;
    --bg-raised: #fbfbfd;
    --border: #dde1e6;
    --text: #1a1d23;
    --text-dim: #5b6270;
    --accent: #2f5fda;
    --accent-bg: #eaf0ff;
    --class-color: #7a3fd1;
    --class-bg: #f2eaff;
    --fn-color: #1f8a4c;
    --fn-bg: #e9f7ef;
    --const-color: #a15c00;
    --const-bg: #fdf3e2;
    --priv-color: #8a8f9a;
    --priv-bg: #f0f1f3;
    --test-color: #0e7c3a;
    --test-bg: #e6f5ec;
    --warn-color: #b45309;
    --warn-bg: #fef3cd;
    --cat-entry: #2f5fda; --cat-entry-bg: #e0eaff; --cat-entry-border: #a0bcf8;
    --cat-core: #7a3fd1; --cat-core-bg: #f0e6ff; --cat-core-border: #c4a0f0;
    --cat-base: #1f8a4c; --cat-base-bg: #e2f5ea; --cat-base-border: #8fd4a8;
    --cat-test: #6b7280; --cat-test-bg: #f0f1f3; --cat-test-border: #c0c5cc;
    --shadow: 0 1px 2px rgba(20, 22, 30, 0.04), 0 1px 8px rgba(20, 22, 30, 0.03);
    --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Pretendard, "Noto Sans KR", sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #121317; --bg-card: #1c1f26; --bg-subtle: #22262e; --bg-raised: #20232a;
      --border: #2c313a; --text: #e7e9ee; --text-dim: #9aa2b1;
      --accent: #7da3ff; --accent-bg: #1c2740;
      --class-color: #c298ff; --class-bg: #29203f;
      --fn-color: #5fd08a; --fn-bg: #12291c;
      --const-color: #f0b357; --const-bg: #382a11;
      --priv-color: #6e7480; --priv-bg: #1e2028;
      --test-color: #4ade80; --test-bg: #0f2818;
      --warn-color: #fbbf24; --warn-bg: #3b2e0a;
      --cat-entry: #7da3ff; --cat-entry-bg: #1c2740; --cat-entry-border: #3b5a9e;
      --cat-core: #c298ff; --cat-core-bg: #29203f; --cat-core-border: #6b4a9e;
      --cat-base: #5fd08a; --cat-base-bg: #12291c; --cat-base-border: #2a6b40;
      --cat-test: #9aa2b1; --cat-test-bg: #22262e; --cat-test-border: #3a3f4a;
      --shadow: 0 1px 2px rgba(0, 0, 0, 0.25), 0 1px 10px rgba(0, 0, 0, 0.2);
    }
  }
  :root[data-theme="dark"] {
    --bg: #121317; --bg-card: #1c1f26; --bg-subtle: #22262e; --bg-raised: #20232a;
    --border: #2c313a; --text: #e7e9ee; --text-dim: #9aa2b1;
    --accent: #7da3ff; --accent-bg: #1c2740;
    --class-color: #c298ff; --class-bg: #29203f;
    --cat-entry: #7da3ff; --cat-entry-bg: #1c2740; --cat-entry-border: #3b5a9e;
    --cat-core: #c298ff; --cat-core-bg: #29203f; --cat-core-border: #6b4a9e;
    --cat-base: #5fd08a; --cat-base-bg: #12291c; --cat-base-border: #2a6b40;
    --cat-test: #9aa2b1; --cat-test-bg: #22262e; --cat-test-border: #3a3f4a;
    --fn-color: #5fd08a; --fn-bg: #12291c;
    --const-color: #f0b357; --const-bg: #382a11;
    --priv-color: #6e7480; --priv-bg: #1e2028;
    --test-color: #4ade80; --test-bg: #0f2818;
    --warn-color: #fbbf24; --warn-bg: #3b2e0a;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.25), 0 1px 10px rgba(0, 0, 0, 0.2);
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: var(--sans); line-height: 1.55;
  }
  .wrap { max-width: 1120px; margin: 0 auto; padding: 32px 20px 72px; }

  header { margin-bottom: 22px; }
  header .kicker {
    font-size: 12px; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--text-dim); font-weight: 700;
  }
  header h1 { font-size: 28px; margin: 4px 0 6px; letter-spacing: -0.01em; }
  header .tagline { font-size: 15px; color: var(--text-dim); max-width: 62ch; }

  nav.toc {
    display: flex; gap: 4px; margin: 18px 0 0; border-bottom: 1px solid var(--border);
    overflow-x: auto;
  }
  nav.toc a {
    font-size: 12.5px; font-weight: 600; color: var(--text-dim); text-decoration: none;
    padding: 8px 4px; margin-right: 18px; border-bottom: 2px solid transparent;
    white-space: nowrap;
  }
  nav.toc a:hover { color: var(--accent); }
  nav.toc a.active { color: var(--accent); border-bottom-color: var(--accent); }

  section { margin: 30px 0; scroll-margin-top: 16px; }
  h2 {
    font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-dim); margin: 0 0 12px; font-weight: 700;
  }

  /* ---- stat tiles ---- */
  .stats {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 22px;
  }
  .stat-tile {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 14px; box-shadow: var(--shadow);
  }
  .stat-tile .n { font-size: 22px; font-weight: 700; line-height: 1.1; }
  .stat-tile .label { font-size: 11.5px; color: var(--text-dim); margin-top: 3px; }
  .stat-tile.highlight .n { color: var(--accent); }

  /* ---- overview: two columns ---- */
  .overview-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px; align-items: start; }
  @media (max-width: 760px) { .overview-grid { grid-template-columns: 1fr; } }
  .card {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    padding: 18px 20px; box-shadow: var(--shadow);
  }
  .card h3 {
    font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-dim); margin: 0 0 10px; font-weight: 700;
  }
  .card + .card { margin-top: 14px; }
  .purpose-text { margin: 0; font-size: 14.5px; white-space: pre-line; }

  .feature-list { list-style: none; margin: 12px 0 0; padding: 0; display: flex; flex-direction: column; gap: 7px; }
  .feature-list li {
    font-size: 13.5px; padding-left: 20px; position: relative;
  }
  .feature-list li::before {
    content: "\\2713"; position: absolute; left: 0; color: var(--accent); font-weight: 700; font-size: 12px;
  }

  .stack-list { display: flex; flex-direction: column; gap: 8px; }
  .stack-item { display: flex; justify-content: space-between; gap: 10px; font-size: 13px; align-items: baseline; }
  .stack-item .stack-name { font-weight: 700; white-space: nowrap; }
  .stack-item .stack-note { color: var(--text-dim); text-align: right; }

  .field-row { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
  .field-row:first-child { margin-top: 0; }
  .field-label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-dim); font-weight: 700;
  }
  .pill-row { display: flex; flex-wrap: wrap; gap: 6px; }
  .pill {
    font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
    background: var(--bg-subtle); color: var(--text-dim);
  }
  code, .mono { font-family: var(--mono); }
  .code-block {
    font-family: var(--mono); font-size: 12.5px; background: var(--bg-subtle);
    border-radius: 6px; padding: 8px 12px; display: inline-block;
  }

  /* ---- compat card ---- */
  .compat-row { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-top: 6px; }
  .compat-row:first-child { margin-top: 0; }
  .compat-label { font-weight: 600; min-width: 90px; flex-shrink: 0; }
  .compat-val { font-family: var(--mono); }

  /* ---- external deps section ---- */
  .ext-deps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
  .ext-dep-card {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; box-shadow: var(--shadow); display: flex; flex-direction: column; gap: 6px;
  }
  .ext-dep-head { display: flex; justify-content: space-between; align-items: center; }
  .ext-dep-name { font-family: var(--mono); font-weight: 700; font-size: 14px; }
  .ext-dep-cat {
    font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 7px;
    border-radius: 5px; letter-spacing: 0.04em;
  }
  .ext-dep-cat.stdlib { background: var(--accent-bg); color: var(--accent); }
  .ext-dep-cat.third_party { background: var(--const-bg); color: var(--const-color); }
  .ext-dep-users { font-size: 12px; color: var(--text-dim); }
  .ext-dep-users span { font-family: var(--mono); }
  .ext-dep-group-label {
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-dim); grid-column: 1 / -1; margin-top: 6px;
  }
  .ext-dep-group-label:first-child { margin-top: 0; }

  /* ---- dependency diagram ---- */
  .diagram-caption { font-size: 12.5px; color: var(--text-dim); margin: -4px 0 10px; }
  .diagram-legend {
    display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 12px; font-size: 12px;
  }
  .legend-item { display: flex; align-items: center; gap: 5px; }
  .legend-dot {
    width: 12px; height: 12px; border-radius: 4px; border: 2px solid;
  }
  .diagram-wrap {
    position: relative; overflow-x: auto; padding: 24px 16px 14px;
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    box-shadow: var(--shadow);
  }
  .diagram-svg { position: absolute; top: 0; left: 0; pointer-events: none; }
  .diagram-edge { fill: none; stroke-width: 2.5; opacity: 0.5; transition: opacity 0.15s, stroke-width 0.15s; }
  .diagram-edge.highlight { opacity: 1; stroke-width: 3; }
  .diagram-edge.dim { opacity: 0.1; }
  .diagram-row {
    display: flex; gap: 18px; justify-content: center; margin-bottom: 52px;
    position: relative; z-index: 1;
  }
  .diagram-row:last-child { margin-bottom: 8px; }
  .diagram-node {
    border: 2px solid var(--border); border-radius: 10px; padding: 9px 16px;
    background: var(--bg-raised); font-family: var(--mono); font-size: 12.5px; font-weight: 700;
    cursor: pointer; white-space: nowrap; transition: opacity 0.15s, border-color 0.15s, transform 0.15s;
    box-shadow: var(--shadow);
  }
  .diagram-node:hover { transform: translateY(-1px); }
  .diagram-node.highlight { transform: translateY(-2px); box-shadow: 0 2px 12px rgba(0,0,0,0.12); }
  .diagram-node.dim { opacity: 0.2; }
  .diagram-node.cat-entry { background: var(--cat-entry-bg); border-color: var(--cat-entry-border); color: var(--cat-entry); }
  .diagram-node.cat-core { background: var(--cat-core-bg); border-color: var(--cat-core-border); color: var(--cat-core); }
  .diagram-node.cat-base { background: var(--cat-base-bg); border-color: var(--cat-base-border); color: var(--cat-base); }
  .diagram-node.cat-test { background: var(--cat-test-bg); border-color: var(--cat-test-border); color: var(--cat-test); }
  .diagram-empty { color: var(--text-dim); font-size: 13px; padding: 8px; }

  .search-input {
    width: 100%; font-family: inherit; font-size: 14px; padding: 10px 14px;
    border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card);
    color: var(--text); margin-bottom: 14px; box-shadow: var(--shadow);
  }
  .search-input:focus { outline: none; border-color: var(--accent); }

  .modules { display: flex; flex-direction: column; gap: 10px; }
  .module {
    background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px 18px; cursor: pointer; scroll-margin-top: 20px; box-shadow: var(--shadow);
  }
  .module.flash { border-color: var(--accent); }
  .module-expand {
    font-size: 10px; color: var(--text-dim); transition: transform 0.15s;
    display: inline-block; margin-left: auto; flex-shrink: 0;
  }
  .module.open .module-expand { transform: rotate(90deg); }
  .module-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }
  .module-path-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .module-path { font-family: var(--mono); font-size: 14px; font-weight: 700; color: var(--accent); }
  .badge {
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
    padding: 2px 7px; border-radius: 5px;
  }
  .badge-entry { background: var(--accent-bg); color: var(--accent); }
  .badge-tested { background: var(--test-bg); color: var(--test-color); }
  .badge-untested { background: var(--priv-bg); color: var(--priv-color); }
  .badge-all { background: var(--fn-bg); color: var(--fn-color); }
  .module-meta { font-size: 11.5px; color: var(--text-dim); flex-shrink: 0; white-space: nowrap; text-align: right; }
  .module-role { font-size: 13.5px; margin-top: 6px; color: var(--text); white-space: pre-line; }

  /* metrics bar under role */
  .module-metrics {
    display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px;
    font-size: 11.5px; color: var(--text-dim);
  }
  .metric-item { display: flex; align-items: center; gap: 3px; }
  .metric-item .mi-label { opacity: 0.7; }
  .metric-item .mi-val { font-weight: 700; font-family: var(--mono); }
  .metric-item.warn .mi-val { color: var(--warn-color); }

  .module-body { display: none; margin-top: 14px; padding-top: 14px; border-top: 1px dashed var(--border); }
  .module.open .module-body { display: block; }

  .rel-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 10px; }
  .chip {
    font-family: var(--mono); font-size: 11.5px; padding: 3px 9px; border-radius: 6px;
    background: var(--bg-subtle); color: var(--text-dim); cursor: pointer;
  }
  .chip:hover { color: var(--accent); }
  .rel-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); font-weight: 700; margin-bottom: 4px; }

  /* visibility toggle */
  .vis-toggle {
    display: flex; align-items: center; gap: 6px; margin: 8px 0 4px;
    font-size: 11.5px; color: var(--text-dim); cursor: pointer; user-select: none;
  }
  .vis-toggle input { margin: 0; }

  .sym-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }
  .sym-table td { padding: 6px 6px; border-top: 1px solid var(--border); vertical-align: top; }
  .sym-name { font-family: var(--mono); white-space: nowrap; }
  .sym-kind {
    font-size: 10.5px; font-weight: 700; text-transform: uppercase; padding: 1px 6px;
    border-radius: 5px; white-space: nowrap;
  }
  .sym-kind.class { background: var(--class-bg); color: var(--class-color); }
  .sym-kind.function, .sym-kind.method { background: var(--fn-bg); color: var(--fn-color); }
  .sym-kind.constant { background: var(--const-bg); color: var(--const-color); }
  .sym-vis {
    font-size: 9.5px; font-weight: 700; text-transform: uppercase; padding: 1px 5px;
    border-radius: 4px; white-space: nowrap;
  }
  .sym-vis.private { background: var(--priv-bg); color: var(--priv-color); }
  .sym-role { color: var(--text-dim); }
  .sym-refs { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; align-items: center; }
  .ref-arrow { font-size: 11px; color: var(--text-dim); margin-right: 2px; }
  .ref-chip {
    font-family: var(--mono); font-size: 10.5px; padding: 1px 6px;
    border-radius: 4px; background: var(--accent-bg); color: var(--accent);
    cursor: pointer; white-space: nowrap;
  }
  .ref-chip:hover { opacity: 0.75; }
  tr.sym-private { opacity: 0.55; }
  tr.sym-private.show-private { opacity: 1; }

  .empty-state { text-align: center; padding: 30px; color: var(--text-dim); font-size: 14px; }
  footer { margin-top: 40px; font-size: 12px; color: var(--text-dim); text-align: center; }

  /* module category left border */
  .module.mod-cat-entry { border-left: 3px solid var(--cat-entry); }
  .module.mod-cat-core { border-left: 3px solid var(--cat-core); }
  .module.mod-cat-base { border-left: 3px solid var(--cat-base); }
  .module.mod-cat-test { border-left: 3px solid var(--cat-test); }

  /* toolbar: search + sort */
  .toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 14px; }
  .toolbar .search-input { margin-bottom: 0; flex: 1; }
  .sort-select {
    font-family: inherit; font-size: 13px; padding: 9px 10px;
    border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card);
    color: var(--text); cursor: pointer; box-shadow: var(--shadow);
  }
  .sort-select:focus { outline: none; border-color: var(--accent); }

  /* stat tile click */
  .stat-tile[data-action] { cursor: pointer; transition: border-color 0.15s; }
  .stat-tile[data-action]:hover { border-color: var(--accent); }

  /* search highlight */
  .search-match { background: var(--warn-bg); color: var(--warn-color); border-radius: 2px; padding: 0 1px; }

  @media print {
    body { background: white !important; color: black !important; }
    .diagram-wrap, .module, .card, .stat-tile, .ext-dep-card {
      box-shadow: none !important; break-inside: avoid;
    }
    .module-body { display: block !important; }
    .toolbar, nav.toc { display: none !important; }
    .diagram-node { border: 1px solid #999 !important; }
    tr.sym-private { display: table-row !important; opacity: 0.55; }
    footer::after { content: " · 인쇄본"; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="kicker">코드 맵 — 읽기 전용</div>
    <h1>__PROJECT_NAME__</h1>
    <div class="tagline" id="tagline"></div>
    <nav class="toc">
      <a href="#overview">개요</a>
      <a href="#ext-deps">외부 의존성</a>
      <a href="#diagram">의존 관계</a>
      <a href="#modules">모듈</a>
    </nav>
  </header>

  <div class="stats" id="stats"></div>

  <section id="overview">
    <h2>개요</h2>
    <div class="overview-grid">
      <div class="card">
        <h3>목적</h3>
        <p class="purpose-text" id="purpose"></p>
        <div id="features-wrap"></div>
      </div>
      <div id="right-col"></div>
    </div>
  </section>

  <section id="ext-deps">
    <h2>외부 의존성 (<span id="ext-deps-count"></span>)</h2>
    <div class="ext-deps-grid" id="ext-deps-list"></div>
  </section>

  <section id="diagram">
    <h2>모듈 의존 관계</h2>
    <div class="diagram-caption">A → B = B가 A를 import. 위쪽 레이어일수록 다른 모듈에 덜 의존하는 기반 모듈. 노드에 호버하면 연결된 엣지만 강조.</div>
    <div class="diagram-legend" id="diagram-legend"></div>
    <div class="diagram-wrap"><div id="diagram-inner"></div></div>
  </section>

  <section id="modules">
    <h2>모듈 (<span id="module-count-label"></span>)</h2>
    <div class="toolbar">
      <input class="search-input" id="search" type="text" placeholder="경로, 설명, 심볼 이름으로 검색…">
      <select class="sort-select" id="sort-select">
        <option value="path">경로순</option>
        <option value="loc">코드 줄수 ↓</option>
        <option value="complexity">복잡도 ↓</option>
        <option value="fanin">사용 빈도 ↓</option>
      </select>
    </div>
    <div class="modules" id="modules-list"></div>
    <div class="empty-state" id="empty-state" style="display:none;">일치하는 모듈이 없습니다.</div>
  </section>

  <footer>code-map 스킬로 생성 · 결함 감사가 아닌 읽기 전용 구조 요약</footer>

</div>

<script id="codemap-data" type="application/json">
__CODEMAP_DATA_JSON__
</script>

<script>
(function () {
  const data = JSON.parse(document.getElementById('codemap-data').textContent);
  const project = data.project;
  const modules = data.modules;
  const externalDeps = data.external_deps || [];
  const compat = data.compatibility || null;
  const byPath = new Map(modules.map(m => [m.path, m]));
  const entrySet = new Set(project.entry_points || []);

  const dependedOnBy = new Map(modules.map(m => [m.path, []]));
  modules.forEach(m => (m.depends_on || []).forEach(dep => {
    if (dependedOnBy.has(dep)) dependedOnBy.get(dep).push(m.path);
  }));

  function normStack(s) {
    return typeof s === 'string' ? { name: s, note: '' } : { name: s.name, note: s.note || '' };
  }
  const stack = (project.stack || []).map(normStack);

  const _escEl = document.createElement('span');
  function esc(s) {
    _escEl.textContent = s;
    return _escEl.innerHTML;
  }

  // ---- tagline ----
  const firstSentence = (project.purpose || '').split(/(?<=[.!?。])\\s/)[0];
  document.getElementById('tagline').textContent = firstSentence || '';

  // ---- stat tiles ----
  const allSymbols = modules.flatMap(m => m.symbols || []);
  const totalLoc = modules.reduce((sum, m) => sum + (m.loc || 0), 0);
  const thirdPartyCount = externalDeps.filter(d => d.category === 'third_party').length;
  const testFiles = new Set();
  modules.forEach(m => (m.tested_by || []).forEach(t => testFiles.add(t)));
  const sourceModules = modules.filter(m => !m.path.startsWith('test_') && !m.path.endsWith('_test.py') && !m.path.split('/').some(p => p === 'tests' || p === 'test'));
  const sourcePathSet = new Set(sourceModules.map(m => m.path));
  const testedCount = sourceModules.filter(m => (m.tested_by || []).length > 0).length;

  const stats = [
    { n: modules.length, label: '모듈', action: 'modules' },
    { n: allSymbols.length, label: '심볼', action: 'modules' },
    { n: totalLoc || '—', label: '총 라인 수' },
    { n: externalDeps.length, label: '외부 의존성', sub: thirdPartyCount + ' 서드파티', action: 'ext-deps' },
    { n: testedCount + '/' + sourceModules.length, label: '테스트 커버', hl: testedCount === sourceModules.length, action: 'modules' },
  ];
  document.getElementById('stats').innerHTML = stats.map(s =>
    '<div class="stat-tile' + (s.hl ? ' highlight' : '') + '"' + (s.action ? ' data-action="' + s.action + '"' : '') + '>' +
    '<div class="n">' + s.n + '</div>' +
    '<div class="label">' + s.label + (s.sub ? ' <span style="opacity:.6">(' + s.sub + ')</span>' : '') + '</div></div>'
  ).join('');
  document.querySelectorAll('.stat-tile[data-action]').forEach(function(tile) {
    tile.addEventListener('click', function() {
      var target = document.getElementById(tile.dataset.action);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  // ---- overview: purpose + features ----
  document.getElementById('purpose').textContent = project.purpose || '';
  const features = project.features || [];
  document.getElementById('features-wrap').innerHTML = features.length ? (
    '<h3 style="margin-top:16px;">주요 기능</h3>' +
    '<ul class="feature-list">' + features.map(f => '<li>' + esc(f) + '</li>').join('') + '</ul>'
  ) : '';

  // ---- right column: stack + compat + entry + run ----
  const rightCol = document.getElementById('right-col');
  let rightHtml = '';

  if (stack.length) {
    rightHtml += '<div class="card"><h3>기술 스택</h3><div class="stack-list">' +
      stack.map(s => '<div class="stack-item"><span class="stack-name">' + esc(s.name) + '</span><span class="stack-note">' + esc(s.note) + '</span></div>').join('') +
      '</div>';
    const entryHtml = (project.entry_points || []).length ? (
      '<div class="field-row"><div class="field-label">진입점</div><div class="pill-row">' +
      project.entry_points.map(s => '<span class="pill mono">' + esc(s) + '</span>').join('') + '</div></div>'
    ) : '';
    const runHtml = project.how_to_run ? (
      '<div class="field-row"><div class="field-label">실행</div><div class="code-block">' + esc(project.how_to_run) + '</div></div>'
    ) : '';
    rightHtml += entryHtml + runHtml + '</div>';
  }

  if (compat) {
    rightHtml += '<div class="card"><h3>호환성</h3>';
    if (compat.python_requires) {
      rightHtml += '<div class="compat-row"><span class="compat-label">Python</span><span class="compat-val">' + esc(compat.python_requires) + '</span></div>';
    }
    if (compat.platforms && compat.platforms.length) {
      rightHtml += '<div class="compat-row"><span class="compat-label">플랫폼</span><span>' + compat.platforms.map(p => esc(p)).join(', ') + '</span></div>';
    }
    if (compat.optional_groups) {
      const groups = Object.entries(compat.optional_groups);
      if (groups.length) {
        rightHtml += '<div class="field-row" style="margin-top:10px"><div class="field-label">선택적 의존성</div>';
        groups.forEach(function(g) {
          const vals = Array.isArray(g[1]) ? g[1] : g[1].split(',').map(function(s){return s.trim();});
          rightHtml += '<div style="font-size:12.5px;margin-top:4px"><strong>' + esc(g[0]) + ':</strong> <span style="color:var(--text-dim)">' + vals.map(v => esc(v)).join(', ') + '</span></div>';
        });
        rightHtml += '</div>';
      }
    }
    if (compat.source) {
      rightHtml += '<div style="font-size:11px;color:var(--text-dim);margin-top:8px">출처: ' + esc(compat.source) + '</div>';
    }
    rightHtml += '</div>';
  }

  rightCol.innerHTML = rightHtml;

  // ---- external deps section ----
  const extDepsEl = document.getElementById('ext-deps-list');
  document.getElementById('ext-deps-count').textContent = externalDeps.length;

  if (!externalDeps.length) {
    extDepsEl.innerHTML = '<div class="empty-state">외부 의존성이 없습니다.</div>';
  } else {
    const thirdParty = externalDeps.filter(d => d.category === 'third_party');
    const stdlibDeps = externalDeps.filter(d => d.category === 'stdlib');
    function depCard(d) {
      return '<div class="ext-dep-card">' +
        '<div class="ext-dep-head">' +
        '<span class="ext-dep-name">' + esc(d.name) + '</span>' +
        '<span class="ext-dep-cat ' + d.category + '">' + (d.category === 'third_party' ? '서드파티' : '표준 라이브러리') + '</span>' +
        '</div>' +
        '<div class="ext-dep-users">사용: ' + (d.used_by || []).map(function(u) { return '<span>' + esc(u) + '</span>'; }).join(', ') + '</div>' +
        '</div>';
    }
    let html = '';
    if (thirdParty.length) {
      html += '<div class="ext-dep-group-label">서드파티 (' + thirdParty.length + ')</div>';
      html += thirdParty.map(depCard).join('');
    }
    if (stdlibDeps.length) {
      html += '<div class="ext-dep-group-label">표준 라이브러리 (' + stdlibDeps.length + ')</div>';
      html += stdlibDeps.map(depCard).join('');
    }
    extDepsEl.innerHTML = html;
  }

  // ---- module categories ----
  function isTestPath(p) {
    const name = p.split('/').pop();
    return name.startsWith('test_') || name.endsWith('_test.py') || p.split('/').some(function(s){return s==='tests'||s==='test';});
  }
  const catMap = new Map();
  const CAT_COLORS = {
    entry: { stroke: 'var(--cat-entry)', css: 'cat-entry', label: '진입점' },
    core:  { stroke: 'var(--cat-core)',  css: 'cat-core',  label: '핵심 로직' },
    base:  { stroke: 'var(--cat-base)',  css: 'cat-base',  label: '기반 모듈' },
    test:  { stroke: 'var(--cat-test)',  css: 'cat-test',  label: '테스트' },
  };
  modules.forEach(function(m) {
    if (isTestPath(m.path)) { catMap.set(m.path, 'test'); return; }
    if (entrySet.has(m.path)) { catMap.set(m.path, 'entry'); return; }
    const fanOut = (m.depends_on || []).length;
    if (fanOut === 0) { catMap.set(m.path, 'base'); }
    else { catMap.set(m.path, 'core'); }
  });

  // ---- dependency diagram (layered DAG) ----
  const diagramEl = document.getElementById('diagram-inner');
  const nodeEls = new Map();
  const edgeEls = [];

  function buildDiagram() {
    diagramEl.style.position = 'relative';
    if (!modules.length) {
      diagramEl.innerHTML = '<div class="diagram-empty">모듈이 없습니다.</div>';
      return;
    }

    // legend
    const legendWrap = document.getElementById('diagram-legend');
    if (legendWrap) {
      const used = new Set(catMap.values());
      legendWrap.innerHTML = ['entry','core','base','test'].filter(c => used.has(c)).map(function(c) {
        const cc = CAT_COLORS[c];
        return '<div class="legend-item"><div class="legend-dot" style="background:var(--' + cc.css + '-bg);border-color:var(--' + cc.css + '-border)"></div>' + cc.label + '</div>';
      }).join('');
    }

    const layer = new Map();
    function calc(path, visiting) {
      if (layer.has(path)) return layer.get(path);
      if (visiting.has(path)) { layer.set(path, 0); return 0; }
      visiting.add(path);
      const m = byPath.get(path);
      const deps = ((m && m.depends_on) || []).filter(d => byPath.has(d));
      let l = 0;
      deps.forEach(d => { l = Math.max(l, calc(d, visiting) + 1); });
      visiting.delete(path);
      layer.set(path, l);
      return l;
    }
    modules.forEach(m => calc(m.path, new Set()));

    const maxLayer = Math.max(0, ...modules.map(m => layer.get(m.path)));
    const rows = Array.from({ length: maxLayer + 1 }, () => []);
    modules.forEach(m => rows[layer.get(m.path)].push(m));
    rows.forEach(row => row.sort((a, b) => a.path.localeCompare(b.path)));

    diagramEl.innerHTML = '';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'diagram-svg');
    diagramEl.appendChild(svg);

    nodeEls.clear();
    rows.forEach(row => {
      const rowEl = document.createElement('div');
      rowEl.className = 'diagram-row';
      row.forEach(m => {
        const el = document.createElement('div');
        const cat = catMap.get(m.path) || 'core';
        el.className = 'diagram-node ' + CAT_COLORS[cat].css;
        el.textContent = m.path;
        el.title = (CAT_COLORS[cat].label) + ' — ' + (m.role || m.path);
        el.dataset.path = m.path;
        el.addEventListener('click', () => focusModule(m.path));
        el.addEventListener('mouseenter', () => highlightConnections(m.path));
        el.addEventListener('mouseleave', clearHighlight);
        rowEl.appendChild(el);
        nodeEls.set(m.path, el);
      });
      diagramEl.appendChild(rowEl);
    });

    requestAnimationFrame(() => drawEdges(svg));
  }

  function highlightConnections(path) {
    const deps = new Set((byPath.get(path) || {}).depends_on || []);
    const users = new Set(dependedOnBy.get(path) || []);
    const connected = new Set([path, ...deps, ...users]);
    nodeEls.forEach(function(el, p) {
      el.classList.toggle('dim', !connected.has(p));
      el.classList.toggle('highlight', p === path);
    });
    edgeEls.forEach(function(e) {
      const isConn = (e._from === path || e._to === path);
      e.el.classList.toggle('highlight', isConn);
      e.el.classList.toggle('dim', !isConn);
    });
  }
  function clearHighlight() {
    nodeEls.forEach(function(el) { el.classList.remove('dim', 'highlight'); });
    edgeEls.forEach(function(e) { e.el.classList.remove('highlight', 'dim'); });
  }

  function drawEdges(svg) {
    const wrapRect = diagramEl.getBoundingClientRect();
    svg.setAttribute('width', diagramEl.scrollWidth || wrapRect.width);
    svg.setAttribute('height', diagramEl.scrollHeight || wrapRect.height);

    const cats = ['entry','core','base','test'];
    const markerDefs = cats.map(function(c) {
      return '<marker id="arrow-' + c + '" viewBox="0 0 10 10" refX="9" refY="5" ' +
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">' +
        '<path d="M0,1 L9,5 L0,9 z" fill="' + CAT_COLORS[c].stroke + '" opacity="0.7"></path></marker>';
    }).join('');
    svg.innerHTML = '<defs>' + markerDefs + '</defs>';

    edgeEls.length = 0;
    modules.forEach(m => {
      const toEl = nodeEls.get(m.path);
      if (!toEl) return;
      const toCat = catMap.get(m.path) || 'core';
      (m.depends_on || []).forEach(dep => {
        const fromEl = nodeEls.get(dep);
        if (!fromEl) return;
        const fr = fromEl.getBoundingClientRect();
        const tr = toEl.getBoundingClientRect();
        const x1 = fr.left + fr.width / 2 - wrapRect.left;
        const y1 = fr.bottom - wrapRect.top;
        const x2 = tr.left + tr.width / 2 - wrapRect.left;
        const y2 = tr.top - wrapRect.top;
        const midY = (y1 + y2) / 2;
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M ' + x1 + ' ' + y1 + ' C ' + x1 + ' ' + midY + ', ' + x2 + ' ' + midY + ', ' + x2 + ' ' + y2);
        path.setAttribute('class', 'diagram-edge');
        path.setAttribute('stroke', CAT_COLORS[toCat].stroke);
        path.setAttribute('marker-end', 'url(#arrow-' + toCat + ')');
        svg.appendChild(path);
        edgeEls.push({ el: path, _from: dep, _to: m.path });
      });
    });
  }

  buildDiagram();
  window.addEventListener('resize', () => {
    const svg = diagramEl.querySelector('svg');
    if (svg) drawEdges(svg);
  });

  // ---- module cards ----
  const modulesEl = document.getElementById('modules-list');
  const emptyEl = document.getElementById('empty-state');
  document.getElementById('module-count-label').textContent = modules.length;

  // search highlight helper
  function hl(s, q) {
    const escaped = esc(s);
    if (!q) return escaped;
    var re = new RegExp('(' + q.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ')', 'gi');
    return escaped.replace(re, '<span class="search-match">$1</span>');
  }

  function symbolRow(sym, q) {
    const isPriv = sym.visibility === 'private';
    const refs = sym.refs || [];
    let refsHtml = '';
    if (refs.length) {
      refsHtml = '<div class="sym-refs"><span class="ref-arrow">&rarr;</span>' +
        refs.map(function(r) {
          const parts = r.split('::');
          return '<span class="ref-chip" data-path="' + esc(parts[0]) + '" title="' + esc(r) + '">' + esc(parts[1]) + '</span>';
        }).join('') + '</div>';
    }
    return '<tr class="' + (isPriv ? 'sym-private' : '') + '" data-vis="' + (sym.visibility || 'public') + '">' +
      '<td class="sym-name">' + hl(sym.name, q) + '</td>' +
      '<td><span class="sym-kind ' + (sym.kind || '') + '">' + ({class:'클래스',function:'함수',method:'메서드',constant:'상수'}[sym.kind] || sym.kind || '') + '</span></td>' +
      (isPriv ? '<td><span class="sym-vis private">비공개</span></td>' : '<td></td>') +
      '<td class="sym-role">' + hl(sym.role || '', q) + refsHtml + '</td>' +
      '</tr>';
  }

  function chip(path, label) {
    return '<span class="chip" data-path="' + esc(path) + '">' + esc(label) + '</span>';
  }

  function matchesQuery(m, q) {
    if (!q) return true;
    if (m.path.toLowerCase().includes(q)) return true;
    if ((m.role || '').toLowerCase().includes(q)) return true;
    return (m.symbols || []).some(s => s.name.toLowerCase().includes(q) || (s.role || '').toLowerCase().includes(q));
  }

  // sorting
  let currentSort = 'path';
  function sortModules(list) {
    var sorted = list.slice();
    switch (currentSort) {
      case 'loc': sorted.sort(function(a, b) { return (b.loc || 0) - (a.loc || 0); }); break;
      case 'complexity': sorted.sort(function(a, b) {
        var an = (a.metrics || {}).max_nesting || 0, bn = (b.metrics || {}).max_nesting || 0;
        if (bn !== an) return bn - an;
        return ((b.metrics || {}).avg_fn_length || 0) - ((a.metrics || {}).avg_fn_length || 0);
      }); break;
      case 'fanin': sorted.sort(function(a, b) {
        return (dependedOnBy.get(b.path) || []).length - (dependedOnBy.get(a.path) || []).length;
      }); break;
      default: sorted.sort(function(a, b) { return a.path.localeCompare(b.path); });
    }
    return sorted;
  }

  function toggleModule(el) {
    var isOpen = el.classList.toggle('open');
    el.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  function renderModules(filterText) {
    modulesEl.innerHTML = '';
    const q = (filterText || '').toLowerCase();
    const visible = sortModules(modules.filter(m => matchesQuery(m, q)));
    emptyEl.style.display = visible.length ? 'none' : 'block';

    visible.forEach(m => {
      const el = document.createElement('div');
      const cat = catMap.get(m.path) || 'core';
      el.className = 'module mod-' + CAT_COLORS[cat].css;
      el.id = 'mod-' + encodeURIComponent(m.path);
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.setAttribute('aria-expanded', 'false');
      const deps = m.depends_on || [];
      const usedBy = dependedOnBy.get(m.path) || [];
      const fanIn = usedBy.length;
      const fanOut = deps.length;
      const metrics = m.metrics || {};
      const testedBy = m.tested_by || [];
      const isTest = m.path.startsWith('test_') || m.path.endsWith('_test.py') || m.path.split('/').some(function(p){return p==='tests'||p==='test';});
      const hasAll = m.has_all || false;
      const syms = m.symbols || [];
      const publicSyms = syms.filter(s => s.visibility !== 'private');
      const privateSyms = syms.filter(s => s.visibility === 'private');

      const metaParts = [];
      if (m.loc) metaParts.push(m.loc + ' 줄');
      metaParts.push(publicSyms.length + (privateSyms.length ? '+' + privateSyms.length : '') + ' 심볼');

      // badges
      let badges = '';
      if (entrySet.has(m.path)) badges += '<span class="badge badge-entry">진입점</span>';
      if (hasAll) badges += '<span class="badge badge-all">__all__</span>';
      if (!isTest && testedBy.length) badges += '<span class="badge badge-tested">테스트됨</span>';
      if (!isTest && !testedBy.length && sourcePathSet.has(m.path)) badges += '<span class="badge badge-untested">테스트 없음</span>';

      // metrics bar
      let metricsHtml = '';
      if (metrics.functions !== undefined || fanIn || fanOut) {
        const items = [];
        if (fanIn) items.push('<span class="metric-item"><span class="mi-label">사용됨</span> <span class="mi-val">' + fanIn + '</span></span>');
        if (fanOut) items.push('<span class="metric-item"><span class="mi-label">의존</span> <span class="mi-val">' + fanOut + '</span></span>');
        if (metrics.functions !== undefined) items.push('<span class="metric-item"><span class="mi-label">함수</span> <span class="mi-val">' + metrics.functions + '</span></span>');
        if (metrics.classes) items.push('<span class="metric-item"><span class="mi-label">클래스</span> <span class="mi-val">' + metrics.classes + '</span></span>');
        if (metrics.avg_fn_length) items.push('<span class="metric-item' + (metrics.avg_fn_length > 30 ? ' warn' : '') + '"><span class="mi-label">평균 길이</span> <span class="mi-val">' + metrics.avg_fn_length + '</span></span>');
        if (metrics.max_nesting) items.push('<span class="metric-item' + (metrics.max_nesting > 4 ? ' warn' : '') + '"><span class="mi-label">중첩</span> <span class="mi-val">' + metrics.max_nesting + '</span></span>');
        if (items.length) metricsHtml = '<div class="module-metrics">' + items.join('') + '</div>';
      }

      // tested-by in body
      let testedHtml = '';
      if (testedBy.length) {
        testedHtml = '<div class="rel-label">테스트 파일</div><div class="rel-row">' + testedBy.map(t => chip(t, t)).join('') + '</div>';
      }

      // visibility toggle
      let visToggle = '';
      if (privateSyms.length) {
        visToggle = '<label class="vis-toggle"><input type="checkbox" class="vis-cb"> 비공개 심볼 표시 (' + privateSyms.length + '개)</label>';
      }

      el.innerHTML =
        '<div class="module-head">' +
          '<div class="module-path-row">' +
            '<span class="module-expand">&#9654;</span>' +
            '<span class="module-path">' + hl(m.path, q) + '</span>' +
            badges +
          '</div>' +
          '<div class="module-meta">' + metaParts.join(' \\u00B7 ') + '</div>' +
        '</div>' +
        '<div class="module-role">' + hl(m.role, q) + '</div>' +
        metricsHtml +
        '<div class="module-body">' +
          (deps.length ? '<div class="rel-label">의존 대상</div><div class="rel-row">' + deps.map(d => chip(d, d)).join('') + '</div>' : '') +
          (usedBy.length ? '<div class="rel-label">사용처</div><div class="rel-row">' + usedBy.map(d => chip(d, d)).join('') + '</div>' : '') +
          testedHtml +
          (syms.length ? (
            visToggle +
            '<table class="sym-table"><tbody>' + syms.map(function(s) { return symbolRow(s, q); }).join('') + '</tbody></table>'
          ) : '') +
        '</div>';

      el.addEventListener('click', function(e) {
        if (e.target.classList.contains('chip') || e.target.classList.contains('ref-chip') || e.target.tagName === 'INPUT' || e.target.tagName === 'LABEL') return;
        toggleModule(el);
      });
      el.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleModule(el); }
      });
      el.querySelectorAll('.chip').forEach(c => {
        c.addEventListener('click', function(e) {
          e.stopPropagation();
          focusModule(c.dataset.path);
        });
      });
      el.querySelectorAll('.ref-chip').forEach(c => {
        c.addEventListener('click', function(e) {
          e.stopPropagation();
          focusModule(c.dataset.path);
        });
      });
      const cb = el.querySelector('.vis-cb');
      if (cb) {
        cb.addEventListener('change', function() {
          el.querySelectorAll('tr.sym-private').forEach(function(tr) {
            if (cb.checked) { tr.classList.add('show-private'); tr.style.display = ''; }
            else { tr.classList.remove('show-private'); tr.style.display = 'none'; }
          });
        });
        el.querySelectorAll('tr.sym-private').forEach(function(tr) { tr.style.display = 'none'; });
      }
      modulesEl.appendChild(el);
    });
  }

  function focusModule(path) {
    const searchEl = document.getElementById('search');
    let el = document.getElementById('mod-' + encodeURIComponent(path));
    if (!el && searchEl.value) {
      searchEl.value = '';
      renderModules('');
      el = document.getElementById('mod-' + encodeURIComponent(path));
    }
    if (!el) return;
    el.classList.add('open', 'flash');
    el.setAttribute('aria-expanded', 'true');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => el.classList.remove('flash'), 1200);

    nodeEls.forEach((nodeEl, p) => nodeEl.classList.toggle('highlight', p === path));
  }

  document.getElementById('search').addEventListener('input', function(e) {
    const q = e.target.value.toLowerCase();
    renderModules(q);
    nodeEls.forEach((nodeEl, p) => {
      const m = byPath.get(p);
      nodeEl.classList.toggle('dim', !matchesQuery(m, q));
    });
  });

  document.getElementById('sort-select').addEventListener('change', function(e) {
    currentSort = e.target.value;
    renderModules(document.getElementById('search').value);
  });

  renderModules('');

  // ---- scroll spy for TOC ----
  const tocLinks = document.querySelectorAll('nav.toc a');
  const sections = Array.from(tocLinks).map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  const observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        tocLinks.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id));
      }
    });
  }, { rootMargin: '-20% 0px -70% 0px' });
  sections.forEach(s => observer.observe(s));
})();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    main()
