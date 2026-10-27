# Codex 앱 스킬 가이드 (이 번들을 포함한 저장소용)

이 저장소의 `.agents/skills/` 에 스킬 17개가 있다. 태스크에서 `$스킬이름` 으로 부르거나 설명에 맞는 요청이면 Codex 가 스스로 고른다.
`optional/skills/` 는 탐색 경로 밖이다. 사용자가 켜 달라고 하면 그 폴더를 `.agents/skills/` 로 복사한 뒤 쓴다.

## 실행 환경

- 폐쇄망 Windows x64, CPython 3.12. 네트워크·외부 API·CDN·npm·Playwright 없음. API 키를 묻는 단계가 나오면 그 기능은 이 복사본에서 제거된 것이니 건너뛴다.
- Python 은 `.venv-skills/Scripts/python.exe` (Git Bash: `source .venv-skills/Scripts/activate`). `python3` 대신 `python` 을 쓴다. 스킬 문서의 `python3 ${SKILL_DIR}/...` 는 경로를 바꿔 쓴다.
- 스크립트 경로는 SKILL.md 가 있는 디렉터리 기준 `scripts/` 다: `python .agents/skills/code-map/scripts/codemap_dashboard.py project.json -o docs/codemap.html`.
- 비대화형 태스크에서는 중간 확인을 구하지 말고 끝까지 간다. 대화형이면 범위가 모호할 때만 묻는다.

## 단계별 스킬 (강제 순서 아님)

| 단계 | 스킬 | 규칙 |
|---|---|---|
| 이해 (읽기 전용) | `code-map` | 모듈·심볼·의존관계 JSON → 자체 완결 HTML. 코드 수정 금지 |
| 구현 | `test-driven-development` | 실패하는 테스트 → 최소 구현 → 리팩터. 테스트가 먼저 실패하는 것을 확인하고 기록 |
| 구현 | `property-based-testing` | 변환·파서·수치 함수에 Hypothesis 속성 테스트 |
| 구현 | `bash-defensive-patterns` | 셸 스크립트를 쓸 때 `set -euo pipefail` 등 방어 패턴 |
| 디버깅 | `systematic-debugging` | 재현 → 패턴 → 가설 → 수정. 원인 없이 수정하지 않는다 |
| 검사 (읽기 전용) | `code-audit` | 전체(`codebase-audit`) 또는 diff(`changes-audit`) 결함 리포트 HTML. 결함을 고치지 않는다 |
| 검사 (읽기 전용) | `differential-review` | diff 의 보안·회귀·영향 범위·테스트 커버리지 검토. `gh` 없이 `git diff <base>..<head>` 로 대상을 잡는다 |
| 검사 | `test-gap` | "분석만" 이면 플랜만, "작성" 이면 테스트 코드 생성 |
| 마감 | `verification-before-completion` | 완료·수정·통과를 말하기 전에 검증 명령을 실행하고 출력을 확인 |
| 마감 | `receiving-code-review` | 리뷰 지적은 검증한 뒤 반영. 맞장구로 반영하지 않는다 |
| 보고서 | `report-templates` | 상태 보고·결정 기록·PR 설명 양식. 내용(근거 수치·날짜·경로)을 마크다운으로 먼저 쓰고 양식에 채운다 |
| 보고서 | `postmortem-writing` | 장애·실패 회고 |
| 자료화 | `html-ppt` → `html-to-pdf` / `pdf` | HTML 덱 → PDF. Chrome headless 가 막힌 PC 에서는 `pdf`(reportlab) |
| 자료화 | `archscribe`, `matplotlib` | 다이어그램(Pillow 렌더러), 그래프 |

## 자료화 운용 규칙

내용과 형식을 분리한다. 스킬은 형식(레이아웃·테마·오프라인 자산·PDF 변환)만 책임진다.
1. 저장소의 README·docs·결과 파일을 읽고 보고서 **내용을 마크다운으로 먼저** 쓴다(독자, 결정할 것, 근거 수치·날짜 포함). 이 단계에서는 스킬을 부르지 않는다.
2. 그 마크다운을 입력으로 스킬을 불러 HTML·PDF 로 **렌더링만** 시킨다.
3. 결과를 눈으로 확인한다(PNG 썸네일, PDF 첫 페이지). 형식 흠은 CSS 에서, 내용 흠은 1번으로 돌아가 고친다.

HTML 은 자체 완결이어야 한다: 외부 `<script src>`·`<link>` 없음, 글꼴은 `Segoe UI`·`Malgun Gothic`·`Consolas`, 이미지는 `data:` URI 또는 같은 폴더.

## 산출물 저장

- HTML 리포트: `docs/<project>-codemap.html`, `docs/<project>-audit.html`
- 마크다운 보고서: `docs/reports/<yyyy-mm-dd>-<topic>.md`
- 발표 자료·PDF: 저장소 밖(예: `D:\work\자료`) 또는 `outputs/`(git-ignored)
- 태스크에서 다른 경로를 지정하면 그 경로를 따른다.

## 토큰 절약

- 범위를 좁힌다: "전체 레포" 대신 "src/models/ 디렉터리만".
- 최소 조합: `code-map` + `code-audit`. 검토만이면 `differential-review` 하나.
- `test-gap` 은 "분석만", `systematic-debugging` 은 "진단만" 으로 요청할 수 있다.
- 한 태스크에 관련 스킬을 묶으면 컨텍스트를 공유한다.
