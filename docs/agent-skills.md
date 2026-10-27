# 에이전트 스킬 번들 — 설치·수정 내역·선정 기준 (폐쇄망 Windows, Codex 앱)

사용법은 `README.md`, 라이선스는 `THIRD_PARTY_NOTICES.md`, 출처 커밋은 `docs/source-inventory.md`에 있다.
이 문서는 설치 절차, 업스트림 대비 수정, 확인/미확인 사항, 넣지 않은 것과 이유를 기록한다.

재구성일: 2026-10-28 (이전 구성: `jake-private/.agents/skills` 14종, 2026-10-23).

## 1. 구성 원칙

- `.agents/skills/`(17종)만 Codex 가 자동 탐색한다. `optional/skills/`(10종)는 탐색 경로 밖이라 목록 예산을 쓰지 않는다.
- Codex 는 스킬 목록(name·description·경로)에 **컨텍스트의 2%**(창 크기를 모르면 8,000자)만 쓴다. 넘치면 설명을 줄이다가 스킬을 빼고 경고한다.
  `~/.codex/config.toml` 의 `skills.max_context_tokens` 로 최대 10,000 토큰까지만 올릴 수 있다. 그래서 description 은 400자 안팎으로 유지한다.
- 외부망·CDN·API 키·npm·Playwright 가 필요한 기능은 넣지 않거나 제거했다. `scripts/verify_skills.py` 의 `offline assets` 검사가 `src=`/`href=` 외부 URL 을 잡는다.
- 모든 description 앞에 `[KO] …` 한국어 트리거를 둔다. Codex 는 description 매칭으로 스킬을 고르므로 한국어 요청에도 자동 호출된다.

## 2. 설치

사전 조건: Windows x64, CPython 3.12 x64, Git Bash, 사내 PyPI simple index, Chrome 또는 Edge(PDF·PNG 용). `uv` 는 쓰지 않는다.

```bash
export PIP_INDEX_URL="https://<corporate-pypi>/simple"
scripts/install_skills.sh                 # 핵심 10개 패키지 (requirements-skills.txt)
scripts/install_skills.sh --with-optional # + ppt-master·polars 패키지 (requirements-optional.txt)
```

스크립트가 하는 일: `.venv-skills` 생성(`py -3.12`) → 고정 버전을 **binary wheel 만** 설치 → `pip check` → `scripts/verify_skills.py`.
검증 출력의 `required` 가 모두 PASS 면 설치 완료다. `optional` 의 `chrome headless pdf` 가 WARN 이면 PDF 는 `html-to-pdf` 대신 `pdf`(reportlab) 로 만든다.

Codex 앱에서 Python 을 쓸 때는 `.venv-skills/Scripts/python.exe` 를 쓴다(Git Bash: `source .venv-skills/Scripts/activate`).
Windows 의 `python3` 는 Store 스텁으로 빠질 수 있으니 `python` 을 쓴다.

사내 미러에 없는 wheel 이 있으면 그 wheel 만 따로 반입한다(`pip install` 단계에서 `No matching distribution` 으로 드러난다).

## 3. 스킬 활성화 방식

| 방법 | 효과 |
|---|---|
| 이 저장소를 Codex 에서 연다 | `.agents/skills/*` 자동 인식(저장소 범위) |
| `%USERPROFILE%\.agents\skills` 로 복사 또는 링크 | 모든 저장소에서 사용(사용자 범위). Codex 는 심볼릭 링크 폴더를 따라간다 |
| `optional/skills/<이름>` 을 `.agents/skills/` 로 복사 | 선택 스킬 활성화. 목록 예산을 확인한다 |
| `~/.codex/config.toml` 에 `[[skills.config]] path="…/SKILL.md" enabled=false` | 파일은 두고 끈다. Codex 재시작 필요 |
| `agents/openai.yaml` 의 `policy.allow_implicit_invocation: false` | 자동 호출 금지, `$skill` 명시 호출만 허용 |

## 4. 업스트림 대비 수정 내용

| 스킬 | 수정 |
|---|---|
| `html-ppt` | `assets/fonts.css` 의 Google Fonts `@import` 8개를 시스템 글꼴 별칭으로 교체. 차트·코드 레이아웃의 jsDelivr 참조를 `assets/vendor/`(Chart.js 4.4.3, highlight.js 11.10.0)로 교체. macOS 전용 `new-deck.sh`/`render.sh` 를 `scripts/new_deck.py`/`render.py` 로 이식. `docs/`, `examples/`, `scripts/verify-output/` 제외. **2026-10-28: description 을 818자 → 약 330자로 축약** |
| `html-to-pdf` | 중국어 SKILL.md 를 영어(안내는 한국어)로 재작성, 고정 경로를 `.agents/skills/html-to-pdf/...` 로 변경. 스크립트는 원본 그대로 |
| `systematic-debugging` | `superpowers:` 접두 교차 참조 2곳을 일반 문장으로. 평가용 `test-*.md`, `CREATION-LOG.md` 제외 |
| `test-driven-development` | **신규(2026-10-28)**. `writing-good-tests.md` 의 `superpowers:writing-skills` 참조 1곳 제거. description 에 `[KO]` 접두 추가 |
| `differential-review` | **신규(2026-10-28)**. trailofbits 원본에서 `methodology.md`·`reporting.md` 만 번들, `patterns.md`/`adversarial.md`(Solidity) 제외. 서브에이전트(`adversarial-modeler`) 단계는 같은 세션에서 체크리스트로 대신. `gh pr view` 줄에 오프라인 안내 추가 |
| `report-templates` | **신규(2026-10-28)**. K-Dense `markdown-mermaid-writing/templates` 중 상태 보고·결정 기록·PR 3종만 발췌. 번들하지 않은 스타일 가이드로 가는 링크 줄 제거. SKILL.md 는 자체 작성 |
| `property-based-testing` | **2026-10-28: description 988자 → 약 430자로 축약**(Solidity/Echidna 문구 제거). 본문은 원본 그대로 |
| `code-map`, `code-audit`, `test-gap` | 2026-10-28: description 에 `[KO]` 접두 추가. 본문·스크립트 변경 없음 |
| `matplotlib` | `uv run --isolated --with ...` 예시 2곳을 `python scripts/...` 로 |
| `archscribe` | Pillow 렌더러 경로만 사용(Playwright·ffmpeg 미설치). `assets/previews` 제외. 한글 지원 패치: `render_animated_diagram.py` 의 `has_cjk()` 에 한글 범위 추가, 글꼴 후보에 `malgun.ttf`/`AppleSDGothicNeo.ttc`/NanumGothic 추가 |
| `pdf` | 원본 그대로(`[KO]` 접두만) |
| `optional/code-flow`, `optional/code-arch` | 2026-10-28: 렌더러의 Google Fonts `<link>` 1줄씩 제거. 시스템 글꼴 폴백은 원래 있었음 |
| `optional/ppt-master` | `templates/icons/{chunk-filled,simple-icons,tabler-outline}`(44 MB), `templates/sounds`(12 MB), `scripts/tests`, `.env.example` 제외 → 26 MB. 이미지 생성·검색, TTS, 웹 수집 모듈의 패키지는 설치하지 않음. 무결성 게이트 스크립트·SKILL.md frontmatter 는 수정하지 않음 |
| `optional/frontend-slides` | 웹폰트 규칙을 시스템 글꼴 규칙으로 교체, `html-template.md` 의 `<link>` 제거, Vercel 배포·Playwright PDF 단계 제거 |
| 모든 스킬 | description 앞 `[KO] …` 한국어 트리거. `allowed-tools:` 등 Claude 전용 frontmatter 는 Codex 가 무시한다 |

## 5. 확인된 것과 확인되지 않은 것

확인됨(외부망 Mac, CPython 3.12.13):

- 2026-10-28: `scripts/verify_skills.py` 를 새 구조로 실행 — `required`(패키지 10개 import, `.agents/skills` 17개 폴더 name 중복 없음, `offline assets`) 결과는 README 「검증」절과 커밋 메시지에 기록.
- 2026-10-23(이전 구성): `install_skills.sh` + `verify_skills.py` 전체 PASS, `html-ppt` 덱 생성·PNG 캡처, `ppt-master` 8장 PPTX 생성(154초, 네트워크 호출 없음, 컨텍스트 약 70k 토큰 필요 — 그래서 optional 로 이동).

미검증(폐쇄망 Windows 에서 처음 설치할 때 확인):

- 사내 PyPI 에 핵심 10개 wheel(+선택 6개)이 모두 있는지.
- 사내 Chrome/Edge 가 `--headless --print-to-pdf` 를 허용하는지 — `verify_skills.py` 의 optional 항목이 판정.
- Codex 앱이 이 저장소를 열었을 때 17개 스킬이 모두 목록에 보이는지 — 잘리면 `skills.max_context_tokens` 를 올리거나 description 을 더 줄인다.
- 새로 넣은 `test-driven-development`·`differential-review`·`report-templates` 의 실제 결과물 품질(문서·의존성 기준으로만 선정).

## 6. 넣지 않은 것과 이유

| 후보 | 제외 이유 |
|---|---|
| obra/superpowers `writing-plans`, `brainstorming`, `executing-plans`, `subagent-driven-development`, `dispatching-parallel-agents`, `requesting-code-review` | 서브에이전트 디스패치·`superpowers:` 교차 참조에 묶여 있음(`writing-plans` 는 "REQUIRED SUB-SKILL" 2곳). `brainstorming` 은 외부 로고 로드. 플러그인 전체는 SessionStart 훅으로 방법론 강제 |
| mattpocock/skills `tdd`, `grill-me` | `/code-review` 서브에이전트, 자체 `GLOSSARY.md`/ADR 규약, 네트워크 자동 갱신에 묶임. obra TDD 로 대체 |
| trailofbits `static-analysis`, `supply-chain-risk-auditor`, `second-opinion`, `gh-cli`, `modern-python`, `insecure-defaults` | CodeQL·Semgrep·네트워크·외부 모델·훅 의존 |
| K-Dense `markdown-mermaid-writing` 본체 | Mermaid 렌더에 Node.js 22+ 와 Chromium 필요(`SKILL.md:6`). 스타일 가이드 60 KB 는 보고서 용도에 과함. 템플릿 3종만 `report-templates` 로 발췌 |
| openai/plugins (figma, notion, sentry, vercel …) | 외부 SaaS 연동. 폐쇄망 무관. `plugins/superpowers/skills/` 는 obra 스킬의 Codex 포장본이라 출처 URL 로만 쓸 수 있음 |
| skills.sh 상위권 `find-skills`, `agent-browser`, `frontend-design` | 네트워크·브라우저 전제, 목적(코딩·레포 보고서)과 무관 |
| `dashi-ppt-skill`, `guizang-ppt-skill` | 첫 실행 시 `npm install`·Chromium 다운로드 또는 CDN 3종, AGPL, 중국어 전용 |
| `drawio-skill`, `drawio-mcp` | draw.io Desktop 필요(설치 가능 여부 미정) |
| `typst-skills`, `codebase-to-course` | 라이선스 파일 없음 → 재배포 불가 |
| `excalidraw-skill`, `minorun-marp-skill` | npm 빌드형 MCP 서버 / marp-cli·puppeteer 의존 |
| neo4j-contrib `neo4j-*` | Neo4j 5.26 Community 와 불일치 확인, 현재 규모에서 이득 없음 |
| `fast-mlx` | Apple Silicon 전용 |

### optional 로 내린 것과 이유 (2026-10-28)

| 스킬 | 이유 |
|---|---|
| `ppt-master` | 충실히 따르면 약 280 KB(≈70k 토큰)를 읽어야 함. PPTX 가 꼭 필요할 때만 켠다 |
| `frontend-slides` | `html-ppt` 와 역할 중복(HTML 슬라이드). 단일 파일 애니메이션 덱이 필요할 때만 |
| `polars` | 표 데이터 처리가 일상 업무가 아님 |
| `code-flow`, `code-arch` | `archscribe`·`code-map` 과 역할 중복. 자동 분석 다이어그램이 필요할 때만 |
| `debug-fix` | `systematic-debugging` 과 중복 |
| `define-goal`, `code-port` | 사용 빈도 낮음 |
| `security-best-practices`(432 KB), `security-threat-model` | 보안 검토가 실제 업무일 때만. 참고 문서가 커서 기본 목록에서 제외 |

## 7. 업스트림 갱신

외부망에서 `docs/source-inventory.md` 의 저장소에서 해당 디렉터리만 다시 가져와 §4 의 수정을 재적용한다.
갱신 후 `scripts/install_skills.sh` 로 검증하고, 새 외부 참조가 생기지 않았는지 `verify_skills.py` 의 `offline assets` 결과로 확인한다.
`openai/skills` 는 deprecated 라 갱신원이 아니다(`openai/plugins` 로 이동했으나 폐쇄망에 맞는 스킬은 없음).
