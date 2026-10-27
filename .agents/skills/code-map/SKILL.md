---
name: code-map
description: "[KO] 낯선 레포 구조 파악·모듈/의존관계 HTML 대시보드를 만들 때. Read (never modify) an unfamiliar repo and produce a self-contained, git-transferable HTML dashboard describing what it does and how it's structured -- purpose, module responsibilities, key symbols, and a dependency diagram -- via this skill's bundled scripts/codemap_dashboard.py. Use when the user wants to understand a new/unfamiliar codebase (what it does, how it's organized), as opposed to auditing it for defects (that's the code-audit skill)."
---

# Code Map

역할: 처음 보는 레포를 **읽기만 하고** "뭘 하는 코드인지, 어떻게 구성돼 있는지"를
정적 HTML 한 장으로 정리한다. `code-audit` 스킬과 목적이 다르다 —
결함(finding)도 severity도 없다. 코드를 고치지 않는다.

이 스킬은 전역 설치본이다 — 스크립트는 이 SKILL.md와 같은 디렉터리 아래
`scripts/`에 번들돼 있다. 예: 이 파일이 `~/.agents/skills/code-map/SKILL.md`라면
`~/.agents/skills/code-map/scripts/`.

## 0. 스코프

대상 레포 경로, 사람이 읽을 프로젝트 이름을 확인한다. README/docs가 있으면
먼저 읽어 목적(purpose)의 초안으로 삼되, 실제 코드로 검증한다 — 문서가
과장/누락됐을 수 있다는 걸 감안한다.

## 1. 모듈 목록 + 의존관계 스캐폴딩 (기계적으로 가능한 부분)

- **Python 프로젝트**: `scripts/extract_python_symbols.py <repo>`로
  스켈레톤 JSON을 뽑는다 — 파일 목록, 클래스/함수/메서드 이름, 프로젝트 내부
  import로부터 추론한 `depends_on` 엣지까지 자동으로 채워진다. 추가로 6가지
  분석 축 데이터를 자동 추출한다:
  1. **외부 의존성** — stdlib / third-party 분류, 모듈별 사용처
  2. **가시성** — `_` 접두어 기반 public/private 태깅, `__all__` 존재 여부
  3. **복잡도 지표** — 함수 수, 평균 함수 길이, 최대 중첩 깊이
  4. **결합도** — `depends_on` 엣지 (fan-in/fan-out은 렌더 시점 계산)
  5. **테스트 매핑** — test 파일의 import 분석으로 테스트 대상 모듈 자동 연결
  6. **호환성** — pyproject.toml/setup.cfg에서 python_requires, 플랫폼 등 파싱
  또한 **교차 모듈 심볼 참조**를 2-pass AST 분석으로 추출한다 — 각 함수가
  어떤 외부 심볼을 실제로 참조하는지 `refs` 필드에 기록.
  `role` 필드는 전부 빈 문자열로 남는다 — 이건 네가 직접 읽고 채워야 한다.
- **JS/TS 프로젝트**: 전용 추출기가 없다. 대신 이미 잘 만들어진 도구를 그대로
  쓴다 — `madge --json <entry>` 또는 `dependency-cruiser --output-type json`으로
  의존관계 그래프를 뽑고, 그 결과를 이 스킬의 `depends_on` 스키마로 옮긴다
  (심볼 목록은 직접 읽어서 채움).
- 다른 언어: 위와 같은 패턴(기계적 의존관계 추출 도구 + 직접 읽어서 role 채우기)을
  따르되, 전용 도구가 없으면 grep으로 import/require 문을 뽑아 수동으로
  `depends_on`을 구성한다.

## 2. 읽고 채우기 (자동화 불가 — 의미 이해가 필요한 부분)

**언어: 모든 콘텐츠는 한글로 작성한다.** `project.purpose`, `project.features`,
`project.stack[].note`, `project.entry_points`, `project.how_to_run`, 각 모듈의
`role`, 심볼의 `role` 등 사람이 읽는 설명 텍스트는 전부 한글이어야 한다.
코드 식별자(클래스명, 함수명, 파일 경로 등)와 기술 용어(DAG, API, CLI 등)는
원어 그대로 쓰되, 설명 문장 자체는 한글로 쓴다.

스켈레톤을 열어 각 모듈을 실제로 읽고:

- `project.purpose` — 처음 보는 사람 기준 1~2문단. README를 베끼지 말고 코드로
  확인한 사실을 반영한다.
- `project.features` — 사용자 관점에서 이 프로젝트가 하는 일을 한 줄씩 (개요를
  "한눈에" 파악하게 하는 핵심 섹션 — 빼먹지 말 것)
- `project.stack` — 문자열도 되지만, 가능하면 `{"name": "...", "note": "..."}`로
  각 기술을 왜/어떻게 쓰는지 한 줄 덧붙인다
- `project.entry_points`, `project.how_to_run`
- 각 모듈의 `role` — 이 파일의 책임을 한두 문장으로. `loc`는
  `extract_python_symbols.py`가 자동으로 채워준다(직접 셀 필요 없음)
- 중요한 심볼(클래스/주요 함수/주요 메서드)의 `role` — 사소한 getter 등은 비워도
  됨 (렌더러가 빈 값은 그냥 안 보여줌)
- `tested_by` 자동 매핑을 확인하고, 누락된 테스트 모듈이 있으면 보충
- `external_deps`에서 third-party 항목의 용도를 확인 (대시보드에 자동 표시됨)
- `compatibility` 데이터가 파싱되었으면 정확성 확인, 없으면 수동 보충 가능

너무 자잘한 private 헬퍼까지 다 채우려 하지 않는다 — 처음 보는 사람이 "이
레포가 어떻게 굴러가는지" 파악하는 데 필요한 만큼만.

## 3. 렌더

```sh
python3 <이 SKILL.md가 있는 디렉터리>/scripts/codemap_dashboard.py project.json -o <repo>-codemap.html
```

- 필수 필드 검증(스키마는 `codemap_dashboard.py --example` 참고), `depends_on`이
  존재하지 않는 모듈을 가리키면 에러로 알려준다.
- 결과 HTML은 외부 리소스 의존이 전혀 없다 — file://로 바로 열리고, git으로
  폐쇄망에 반입해도 그대로 동작한다.
- 의존관계 다이어그램은 라이브러리 없이 순수 JS로 그린 layered DAG(SVG) —
  `depends_on`이 없는 모듈이 위쪽 레이어, 많이 의존할수록 아래쪽. 모듈은
  진입점/핵심로직/기반/테스트 4종으로 자동 분류되어 색상 코딩됨.
  노드에 호버하면 연결된 엣지만 강조되고, 클릭하면 해당 모듈 카드로 이동.
  모듈 카드를 클릭하면 펼쳐지고, 검색창으로 경로/설명을 필터링할 수 있다.
  각 심볼에 교차 모듈 참조(refs)가 있으면 클릭 가능한 칩으로 표시된다.

## 4. 결과 보고

생성된 HTML 경로를 알려주고, 다이어그램이 실제 import 문에서 뽑은 엣지인지
(신뢰 가능) 아니면 일부를 수동으로 구성했는지(추정 가능성) 알려준다.

## 참고 — 관련 오픈소스 (대체 아님, 각자 다른 용도)

- **gitdiagram** (ahmedkhaleel2004/gitdiagram): 레포 트리+README를 LLM에 보내
  Mermaid 아키텍처 다이어그램을 생성. 호스팅형 SaaS(Vercel+R2+Redis)에 OpenAI
  API 호출이 필요해 폐쇄망에서 그대로 못 씀 — 개방망에서 한 번 생성해 Mermaid/PNG로
  내보낸 뒤 그 산출물만 git으로 반입하는 방식이면 보완적으로 쓸 수 있음. 실제
  import 엣지가 아니라 LLM이 추정한 구조라 이 스킬보다 얕음.
- **madge / dependency-cruiser / arkit** (JS·TS): 실제 import 기반 의존관계
  그래프 추출 — 1단계에서 그대로 활용.
- **pydeps**: Python용 동일 목적이지만 Graphviz 바이너리가 필요하고 산출물이
  단일 SVG라 이 스킬의 `extract_python_symbols.py`(stdlib만 사용, 심볼까지 같이
  추출) 쪽이 이 워크플로엔 더 맞음.
- **Sourcetrail**: 딱 이 용도(인터랙티브 소스 탐색기)였지만 2021년에 개발 중단.
- **CodeCharta**: 의존관계가 아니라 LOC/복잡도 같은 정량 지표를 "코드 도시"로
  시각화 — 다른 종류의 통찰이라 이 스킬을 대체하지 않음, 나중에 보완 레이어로
  고려 가능.
