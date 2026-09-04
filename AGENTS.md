# Codex Skills 사용 가이드

이 레포에는 `.codex/skills/`에 5개 스킬이 포함되어 있다.
사용자가 스킬 이름을 언급하면 해당 SKILL.md의 지침을 따른다.

## 스킬 호출 규칙

- `code-map`, `code-flow`, `code-arch`: 코드를 **읽기만** 한다. 절대 수정하지 않는다.
- `code-audit`: 결함을 찾아 리포트를 생성한다. 코드를 수정하지 않는다.
- `test-gap`: 사용자가 `analysis only`를 요청하면 분석만 한다. `implement`를 요청하면 테스트 코드를 작성한다.

## 산출물 저장 위치

HTML 산출물은 `docs/` 디렉터리에 저장한다:
- `docs/<project>-codemap.html`
- `docs/<project>-dataflow.html`
- `docs/<project>-architecture.html`
- `docs/<project>-audit.html`

## 권장 실행 순서

1. code-map → 2. code-flow → 3. code-arch → 4. (구현) → 5. code-audit → 6. test-gap

순서를 강제하지 않는다. 사용자가 특정 스킬만 요청하면 해당 스킬만 실행한다.
