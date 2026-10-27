---
name: report-templates
description: "[KO] 주간/월간 상태 보고·결정 기록(ADR)·PR 설명을 정해진 마크다운 양식으로 쓸 때. Three Markdown templates (status report / executive briefing, decision record, pull request) with a fill-in checklist. Use when the user asks for a status report, project update, decision record, ADR, or PR description; not for incident postmortems (use postmortem-writing)."
---

# Report templates

Markdown templates for the three reports that repeat most often in repository work.
Writing needs no runtime. The output is a plain `.md` file.

| Template | Use for | File |
|---|---|---|
| Status report | weekly/monthly update, executive briefing, risk register | `templates/status_report.md` |
| Decision record | ADR: one decision, its options, and consequences | `templates/decision_record.md` |
| Pull request | PR body with before/after evidence and test notes | `templates/pull_request.md` |

## How to use

1. Read the repository evidence first (README, docs, test output, git log). Write the content as bullet notes before opening a template.
2. Copy the matching template and fill every section. Delete a section only when the template says it is optional.
3. Put numbers, dates, and file paths in the text. "Improved" without a number is not finished.
4. Lead with what the reader must act on: the TL;DR, the decisions needed, the risks.
5. Diagrams: keep Mermaid blocks as text. The air-gapped host may not render them; add a one-line text description under each block.

## Rules for this bundle

- No network. Do not fetch external templates or images.
- Save under the path the user gives. Default: `docs/reports/<yyyy-mm-dd>-<topic>.md`.
- For incident postmortems use the `postmortem-writing` skill instead.

## Source

Templates come from `K-Dense-AI/scientific-agent-skills` (`skills/markdown-mermaid-writing/templates`, MIT), which carry them from
`SuperiorByteWorks-LLC/agent-project` (Apache-2.0). The style-guide back-links were removed because the guides are not bundled.
