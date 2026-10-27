# Third-party notices

Every skill directory keeps its upstream LICENSE file. Source commits and the SHA-256 of each copied license file are in
`docs/source-inventory.md`. Modifications made in this repository are listed in `docs/agent-skills.md` §4
(every SKILL.md `description` additionally carries a `[KO] …` Korean trigger prefix).

## `.agents/skills/` (active bundle)

| Directory | Upstream | License |
|---|---|---|
| `systematic-debugging`, `verification-before-completion`, `receiving-code-review`, `test-driven-development` | obra/superpowers | MIT |
| `property-based-testing`, `differential-review` | trailofbits/skills | CC-BY-SA-4.0 — modified copies must stay CC-BY-SA-4.0 with attribution; see `LICENSES/CC-BY-SA-4.0.txt` |
| `bash-defensive-patterns`, `postmortem-writing` | wshobson/agents | MIT |
| `matplotlib` | K-Dense-AI/scientific-agent-skills | MIT |
| `report-templates` | templates from K-Dense-AI/scientific-agent-skills (MIT), originally SuperiorByteWorks-LLC/agent-project | Apache-2.0 (`report-templates/LICENSE`, `NOTICE.md`) |
| `pdf` | openai/skills (`skills/.curated/pdf`) | Apache-2.0 (`pdf/LICENSE.txt`) |
| `html-ppt` | lewislulu/html-ppt-skill | MIT. Bundled `assets/vendor/`: Chart.js 4.4.3 (MIT), highlight.js 11.10.0 (BSD-3-Clause) |
| `archscribe` | lazypay/Archscribe | MIT. Bundled fonts: Excalifont, Noto Sans SC subset (SIL OFL, see `archscribe/assets/fonts`) |
| `html-to-pdf` | CSlawyer1985/html-to-pdf-skill | MIT |
| `code-map`, `code-audit`, `test-gap` | this repository | same as repository |

## `optional/skills/` (not on the Codex discovery path)

| Directory | Upstream | License |
|---|---|---|
| `ppt-master` | hugohe3/ppt-master (`skills/ppt-master`) | MIT. Icon sets under `templates/icons` carry their own notices |
| `frontend-slides` | zarazhangrui/frontend-slides | MIT |
| `polars` | K-Dense-AI/scientific-agent-skills | MIT |
| `security-best-practices`, `security-threat-model`, `define-goal` | openai/skills (`skills/.curated/*`) | Apache-2.0 (`LICENSE.txt` in each) |
| `code-flow`, `code-arch`, `code-port`, `debug-fix` | this repository | same as repository |

Python packages installed from `requirements-skills.txt` / `requirements-optional.txt` are not redistributed here.
PyMuPDF (used only by `html-to-pdf`) is AGPL-3.0.
