# 출처 기록 (에이전트 스킬)

점검일: 2026-10-28. 외부망에서 아래 커밋의 해당 디렉터리만 가져와 복사했다. 수정 내용은 `docs/agent-skills.md` §4,
라이선스 요약은 `THIRD_PARTY_NOTICES.md`에 있다. 해시는 각 스킬 폴더에 복사한 LICENSE 파일의 SHA-256이다.

| 원본 레포 | 기준 커밋 | 가져온 경로 | 라이선스 | LICENSE SHA-256 |
|---|---|---|---|---|
| `obra/superpowers` | `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` | `skills/{systematic-debugging,verification-before-completion,receiving-code-review,test-driven-development}` | MIT | `a37e0e9697144819e1d965176ac4ae5bc3fa02d11e7812036bbcadf6dafe2400` |
| `K-Dense-AI/scientific-agent-skills` | `593377bb048752abb0152deab9fbb1083a6087df` (matplotlib, polars) / `5f2bc0341354fd5590aef76a533ada1e1e5b4e62` (report-templates 의 `templates/`) | `skills/{matplotlib,polars}`, `skills/markdown-mermaid-writing/templates/{status_report,decision_record,pull_request}.md` | MIT (`LICENSE.md`); 템플릿 원저작 Apache-2.0 | `09b02a3c9df3053c55531d503357a9c7cde275970e6c3ceaa1ddf5f0e90b40c1` |
| `trailofbits/skills` | `196a9073ab10d35bacf111f945e02c00b2c6883a` (property-based-testing); differential-review 는 2026-10-23 로컬 트리밍본에서 복사(원본 커밋 미기록) | `plugins/property-based-testing/skills/property-based-testing`, `plugins/differential-review/skills/differential-review` 중 `SKILL.md`, `methodology.md`, `reporting.md` | CC-BY-SA-4.0 | `7abe19ec9bb73b36141b999b861d24ad855e808bafe0f81e84cce28556f6c297` |
| `wshobson/agents` | `0874a27b17a22e2b7c2e2bcd725768e0803cad06` | `plugins/shell-scripting/skills/bash-defensive-patterns`, `plugins/incident-response/skills/postmortem-writing` | MIT | `f89abb55d9f073f38f1703e4518f0613c788c6174be7f13b8dfe48a1c076c746` |
| `openai/skills` (deprecated → openai/plugins) | `49f948faa9258a0c61caceaf225e179651397431` | `skills/.curated/{pdf,security-best-practices,security-threat-model,define-goal}` | Apache-2.0 | `4dd13869245e356246a5b770723247bbb80a8f07a181d1d3d873a1734297cdb9` |
| `lewislulu/html-ppt-skill` | `fd1629067909ff55b36b905476de4e5f26062a1f` | 루트(단, `docs/`, `examples/`, `scripts/verify-output/`, `scripts/*.sh` 제외) | MIT | `a5ed4059e25a3ec35e439abd2623753d1f42d4aa4989ffb5c6b7a97b61f6a949` |
| `zarazhangrui/frontend-slides` | `9906a34d640d2111f724544cbc50f7f130569ae1` | 루트(단, `plugins/`, `scripts/deploy.sh`, `scripts/export-pdf.sh` 제외) | MIT | `62928eb197fe4662d1efc3af0735b3ba5df3c0308badd9a2baf2b619009f5366` |
| `lazypay/Archscribe` | `46ea42cfc6c557ab238867c390bb18320fd36769` | `SKILL.md`, `README.en.md`, `requirements.txt`, `scripts/`, `references/`, `agents/`, `assets/{fonts,icons,vendor,default-spec.json}` | MIT | `4eb0467d029cf990c0d08b8f4a3e05e279ed675f428edbd414fe3126d809da80` |
| `CSlawyer1985/html-to-pdf-skill` | `6f6e653112f7a1a56342796b2a6fe460725c260e` | 루트(단, `CONTRIBUTING.md` 제외; `SKILL.md`는 재작성) | MIT | `f6089584054f72089334322b4aab00433ed2b38f904c57790fad724267a1e871` |
| `hugohe3/ppt-master` | `523e5bd972f94c3cac8742fec0d54d43824a17bb` | `skills/ppt-master` (제외: `templates/icons/{chunk-filled,simple-icons,tabler-outline}`, `templates/sounds`, `scripts/tests`, `.env.example`) | MIT | `80cefc234c1ec12a8cece4344f16300c634fa03df7891686fcf979e3828f0921` |

벤더 JS(`html-ppt/assets/vendor/`): Chart.js 4.4.3 `chart.umd.min.js` `d46d97a1fd022c5fb29fa2f45ebcbc32202d73aeebf076ce5f7248f5498fc7d7`,
highlight.js 11.10.0 `highlight.min.js`(cdnjs 빌드) `471ef9ae90c407af440fcdc48edfeeb562106b3267bd12d99071c162fb52ed32`, `tokyo-night-dark.min.css`
`3c24d046d2e1e02b9e8beb641f9dc639c76ff44ad89f0fbac9eab9062d55f51b`.

자체 제작 스킬(`code-map`, `code-audit`, `code-flow`, `code-arch`, `code-port`, `debug-fix`, `test-gap`)은 이 저장소의 git 이력이 출처다.
2026-10-23 이전 구성은 `jake-private` 저장소의 `docs/agent-skills.md`·`docs/source-inventory.md`에 있다.
