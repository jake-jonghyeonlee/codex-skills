#!/usr/bin/env python3
"""/code-review findings (ReportFindings shape) -> audit_dashboard.py schema.

Usage:
    python3 code_review_adapter.py review.json --repo my-project -o findings.json
    python3 audit_dashboard.py findings.json -o my-project-audit.html

Input: a JSON array of code-review findings -- the same shape passed to the
ReportFindings tool's `findings` argument, e.g.:

[
  {
    "file": "src/foo.py",
    "line": 42,
    "category": "correctness",
    "summary": "one-sentence statement of the defect",
    "failure_scenario": "concrete input/state -> wrong output/crash",
    "short_summary": "compressed label, <=60 chars",
    "verdict": "CONFIRMED"
  }
]

A finding may also carry explicit "severity" and/or "lens" keys -- set these
after a human skim (per the code-audit skill's checkpoint step) to
override this script's category/verdict-based guess for that one item.

Known coverage gaps versus jake:audit (worth knowing before relying on this):
  - No "contract" lens equivalent -- code-review doesn't hunt for doc-vs-code
    mismatches, so that lens will always come back empty through this path.
  - No native blocking/advisory severity axis -- `infer_severity()` below is
    a heuristic (category + verdict), not a judgment code-review actually
    made. Treat the result as a starting point to skim, not ground truth.
  - No "suggested fix" field -- `summary` is reused for the fix slot since
    it's the closest thing code-review returns.

For a freshly received repo with no meaningful diff/base branch, point
/code-review at a path target covering the whole tree (e.g. a broad `high`
or `max` effort run against the repo root) rather than relying on its
diff-only default -- otherwise it may find nothing to review.
"""

import argparse
import datetime
import json
import sys

CATEGORY_TO_LENS = {
    "correctness": "correctness",
    "test-coverage": "evidence",
}
# Anything else (simplification, efficiency, reuse, duplication, dead-code,
# ...) falls into "structure" -- see infer_lens().

VALID_LENSES = {"correctness", "contract", "structure", "evidence"}
VALID_SEVERITIES = {"blocking", "advisory", "low-confidence"}


def infer_lens(category):
    return CATEGORY_TO_LENS.get(category, "structure")


def infer_severity(finding):
    if finding.get("verdict") == "PLAUSIBLE":
        return "low-confidence"
    if finding.get("category") == "correctness":
        return "blocking"
    return "advisory"


def convert(reviews, repo, target, mode, date, audited_clean):
    findings = []
    unmapped_categories = set()

    for r in reviews:
        if "file" not in r or "summary" not in r or "failure_scenario" not in r:
            raise ValueError(f"finding missing required field(s) (file/summary/failure_scenario): {r}")

        category = r.get("category", "")
        if category and category not in CATEGORY_TO_LENS:
            unmapped_categories.add(category)

        lens = r.get("lens") or infer_lens(category)
        if lens not in VALID_LENSES:
            raise ValueError(f"finding has invalid lens override '{lens}': {r}")

        severity = r.get("severity") or infer_severity(r)
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"finding has invalid severity override '{severity}': {r}")

        site = r["file"]
        if r.get("line"):
            site += f":{r['line']}"

        findings.append({
            "site": site,
            "lens": lens,
            "severity": severity,
            "title": r.get("short_summary") or r["summary"][:60],
            "scenario": r["failure_scenario"],
            "fix": r["summary"],
        })

    if unmapped_categories:
        print(
            f"note: categories mapped into the 'structure' bucket: {sorted(unmapped_categories)}",
            file=sys.stderr,
        )

    return {
        "run": {"repo": repo, "target": target, "mode": mode, "date": date},
        "audited_clean": audited_clean,
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", help="code-review findings JSON file ('-' or omitted for stdin)")
    parser.add_argument("--repo", required=True, help="project name, e.g. my-project")
    parser.add_argument("--target", default="HEAD", help="e.g. main@<commit>")
    parser.add_argument("--mode", default="codebase-audit", choices=["codebase-audit", "changes-audit"])
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument(
        "--audited-clean",
        default="code-review로 스캔했고, 아래 목록 외 항목은 findings가 보고되지 않음.",
        help="one-line summary shown in the dashboard footer",
    )
    parser.add_argument("-o", "--output", help="output path (default: stdout)")
    args = parser.parse_args()

    raw = sys.stdin.read() if args.input in (None, "-") else open(args.input, encoding="utf-8").read()

    try:
        reviews = json.loads(raw)
        if not isinstance(reviews, list):
            raise ValueError("input must be a JSON array of findings")
        data = convert(reviews, args.repo, args.target, args.mode, args.date, args.audited_clean)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    out = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
