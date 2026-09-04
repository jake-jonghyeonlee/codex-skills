# Codex Skills

Codex 앱 전용 코드 분석 스킬 5종.
GitHub 레포에 `.codex/` 디렉터리를 포함시키면 Codex 앱이 자동 인식한다.

> **CLI(codex CLI)가 아닌 Codex 앱(cloud)에서 사용하는 것을 전제로 설계.**
> 모든 스크립트는 표준 라이브러리만 사용하며 외부 패키지 설치 불필요.

## 개발 워크플로우와 스킬 배치

```
┌─────────────────────────────────────────────────────────┐
│  1. 이해        2. 구현        3. 검사        4. 테스트  │
│  ──────────    ──────────    ──────────    ──────────    │
│  code-map      (Codex 앱     code-audit    test-gap     │
│  code-flow      기본 기능)                               │
│  code-arch                                              │
└─────────────────────────────────────────────────────────┘
```

---

### Phase 1 — 이해 (코드를 읽고 구조를 파악)

구현 전에 레포를 세 가지 관점으로 분석한다.
코드를 수정하지 않고 읽기만 하며, 각각 독립 실행 가능한 HTML을 생성한다.

| 순서 | 스킬 | 질문 | 산출물 |
|:----:|------|------|--------|
| 1-1 | **code-map** | "이 파일이 뭘 하지?" | 모듈·심볼·의존관계 대시보드 |
| 1-2 | **code-flow** | "데이터가 어떻게 흘러가지?" | 파이프라인별 데이터 흐름도 |
| 1-3 | **code-arch** | "전체 계층이 어떻게 나뉘지?" | 계층 구조 + 횡단 관심사 다이어그램 |

**사용 시점**: 처음 보는 레포, 대규모 리팩토링 전, 온보딩 문서 작성 시

**Codex 앱 태스크 예시**:
```
이 레포의 구조를 code-map 스킬로 분석해줘.
결과 HTML을 docs/codemap.html로 저장하고 커밋해.
```
```
code-arch 스킬로 이 프로젝트의 아키텍처 다이어그램을 만들어줘.
ML/DL 프로젝트이고 모델 구조를 중심으로 분석해.
```

### Phase 2 — 구현

Codex 앱의 기본 코딩 기능으로 진행한다. 별도 스킬 불필요.
Phase 1에서 생성된 HTML 산출물을 참고하면 구조를 이해한 상태에서 작업 가능.

### Phase 3 — 검사 (코드 결함 탐지)

구현 후 코드 품질을 점검한다.

| 스킬 | 질문 | 산출물 |
|------|------|--------|
| **code-audit** | "이 코드에 버그가 있나?" | 결함 리포트 HTML (심각도·위치·설명) |

**찾는 것**: 정확성 결함, 보안 취약점, 문서-코드 불일치, 구조적 문제

**두 가지 모드**:
- `changes-audit` — 변경된 코드(diff)만 검토 → PR 올리기 전 자체 점검
- `codebase-audit` — 전체 레포 검토 → 신규 레포 온보딩, 인수인계 시

**Codex 앱 태스크 예시**:
```
code-audit 스킬로 이 레포 전체를 감사해줘.
결과를 docs/audit-report.html로 저장하고 커밋해.
```
```
최근 변경사항(main 브랜치 대비 diff)을 code-audit으로 검토해줘.
```

### Phase 4 — 테스트 (테스트 갭 분석)

검사에서 발견된 결함과 기존 코드 모두에 대해 테스트 누락을 분석한다.

| 스킬 | 질문 | 산출물 |
|------|------|--------|
| **test-gap** | "테스트가 빠진 곳이 어디지?" | 리스크 기반 테스트 플랜 또는 테스트 코드 |

**찾는 것**: 경계값 미검증, 에러 처리 미테스트, 타입 불일치 가능성, 공개 API 미검증

**두 가지 모드**:
- `analysis only` — 테스트 플랜만 출력 (코드 수정 없음)
- `design and implement` — 테스트 코드까지 작성하여 커밋

**ML/DL 프로젝트 참고**: Codex 앱 샌드박스에 GPU가 없어도 다음 테스트는 가능:
- 텐서 shape 검증 (`assert output.shape == (B, 1000)`)
- 설정/하이퍼파라미터 파싱
- 전처리 파이프라인 (CPU로 충분)
- 모델 구조 검증 (레이어 수, 파라미터 수)
- 에러 핸들링 (잘못된 입력 시 올바른 에러 발생)

**Codex 앱 태스크 예시**:
```
test-gap 스킬로 이 레포의 테스트 갭을 분석해줘.
분석만 하고 코드는 수정하지 마.
```
```
test-gap 스킬로 models/ 디렉터리의 테스트 갭을 찾고,
빠진 유닛 테스트를 tests/에 작성해서 커밋해.
GPU 없이 실행 가능한 테스트만 만들어.
```

---

## 스킬 간 연계

```
code-map ──→ 구조 파악 후 어디를 고칠지 판단
code-flow ──→ 데이터 흐름 이해 후 사이드 이펙트 예측
code-arch ──→ 전체 그림에서 변경 영향 범위 확인
                │
                ▼
           구현 (Codex 앱)
                │
                ▼
code-audit ──→ 결함 발견
                │
                ▼
test-gap ───→ 결함 재발 방지 테스트 + 나머지 갭 채우기
```

**한 번에 여러 스킬 사용 예시** (Codex 앱 태스크):
```
이 ML 레포를 분석해줘:
1. code-map으로 모듈 구조를 docs/codemap.html로
2. code-arch로 아키텍처를 docs/architecture.html로
3. code-audit으로 결함 리포트를 docs/audit.html로
모두 생성해서 커밋해.
```

---

## 설치 방법

### 방법 1: 직접 복사 (권장)

분석 대상 프로젝트에 `.codex/` 디렉터리를 복사:

```sh
# 이 레포를 클론
git clone https://github.com/jake-jonghyeonlee/codex-skills.git

# 대상 프로젝트에 복사
cp -r codex-skills/.codex/ /path/to/target-project/
cp codex-skills/AGENTS.md /path/to/target-project/

# 커밋
cd /path/to/target-project
git add .codex/ AGENTS.md
git commit -m "chore: Codex 앱 스킬 추가"
git push
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

| 스킬 | Phase | 스크립트 | 외부 의존성 | 산출물 |
|------|:-----:|:--------:|:----------:|--------|
| **code-map** | 이해 | `extract_python_symbols.py` + `codemap_dashboard.py` | 없음 | HTML |
| **code-flow** | 이해 | `detect_project_type.py` + `render_dataflow.py` | 없음 | HTML |
| **code-arch** | 이해 | `render_architecture.py` | 없음 | HTML |
| **code-audit** | 검사 | `code_review_adapter.py` + `audit_dashboard.py` | 없음 | HTML |
| **test-gap** | 테스트 | 없음 (SKILL.md만) | 없음 | 분석 / 테스트 코드 |

모든 Python 스크립트는 **표준 라이브러리만** 사용. Codex 앱 클라우드 샌드박스에서 추가 설치 없이 실행 가능.
