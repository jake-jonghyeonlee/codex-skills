---
name: code-arch
description: "Read (never modify) a repo and produce a self-contained HTML architecture diagram showing layered structure, key components, cross-cutting concerns (hooks/middleware/plugins), and extension points. Complements code-map (structure) and code-flow (data flow) by providing the 'big picture' mental model."
---

# Code Architecture

역할: 레포를 **읽기만 하고** 계층 구조 · 핵심 컴포넌트 · 횡단 관심사 ·
확장 포인트를 한 장의 인터랙티브 HTML 아키텍처 다이어그램으로 정리한다.
코드를 고치지 않는다.

이 스킬은 전역 설치본이다 — 스크립트는 이 SKILL.md와 같은 디렉터리 아래
`scripts/`에 번들돼 있다.

## 0. 스코프

대상 레포 경로와 프로젝트 이름을 확인한다. README/docs가 있으면 먼저 읽어
아키텍처의 초안을 잡되, 실제 코드로 검증한다.

## 1. 코드 읽기 — 계층 식별

진입점(main, CLI, app factory, HTTP handler 등)부터 시작해 **위→아래**로 읽는다.

### 식별할 것

| 항목 | 찾는 법 |
|------|---------|
| **계층 (Layer)** | import 방향이 한쪽으로만 흐르는 경계 — 상위 계층이 하위를 import하지 그 반대가 아닌 지점 |
| **핵심 컴포넌트** | 각 계층에서 public API를 제공하는 클래스/함수/모듈 |
| **횡단 관심사** | 여러 계층을 관통하는 시스템 — 훅(pluggy/signals), 미들웨어, 로깅, 인증, 이벤트 버스 등 |
| **확장 포인트** | 사용자가 상속/구현/등록으로 커스터마이즈 가능한 지점 — 추상 클래스, 플러그인 레지스트리, 설정 교체 |

### 유형별 가이드

| 유형 | 전형적 계층 구조 | 주의할 횡단 관심사 |
|------|-----------------|-------------------|
| **프레임워크/라이브러리** | 진입점 → 코어 API → 내부 엔진 → 기반 유틸 | 훅/이벤트, 플러그인, 설정 로더 |
| **웹 서버** | 라우터 → 미들웨어 → 핸들러 → 서비스 → 데이터 접근 → DB | 인증, 로깅, 에러 핸들링 |
| **CLI 도구** | CLI 파서 → 커맨드 → 비즈니스 로직 → I/O | 설정, 로깅 |
| **ML/딥러닝** | 데이터 로더 → 전처리 → 모델 → 학습 루프 → 평가 → 체크포인트 | 실험 추적, 로깅 |
| **프론트엔드** | 라우터 → 페이지 → 컴포넌트 → 상태 관리 → API 클라이언트 | 인증, 에러 경계, 테마 |

## 2. JSON 작성

**언어: 모든 콘텐츠는 한글로 작성한다.** 계층 이름, 컴포넌트 설명, 횡단 관심사
설명, 확장 포인트 안내 등 사람이 읽는 텍스트는 전부 한글이어야 한다.
코드 식별자와 기술 용어는 원어 그대로 쓰되, 설명 문장은 한글로 쓴다.

```json
{
  "project": {
    "name": "프로젝트명",
    "version": "v1.0",
    "description": "한 줄 설명"
  },
  "groups": [
    {"name": "그룹 이름", "from": 2, "to": 3, "preset": "green"}
  ],
  "layers": [
    {
      "title": "계층 이름",
      "sub": "관련 파일 경로 또는 텐서 형상 변화",
      "preset": "blue",
      "components": [
        {"name": "ClassName", "main": true, "tip": "이 컴포넌트가 하는 일 — 동작 원리와 설계 이유까지"},
        {"name": "helper_func", "tip": "보조 설명"}
      ],
      "ext": {"label": "확장 이름", "tip": "확장 방법 설명"}
    }
  ],
  "crosscuts": [
    {
      "name": "Hook 시스템",
      "color": "pink",
      "points": [
        {"at_layer": 1, "name": "before_xxx"},
        {"at_layer": 3, "name": "after_xxx"}
      ]
    }
  ],
  "lifecycle": [
    {"name": "step_name", "desc": "이 단계에서 일어나는 일"}
  ],
  "extensions": [
    {"key": "Hook", "val": "pluggy 기반 — @hook_impl로 구현"}
  ]
}
```

### 필드 규칙

- `layers`: 위→아래 순서 (사용자에 가까운 것이 위). 5~8개가 적당.
- `layers[].preset`: `blue`, `purple`, `green`, `amber`, `teal`, `gray`, `red`, `pink`,
  `indigo`, `orange` 중 택 1. 인접 계층은 서로 다른 색을 쓴다.
- `layers[].sub`: 관련 파일 경로, 또는 DL 프로젝트에서는 텐서 형상 변화
  `(B, C_in, H, W) → (B, C_out, H', W')` 형식으로 데이터 흐름을 표시.
- `layers[].components`: 주요 클래스/함수. `main: true`면 굵게 표시. 계층당 3~6개.
  `tip`에는 **동작 원리와 설계 이유**를 상세히 — 클릭 시 사이드 패널에 표시됨.
- `layers[].ext`: 그 계층의 확장 포인트. 없으면 생략.
- `groups`: 인접 계층을 시각적으로 묶는 그룹. 왼쪽 브래킷 + 라벨로 표시.
  `from`/`to`는 0-기반 레이어 인덱스 (inclusive). 없으면 생략.
- `crosscuts`: 횡단 관심사. 오른쪽 레일로 표시. 이 프로젝트 고유의 횡단 관심사만
  넣는다 — 잔차 연결·Drop Path 같은 범용 기법은 컴포넌트 tip에서 설명.
- `crosscuts[].points[].at_layer`: 0-기반 레이어 인덱스. 해당 레이어 중앙에
  자동 정렬. `at` (0.0~1.0 비율)도 여전히 지원하지만 `at_layer` 권장.
- `crosscuts[].color`: 프리셋 이름. 기본값 `pink`.
- `lifecycle`: 실행 순서 — 실제 데이터 변환 과정을 단계별로 기술.
  레이어 이름을 반복하지 말고, 각 단계에서 **데이터가 어떻게 바뀌는지** 쓴다.
- `extensions`: 확장 포인트 요약 목록. 없으면 빈 배열.

## 3. 렌더

```sh
python3 <이 SKILL.md가 있는 디렉터리>/scripts/render_architecture.py arch.json -o <project>-architecture.html
```

결과 HTML은 외부 리소스 의존 없이(Google Fonts 제외) 독립 실행 가능하다.
다크/라이트 테마 모두 지원. 인터랙티브 기능:
- **사이드 패널**: 컴포넌트 클릭 시 오른쪽에 상세 패널 표시 (이름 + tip 텍스트 + 소속 레이어). Esc 또는 배경 클릭으로 닫기.
- **접기/펼치기**: 레이어 헤더 클릭으로 컴포넌트 접기/펼치기. 그룹 태그 클릭으로 그룹 내 전체 레이어 일괄 접기/펼치기.
- 횡단 관심사 레일, 확장 포인트 배지 포함.

## 4. 결과 보고

생성된 HTML 경로를 알려주고, 계층 구분이 코드의 실제 import 방향에 기반한 것인지
아니면 논리적 분류인지 명시한다.

## 참고 — 다른 스킬과의 관계

- **code-map**: 모듈·심볼 단위의 구조 — "이 파일이 뭘 하지?"
- **code-flow**: 데이터 흐름 — "실행하면 데이터가 어떻게 흘러가지?"
- **code-arch** (이 스킬): 전체 그림 — "계층이 어떻게 나뉘고 어디서 확장하지?"

세 스킬을 함께 쓰면 처음 보는 코드베이스를 구조/흐름/전체 그림 세 축으로
빠르게 파악할 수 있다.
