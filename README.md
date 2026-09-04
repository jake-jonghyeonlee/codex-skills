# Codex Skills

Codex 앱 전용 코드 개발·분석·보안 스킬 10종.
GitHub 레포에 `.codex/` 디렉터리를 포함시키면 Codex 앱이 자동 인식한다.

> **CLI(codex CLI)가 아닌 Codex 앱(cloud)에서 사용하는 것을 전제로 설계.**
> 모든 스크립트는 표준 라이브러리만 사용하며 외부 패키지 설치 불필요.
> 폐쇄망 환경에서 토큰을 절약하면서 사용 가능.

---

## 전체 워크플로우

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  0. 목표 정의    1. 이해        2. 구현           3. 검사       4. 보안·테스트 │
│  ───────────   ──────────   ──────────────    ──────────    ──────────────   │
│  define-goal   code-map     Codex 앱 기본      code-audit    security-*      │
│                code-flow    + debug-fix (버그)                test-gap        │
│                code-arch    + code-port (이식)                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 시나리오 A — 새 코드 작성 (새 프로젝트 / 새 기능)

처음부터 만드는 경우. 목표를 먼저 정의하고, 참고 레포가 있으면 분석 후 구현.

```
 0. 목표 정의         1. 참고 분석 (선택)      2. 구현            3. 검사          4. 보안·테스트
 ──────────         ──────────────         ──────────────    ──────────      ──────────────
 define-goal        code-map               Codex 앱 기본       code-audit      security-best-practices
                    code-flow              + code-port (이식)   (codebase)      security-threat-model
                    code-arch                                                  test-gap (implement)
     │                   │                      │                │                  │
     ▼                   ▼                      ▼                ▼                  ▼
 "뭘 만들지?          "참고 레포가             "코드 작성,       "작성한 코드에     "보안 취약점은?
  성공 기준은?"        어떻게 돌아가지?"        참고 코드 이식"    버그 있나?"       테스트 빠진 곳은?"
```

**code-port 활용**: 참고 레포의 특정 기능을 가져올 때 — 라이선스 확인, 타겟 프로젝트 컨벤션 준수, 출처 기록까지 구조화

**Codex 앱 태스크 예시**:

```
Step 0 (목표):
define-goal 스킬로 이 프로젝트의 목표를 정의해줘.
"PyTorch 기반 이미지 분류 모델, ImageNet top-1 accuracy 80% 이상,
학습 코드 + 추론 API 포함" 기준으로.

Step 1 (참고 분석):
https://github.com/xxx/reference-repo 를
code-map + code-arch 스킬로 분석해서 docs/에 HTML 저장해.

Step 2 (구현 — 이식):
code-port 스킬로 reference-repo의 MambaVisionMixer 클래스를
이 프로젝트의 src/models/에 이식해줘.
타겟 프로젝트 컨벤션에 맞게 조정하고 출처 기록해.

Step 3 (검사):
code-audit 스킬로 이 레포 전체를 codebase-audit 모드로 감사해줘.

Step 4 (보안 + 테스트):
security-best-practices 스킬로 보안 리뷰 리포트 작성해줘.
test-gap 스킬로 src/ 테스트 갭 찾고 tests/에 유닛 테스트 작성해.
```

---

## 시나리오 B — 버그 수정

이미 있는 코드의 결함을 수정하는 경우. 구조 파악 → 재현 → 진단 → 수정.

```
 0. 목표 정의         1. 구조 파악 (필수)      2. 버그 수정         3. 검사          4. 보안·테스트
 ──────────         ──────────────         ──────────────      ──────────      ──────────────
 define-goal        code-map               debug-fix            code-audit      security-best-practices
                    code-flow              (재현→진단→수정→검증)  (changes)       test-gap (implement)
                    code-arch
     │                   │                      │                │                  │
     ▼                   ▼                      ▼                ▼                  ▼
 "뭘 고칠지?          "지금 코드가             "버그 재현 →       "수정한 부분에     "보안 패턴 위반은?
  완료 기준은?"        어떻게 구성돼 있지?"      원인 진단 → 수정"  문제 없나?"       회귀 테스트 빠졌나?"
```

**debug-fix 핵심 흐름**: 재현 → 가설 수립 → 반증 → 근본 원인 → 최소 수정 → 회귀 테스트

**Codex 앱 태스크 예시**:

```
Step 0 (목표):
define-goal 스킬로 목표 정의해줘.
"models/attention.py에서 head_dim이 0일 때 ZeroDivisionError 발생.
수정 후 기존 테스트 통과 + 회귀 테스트 추가"

Step 1 (구조 파악):
code-map 스킬로 models/ 디렉터리의 구조를 분석해줘.

Step 2 (버그 수정):
debug-fix 스킬로 이 버그를 수정해줘.
재현 → 근본 원인 진단 → 수정 → 회귀 테스트까지.

Step 3 (검사):
code-audit 스킬로 main 대비 변경사항을 changes-audit 모드로 검토해줘.

Step 4 (테스트):
test-gap 스킬로 수정된 파일 관련 테스트 갭 확인하고
빠진 테스트 작성해.
```

---

## 시나리오 C — 리팩토링 / 기능 추가

기존 코드의 구조를 개선하거나 새 기능을 추가하는 경우.

```
 0. 목표 정의         1. 구조 파악 (필수)      2. 수정              3. 검사          4. 보안·테스트
 ──────────         ──────────────         ──────────────      ──────────      ──────────────
 define-goal        code-map               Codex 앱 기본         code-audit      security-best-practices
                    code-flow              + code-port (이식)     (changes)       test-gap (analysis)
                    code-arch
     │                   │                      │                │                  │
     ▼                   ▼                      ▼                ▼                  ▼
 "뭘 바꿀지?          "지금 코드가             "리팩토링 /        "수정한 부분에     "보안 패턴 위반은?
  완료 기준은?"        어떻게 구성돼 있지?"      기능 추가"         문제 없나?"       변경 관련 테스트는?"
```

**Codex 앱 태스크 예시**:

```
Step 0 (목표):
define-goal 스킬로 목표 정의해줘.
"Attention 클래스의 head 수를 설정 가능하게 리팩토링,
기존 테스트 전부 통과, 새 파라미터에 대한 테스트 추가"

Step 1 (구조 파악):
code-map + code-flow + code-arch 스킬로 이 레포를 분석해줘.

Step 2 (수정):
models/transformer.py의 Attention 클래스에서
multi-head attention의 head 수를 설정 가능하게 리팩토링해.

Step 3 (검사):
code-audit 스킬로 main 대비 변경사항을 changes-audit 모드로 검토해줘.

Step 4 (테스트):
test-gap 스킬로 수정된 models/transformer.py 관련 테스트 갭 분석해줘.
분석만 하고 코드는 수정하지 마.
```

---

## 시나리오 D — 코드 리뷰 / 인수인계 (구현 없음)

남이 작성한 코드를 검토하거나 인수받는 경우. 이해 + 검사 + 보안만 수행.

```
 1. 구조 파악              2. 결함 검사              3. 보안 검토              4. 테스트 갭
 ──────────────          ──────────              ──────────────          ──────────
 code-map                code-audit              security-best-practices  test-gap
 code-flow               (codebase)              security-threat-model    (analysis only)
 code-arch
     │                       │                       │                       │
     ▼                       ▼                       ▼                       ▼
 "이 코드 전체 구조는?"   "버그·구조적 문제는?"    "보안 위협은 뭐가 있지?"  "테스트 빠진 위험 지점은?"
```

**Codex 앱 태스크 예시**:

```
이 레포를 전체 분석해줘:
1. code-map으로 구조 → docs/codemap.html
2. code-flow로 데이터 흐름 → docs/dataflow.html
3. code-arch로 아키텍처 → docs/architecture.html
4. code-audit으로 결함 리포트 → docs/audit.html
5. security-best-practices로 보안 리포트 → docs/security-report.md
6. security-threat-model로 위협 모델 → docs/threat-model.md
7. test-gap으로 테스트 갭 분석 (분석만, 코드 수정 없음)
모두 생성해서 커밋해.
```

---

## 시나리오 비교

|  | A. 새 코드 | B. 버그 수정 | C. 리팩토링 | D. 코드 리뷰 |
|--|:---------:|:----------:|:---------:|:----------:|
| **define-goal** | ✅ 목표 정의 | ✅ 수정 기준 | ✅ 완료 기준 | — |
| **code-map** | 선택 | ✅ 필수 | ✅ 필수 | ✅ 필수 |
| **code-flow** | 선택 | ✅ 필수 | ✅ 필수 | ✅ 필수 |
| **code-arch** | 선택 | 선택 | ✅ 필수 | ✅ 필수 |
| **debug-fix** | — | ✅ **핵심** | — | — |
| **code-port** | ✅ 이식 시 | — | ✅ 이식 시 | — |
| **code-audit** | `codebase` | `changes` | `changes` | `codebase` |
| **security-b.p.** | ✅ 검토 | ✅ 검토 | ✅ 검토 | ✅ 검토 |
| **security-t.m.** | ✅ 모델링 | — | — | ✅ 모델링 |
| **test-gap** | `implement` | `implement` | `analysis` | `analysis` |

---

## 스킬 상세

### Phase 0 — define-goal (목표 정의)

| 항목 | 내용 |
|------|------|
| **질문** | "뭘 만들지? 성공 기준은? 완료를 어떻게 검증하지?" |
| **동작** | 모호한 의도를 구체적·측정 가능한 목표로 변환 |
| **산출물** | 목표 문장 (검증 방법 + 범위 포함) |
| **토큰** | 최소 — 구현 전 목표 명확화로 하류 토큰 절약 |
| **출처** | [openai/skills](https://github.com/openai/skills) 공식 curated |

### Phase 1 — 이해 (code-map / code-flow / code-arch)

| 스킬 | 질문 | 산출물 |
|------|------|--------|
| **code-map** | "이 파일이 뭘 하지? 의존관계는?" | 모듈·심볼·의존관계 HTML 대시보드 |
| **code-flow** | "데이터가 어떻게 흘러가지?" | 파이프라인별 데이터 흐름 HTML |
| **code-arch** | "계층이 어떻게 나뉘지? 횡단 관심사는?" | 아키텍처 HTML (사이드 패널 + 접기) |

### Phase 2 — 구현 (debug-fix / code-port)

| 스킬 | 질문 | 동작 | 산출물 |
|------|------|------|--------|
| **debug-fix** | "이 버그의 근본 원인은?" | 재현 → 가설·반증 → 근본 원인 → 최소 수정 → 회귀 테스트 | 수정된 코드 + 검증 결과 |
| **code-port** | "저 레포의 기능을 가져오려면?" | 소스 분석 → 호환성 확인 → 타겟 컨벤션 적용 → 출처 기록 → 검증 | 이식된 코드 + 출처·차이점 리포트 |

**debug-fix vs Codex 앱 기본 코딩의 차이**:

| | Codex 앱 기본 | debug-fix 스킬 |
|--|:------------:|:-------------:|
| 접근 | "고쳐줘" → 바로 수정 시도 | 재현 → 가설 → 반증 → 근본 원인 |
| 증거 | 없음 | 원인 체인 + 재현 로그 |
| 검증 | 수정 후 테스트 실행 | 수정 전 실패 확인 → 수정 후 통과 확인 |
| 범위 | 넓게 건드릴 수 있음 | 가장 좁은 수정 (side effect 최소화) |

**code-port vs 수동 복사의 차이**:

| | 수동 복사 | code-port 스킬 |
|--|:--------:|:-------------:|
| 라이선스 | 확인 안 함 | 라이선스·출처 확인 → 기록 |
| 컨벤션 | 소스 그대로 | 타겟 프로젝트 네이밍·구조에 맞게 변환 |
| 호환성 | 수동 확인 | 비호환 사항 자동 식별 (버전, 동기/비동기 등) |
| 검증 | 수동 | 소스 테스트 → 타겟 환경 테스트 비교 |

### Phase 3 — code-audit (코드 감사)

| 항목 | 내용 |
|------|------|
| **질문** | "이 코드에 버그가 있나?" |
| **모드** | `codebase-audit` (전체) / `changes-audit` (diff) |
| **찾는 것** | 정확성 결함, 로직 에러, 문서-코드 불일치, 구조적 문제 |
| **산출물** | 결함 리포트 HTML (심각도·위치·설명) |

### Phase 4a — 보안 (security-best-practices / security-threat-model)

| 스킬 | 질문 | 산출물 |
|------|------|--------|
| **security-best-practices** | "보안 코딩 패턴을 따르고 있나?" | `security-report.md` (심각도별 취약점 + 수정 제안) |
| **security-threat-model** | "이 시스템의 위협과 공격 경로는?" | `threat-model.md` (자산·경계·위협·완화책) |

**차이점**:

| | security-best-practices | security-threat-model |
|--|------------------------|----------------------|
| **관점** | 코드 패턴 수준 (구현) | 시스템 수준 (아키텍처) |
| **찾는 것** | pickle 역직렬화, 하드코딩 키, SQL 인젝션, XSS | 신뢰 경계, 공격 경로, 권한 상승, 데이터 유출 경로 |
| **참고 자료** | Python/JS/TS/Go 프레임워크별 보안 가이드 내장 | 프롬프트 템플릿 + 컨트롤·자산 체크리스트 내장 |

### Phase 4b — test-gap (테스트 갭 분석)

| 항목 | 내용 |
|------|------|
| **질문** | "테스트가 빠진 위험 지점이 어디지?" |
| **모드** | `analysis only` (분석만) / `design and implement` (테스트 작성) |
| **찾는 것** | 경계값 미검증, 에러 처리 미테스트, 타입 불일치, 공개 API 미검증 |
| **ML 참고** | GPU 불필요 — shape 검증, config 파싱, 전처리, 에러 핸들링 |

---

## 토큰 효율 가이드 (폐쇄망용)

토큰이 제한된 환경에서 효율적으로 사용하는 방법:

| 전략 | 설명 |
|------|------|
| **define-goal 먼저** | 목표를 명확히 하면 불필요한 탐색·재작업 방지 → 토큰 절약 |
| **필요한 스킬만** | 10개 전부 돌리지 말고 시나리오에 맞는 것만 선택 |
| **analysis only** | test-gap은 분석만 요청하면 토큰 크게 절약 |
| **diagnosis only** | debug-fix도 "진단만" 요청 가능 (코드 수정 없음) |
| **한 태스크에 묶기** | 여러 스킬을 한 태스크에 넣으면 컨텍스트 공유로 효율적 |
| **범위 한정** | "전체 레포" 대신 "src/models/ 디렉터리만"으로 범위 좁히기 |

**최소 조합** (리뷰만):
```
code-map + code-audit → 구조 파악 + 결함 탐지
```

**버그 수정 조합**:
```
define-goal + code-map + debug-fix + test-gap → 목표 → 구조 → 수정 → 검증
```

**개발 조합**:
```
define-goal + code-map + code-audit + test-gap → 목표 → 구조 → 검사 → 테스트
```

**풀 세트** (시간·토큰 여유 있을 때):
```
10개 전부 — 목표 → 이해 → 구현 → 검사 → 보안 → 테스트 완전 커버
```

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

| 스킬 | Phase | 유형 | 스크립트 | 토큰 | 출처 |
|------|:-----:|:----:|:--------:|:----:|------|
| **define-goal** | 0. 목표 | 계획 | 없음 | 최소 | openai 공식 |
| **code-map** | 1. 이해 | 분석 | `extract_python_symbols.py` + `codemap_dashboard.py` | 보통 | 자체 |
| **code-flow** | 1. 이해 | 분석 | `detect_project_type.py` + `render_dataflow.py` | 보통 | 자체 |
| **code-arch** | 1. 이해 | 분석 | `render_architecture.py` | 보통 | 자체 |
| **debug-fix** | 2. 구현 | 수정 | 없음 | 보통 | 자체 |
| **code-port** | 2. 구현 | 이식 | 없음 | 보통 | 자체 |
| **code-audit** | 3. 검사 | 감사 | `code_review_adapter.py` + `audit_dashboard.py` | 보통 | 자체 |
| **security-best-practices** | 4. 보안 | 보안 | 없음 (references 내장) | 적음 | openai 공식 |
| **security-threat-model** | 4. 보안 | 보안 | 없음 (references 내장) | 적음 | openai 공식 |
| **test-gap** | 4. 테스트 | 분석/구현 | 없음 | 적음~보통 | 자체 |

모든 Python 스크립트는 **표준 라이브러리만** 사용. Codex 앱 클라우드 샌드박스에서 추가 설치 없이 실행 가능.
