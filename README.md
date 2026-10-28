# codex-skills — 폐쇄망 Codex 앱용 스킬 번들

코딩 작업과 저장소 보고서 작성에 쓰는 에이전트 스킬 **17종**(+선택 10종)을 한 저장소에 모았다.
대상 환경은 사내 폐쇄망 Windows x64, CPython 3.12, Codex 앱(ChatGPT 데스크톱·Codex CLI·IDE 확장)이다.
외부망·CDN·API 키·npm·Playwright 가 필요한 기능은 넣지 않거나 제거했다.

- 설치·수정 내역·선정 기준: [`docs/agent-skills.md`](docs/agent-skills.md)
- 출처 커밋·라이선스: [`docs/source-inventory.md`](docs/source-inventory.md), [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
- Codex 가 따르는 운영 규칙: [`AGENTS.md`](AGENTS.md) (대상 저장소에 같이 복사한다)
- Codex 앱 전역 규칙(행동·문서 신뢰도·통제 언어·Git 안전): [`global/AGENTS.md`](global/AGENTS.md) → `%USERPROFILE%\.codex\AGENTS.md` 로 복사. 출처와 근거는 [`docs/global-rules.md`](docs/global-rules.md)
- Codex 앱 로컬 설정(실행 정책 rules, config 키, 프로필, 서브에이전트 역할): [`codex-home/`](codex-home/) → `%USERPROFILE%\.codex\` 아래. 설명은 [`docs/codex-home.md`](docs/codex-home.md)

## 1. 구성

```
.agents/skills/     ← Codex 가 자동 탐색하는 17종
optional/skills/    ← 탐색 경로 밖. 필요할 때 .agents/skills/ 로 복사해 켠다 (10종)
global/AGENTS.md    ← Codex 앱 전역 규칙. %USERPROFILE%\.codex\AGENTS.md 로 복사 (모든 저장소에 적용)
codex-home/         ← rules/default.rules, config.toml.example, review·qa 프로필, agents/*.toml, 사용량 hook (docs/codex-home.md)
scripts/            ← install_skills.sh, verify_skills.py
requirements-skills.txt / requirements-optional.txt
```

| 단계 | 스킬 | 하는 일 | Python 의존 | 그 외 |
|---|---|---|---|---|
| 이해 | `code-map` | 레포 구조·모듈·의존관계 → 자체 완결 HTML 대시보드 | 없음 | — |
| 구현 | `test-driven-development` | 실패하는 테스트 → 최소 구현 → 리팩터 규율 | 없음 | — |
| 구현 | `property-based-testing` | Hypothesis 속성 테스트 작성·검토 | hypothesis | — |
| 구현 | `bash-defensive-patterns` | 방어적 셸 스크립트 패턴 | 없음 | — |
| 디버깅 | `systematic-debugging` | 재현 → 패턴 → 가설 → 수정 4단계 | 없음 | — |
| 검사 | `code-audit` | 전체/diff 결함 감사 → HTML 리포트 | 없음 | — |
| 검사 | `differential-review` | diff 의 보안·회귀·영향 범위·테스트 커버리지 리뷰 → 마크다운 | 없음 | git |
| 검사 | `test-gap` | 테스트 빠진 위험 지점 분석·보강 | 없음 | — |
| 마감 | `verification-before-completion` | 완료 선언 전 검증 명령 실행·출력 확인 게이트 | 없음 | — |
| 마감 | `receiving-code-review` | 리뷰 지적을 검증한 뒤 반영 | 없음 | — |
| 보고서 | `report-templates` | 상태 보고·결정 기록(ADR)·PR 설명 양식 3종 | 없음 | — |
| 보고서 | `postmortem-writing` | 장애·실패 회고 문서 | 없음 | — |
| 자료화 | `html-ppt` | 36 테마 HTML 슬라이드 덱(폴더형), PNG 캡처 | 없음 | Chrome/Edge(PNG) |
| 자료화 | `html-to-pdf` | HTML/HTML 덱 → PDF(캡처형·벡터형) | PyMuPDF, websocket-client | Chrome/Edge |
| 자료화 | `pdf` | reportlab 으로 PDF 직접 생성·검토(Chrome 불필요) | reportlab, pdfplumber, pypdf | — |
| 자료화 | `archscribe` | 손그림 느낌 아키텍처 다이어그램(.excalidraw/PNG) | Pillow, svg.path | — |
| 자료화 | `matplotlib` | 그래프 작성 규칙·템플릿 | matplotlib, numpy | — |

선택(`optional/skills/`): `ppt-master`(네이티브 PPTX, 컨텍스트 비용 큼), `frontend-slides`(단일 파일 애니메이션 덱), `polars`,
`code-flow`, `code-arch`, `debug-fix`, `define-goal`, `code-port`, `security-best-practices`, `security-threat-model`. 내린 이유는 `docs/agent-skills.md` §6.

## 2. 설치 (폐쇄망 Windows, Git Bash)

```bash
git clone <사내 git>/codex-skills.git && cd codex-skills
export PIP_INDEX_URL="https://<corporate-pypi>/simple"
scripts/install_skills.sh                  # .venv-skills 생성 + 핵심 패키지 10개 + 검증
scripts/install_skills.sh --with-optional  # ppt-master·polars 까지 쓸 때
```

검증 출력의 `required` 가 전부 PASS 면 끝이다. `optional` 의 `chrome headless pdf` 가 WARN 이면 PDF 는 `pdf` 스킬로 만든다.
Codex 가 Python 을 쓸 때는 `.venv-skills/Scripts/python.exe` 를 쓰게 한다.

**전역 규칙 설치** (한 번만):

```bash
mkdir -p ~/.codex && cp global/AGENTS.md ~/.codex/AGENTS.md    # Windows: %USERPROFILE%\.codex\AGENTS.md
```

Codex 는 `~/.codex/AGENTS.md` 를 모든 저장소에서 먼저 읽고, 그 뒤에 저장소 루트의 AGENTS.md 를 붙인다.
합산 상한은 32 KiB(`project_doc_max_bytes`)다. 전역 8.7 KB + 이 번들의 AGENTS.md 4.4 KB 라 여유가 있지만,
저장소 AGENTS.md 가 20 KB 를 넘으면 `~/.codex/config.toml` 에서 상한을 올린다. 파일을 바꾸면 Codex 를 다시 시작한다.

**다른 저장소에서 쓰기** (셋 중 하나):

```bash
# a) 저장소 범위: 대상 레포에 복사
cp -r codex-skills/.agents <대상레포>/ && cp codex-skills/AGENTS.md <대상레포>/
# b) 사용자 범위: 모든 레포에서 보이게 링크(Codex 는 심볼릭 링크 폴더를 따라간다)
ln -s "$(pwd)/.agents/skills" ~/.agents/skills        # Windows 는 %USERPROFILE%\.agents\skills 로 복사
# c) 선택 스킬 켜기
cp -r optional/skills/ppt-master .agents/skills/
```

## 3. 호출 방법 — 꼭 따로 불러야 하나?

아니다. 두 경로가 다 열려 있다.

| 방식 | 어떻게 | 언제 쓰나 |
|---|---|---|
| **자동(암시) 호출** | 그냥 한국어로 요청한다. Codex 가 스킬 목록의 description 과 요청을 맞춰 스스로 고른다. 모든 description 앞에 `[KO] …` 트리거를 넣어 두었다 | 디버깅·검증·리뷰 반영처럼 "규율" 성격의 스킬. 예: "왜 테스트가 깨지지?" → `systematic-debugging` |
| **명시 호출** | 프롬프트에 `$code-map`, `$differential-review` 처럼 적는다. ChatGPT 데스크톱은 `@`, Codex CLI/IDE 는 `/skills` 또는 `$` 로 고른다 | 산출물이 있는 스킬(HTML·PDF·보고서)과 단계가 정해진 워크플로우. 어떤 스킬이 돌았는지 확실히 하고 싶을 때 |

권장: **산출물 스킬은 명시 호출, 규율 스킬은 자동에 맡긴다.** 자동 호출이 빗나가면 명시 호출로 바꾸면 된다.
스킬 목록 예산은 컨텍스트의 2%(최대 10,000 토큰)라서 17종 전부가 보이는지 Codex 의 스킬 패널에서 한 번 확인한다. 잘리면 `optional/` 로 더 내린다.

특정 스킬의 자동 호출을 막으려면 그 스킬의 `agents/openai.yaml` 에 `policy: {allow_implicit_invocation: false}` 를 두면 `$skill` 로만 불린다.

## 4. 시나리오별 활용

### A. 기능 추가 / 리팩토링

```
1. $code-map 으로 src/<모듈> 범위만 분석해서 docs/<project>-codemap.html 에 저장해.     ← 구조 파악(읽기 전용)
2. $test-driven-development 로 <기능> 을 구현해. 실패하는 테스트부터 쓰고, 실패 출력을 보여 준 뒤 구현해.
3. (변환·파서·수치 함수가 있으면) $property-based-testing 으로 왕복/불변량 속성 테스트를 추가해.
4. $test-gap 으로 변경 파일 관련 테스트 갭을 분석만 해. 코드는 수정하지 마.
5. $verification-before-completion — 테스트·린트를 실제로 실행하고 출력을 붙여서 결과를 보고해.
```

### B. 버그 수정

```
1. $systematic-debugging 으로 <증상> 의 원인을 찾아. 먼저 재현하고, 원인 없이는 수정하지 마.   ← "진단만" 이라고 하면 수정 없이 끝
2. 원인이 나오면 $test-driven-development 로 재현 테스트를 먼저 쓰고 최소 수정해.
3. $differential-review 로 git diff main..HEAD 를 검토해. 회귀·영향 범위·테스트 누락을 markdown 으로.
4. $verification-before-completion
```

### C. 남의 코드 검토 / 인수인계 (수정 없음)

```
$code-map → docs/<project>-codemap.html
$code-audit 를 codebase-audit 모드로 → docs/<project>-audit.html
$differential-review 로 <base>..<head> 의 변경을 검토 → docs/reports/<날짜>-review.md
$test-gap 분석만
```

리뷰를 **받는** 쪽이면: "이 리뷰 코멘트를 $receiving-code-review 규칙대로 하나씩 검증한 뒤 반영 여부를 정해."

### D. 저장소 보고서 (주간 보고·결정 기록·회고)

```
1. 내용 먼저: README·docs·테스트 결과·git log 를 읽고 보고서 내용을 마크다운 메모로 써.
   (독자, 결정해야 할 것, 근거 수치·날짜·파일 경로 포함. 이 단계는 스킬 없이.)
2. $report-templates 의 status_report 양식에 그 내용을 채워 docs/reports/<날짜>-status.md 로 저장해.
   - 설계 결정이면 decision_record, PR 설명이면 pull_request 양식
   - 장애·실패 회고면 $postmortem-writing
3. 그림이 필요하면 $archscribe(구조도) / $matplotlib(수치 그래프) 로 PNG 를 만들어 같은 폴더에 두고 링크해.
4. 발표용이면 $html-ppt 로 덱을 만들고 $html-to-pdf 로 PDF 를 뽑아. Chrome 이 막혀 있으면 $pdf 로 바로 PDF.
```

내용과 형식을 분리하는 이유: 같은 형식으로 비교했을 때 결과 품질은 스킬이 아니라 모델이 근거 문서를 얼마나 읽었느냐가 결정했다.
스킬의 "간결하게", "카드 3개" 같은 형식 규칙이 내용을 깎으면 읽기용 자료임을 명시하고 표 중심 레이아웃을 쓰게 한다.

## 5. 스킬별 사용 메모

| 스킬 | 프롬프트 예 | 산출물 / 주의 |
|---|---|---|
| `code-map` | `$code-map 으로 이 레포를 분석해 docs/x-codemap.html 저장` | 읽기 전용. 큰 레포는 디렉터리를 지정해 범위를 좁힌다 |
| `code-audit` | `$code-audit codebase-audit 모드` / `changes-audit 로 main 대비` | 결함을 찾기만 한다. 고치려면 별도 지시 |
| `differential-review` | `$differential-review 로 a1b2c3..HEAD 검토` | PR 번호 대신 커밋 범위를 준다(`gh` 없음). 결과는 마크다운 |
| `test-driven-development` | `$test-driven-development 로 X 구현. 실패 출력 먼저 보여 줘` | 테스트가 먼저 실패하는지 확인하는 것이 핵심 |
| `property-based-testing` | `$property-based-testing 으로 encode/decode 왕복 속성 테스트` | hypothesis 필요. 수치 함수·파서에 효과적 |
| `test-gap` | `$test-gap 분석만` / `$test-gap 으로 빠진 테스트 작성` | "분석만" 이면 토큰 절약 |
| `systematic-debugging` | `$systematic-debugging 진단만` | 재현 로그와 원인 체인을 남긴다 |
| `verification-before-completion` | 자동 호출에 맡겨도 되지만 마감 때 명시하면 확실 | 검증 명령의 실제 출력이 없으면 완료가 아니다 |
| `receiving-code-review` | `이 리뷰를 $receiving-code-review 규칙으로 처리` | 지적이 틀렸으면 근거를 들어 반박하게 한다 |
| `report-templates` | `$report-templates status_report 양식으로` | Mermaid 는 텍스트로만 남긴다(폐쇄망에선 렌더 안 될 수 있음) |
| `postmortem-writing` | `$postmortem-writing 으로 어제 배포 실패 회고` | 비난 없는 회고, 타임라인·액션 아이템 |
| `html-ppt` | `$html-ppt 로 8장 덱, 테마 X, 읽기용 고밀도 표` | `scripts/new_deck.py`, `render.py`(PNG). 외부 폰트·CDN 없음 |
| `html-to-pdf` | `$html-to-pdf slides-raster 로 PDF` | 화면 그대로면 `*-raster`, 글자 선택이 필요하면 `screen-vector`, 보고서는 `onepage` |
| `pdf` | `$pdf 로 reportlab 보고서 PDF` | Chrome 없이 동작 |
| `archscribe` | `$archscribe 로 데이터 파이프라인 구조도 PNG` | Pillow 렌더러만. 한글은 Malgun Gothic 폴백. `µ` 같은 기호는 ASCII 로 |
| `matplotlib` | `$matplotlib 으로 epoch-loss 그래프 PNG` | `python scripts/...` 로 실행(uv 아님) |
| `bash-defensive-patterns` | 셸 스크립트 작성 요청 시 자동 | `set -euo pipefail`, 인용, 임시파일 정리 |

## 6. 검증

```bash
.venv-skills/Scripts/python.exe -I scripts/verify_skills.py           # Git Bash: .venv-skills/bin/python (macOS)
```

`required`: Python 3.12, 핵심 패키지 10개 import, `.agents/skills` 17개 폴더의 `name` 유효·중복 없음, **`offline assets`**(HTML/CSS/JS/Python 에 외부 `src=`/`href=` 없음).
`optional`: 선택 패키지 6개, `optional/skills` 폴더, Chrome headless PDF, ppt-master 무결성 게이트. `--strict` 면 optional 실패도 종료 코드 1.

## 7. 업스트림 갱신·추가

외부망에서 `docs/source-inventory.md` 의 커밋 기준으로 해당 디렉터리만 다시 가져오고 `docs/agent-skills.md` §4 의 수정을 재적용한다.
스킬을 더할 때는 (1) 네트워크·npm·Playwright·API 키 의존이 없는지, (2) LICENSE 파일이 있는지, (3) description 이 400자 안팎인지, (4) `verify_skills.py` 의 `offline assets` 가 PASS 인지 확인한다.
