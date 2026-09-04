#!/usr/bin/env python3
"""jake:audit / code-review findings JSON -> self-contained HTML dashboard.

Usage:
    python3 audit_dashboard.py findings.json -o audit.html
    python3 audit_dashboard.py --example > findings.json

No dependencies beyond the standard library. The output HTML embeds its data,
CSS and JS inline (no CDN, no fetch()) so it opens correctly from a plain
`file://` path -- e.g. after being carried into a closed network via git.

Findings JSON schema:

{
  "run": {
    "repo": "my-project",
    "target": "main@<commit>",
    "mode": "changes-audit",   // or "codebase-audit"
    "date": "2026-08-26"
  },
  "audited_clean": "one-line summary of what was checked and came back clean",
  "findings": [
    {
      "site": "path/to/file.py:123",
      "lens": "correctness",        // correctness | contract | structure | evidence
      "severity": "blocking",       // blocking | advisory | low-confidence
      "title": "short one-line description",
      "scenario": "concrete input/state -> wrong outcome",
      "fix": "smallest fix direction"
    }
  ]
}

These field names match jake:audit's own vocabulary (audit-rubric.md's four
lenses, finding-format.md's severity levels), so a jake:audit report can be
transcribed into this JSON with no renaming.
"""

import argparse
import datetime
import json
import sys

REQUIRED_RUN_FIELDS = ["repo", "target", "mode", "date"]
REQUIRED_FINDING_FIELDS = ["site", "lens", "severity", "title", "scenario", "fix"]
VALID_LENSES = {"correctness", "contract", "structure", "evidence"}
VALID_SEVERITIES = {"blocking", "advisory", "low-confidence"}

EXAMPLE_DATA = {
    "run": {
        "repo": "my-project",
        "target": "main@<commit>",
        "mode": "changes-audit",
        "date": datetime.date.today().isoformat(),
    },
    "audited_clean": "렌더링 루프, 입력 처리, 저장/불러오기 경로는 확인했고 이상 없음.",
    "findings": [
        {
            "site": "src/example.py:42",
            "lens": "correctness",
            "severity": "blocking",
            "title": "짧은 한 줄 설명",
            "scenario": "이 입력/상태 -> 이 잘못된 결과 (테스트로 옮길 수 있을 만큼 구체적으로)",
            "fix": "가장 작은 수정 방향",
        }
    ],
}


def validate(data):
    errors = []
    run = data.get("run", {})
    for f in REQUIRED_RUN_FIELDS:
        if not run.get(f):
            errors.append(f"run.{f} is missing")
    if "audited_clean" not in data:
        errors.append("audited_clean is missing")

    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []

    for i, finding in enumerate(findings):
        for f in REQUIRED_FINDING_FIELDS:
            if not finding.get(f):
                errors.append(f"findings[{i}].{f} is missing")
        lens = finding.get("lens")
        if lens and lens not in VALID_LENSES:
            errors.append(f"findings[{i}].lens '{lens}' not in {sorted(VALID_LENSES)}")
        severity = finding.get("severity")
        if severity and severity not in VALID_SEVERITIES:
            errors.append(f"findings[{i}].severity '{severity}' not in {sorted(VALID_SEVERITIES)}")

    if errors:
        raise ValueError("invalid findings JSON:\n  - " + "\n  - ".join(errors))


def render(data):
    project_name = data["run"]["repo"]
    json_blob = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return (
        HTML_TEMPLATE
        .replace("__PROJECT_NAME__", project_name)
        .replace("__AUDIT_DATA_JSON__", json_blob)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", help="findings JSON file ('-' for stdin)")
    parser.add_argument("-o", "--output", help="output HTML path (default: <repo>-audit.html)")
    parser.add_argument("--example", action="store_true", help="print an example findings JSON to stdout and exit")
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

    output_path = args.output or f"{data['run']['repo']}-audit.html"
    html = render(data)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {output_path}")


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PROJECT_NAME__ — Audit Dashboard</title>
<style>
  :root {
    --bg: #f6f7f9;
    --bg-card: #ffffff;
    --bg-subtle: #eef0f3;
    --border: #dde1e6;
    --text: #1a1d23;
    --text-dim: #5b6270;
    --accent: #2f5fda;
    --blocking: #c4291c;
    --blocking-bg: #fdecea;
    --advisory: #a15c00;
    --advisory-bg: #fdf3e2;
    --lowconf: #6b7280;
    --lowconf-bg: #eef0f2;
    --clean: #1f8a4c;
    --clean-bg: #e9f7ef;
    --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Pretendard, "Noto Sans KR", sans-serif;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #14161a;
      --bg-card: #1c1f26;
      --bg-subtle: #22262e;
      --border: #2c313a;
      --text: #e7e9ee;
      --text-dim: #9aa2b1;
      --accent: #7da3ff;
      --blocking: #ff7a6e;
      --blocking-bg: #3a1917;
      --advisory: #f0b357;
      --advisory-bg: #382a11;
      --lowconf: #9aa2b1;
      --lowconf-bg: #262a31;
      --clean: #5fd08a;
      --clean-bg: #12291c;
    }
  }
  :root[data-theme="dark"] {
    --bg: #14161a;
    --bg-card: #1c1f26;
    --bg-subtle: #22262e;
    --border: #2c313a;
    --text: #e7e9ee;
    --text-dim: #9aa2b1;
    --accent: #7da3ff;
    --blocking: #ff7a6e;
    --blocking-bg: #3a1917;
    --advisory: #f0b357;
    --advisory-bg: #382a11;
    --lowconf: #9aa2b1;
    --lowconf-bg: #262a31;
    --clean: #5fd08a;
    --clean-bg: #12291c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    line-height: 1.5;
  }
  .wrap {
    max-width: 920px;
    margin: 0 auto;
    padding: 32px 20px 64px;
  }
  header {
    margin-bottom: 24px;
  }
  header .kicker {
    font-size: 12px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-dim);
    font-weight: 600;
  }
  header h1 {
    font-size: 26px;
    margin: 4px 0 8px;
  }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    font-size: 13px;
    color: var(--text-dim);
  }
  .meta code {
    font-family: var(--mono);
    background: var(--bg-subtle);
    padding: 1px 6px;
    border-radius: 4px;
  }

  .summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 24px 0;
  }
  @media (max-width: 640px) {
    .summary { grid-template-columns: repeat(2, 1fr); }
  }
  .summary-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
  }
  .summary-card .lens-name {
    font-size: 12px;
    color: var(--text-dim);
    margin-bottom: 6px;
  }
  .summary-card .lens-count {
    font-size: 24px;
    font-weight: 700;
  }
  .summary-card .lens-breakdown {
    font-size: 12px;
    color: var(--text-dim);
    margin-top: 4px;
  }

  .totals {
    display: flex;
    gap: 10px;
    margin: 4px 0 20px;
    flex-wrap: wrap;
  }
  .pill {
    font-size: 12px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .pill.blocking { background: var(--blocking-bg); color: var(--blocking); }
  .pill.advisory { background: var(--advisory-bg); color: var(--advisory); }
  .pill.clean { background: var(--clean-bg); color: var(--clean); }

  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }
  .filter-btn {
    font-family: inherit;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 14px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: var(--text-dim);
    cursor: pointer;
  }
  .filter-btn:hover { border-color: var(--accent); color: var(--text); }
  .filter-btn.active {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }

  .findings { display: flex; flex-direction: column; gap: 10px; }
  .finding {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 4px solid var(--lowconf);
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
  }
  .finding[data-severity="blocking"] { border-left-color: var(--blocking); }
  .finding[data-severity="advisory"] { border-left-color: var(--advisory); }
  .finding[data-severity="low-confidence"] { border-left-color: var(--lowconf); }

  .finding-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  .finding-title {
    font-size: 14px;
    font-weight: 600;
  }
  .finding-tags {
    display: flex;
    gap: 6px;
    flex-shrink: 0;
  }
  .tag {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .tag.sev-blocking { background: var(--blocking-bg); color: var(--blocking); }
  .tag.sev-advisory { background: var(--advisory-bg); color: var(--advisory); }
  .tag.sev-low-confidence { background: var(--lowconf-bg); color: var(--lowconf); }
  .tag.lens { background: var(--bg-subtle); color: var(--text-dim); }

  .finding-site {
    font-family: var(--mono);
    font-size: 12px;
    color: var(--accent);
    margin-top: 4px;
  }

  .finding-body {
    display: none;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed var(--border);
    font-size: 13.5px;
  }
  .finding.open .finding-body { display: block; }
  .finding-body .row { margin-bottom: 8px; }
  .finding-body .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-dim);
    margin-bottom: 3px;
    font-weight: 700;
  }

  footer {
    margin-top: 28px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-size: 13px;
    color: var(--text-dim);
  }
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-dim);
    font-size: 14px;
  }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="kicker">jake:audit report</div>
    <h1>__PROJECT_NAME__ — Audit Dashboard</h1>
    <div class="meta"></div>
  </header>

  <div class="totals" id="totals"></div>

  <div class="summary" id="summary"></div>

  <div class="filters" id="filters"></div>

  <div class="findings" id="findings"></div>

  <div class="empty-state" id="empty-state" style="display:none;">이 필터에 해당하는 항목이 없습니다.</div>

  <footer id="footer"></footer>

</div>

<script id="audit-data" type="application/json">
__AUDIT_DATA_JSON__
</script>

<script>
(function () {
  const data = JSON.parse(document.getElementById('audit-data').textContent);
  const findings = data.findings;

  const lensLabels = {
    correctness: '기능 (correctness)',
    contract: '계약/문서 (contract)',
    structure: '구조 (structure)',
    evidence: '근거 (evidence)'
  };
  const sevLabels = {
    blocking: 'BLOCKING',
    advisory: 'ADVISORY',
    'low-confidence': 'LOW-CONF'
  };

  document.querySelector('.meta').innerHTML =
    `<span>repo: <code>${data.run.repo}</code></span>` +
    `<span>target: <code>${data.run.target}</code></span>` +
    `<span>mode: ${data.run.mode}</span>` +
    `<span>date: ${data.run.date}</span>`;

  const blockingCount = findings.filter(f => f.severity === 'blocking').length;
  const advisoryCount = findings.filter(f => f.severity !== 'blocking').length;
  document.getElementById('totals').innerHTML = `
    <span class="pill blocking">반드시 고쳐야 함 ${blockingCount}건</span>
    <span class="pill advisory">참고 사항 ${advisoryCount}건</span>
  `;

  const lensOrder = ['correctness', 'contract', 'structure', 'evidence'];
  const summaryEl = document.getElementById('summary');
  lensOrder.forEach(lens => {
    const items = findings.filter(f => f.lens === lens);
    const b = items.filter(f => f.severity === 'blocking').length;
    const a = items.length - b;
    const card = document.createElement('div');
    card.className = 'summary-card';
    card.innerHTML = `
      <div class="lens-name">${lensLabels[lens]}</div>
      <div class="lens-count">${items.length}</div>
      <div class="lens-breakdown">${items.length === 0 ? '깨끗함' : `${b ? `blocking ${b}` : ''}${b && a ? ' · ' : ''}${a ? `advisory ${a}` : ''}`}</div>
    `;
    summaryEl.appendChild(card);
  });

  const filtersEl = document.getElementById('filters');
  const filterDefs = [
    { key: 'all', label: '전체' },
    { key: 'sev:blocking', label: '반드시 고쳐야 함' },
    { key: 'sev:advisory', label: '참고 사항' },
    { key: 'lens:correctness', label: lensLabels.correctness },
    { key: 'lens:contract', label: lensLabels.contract },
    { key: 'lens:structure', label: lensLabels.structure },
    { key: 'lens:evidence', label: lensLabels.evidence }
  ];
  let activeFilter = 'all';

  function matches(f, key) {
    if (key === 'all') return true;
    const [type, val] = key.split(':');
    if (type === 'sev') return val === 'blocking' ? f.severity === 'blocking' : f.severity !== 'blocking';
    if (type === 'lens') return f.lens === val;
    return true;
  }

  filterDefs.forEach(def => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn' + (def.key === 'all' ? ' active' : '');
    btn.textContent = def.label;
    btn.addEventListener('click', () => {
      activeFilter = def.key;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      render();
    });
    filtersEl.appendChild(btn);
  });

  const findingsEl = document.getElementById('findings');
  const emptyEl = document.getElementById('empty-state');

  function render() {
    findingsEl.innerHTML = '';
    const visible = findings
      .slice()
      .sort((a, b) => (a.severity === 'blocking' ? 0 : 1) - (b.severity === 'blocking' ? 0 : 1))
      .filter(f => matches(f, activeFilter));

    emptyEl.style.display = visible.length ? 'none' : 'block';

    visible.forEach(f => {
      const card = document.createElement('div');
      card.className = 'finding';
      card.dataset.severity = f.severity;
      card.innerHTML = `
        <div class="finding-head">
          <div>
            <div class="finding-title">${f.title}</div>
            <div class="finding-site">${f.site}</div>
          </div>
          <div class="finding-tags">
            <span class="tag lens">${lensLabels[f.lens].split(' ')[0]}</span>
            <span class="tag sev-${f.severity}">${sevLabels[f.severity]}</span>
          </div>
        </div>
        <div class="finding-body">
          <div class="row">
            <div class="label">실패 시나리오</div>
            <div>${f.scenario}</div>
          </div>
          <div class="row">
            <div class="label">수정 방향</div>
            <div>${f.fix}</div>
          </div>
        </div>
      `;
      card.addEventListener('click', () => card.classList.toggle('open'));
      findingsEl.appendChild(card);
    });
  }
  render();

  document.getElementById('footer').innerHTML =
    `<strong>감사 범위 및 클린 항목:</strong> ${data.audited_clean}`;
})();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    main()
