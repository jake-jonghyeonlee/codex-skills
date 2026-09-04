# Codex Skills

Codex 앱 전용 코드 분석 스킬 5종.
GitHub 레포에 `.codex/` 디렉터리를 포함시키면 Codex 앱이 자동 인식한다.

> **CLI(codex CLI)가 아닌 Codex 앱(cloud)에서 사용하는 것을 전제로 설계.**
> 모든 스크립트는 표준 라이브러리만 사용하며 외부 패키지 설치 불필요.

---

## 시나리오별 워크플로우

### A. 새 코드 작성 (새 프로젝트 / 새 기능)

처음부터 만드는 경우. 참고 레포가 있으면 먼저 분석하고, 없으면 바로 구현.

```
 참고 레포 분석 (선택)          구현                검사              테스트
 ─────────────────          ──────────        ──────────        ──────────
 code-map                   Codex 앱           code-audit        test-gap
 code-flow                  기본 기능           (codebase-audit)  (implement)
 code-arch
     │                          │                  │                  │
     ▼                          ▼                  ▼                  ▼
 "참고 레포가 어떻게         "코드 작성"        "작성한 코드에       "테스트 빠진 곳
  돌아가는지 파악"                               버그 있나?"         찾아서 작성"
```

**Codex 앱 태스크 예시**:

```
Step 1 (참고 분석):
https://github.com/xxx/reference-repo 를
code-map + code-arch 스킬로 분석해서 docs/에 HTML 저장해.

Step 2 (구현):
분석 결과 참고해서 src/model.py에 새 모델 클래스 작성해.

Step 3 (검사):
code-audit 스킬로 이 레포 전체를 codebase-audit 모드로 감사해줘.
결과를 docs/audit.html로 저장.

Step 4 (테스트):
test-gap 스킬로 src/ 디렉터리의 테스트 갭을 찾고
tests/에 유닛 테스트 작성해서 커밋해. GPU 불필요한 것만.
```

---

### B. 기존 코드 수정 (버그 수정 / 리팩토링 / 기능 추가)

이미 있는 코드를 변경하는 경우. 먼저 현재 구조를 이해하고 수정한다.

```
 현재 구조 이해               수정                검사              테스트
 ──────────────            ──────────        ──────────        ──────────
 code-map                  Codex 앱           code-audit        test-gap
 code-flow                 기본 기능           (changes-audit)   (analysis)
 code-arch
     │                          │                  │                  │
     ▼                          ▼                  ▼                  ▼
 "지금 코드가 어떻게         "코드 수정"        "수정한 부분에       "변경 관련 테스트
  구성돼 있는지 파악"                            문제 없나?"         빠진 곳 확인"
```

**Codex 앱 태스크 예시**:

```
Step 1 (구조 파악):
이 레포를 code-map + code-flow + code-arch 스킬로 분석해줘.
결과를 docs/에 HTML로 저장하고 커밋해.

Step 2 (수정):
models/transformer.py의 Attention 클래스에서
multi-head attention의 head 수를 설정 가능하게 리팩토링해.

Step 3 (검사):
code-audit 스킬로 main 대비 변경사항(diff)을 changes-audit 모드로 검토해줘.

Step 4 (테스트):
test-gap 스킬로 수정된 models/transformer.py 관련 테스트 갭을 분석해줘.
분석만 하고 코드는 수정하지 마.
```

---

## 시나리오 비교

|  | 새 코드 작성 | 기존 코드 수정 |
|--|:----------:|:------------:|
| **Phase 1 목적** | 참고 레포 분석 (선택) | 현재 레포 구조 파악 (필수) |
| **code-map** | 참고용 — 비슷한 프로젝트 구조 벤치마크 | 필수 — 수정 전 의존관계 확인 |
| **code-flow** | 참고용 — 데이터 흐름 패턴 참고 | 필수 — 수정이 흐름에 미치는 영향 예측 |
| **code-arch** | 참고용 — 아키텍처 패턴 참고 | 필수 — 변경 영향 범위 파악 |
| **code-audit 모드** | `codebase-audit` (전체 스캔) | `changes-audit` (diff만 검토) |
| **test-gap 모드** | `implement` (테스트 코드 작성) | `analysis` (갭 분석만, 또는 회귀 테스트 작성) |

---

## 스킬 상세

### code-map — 구조 파악

| 항목 | 내용 |
|------|------|
| **질문** | "이 파일이 뭘 하지? 모듈 간 의존관계는?" |
| **동작** | 코드 읽기 전용, 수정 없음 |
| **산출물** | 모듈·심볼·의존관계 HTML 대시보드 |
| **스크립트** | `extract_python_symbols.py` → JSON → `codemap_dashboard.py` → HTML |

### code-flow — 데이터 흐름

| 항목 | 내용 |
|------|------|
| **질문** | "데이터가 어떻게 흘러가지? 파이프라인 구조는?" |
| **동작** | 프로젝트 유형 자동 감지 (ML, 웹, CLI, 파이프라인, 프론트엔드) → 읽기 전용 |
| **산출물** | 파이프라인별 데이터 흐름 HTML 다이어그램 |
| **스크립트** | `detect_project_type.py` → 유형 판별 → JSON → `render_dataflow.py` → HTML |

### code-arch — 아키텍처

| 항목 | 내용 |
|------|------|
| **질문** | "전체 계층이 어떻게 나뉘고, 횡단 관심사는 뭐지?" |
| **동작** | 코드 읽기 전용, 수정 없음 |
| **산출물** | 계층 구조 + 횡단 관심사 HTML 다이어그램 |
| **스크립트** | JSON → `render_architecture.py` → HTML |
| **인터랙티브** | 컴포넌트 클릭 → 사이드 패널, 레이어/그룹 접기·펼치기 |

### code-audit — 코드 감사

| 항목 | 내용 |
|------|------|
| **질문** | "이 코드에 버그나 보안 취약점이 있나?" |
| **동작** | 결함 탐지 전용, 코드 수정 없음 |
| **산출물** | 결함 리포트 HTML (심각도·위치·설명) |
| **모드** | `codebase-audit` (전체) / `changes-audit` (diff) |
| **찾는 것** | 정확성 결함, 보안 취약점, 문서-코드 불일치, 구조적 문제 |

### test-gap — 테스트 갭 분석

| 항목 | 내용 |
|------|------|
| **질문** | "테스트가 빠진 위험 지점이 어디지?" |
| **동작** | 코드 읽고 리스크 기반 분석. 모드에 따라 테스트 코드 작성 가능 |
| **산출물** | 테스트 플랜 (analysis) 또는 테스트 코드 (implement) |
| **모드** | `analysis only` (코드 수정 없음) / `design and implement` (테스트 작성) |
| **ML 참고** | GPU 불필요 — shape 검증, config 파싱, 전처리, 에러 핸들링 테스트 가능 |

---

## 설치 방법

### 방법 1: 직접 복사 (권장)

```sh
git clone https://github.com/jake-jonghyeonlee/codex-skills.git
cp -r codex-skills/.codex/ /path/to/target-project/
cp codex-skills/AGENTS.md /path/to/target-project/
cd /path/to/target-project
git add .codex/ AGENTS.md && git commit -m "chore: Codex 앱 스킬 추가" && git push
```

### 방법 2: 서브모듈

```sh
cd /path/to/target-project
git submodule add https://github.com/jake-jonghyeonlee/codex-skills.git .codex-skills
ln -s .codex-skills/.codex .codex
cp .codex-skills/AGENTS.md .
```

### 방법 3: Codex 앱 태스크에서 직접 설치

```
https://github.com/jake-jonghyeonlee/codex-skills 레포에서
.codex/ 디렉터리와 AGENTS.md를 이 프로젝트 루트로 복사하고 커밋해.
```

---

## 포함 스킬 요약

| 스킬 | 시나리오 A (새 코드) | 시나리오 B (수정) | 스크립트 | 산출물 |
|------|:------------------:|:----------------:|:--------:|--------|
| **code-map** | 참고 분석 | 구조 파악 | `extract_python_symbols.py` + `codemap_dashboard.py` | HTML |
| **code-flow** | 참고 분석 | 흐름 파악 | `detect_project_type.py` + `render_dataflow.py` | HTML |
| **code-arch** | 참고 분석 | 영향 범위 | `render_architecture.py` | HTML |
| **code-audit** | 전체 감사 | diff 검토 | `code_review_adapter.py` + `audit_dashboard.py` | HTML |
| **test-gap** | 테스트 작성 | 갭 분석 | 없음 (SKILL.md만) | 분석 / 코드 |

모든 Python 스크립트는 **표준 라이브러리만** 사용. Codex 앱 클라우드 샌드박스에서 추가 설치 없이 실행 가능.
