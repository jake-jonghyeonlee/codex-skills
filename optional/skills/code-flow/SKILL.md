---
name: code-flow
description: "Auto-detect a project's type (ML/DL, web server, CLI, data pipeline, library, frontend) and render an interactive, self-contained HTML data-flow diagram from its pipelines. Use when the user wants a visual data-flow diagram of a codebase, as opposed to a defect audit (code-audit), a structure overview (code-map), or an architecture diagram (code-arch)."
---

# Project Diagrams

역할: 프로젝트의 **데이터 흐름도**를 자동 생성한다.
프로젝트 유형을 자동 감지하고, 파이프라인 흐름을 분석하여
인터랙티브 HTML 다이어그램으로 렌더링한다.

이 스킬은 전역 설치본이다 — 스크립트는 이 SKILL.md와 같은 디렉터리 아래
`scripts/`에 번들돼 있다. 예: 이 파일이 `~/.codex/skills/code-flow/SKILL.md`라면
`~/.codex/skills/code-flow/scripts/`.

## 0. 프로젝트 유형 감지

```sh
python3 <이 SKILL.md가 있는 디렉터리>/scripts/detect_project_type.py <repo-root>
```

가중치 점수 기반으로 프로젝트를 분류한다:

| 신호 종류 | 예시 | 설명 |
|-----------|------|------|
| **import 문** | `torch`, `flask`, `pandas` | 핵심 프레임워크 import에 높은 가중치 |
| **파일명** | `train.py`, `app.py`, `etl.py` | 관례적 파일명 패턴 매칭 |
| **디렉토리** | `routes/`, `models/`, `dags/` | 프레임워크별 디렉토리 구조 |
| **코드 패턴** | `nn.Module`, `@app.route`, `DataFrame` | 정규식으로 코드 내 패턴 탐색 |

지원하는 유형:
- **ml_dl** — ML/딥러닝 (PyTorch, TensorFlow, JAX, sklearn 등)
- **web_server** — 웹 서버/API (Flask, Django, FastAPI, Express 등)
- **cli_tool** — CLI 도구 (argparse, click, typer 등)
- **data_pipeline** — 데이터 파이프라인/ETL (pandas, Airflow, Spark 등)
- **library** — 라이브러리/패키지
- **frontend** — 프론트엔드 (React, Vue, Angular, Next.js 등)

출력에는 `suggested_pipelines`(분석할 파이프라인 후보)와
`suggested_data_types`(자료형 색상 프리셋)이 포함된다.

## 1. 코드 읽기 — 파이프라인 추출

감지 결과의 `entry_points`부터 읽기 시작한다. 유형별 분석 포인트:

### ml_dl
- **학습**: 데이터 로딩 → 전처리 → DataLoader → 모델 순전파 → 손실 계산 → 역전파 → 체크포인트
- **추론**: 입력 로딩 → 전처리 → 모델 순전파 → 후처리 → 출력 저장
- 각 단계에서 **자료형 변환**(PIL→numpy→Tensor 등)과 **텐서 형태**(BCHW 등)를 추적

### web_server
- **요청 흐름**: 클라이언트 요청 → 미들웨어 체인 → 라우터 → 핸들러/컨트롤러 → DB 접근 → 응답
- **인증**: 요청 → 토큰 추출 → 검증 → 사용자 조회 → 권한 확인
- 각 단계에서 **데이터 형태**(Request → dict → Model → Response 등)를 추적

### cli_tool
- **명령 실행**: CLI 인자 → 파싱 → 검증 → 핵심 로직 → 출력 포맷팅 → stdout/파일
- 서브커맨드가 여러 개면 주요 커맨드별로 별도 파이프라인

### data_pipeline
- **ETL**: 소스(DB/파일/API) → 추출 → 정제 → 변환 → 집계 → 적재(DB/파일)
- DAG가 있으면 태스크 간 의존관계도 파이프라인으로 표현

### library
- **공개 API 호출**: 사용자 입력 → API 함수 → 내부 처리 → 반환값
- 주요 public 함수/클래스의 데이터 흐름

### frontend
- **사용자 인터랙션**: 이벤트 → 핸들러 → 상태 업데이트 → 리렌더링
- **데이터 페칭**: 컴포넌트 마운트 → API 호출 → 응답 처리 → 상태 저장 → UI 반영

## 2. JSON 작성

**언어: 모든 콘텐츠는 한글로 작성한다.** `project.description`, `project.type_label`,
각 파이프라인의 `name`, 노드의 `label`과 `detail`, 타입의 `label` 등
사람이 읽는 설명 텍스트는 전부 한글이어야 한다.
코드 식별자(함수명, 클래스명 등)와 기술 용어(API, CLI, DAG 등)는
원어 그대로 쓰되, 설명 문장 자체는 한글로 쓴다.

감지 결과의 `suggested_data_types`를 기본으로 하되, 프로젝트에 맞게 조정한다.

```json
{
  "project": {
    "name": "프로젝트 이름",
    "type_label": "감지된 유형 라벨",
    "description": "파이프라인 요약 설명"
  },
  "types": {
    "type_key": {
      "label": "표시 이름",
      "preset": "gray|red|orange|amber|green|teal|blue|indigo|purple|pink"
    }
  },
  "pipelines": [
    {
      "name": "파이프라인 이름",
      "source": "소스 파일명 (선택)",
      "steps": [
        {"label": "단계 이름", "detail": "형태/포맷 정보", "type": "type_key"},
        {"arrow": "함수/메서드 이름"},
        {"label": "다음 단계", "detail": "변환된 형태", "type": "다른_type_key"}
      ]
    }
  ]
}
```

규칙:
- `steps`는 **노드**(`label`+`type`)와 **화살표**(`arrow`)가 번갈아 나온다
- `detail`은 선택적이지만, 자료형/형태 정보를 넣으면 코드 이해에 큰 도움이 된다
- 노드를 5~8개 수준으로 유지 — 너무 세부적이면 가독성이 떨어진다
- 화살표의 `arrow`에는 실제 함수/메서드 이름을 넣는다

## 3. 렌더링

```sh
python3 <이 SKILL.md가 있는 디렉터리>/scripts/render_dataflow.py pipelines.json -o <project>-dataflow.html
```

결과 HTML은 외부 의존성 없이(Google Fonts 제외) 독립 실행 가능하다.
다크/라이트 테마 모두 지원한다.

## 4. 아키텍처 다이어그램 (선택 — 에이전트 수동 작성)

아키텍처 다이어그램은 프로젝트마다 구조가 너무 다르므로 자동 렌더러 대신
에이전트가 코드를 읽고 직접 HTML/SVG로 작성한다. 유형별 가이드:

| 유형 | 추천 레이아웃 | 핵심 요소 |
|------|--------------|-----------|
| ml_dl | U자형 / 순차 블록 다이어그램 | 레이어별 채널 수·해상도, 스킵 연결 |
| web_server | 계층형 (Client→Server→DB) | 미들웨어 스택, 요청/응답 흐름 |
| cli_tool | 순차 흐름 | 인자 파싱 → 처리 → 출력 |
| data_pipeline | 좌→우 DAG | 태스크 노드, 의존 엣지 |
| library | 동심원/계층 | 공개 API → 내부 → 기반 |
| frontend | 컴포넌트 트리 + 상태 흐름 | 컴포넌트 계층, store, API 계층 |

아키텍처 다이어그램은 데이터 흐름도와 같은 페이지에 넣거나
별도 HTML로 분리해도 된다.

## 참고

- `code-map`, `code-arch` 스킬과 함께 사용하면 **구조(code-map)** + **흐름(code-flow)** +
  **전체 그림(code-arch)**으로 처음 보는 레포를 빠르게 파악할 수 있다
- `detect_project_type.py`는 Python·JS/TS·Go 프로젝트를 스캔한다.
  다른 언어는 파일명/디렉토리 패턴으로만 판별한다
