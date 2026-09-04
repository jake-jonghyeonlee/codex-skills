#!/usr/bin/env python3
"""Render a layered architecture diagram from a JSON definition.

Usage: python3 render_architecture.py <arch.json> -o <output.html>

JSON schema: see SKILL.md for full spec and examples.
"""

import json
import sys
from pathlib import Path

PRESETS = {
    "gray":   {"light": ("#7a7d86", "#eae8e4", "#c8c4bc"), "dark": ("#9a9da6", "#28272a", "#3e3c38")},
    "red":    {"light": ("#c43b3b", "#fae8e8", "#e8b0b0"), "dark": ("#f08080", "#3a1e1e", "#5a2e2e")},
    "orange": {"light": ("#c75a20", "#faeee4", "#e8c4a0"), "dark": ("#e8915a", "#352418", "#4a3420")},
    "amber":  {"light": ("#b07020", "#f5e8d4", "#e0c8a0"), "dark": ("#e0a070", "#352a1e", "#4a3e2a")},
    "green":  {"light": ("#3a8a5c", "#d8eee2", "#a8d4b8"), "dark": ("#5ec88a", "#1a2e22", "#2a4434")},
    "teal":   {"light": ("#1a8a7a", "#d4ede8", "#a0d4c8"), "dark": ("#50c8b4", "#162e2a", "#2a4440")},
    "blue":   {"light": ("#3b6fd4", "#dce7f5", "#b0c8e8"), "dark": ("#7da3f0", "#1e2a42", "#2e4060")},
    "indigo": {"light": ("#4b50c8", "#e0dff5", "#b0aee8"), "dark": ("#8a8ef0", "#22204a", "#343060")},
    "purple": {"light": ("#8b5cc4", "#ecdff8", "#cdb8e8"), "dark": ("#b88ee8", "#2a2040", "#3e3060")},
    "pink":   {"light": ("#c44a7a", "#fae8f0", "#e8aac4"), "dark": ("#e88aaa", "#3a1e2a", "#5a2e3e")},
}


def validate(data):
    assert "project" in data, "missing 'project'"
    assert "name" in data["project"], "missing 'project.name'"
    assert "layers" in data and len(data["layers"]) > 0, "missing 'layers'"
    n_layers = len(data["layers"])
    for i, layer in enumerate(data["layers"]):
        assert "title" in layer, f"layer[{i}] missing 'title'"
        p = layer.get("preset", "blue")
        assert p in PRESETS, f"layer[{i}] unknown preset '{p}'"
        assert "components" in layer and len(layer["components"]) > 0, f"layer[{i}] needs 'components'"
    for cc in data.get("crosscuts", []):
        assert "name" in cc, "crosscut missing 'name'"
        assert "points" in cc and len(cc["points"]) > 0, "crosscut missing 'points'"
        p = cc.get("color", "pink")
        assert p in PRESETS, f"crosscut unknown color '{p}'"
        for pt in cc["points"]:
            assert "at" in pt or "at_layer" in pt, "crosscut point needs 'at' or 'at_layer'"
            if "at_layer" in pt:
                idx = pt["at_layer"]
                assert 0 <= idx < n_layers, f"at_layer={idx} out of range (0..{n_layers-1})"
    for gi, g in enumerate(data.get("groups", [])):
        assert "name" in g, f"group[{gi}] missing 'name'"
        assert "from" in g and "to" in g, f"group[{gi}] missing 'from'/'to'"
        assert 0 <= g["from"] <= g["to"] < n_layers, (
            f"group[{gi}] range {g['from']}..{g['to']} out of bounds (0..{n_layers-1})")
        p = g.get("preset", "blue")
        assert p in PRESETS, f"group[{gi}] unknown preset '{p}'"


def build_layer_vars(layers):
    light_vars, dark_vars = [], []
    for i, layer in enumerate(layers):
        p = layer.get("preset", "blue")
        fl, bl, brl = PRESETS[p]["light"]
        fd, bd, brd = PRESETS[p]["dark"]
        light_vars.append(f"  --l{i}-bg: {bl}; --l{i}-border: {brl}; --l{i}-fg: {fl};")
        dark_vars.append(f"  --l{i}-bg: {bd}; --l{i}-border: {brd}; --l{i}-fg: {fd};")
    return "\n".join(light_vars), "\n".join(dark_vars)


def build_crosscut_vars(crosscuts):
    light_vars, dark_vars = [], []
    for i, cc in enumerate(crosscuts):
        p = cc.get("color", "pink")
        fl, bl, _ = PRESETS[p]["light"]
        fd, bd, _ = PRESETS[p]["dark"]
        light_vars.append(f"  --cc{i}: {fl}; --cc{i}-bg: {bl};")
        dark_vars.append(f"  --cc{i}: {fd}; --cc{i}-bg: {bd};")
    return "\n".join(light_vars), "\n".join(dark_vars)


def build_group_vars(groups):
    light_vars, dark_vars = [], []
    for i, g in enumerate(groups):
        p = g.get("preset", "blue")
        fl, bl, _ = PRESETS[p]["light"]
        fd, bd, _ = PRESETS[p]["dark"]
        light_vars.append(f"  --g{i}: {fl}; --g{i}-bg: {bl};")
        dark_vars.append(f"  --g{i}: {fd}; --g{i}-bg: {bd};")
    return "\n".join(light_vars), "\n".join(dark_vars)


TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — 아키텍처</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap&family=JetBrains+Mono:wght@400;500;600&display=swap">
<style>
:root {{
  --bg: #f5f3ef;
  --bg-card: #ffffff;
  --border: #ddd9d2;
  --text: #2d2f36;
  --text-dim: #7a7d86;
  --text-faint: #a8abb4;
  --accent: #3b6fd4;
  --lc-color: #3a8a5c; --lc-bg: #d8eee2;
  --shadow: 0 1px 3px rgba(30,28,24,.06);
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
  --sans: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --comp-bg: #ffffff;
  --comp-shadow: 0 1px 4px rgba(30,28,24,.08);
  --ext-color: #d45a5a; --ext-bg: #faeaea;
{layer_vars_light}
{crosscut_vars_light}
{group_vars_light}
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #1a1b1f; --bg-card: #24252b; --border: #38393f;
    --text: #e2e3e8; --text-dim: #8b8f9a; --text-faint: #5a5d66;
    --accent: #7da3f0; --shadow: 0 1px 4px rgba(0,0,0,.3);
    --lc-color: #5ec88a; --lc-bg: #1a2e22;
    --comp-bg: #2c2d34; --comp-shadow: 0 1px 4px rgba(0,0,0,.4);
    --ext-color: #f08080; --ext-bg: #3a1e1e;
{layer_vars_dark}
{crosscut_vars_dark}
{group_vars_dark}
  }}
}}
:root[data-theme="dark"] {{
  --bg: #1a1b1f; --bg-card: #24252b; --border: #38393f;
  --text: #e2e3e8; --text-dim: #8b8f9a; --text-faint: #5a5d66;
  --accent: #7da3f0; --shadow: 0 1px 4px rgba(0,0,0,.3);
  --lc-color: #5ec88a; --lc-bg: #1a2e22;
  --comp-bg: #2c2d34; --comp-shadow: 0 1px 4px rgba(0,0,0,.4);
  --ext-color: #f08080; --ext-bg: #3a1e1e;
{layer_vars_dark}
{crosscut_vars_dark}
{group_vars_dark}
}}

* {{ box-sizing: border-box; margin: 0; }}
body {{ background: var(--bg); color: var(--text); font-family: var(--sans); line-height: 1.5; }}
.page {{ max-width: 960px; margin: 0 auto; padding: 40px 20px 60px; }}

header {{ margin-bottom: 28px; }}
.eyebrow {{
  font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-dim); font-weight: 700; margin-bottom: 4px;
}}
h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }}
.desc {{ font-size: 13px; color: var(--text-dim); margin-top: 4px; max-width: 60ch; }}

.arch-grid {{
  display: grid;
  grid-template-columns: 1fr{crosscut_cols};
  gap: 0;
  position: relative;
}}
.layers {{ display: flex; flex-direction: column; gap: 0; position: relative; }}
.layers.has-groups {{ padding-left: 22px; }}

.layer {{
  border-radius: 10px; padding: 14px 16px;
  border: 1.5px solid; position: relative;
  transition: padding .2s;
}}
.layer.collapsed {{ padding-bottom: 10px; }}
.layer-head {{
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
  cursor: pointer; user-select: none;
}}
.layer.collapsed .layer-head {{ margin-bottom: 0; }}
.layer-chevron {{
  font-size: 10px; color: var(--text-faint); transition: transform .2s;
  flex-shrink: 0; width: 12px; text-align: center;
}}
.layer.collapsed .layer-chevron {{ transform: rotate(-90deg); }}
.layer-num {{
  font-size: 9px; font-weight: 700; width: 18px; height: 18px;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: var(--text-dim); border: 1.5px solid var(--border); flex-shrink: 0;
}}
.layer-title {{ font-size: 13px; font-weight: 700; }}
.layer-sub {{ font-size: 10.5px; color: var(--text-dim); margin-left: auto; font-family: var(--mono); }}

.comps {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.layer.collapsed .comps {{ display: none; }}
.comp {{
  background: var(--comp-bg); border-radius: 6px; padding: 6px 10px;
  font-size: 11.5px; font-family: var(--mono); font-weight: 500;
  box-shadow: var(--comp-shadow); border: 1px solid var(--border);
  position: relative; cursor: pointer;
  transition: transform .12s, box-shadow .12s, outline-color .15s;
}}
.comp:hover {{ transform: translateY(-1px); box-shadow: 0 3px 10px rgba(0,0,0,.1); }}
.comp.active {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.comp-main {{ font-weight: 600; }}
.comp .tip {{ display: none; }}

.ext-badge {{
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: var(--ext-bg); color: var(--ext-color);
  font-size: 9.5px; font-weight: 700; padding: 3px 7px;
  border-radius: 4px; border: 1.5px solid var(--ext-color);
  letter-spacing: 0.03em; white-space: nowrap;
}}
.layer.collapsed .ext-badge {{ display: none; }}

.layer-arrow {{
  display: flex; justify-content: center; padding: 6px 0;
}}
.layers.has-groups .layer-arrow {{
  padding-left: 22px;
}}
.arrow-down {{
  width: 2px; height: 20px; background: var(--border); position: relative;
}}
.arrow-down::after {{
  content: ""; position: absolute; bottom: -6px; left: -5px;
  border: 6px solid transparent; border-top: 7px solid var(--border);
}}

/* Layer groups */
.group-bracket {{
  position: absolute; left: 0; width: 4px; border-radius: 2px;
  pointer-events: none; transition: height .2s;
}}
.group-tag {{
  position: absolute; left: 0;
  font-size: 9px; font-weight: 700; font-family: var(--mono);
  padding: 2px 6px; border-radius: 0 4px 4px 0;
  white-space: nowrap; letter-spacing: 0.02em;
  transform: translateY(-100%); margin-top: -2px;
  cursor: pointer; user-select: none;
  transition: opacity .15s;
}}
.group-tag:hover {{ opacity: .7; }}

/* Crosscut rail */
.cc-rail {{
  display: flex; flex-direction: column; align-items: center;
  padding: 0 0 0 6px; position: relative; min-width: 120px;
}}
.cc-label {{
  writing-mode: vertical-rl; text-orientation: mixed;
  font-size: 10px; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase;
  margin-bottom: 8px;
}}
.cc-line {{
  flex: 1; width: 3px;
  border-radius: 2px; position: relative;
}}
.cc-point {{
  position: absolute; left: 0; right: 0;
  display: flex; align-items: center; gap: 0;
  transform: translateY(-50%);
  transition: top .25s ease;
}}
.cc-connector {{
  width: 16px; border-top: 2px dashed; opacity: .5; flex-shrink: 0;
}}
.cc-dot {{
  width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0;
  border: 2.5px solid var(--bg);
}}
.cc-tag {{
  font-size: 9.5px; font-family: var(--mono); font-weight: 600;
  padding: 2px 6px; border-radius: 3px; white-space: nowrap;
  margin-left: 4px; line-height: 1.2;
}}

/* Side panel */
.panel-overlay {{
  position: fixed; inset: 0; background: rgba(0,0,0,.12);
  z-index: 90; opacity: 0; pointer-events: none;
  transition: opacity .2s;
}}
.panel-overlay.open {{ opacity: 1; pointer-events: auto; }}
.side-panel {{
  position: fixed; top: 0; right: 0; width: 360px; height: 100%;
  background: var(--bg-card); border-left: 1.5px solid var(--border);
  box-shadow: -4px 0 24px rgba(0,0,0,.06);
  z-index: 100; transform: translateX(100%);
  transition: transform .25s ease;
  overflow-y: auto; padding: 28px 22px;
}}
.side-panel.open {{ transform: translateX(0); }}
@media (max-width: 700px) {{ .side-panel {{ width: 100%; }} }}
.panel-close {{
  position: absolute; top: 14px; right: 14px;
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; width: 28px; height: 28px;
  font-size: 16px; cursor: pointer; color: var(--text-dim);
  display: flex; align-items: center; justify-content: center;
  transition: background .1s;
}}
.panel-close:hover {{ background: var(--border); }}
.panel-layer-tag {{
  display: inline-block; font-size: 10px; font-weight: 700;
  font-family: var(--mono); padding: 3px 10px;
  border-radius: 5px; margin-bottom: 16px; letter-spacing: 0.02em;
}}
.panel-name {{
  font-size: 15px; font-weight: 700; font-family: var(--mono);
  margin-bottom: 16px; line-height: 1.4;
}}
.panel-desc {{
  font-size: 13px; color: var(--text-dim); line-height: 1.75;
  word-break: keep-all;
}}
.panel-empty {{ color: var(--text-faint); font-style: italic; }}

/* Bottom cards */
.bottom-grid {{
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  margin-top: 24px;
}}
@media (max-width: 600px) {{ .bottom-grid {{ grid-template-columns: 1fr; }} }}

.info-card {{
  background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px; box-shadow: var(--shadow);
}}
.info-title {{
  font-size: 12px; font-weight: 700; margin-bottom: 8px;
  display: flex; align-items: center; gap: 6px;
}}
.info-title .dot {{ width: 8px; height: 8px; border-radius: 50%; }}

.lc-list {{ list-style: none; padding: 0; }}
.lc-list li {{
  font-size: 11px; font-family: var(--mono); padding: 3px 0;
  border-bottom: 1px solid var(--border); color: var(--text-dim);
  display: flex; gap: 6px; align-items: baseline;
}}
.lc-list li:last-child {{ border-bottom: none; }}
.lc-list .ln {{ font-weight: 600; }}
.lc-list .ld {{ font-family: var(--sans); font-size: 10.5px; }}

.ext-list {{ list-style: none; padding: 0; }}
.ext-list li {{
  font-size: 11.5px; padding: 4px 0;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: baseline; gap: 6px;
}}
.ext-list li:last-child {{ border-bottom: none; }}
.ext-list .ek {{
  font-family: var(--mono); font-weight: 600; font-size: 11px;
  color: var(--ext-color); flex-shrink: 0;
}}
.ext-list .ev {{ color: var(--text-dim); font-size: 11px; }}

footer {{ margin-top: 32px; font-size: 11px; color: var(--text-faint); text-align: center; }}
</style>
</head>
<body>
<div class="page">
  <header>
    <div class="eyebrow">아키텍처 다이어그램</div>
    <h1>{title}{version_suffix} — 계층 구조</h1>
    <div class="desc">{description}</div>
  </header>

  <div class="arch-grid">
    <div class="layers" id="layers"></div>
    {crosscut_rails_html}
  </div>

  {bottom_html}

  <footer>code-arch 스킬로 생성</footer>
</div>

<div class="panel-overlay" id="panelOverlay"></div>
<div class="side-panel" id="sidePanel">
  <button class="panel-close" id="panelClose">&times;</button>
  <div class="panel-layer-tag" id="panelLayerTag"></div>
  <div class="panel-name" id="panelName"></div>
  <div class="panel-desc" id="panelDesc"></div>
</div>

<script id="arch-data" type="application/json">
{json_data}
</script>
<script>
const D = JSON.parse(document.getElementById("arch-data").textContent);
const layersEl = document.getElementById("layers");

// --- Render layers ---
D.layers.forEach((l, i) => {{
  if (i > 0) {{
    const aw = document.createElement("div");
    aw.className = "layer-arrow";
    aw.innerHTML = '<div class="arrow-down"></div>';
    layersEl.appendChild(aw);
  }}
  const div = document.createElement("div");
  div.className = "layer";
  div.dataset.idx = i;
  div.style.background = "var(--l" + i + "-bg)";
  div.style.borderColor = "var(--l" + i + "-border)";

  let html = '<div class="layer-head">'
    + '<span class="layer-chevron">▾</span>'
    + '<div class="layer-num">' + (i + 1) + '</div>'
    + '<div class="layer-title">' + l.title + '</div>'
    + (l.sub ? '<div class="layer-sub">' + l.sub + '</div>' : '')
    + '</div><div class="comps">';

  l.components.forEach(c => {{
    html += '<div class="comp' + (c.main ? ' comp-main' : '') + '">'
      + c.name
      + (c.tip ? '<span class="tip">' + c.tip + '</span>' : '')
      + '</div>';
  }});
  html += '</div>';

  if (l.ext) {{
    html += '<div class="ext-badge" title="' + (l.ext.tip || '') + '">' + l.ext.label + '</div>';
  }}

  div.innerHTML = html;
  layersEl.appendChild(div);
}});

const layerEls = layersEl.querySelectorAll(".layer");

// --- Layer collapse/expand ---
layerEls.forEach(el => {{
  el.querySelector(".layer-head").addEventListener("click", () => {{
    el.classList.toggle("collapsed");
    repositionCrosscuts();
    repositionGroups();
  }});
}});

// --- Layer groups ---
const groups = D.groups || [];
if (groups.length) {{
  layersEl.classList.add("has-groups");
  groups.forEach((g, gi) => {{
    const first = layerEls[g.from];
    const last = layerEls[g.to];
    if (!first || !last) return;
    const top = first.offsetTop;
    const bottom = last.offsetTop + last.offsetHeight;
    const bar = document.createElement("div");
    bar.className = "group-bracket";
    bar.dataset.gi = gi;
    bar.style.top = top + "px";
    bar.style.height = (bottom - top) + "px";
    bar.style.background = "var(--g" + gi + ")";
    layersEl.appendChild(bar);
    const tag = document.createElement("div");
    tag.className = "group-tag";
    tag.dataset.gi = gi;
    tag.style.top = top + "px";
    tag.style.color = "var(--g" + gi + ")";
    tag.style.background = "var(--g" + gi + "-bg)";
    tag.textContent = g.name;
    layersEl.appendChild(tag);
    tag.addEventListener("click", () => {{
      const grouped = [...layerEls].slice(g.from, g.to + 1);
      const allCollapsed = grouped.every(e => e.classList.contains("collapsed"));
      grouped.forEach(e => {{
        if (allCollapsed) e.classList.remove("collapsed");
        else e.classList.add("collapsed");
      }});
      repositionCrosscuts();
      repositionGroups();
    }});
  }});
}}

function repositionGroups() {{
  const bars = layersEl.querySelectorAll(".group-bracket");
  const tags = layersEl.querySelectorAll(".group-tag");
  groups.forEach((g, gi) => {{
    const first = layerEls[g.from];
    const last = layerEls[g.to];
    if (!first || !last) return;
    const top = first.offsetTop;
    const bottom = last.offsetTop + last.offsetHeight;
    if (bars[gi]) {{ bars[gi].style.top = top + "px"; bars[gi].style.height = (bottom - top) + "px"; }}
    if (tags[gi]) {{ tags[gi].style.top = top + "px"; }}
  }});
}}

// --- Crosscut points ---
function repositionCrosscuts() {{
  (D.crosscuts || []).forEach((cc, ci) => {{
    const line = document.getElementById("ccLine" + ci);
    if (!line) return;
    const lineRect = line.getBoundingClientRect();
    const points = line.querySelectorAll(".cc-point");
    cc.points.forEach((pt, pi) => {{
      if (pi >= points.length) return;
      const wrap = points[pi];
      if (pt.at_layer !== undefined && layerEls[pt.at_layer]) {{
        const el = layerEls[pt.at_layer];
        const elRect = el.getBoundingClientRect();
        const center = elRect.top + elRect.height / 2;
        const pct = ((center - lineRect.top) / lineRect.height) * 100;
        wrap.style.top = Math.max(0, Math.min(100, pct)) + "%";
      }}
    }});
  }});
}}

(D.crosscuts || []).forEach((cc, ci) => {{
  const line = document.getElementById("ccLine" + ci);
  if (!line) return;
  const lineRect = line.getBoundingClientRect();
  cc.points.forEach(pt => {{
    const wrap = document.createElement("div");
    wrap.className = "cc-point";
    if (pt.at_layer !== undefined && layerEls[pt.at_layer]) {{
      const el = layerEls[pt.at_layer];
      const elRect = el.getBoundingClientRect();
      const center = elRect.top + elRect.height / 2;
      const pct = ((center - lineRect.top) / lineRect.height) * 100;
      wrap.style.top = Math.max(0, Math.min(100, pct)) + "%";
    }} else {{
      wrap.style.top = ((pt.at || 0) * 100) + "%";
    }}
    const color = "var(--cc" + ci + ")";
    const bg = "var(--cc" + ci + "-bg)";
    wrap.innerHTML =
      '<div class="cc-connector" style="border-color:' + color + '"></div>'
      + '<div class="cc-dot" style="background:' + color + '"></div>'
      + '<span class="cc-tag" style="color:' + color + ';background:' + bg + '">' + pt.name + '</span>';
    line.appendChild(wrap);
  }});
}});

// --- Side panel ---
const panel = document.getElementById("sidePanel");
const overlay = document.getElementById("panelOverlay");
const panelTag = document.getElementById("panelLayerTag");
const panelName = document.getElementById("panelName");
const panelDesc = document.getElementById("panelDesc");
let activeComp = null;

function openPanel(comp, layerTitle, layerIdx) {{
  if (activeComp) activeComp.classList.remove("active");
  activeComp = comp;
  comp.classList.add("active");
  const tipEl = comp.querySelector(".tip");
  panelTag.textContent = layerTitle;
  panelTag.style.background = "var(--l" + layerIdx + "-bg)";
  panelTag.style.color = "var(--l" + layerIdx + "-fg)";
  panelTag.style.border = "1px solid var(--l" + layerIdx + "-border)";
  const nameText = comp.firstChild ? comp.firstChild.textContent.trim() : comp.textContent.trim();
  panelName.textContent = nameText;
  if (tipEl && tipEl.textContent.trim()) {{
    panelDesc.textContent = tipEl.textContent;
    panelDesc.classList.remove("panel-empty");
  }} else {{
    panelDesc.textContent = "상세 설명 없음";
    panelDesc.classList.add("panel-empty");
  }}
  panel.classList.add("open");
  overlay.classList.add("open");
}}

function closePanel() {{
  panel.classList.remove("open");
  overlay.classList.remove("open");
  if (activeComp) {{ activeComp.classList.remove("active"); activeComp = null; }}
}}

overlay.addEventListener("click", closePanel);
document.getElementById("panelClose").addEventListener("click", closePanel);
document.addEventListener("keydown", e => {{ if (e.key === "Escape") closePanel(); }});

document.querySelectorAll(".comp").forEach(comp => {{
  const layer = comp.closest(".layer");
  const idx = parseInt(layer.dataset.idx);
  const title = D.layers[idx].title;
  comp.addEventListener("click", e => {{
    e.stopPropagation();
    openPanel(comp, title, idx);
  }});
}});
</script>
</body>
</html>"""


def build_crosscut_rails(crosscuts):
    if not crosscuts:
        return "", ""
    cols = " " + " ".join(["auto"] * len(crosscuts))
    rails = []
    for i, cc in enumerate(crosscuts):
        rails.append(
            f'<div class="cc-rail">'
            f'<div class="cc-label" style="color:var(--cc{i})">{cc["name"]}</div>'
            f'<div class="cc-line" id="ccLine{i}" '
            f'style="background:var(--cc{i}-bg);border:1px solid var(--cc{i})"></div>'
            f'</div>'
        )
    return "\n    ".join(rails), cols


def build_bottom(data, crosscuts):
    has_lifecycle = bool(data.get("lifecycle"))
    has_extensions = bool(data.get("extensions"))
    if not has_lifecycle and not has_extensions:
        return ""

    cards = []
    if has_lifecycle:
        items = "".join(
            f'<li><span style="color:var(--text-faint);font-size:9px;min-width:14px">{j+1}.</span>'
            f'<span class="ln" style="color:var(--lc-color)">{h["name"]}</span>'
            f'<span class="ld">{h.get("desc","")}</span></li>'
            for j, h in enumerate(data["lifecycle"])
        )
        cards.append(
            '<div class="info-card">'
            '<div class="info-title"><div class="dot" style="background:var(--lc-color)"></div>'
            '실행 순서</div>'
            f'<ol class="lc-list">{items}</ol></div>'
        )
    if has_extensions:
        items = "".join(
            f'<li><span class="ek">{e["key"]}</span><span class="ev">{e["val"]}</span></li>'
            for e in data["extensions"]
        )
        cards.append(
            '<div class="info-card">'
            '<div class="info-title"><div class="dot" style="background:var(--ext-color)"></div>'
            '확장 포인트 안내</div>'
            f'<ul class="ext-list">{items}</ul></div>'
        )

    if len(cards) == 1:
        return f'<div style="margin-top:24px">{cards[0]}</div>'
    return f'<div class="bottom-grid">{"".join(cards)}</div>'


def render(data):
    validate(data)
    proj = data["project"]
    crosscuts = data.get("crosscuts", [])
    groups = data.get("groups", [])

    layer_vl, layer_vd = build_layer_vars(data["layers"])
    cc_vl, cc_vd = build_crosscut_vars(crosscuts)
    g_vl, g_vd = build_group_vars(groups)
    rails_html, grid_cols = build_crosscut_rails(crosscuts)
    bottom_html = build_bottom(data, crosscuts)

    version = proj.get("version", "")
    version_suffix = f" {version}" if version else ""

    return TEMPLATE.format(
        title=proj["name"],
        version_suffix=version_suffix,
        description=proj.get("description", ""),
        layer_vars_light=layer_vl,
        layer_vars_dark=layer_vd,
        crosscut_vars_light=cc_vl,
        crosscut_vars_dark=cc_vd,
        group_vars_light=g_vl,
        group_vars_dark=g_vd,
        crosscut_cols=grid_cols,
        crosscut_rails_html=rails_html,
        bottom_html=bottom_html,
        json_data=json.dumps(data, ensure_ascii=False),
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: render_architecture.py <arch.json> [-o output.html]", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    out = None
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            out = Path(sys.argv[idx + 1])

    data = json.loads(src.read_text("utf-8"))
    html = render(data)

    if out:
        out.write_text(html, "utf-8")
        print(f"wrote {out}")
    else:
        print(html)


if __name__ == "__main__":
    main()
