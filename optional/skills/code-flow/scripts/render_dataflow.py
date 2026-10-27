#!/usr/bin/env python3
"""Render data-flow pipeline diagrams from a JSON definition.

Usage: python3 render_dataflow.py <pipelines.json> -o <output.html>

JSON schema (example):
  {
    "project": {
      "name": "My Project",
      "type_label": "ML / 딥러닝",
      "description": "프로젝트 설명"
    },
    "types": {
      "file":   {"label": "파일",   "preset": "gray"},
      "image":  {"label": "이미지", "preset": "amber"},
      "tensor": {"label": "텐서",   "preset": "blue"}
    },
    "pipelines": [
      {
        "name": "학습 파이프라인",
        "source": "train.py",
        "steps": [
          {"label": "이미지 파일", "detail": ".png/.npy", "type": "file"},
          {"arrow": "load_image"},
          {"label": "PIL Image", "detail": "H×W×C", "type": "image"}
        ]
      }
    ]
  }

Preset colors: gray, red, orange, amber, green, teal, blue, indigo, purple, pink
"""

import json
import sys
from pathlib import Path

PRESETS = {
    "gray":   {"light": ("#7a7d86", "#f0efec"), "dark": ("#9a9da6", "#2a2b32")},
    "red":    {"light": ("#c43b3b", "#fae8e8"), "dark": ("#f08080", "#3a1e1e")},
    "orange": {"light": ("#c75a20", "#faeee4"), "dark": ("#e8915a", "#352418")},
    "amber":  {"light": ("#b07020", "#faf0e4"), "dark": ("#e0a070", "#352a1e")},
    "green":  {"light": ("#3a8a5c", "#e8f5ee"), "dark": ("#5ec88a", "#1a2e22")},
    "teal":   {"light": ("#1a8a7a", "#e4f5f2"), "dark": ("#50c8b4", "#162e2a")},
    "blue":   {"light": ("#3b6fd4", "#e8eff9"), "dark": ("#7da3f0", "#1e2a42")},
    "indigo": {"light": ("#4b50c8", "#ecedfa"), "dark": ("#8a8ef0", "#22204a")},
    "purple": {"light": ("#8b5cc4", "#f1ecf9"), "dark": ("#b88ee8", "#2a2040")},
    "pink":   {"light": ("#c44a7a", "#fae8f0"), "dark": ("#e88aaa", "#3a1e2a")},
}


def validate(data):
    assert "project" in data, "missing 'project'"
    assert "name" in data["project"], "missing 'project.name'"
    assert "types" in data, "missing 'types'"
    assert "pipelines" in data and len(data["pipelines"]) > 0, "missing 'pipelines'"
    for t in data["types"].values():
        p = t.get("preset", "gray")
        assert p in PRESETS, f"unknown preset '{p}', choose from: {list(PRESETS.keys())}"
    for pl in data["pipelines"]:
        assert "name" in pl and "steps" in pl, "pipeline needs 'name' and 'steps'"
        for s in pl["steps"]:
            if "arrow" not in s:
                assert "label" in s and "type" in s, f"step needs 'label' and 'type': {s}"
                assert s["type"] in data["types"], f"unknown type '{s['type']}'"


def build_css_vars(types_def):
    light_vars, dark_vars = [], []
    for key, spec in types_def.items():
        preset = PRESETS[spec.get("preset", "gray")]
        fg_l, bg_l = preset["light"]
        fg_d, bg_d = preset["dark"]
        light_vars.append(f"  --t-{key}: {fg_l}; --t-{key}-bg: {bg_l};")
        dark_vars.append(f"  --t-{key}: {fg_d}; --t-{key}-bg: {bg_d};")
    return "\n".join(light_vars), "\n".join(dark_vars)


TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — 데이터 흐름도</title>
<style>
:root {{
  --bg: #f7f6f3;
  --bg-card: #ffffff;
  --bg-subtle: #eeedea;
  --border: #dbd9d3;
  --text: #2d2f36;
  --text-dim: #7a7d86;
  --accent: #3b6fd4;
  --shadow: 0 1px 3px rgba(30,28,24,.06);
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --sans: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
{light_type_vars}
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #18191d; --bg-card: #222329; --bg-subtle: #2a2b32;
    --border: #3a3b42; --text: #e4e5ea; --text-dim: #8b8f9a;
    --accent: #7da3f0;
    --shadow: 0 1px 4px rgba(0,0,0,.3);
{dark_type_vars}
  }}
}}
:root[data-theme="dark"] {{
  --bg: #18191d; --bg-card: #222329; --bg-subtle: #2a2b32;
  --border: #3a3b42; --text: #e4e5ea; --text-dim: #8b8f9a;
  --accent: #7da3f0;
  --shadow: 0 1px 4px rgba(0,0,0,.3);
{dark_type_vars}
}}

* {{ box-sizing: border-box; margin: 0; }}
body {{
  background: var(--bg); color: var(--text);
  font-family: var(--sans); line-height: 1.55;
}}
.wrap {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px 80px; }}

header {{ margin-bottom: 32px; }}
.kicker {{
  font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-dim); font-weight: 700; margin-bottom: 6px;
}}
h1 {{ font-size: 26px; font-weight: 700; letter-spacing: -0.01em; }}
.subtitle {{ font-size: 14px; color: var(--text-dim); margin-top: 4px; max-width: 62ch; }}

.diagram-container {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; box-shadow: var(--shadow);
  overflow-x: auto; padding: 28px 24px; margin-bottom: 24px;
}}
.flow-label {{
  font-size: 13px; font-weight: 700; margin-bottom: 4px;
}}
.flow-source {{
  font-size: 11.5px; color: var(--text-dim); font-family: var(--mono);
  margin-bottom: 16px;
}}
.pipeline {{
  display: flex; align-items: center; gap: 0; min-width: max-content;
  padding-bottom: 6px;
}}
.pipe-node {{
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  flex-shrink: 0;
}}
.pipe-box {{
  border: 2px solid; border-radius: 8px; padding: 8px 14px;
  font-size: 12.5px; font-weight: 600; white-space: nowrap;
  text-align: center; line-height: 1.3; min-width: 72px;
  transition: transform .15s, box-shadow .15s;
}}
.pipe-box:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.1); }}
.pipe-detail {{
  font-size: 10.5px; color: var(--text-dim); font-family: var(--mono);
  white-space: nowrap;
}}
.pipe-arrow {{
  display: flex; flex-direction: column; align-items: center;
  gap: 2px; padding: 0 6px; flex-shrink: 0;
}}
.arrow-line {{
  width: 32px; height: 2px; background: var(--border); position: relative;
}}
.arrow-line::after {{
  content: ""; position: absolute; right: -1px; top: -4px;
  border: 5px solid transparent; border-left: 6px solid var(--border);
}}
.arrow-fn {{
  font-size: 9.5px; font-family: var(--mono); color: var(--accent);
  white-space: nowrap; font-weight: 600;
}}

.legend {{
  display: flex; flex-wrap: wrap; gap: 14px; margin-top: 20px;
  font-size: 11.5px; color: var(--text-dim);
}}
.legend-item {{ display: flex; align-items: center; gap: 5px; }}
.legend-dot {{
  width: 10px; height: 10px; border-radius: 3px; border: 2px solid;
}}
footer {{ margin-top: 40px; font-size: 11.5px; color: var(--text-dim); text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kicker">{type_label}</div>
    <h1>{name} — 데이터 흐름도</h1>
    <div class="subtitle">{description}</div>
  </header>
  <div id="diagrams"></div>
  <div class="legend" id="legend"></div>
  <footer>project-diagrams 스킬로 생성</footer>
</div>

<script id="flow-data" type="application/json">
{json_data}
</script>
<script>
const DATA = JSON.parse(document.getElementById("flow-data").textContent);

// render pipelines
const container = document.getElementById("diagrams");
DATA.pipelines.forEach(pl => {{
  const wrap = document.createElement("div");
  wrap.className = "diagram-container";

  let header = `<div class="flow-label">${{pl.name}}</div>`;
  if (pl.source) header += `<div class="flow-source">${{pl.source}}</div>`;
  wrap.innerHTML = header;

  const pipe = document.createElement("div");
  pipe.className = "pipeline";

  pl.steps.forEach(s => {{
    if (s.arrow) {{
      const d = document.createElement("div");
      d.className = "pipe-arrow";
      d.innerHTML = `<span class="arrow-fn">${{s.arrow}}</span><div class="arrow-line"></div>`;
      pipe.appendChild(d);
    }} else {{
      const d = document.createElement("div");
      d.className = "pipe-node";
      const t = s.type;
      d.innerHTML = `<div class="pipe-box" style="border-color:var(--t-${{t}});background:var(--t-${{t}}-bg);color:var(--t-${{t}})">${{s.label}}</div>`
        + (s.detail ? `<span class="pipe-detail">${{s.detail}}</span>` : "");
      pipe.appendChild(d);
    }}
  }});

  wrap.appendChild(pipe);
  container.appendChild(wrap);
}});

// legend
const leg = document.getElementById("legend");
Object.entries(DATA.types).forEach(([k, v]) => {{
  const d = document.createElement("div");
  d.className = "legend-item";
  d.innerHTML = `<div class="legend-dot" style="border-color:var(--t-${{k}});background:var(--t-${{k}}-bg)"></div>${{v.label}}`;
  leg.appendChild(d);
}});
</script>
</body>
</html>
"""


def render(data, out_path):
    validate(data)
    light_vars, dark_vars = build_css_vars(data["types"])
    proj = data["project"]
    html = TEMPLATE.format(
        title=proj["name"],
        name=proj["name"],
        type_label=proj.get("type_label", ""),
        description=proj.get("description", ""),
        light_type_vars=light_vars,
        dark_type_vars=dark_vars,
        json_data=json.dumps(data, ensure_ascii=False),
    )
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render dataflow pipeline diagrams")
    parser.add_argument("input", help="JSON pipeline definition")
    parser.add_argument("-o", "--output", required=True, help="Output HTML path")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    render(data, args.output)
