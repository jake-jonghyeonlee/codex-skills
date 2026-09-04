# Codex 앱 스킬 가이드

이 레포의 `.codex/skills/`에 8개 스킬이 포함되어 있다.
태스크 설명에서 스킬 이름이 언급되면 해당 SKILL.md의 지침을 따른다.

## 실행 환경

- **Codex 앱 클라우드 샌드박스**에서 실행된다.
- 모든 스크립트는 Python 표준 라이브러리만 사용한다. `pip install` 불필요.
- GPU가 없다. ML/DL 코드 분석은 가능하지만 모델 학습/추론 실행은 불가.
- 비대화형이다. 사용자에게 중간 확인을 구하지 말고 태스크를 끝까지 완수한다.
- 토큰이 제한될 수 있다. 범위를 좁혀서 효율적으로 실행한다.

## 스킬별 동작 규칙

### Phase 0 — 목표 정의
- `define-goal`: 모호한 의도를 구체적·측정 가능한 목표로 변환. 성공 기준과 검증 방법 포함.

### Phase 1 — 읽기 전용 (코드 수정 금지)
- `code-map`: 레포를 읽고 모듈·심볼·의존관계를 JSON으로 정리한 뒤 HTML 대시보드 생성
- `code-flow`: 프로젝트 유형을 자동 감지하고 데이터 흐름을 JSON으로 정리한 뒤 HTML 다이어그램 생성
- `code-arch`: 계층 구조를 분석하고 JSON으로 정리한 뒤 HTML 아키텍처 다이어그램 생성

### Phase 3 — 분석 (코드 수정 금지)
- `code-audit`: 결함을 찾아 HTML 리포트 생성. 결함을 고치지 않는다.

### Phase 4 — 보안·테스트
- `security-best-practices`: 언어/프레임워크별 보안 코딩 패턴 검토. 리포트를 `docs/security-report.md`에 저장. 수정은 사용자 요청 시에만.
- `security-threat-model`: 레포 기반 위협 모델링. 신뢰 경계·자산·공격 경로·완화책 분석. `docs/<project>-threat-model.md`에 저장.
- `test-gap`: "분석만" 요청 시 테스트 플랜만 출력. "작성" 요청 시 테스트 코드 생성.

## 산출물 저장

HTML 산출물은 `docs/` 디렉터리에 저장한다 (없으면 생성):
- `docs/<project>-codemap.html`
- `docs/<project>-dataflow.html`
- `docs/<project>-architecture.html`
- `docs/<project>-audit.html`
- `docs/security-report.md`
- `docs/<project>-threat-model.md`

태스크에서 다른 경로를 지정하면 그 경로를 따른다.

## 스크립트 실행

각 스킬의 Python 스크립트는 SKILL.md가 있는 디렉터리 기준 `scripts/`에 위치한다:

```sh
python3 .codex/skills/code-arch/scripts/render_architecture.py arch.json -o docs/architecture.html
```

## 권장 순서

0. define-goal → 1. code-map/flow/arch → 2. (구현) → 3. code-audit → 4. security-* + test-gap

순서를 강제하지 않는다. 태스크에서 특정 스킬만 요청하면 해당 스킬만 실행한다.

## 토큰 절약 팁

- 범위를 좁혀라: "전체 레포" 대신 "src/models/ 디렉터리만"
- 필요한 스킬만 선택하라: 최소 조합은 code-map + code-audit
- test-gap은 analysis only로 요청하면 토큰 절약
- define-goal을 먼저 실행하면 하류 단계에서 불필요한 탐색 방지
