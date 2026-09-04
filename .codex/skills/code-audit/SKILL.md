---
name: code-audit
description: "Audit a repo (fresh clone, path, or diff) for defects and turn the findings into a self-contained, git-transferable HTML dashboard via this skill's bundled scripts/audit_dashboard.py. Use when the user wants a visual audit report for a repo -- especially one that needs to be carried into a closed/air-gapped network via git, where the report must open from a plain file:// path with no server or internet."
---

# Audit Dashboard

역할: 레포를 결함 관점(정확성/문서-코드 정합/구조/테스트 근거)으로 스캔하고,
그 결과를 정적 HTML 대시보드로 만든다. **findings를 사람이 한 번 훑어보는
체크포인트는 생략하지 않는다** — 3단계에서 이유를 설명.

이 스킬은 전역 설치본이다 — 스크립트는 이 SKILL.md와 같은 디렉터리 아래
`scripts/`에 번들돼 있다. 예: 이 파일이
`~/.codex/skills/code-audit/SKILL.md`라면
`~/.codex/skills/code-audit/scripts/`.

Codex에는 이 워크플로의 1단계를 대신 해주는 **`review-agent`**라는 내장
스킬이 있다(`~/.codex/skills/.system/review-agent`, preinstalled). Claude
Code의 `/code-review`와 같은 역할이다 — **새로 결함 탐지 로직을 만들지 않고
여기에 위임한다.** `allow_implicit_invocation: false`라 자동으로는 안 뜨고
`$review-agent`로 명시 호출해야 한다.

## 0. 스코프 확인

- 대상 경로/레포, 사람이 읽을 프로젝트 이름(`--repo`), target(브랜치@커밋 등)
- 모드: 진단할 로컬 변경/diff가 있으면 `changes-audit`, 방금 받은 새 레포처럼
  diff가 없으면 `codebase-audit` (기본값)

## 1. `review-agent` 실행

`$review-agent`를 명시 호출해서 결함을 찾는다.

- **changes-audit**: 로컬 변경 또는 base-branch 대비 diff를 그대로 검토
  대상으로 넘긴다 — `review-agent`는 원래 이 형태(diff 리뷰)를 위해
  만들어졌다.
- **codebase-audit** (신규/diff 없는 레포): `review-agent`는 "diff 리뷰"가
  기본 전제라 diff가 없으면 볼 게 없다고 여길 수 있다. 이 경우 초기 커밋
  전체(빈 트리 대비 diff, 즉 `git diff <empty-tree-sha>..HEAD` 또는 전체
  파일 목록)를 검토 대상으로 명시하거나, 모듈/파일 단위로 여러 번 나눠서
  호출한다.
- `review-agent`는 결과를 **prose**로 반환한다(JSON 아님) —
  `[P0|P1|P2|P3] 제목 — path:line` + 짧은 설명 문단 형식. 2단계에서 이걸
  구조화된 findings.json으로 옮겨 적는다.
- `review-agent`에는 lens 축이 없다 — `references/rubric.md`를 읽고
  correctness/security 성격이면 `correctness`, performance/maintainability
  성격이면 `structure`로 직접 분류한다. `contract`(문서-코드 정합) 렌즈는
  `review-agent`도 안 보므로 이 경로로는 항상 비어 있다.
- `review-agent`는 이미 "실제로 재현 가능하고, 저자가 고칠 만한 것"만
  걸러서 반환하도록 설계돼 있다(자기 지침에 "추측성 우려·발명한 finding
  금지"가 명시돼 있음) — 그래도 3단계 사람 확인은 생략하지 않는다.

## 2. findings.json 작성 — 한국어로

`review-agent`가 돌려준 각 `[Pn] 제목 — file:line` + 설명 문단을 아래
스키마의 finding 하나로 옮겨 적는다 (`scripts/audit_dashboard.py --example`가
정확한 스키마를 보여준다):

- `site`: `file:line`
- `severity`: `P0`/`P1` → `blocking`, `P2`/`P3` → `advisory`
- `lens`: 1단계 기준으로 직접 분류
- `title`: `review-agent`가 준 제목을 60자 이내 한국어로 번역
- `scenario`: 설명 문단을 한국어로 번역 — 구체성(입력/상태 → 결과)은 그대로
  유지, 뭉뚱그리지 않는다
- `fix`: `review-agent`의 설명에 수정 방향이 들어있으면 그걸 한국어로,
  없으면 finding 내용을 보고 가장 작은 수정 방향을 직접 적는다(원문에 없던
  내용을 새로 채운 경우라는 걸 스스로 인지한다)

**모든 텍스트 필드(`title`/`scenario`/`fix`)는 사용자가 쓰는 언어로 쓴다** —
이 필드들이 그대로 최종 HTML에 노출된다. `site`/`lens`/`severity`처럼 값
자체가 언어와 무관한 필드는 영문 enum 값 그대로 둔다.

```json
{
  "run": {"repo": "...", "target": "...", "mode": "codebase-audit", "date": "YYYY-MM-DD"},
  "audited_clean": "무엇을 봤고 뭐가 깨끗했는지 한 줄",
  "findings": [
    {
      "site": "path/to/file.py:123",
      "lens": "correctness",
      "severity": "blocking",
      "title": "60자 이내 한 줄",
      "scenario": "이 입력/상태 -> 이 잘못된 결과 (테스트로 옮길 수 있을 만큼 구체적으로)",
      "fix": "가장 작은 수정 방향"
    }
  ]
}
```

## 3. 체크포인트 — 사람에게 스킴 보여주기 (생략 금지)

대시보드를 만들기 전에 findings 개수와 한 줄 요약 목록(제목/lens/severity)을
사용자에게 보여주고, 등급이 이상하거나 오탐 같은 게 있으면 확인받는다.

이 단계를 건너뛰지 않는 이유: 감사 대시보드는 "폐쇄망으로 반입해도 되는가"를
사람이 판단하는 근거 자료다. 검증 안 된 후보를 확정된 결과처럼 보이게 만들면
그 판단 근거 자체가 무너진다. 사용자가 "그대로 다 넣어줘"라고 명시적으로 말하면
스킵해도 된다 — 기본값이 스킵-불가일 뿐, 강제는 아니다.

## 4. 대시보드 생성

```sh
python3 <이 SKILL.md가 있는 디렉터리>/scripts/audit_dashboard.py findings.json \
  -o <repo-name>-audit.html
```

## 5. 결과 보고

생성된 HTML 경로를 알려준다. 외부 리소스 의존이 없어 file://로 바로 열리고,
git으로 폐쇄망에 반입해도 그대로 동작한다.
