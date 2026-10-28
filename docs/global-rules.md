# 전역 규칙(`global/AGENTS.md`) — 출처와 근거

작성일: 2026-10-28. 외부망 Mac 의 `~/.claude/CLAUDE.md`·`~/AGENTS.md`(2026-10-25 판) 중 환경에 묶이지 않은 규칙을 추려
폐쇄망 Codex 앱용으로 다시 썼다. 뺀 것: Paseo·MMO·Orca 오케스트레이션 절차, 모델 ID, Gmail·wiki 연동, 연락처, 로컬 경로.

## 1. 왜 짧게 쓰는가

| 출처 | 요지 |
|---|---|
| OpenAI Codex 문서 "Custom instructions with AGENTS.md" | 전역 파일은 Codex 홈(`~/.codex`, `CODEX_HOME`)의 `AGENTS.override.md` → `AGENTS.md` 순으로 하나만 읽는다. 전역 + 저장소 루트 + 하위 디렉터리 파일을 이어 붙이고, 합산 `project_doc_max_bytes`(기본 32 KiB)를 넘으면 뒤는 버린다. 전역에는 "재사용 가능한 작업 합의"(테스트 명령, 패키지 매니저, 의존성 추가 전 확인)만 둔다 |
| OpenAI "Harness engineering"(2026-02, Ryan Lopopolo) | 큰 AGENTS.md 하나는 실패했다. 전역 파일은 지도(목차) 역할만 하고 세부는 `docs/` 에 둔다. 린터 에러 메시지가 수정 방법을 설명하게 한다 |
| Mitchell Hashimoto, Ghostty `AGENTS.md` | 파일은 실패 로그다. 각 줄은 에이전트가 실제로 저지른 실수에서 나온다. 내용은 빌드·테스트·포맷 명령, 디렉터리 지도, 금지 사항뿐 |
| Boris Cherny(Claude Code) 공개 팁, 2차 출처 | 팀 공유 지침 파일을 git 으로 관리하고 실수마다 한 줄 추가. 약 2.5k 토큰 유지 |

결론: 전역 파일은 100줄 안팎, 환경 종속 내용은 저장소 AGENTS.md 로, 실수가 날 때마다 한 줄씩 늘린다.

## 2. 절별 출처

| 절 | 출처 |
|---|---|
| 1–4 (생각·최소 변경·외과적 수정·목표 기반) | multica-ai/andrej-karpathy-skills `CLAUDE.md`(MIT). Andrej Karpathy 가 2025년 말 X 에 올린 LLM 코딩 실수 관찰을 Jiayuan Chang 이 네 원칙으로 정리. Karpathy 본인이 쓴 AGENTS.md 는 없다 |
| 4 (검증 출력 없이는 완료 아님) | 이 번들의 `verification-before-completion` 스킬(obra/superpowers) 과 같은 규칙 |
| 5 (문서 신뢰도) | 외부망 CLAUDE.md "일반 세션" 절. `파일:줄` 근거, 미확인 표시, 질의응답 중 수정 금지 |
| 6 (통제 언어) | 외부망 CLAUDE.md "출력 형식" 절 + ASD-STE100(Simplified Technical English, 항공 정비 문서 표준) 의 핵심 규칙: 한 문장 한 생각, 절차는 한 문장 한 동작, 명령형, 능동태·현재 시제, 20단어 안팎, 문단 6문장 이내, 한 단어 한 뜻, 경고는 동작 앞 |
| 7 (Git·안전) | 외부망 Global Orchestration Policy 의 "Failure routing and recovery" 중 환경 무관 부분. hard reset·stash pop·worktree 삭제 금지, 실패 원인 분류, 실패만으로 모델 상향 금지 |
| 7a (위험 등급·독립 리뷰) | 같은 정책의 "Risk tier" 와 "Validation and independent review". High-risk 목록, diff 로 재판정, 작성자≠리뷰어, PASS 는 commit 단위 |
| 7b (도구 사용) | 외부망 Paseo 운영 규칙 "도구 사용(권한 요청 줄이기)". Read/Edit 도구 → Codex 의 `apply_patch`·범위 읽기로 치환 |
| 5 끝 두 줄 (새 스레드·`/compact`, 좁은 지시) | 외부망 "일반 세션" 의 `/clear`·`/compact` 제안과 정책의 "Context, not effort, dominates usage"(좁은 브리핑, Task 마다 새 세션) |
| 6 (다이어그램·HTML·영상) | 외부망 "출력 형식" 과 "Lead 의 사용자 보고 형식". 스킬 이름은 이 번들에 있는 것으로 치환 |
| 8 (환경) | 이 번들의 `AGENTS.md` "실행 환경" 절과 같다 |

## 2b. 실제 운영 기록에서 추가한 규칙 (2026-10-28)

외부망 Paseo Run 2026-10-22~28 의 워커 계약(`T*_CONTRACT.md`) Constraints, CHECKPOINT 「남은 일」절, 메모리의 feedback 항목에서
반복된 것만 골랐다. 횟수는 계약 파일에서 센 값이다.

| 추가한 줄 | 근거 |
|---|---|
| 1절: 모순·틀린 계약이면 멈추고 묻는다 | 계약 Constraints 에 "계약이 틀렸거나 모호하면 멈추고 코디네이터에게" 7회 |
| 4절: 완료 보고 4분할(한 것·남은 일·범위 밖·사용자 결정) | 모든 CHECKPOINT 가 「남은 일 / 미해결 질문」을 이 구조로 적었다. 범위 밖 발견(N5, F1~F3 등)을 고치지 않고 적는 관행 |
| 6절: 사용자 대상 텍스트는 한국어 | 2026-10-26 change-roi Run 에서 Lead 가 영어로 보고하자 사용자가 "한글로 얘기해" 지시(메모리 `reply-in-korean`) |
| 7절: 커밋 메시지 첫 줄은 이유, 꼬리표는 저장소 규칙 | "커밋 메시지 끝: Co-Authored-By …" 12회. 폐쇄망은 꼬리표가 다를 수 있어 저장소 규칙으로 위임 |
| 7절: 전역 설치·업데이트는 승인 뒤 | Codex 업데이트 프롬프트에서 Enter 가 "Update now" 를 골라 전역 npm 업데이트가 일어난 사고(메모리 `codex-update-prompt-orca`) |
| 8절: 대상 환경 Python 버전·라이브러리 상한 | "numpy·Pillow·표준 라이브러리만, Python 3.8 문법 상한" 8회. ETX 가 3.9.14 로 확인된 뒤에도 같은 규칙 유지(repo-rules particle-sim-compare) |
| 8절: 산출물 byte 불변 확인 | "Windows zip·wheel 불변" 8회, "bundles 바이트 불변" 2회 |
| 8절: 테스트는 네트워크 없이 합성 데이터, 운영 자원 금지 | "테스트는 소켓 차단·합성 데이터" 3회, repo-rules 공통 "live DB·운영 포트 금지", `launchctl` 금지 |

넣지 않은 것: worktree 전용 편집·main 체크아웃 편집 금지(Paseo 구조 전제, 전역 7절 "작업 브랜치" 로 충분), 하위 에이전트 금지(Codex 앱에 없음),
DL2 pin·bundle 경로 같은 저장소 전용 규칙(그 저장소 AGENTS.md 몫), Docker rename·Aside 탭 같은 도구 전용 교훈.

## 2a. 외부망 규칙과 다르게 쓴 곳 (충돌 조정)

| 외부망 규칙 | 폐쇄망 Codex 에서 바꾼 이유와 결과 |
|---|---|
| `/clear` 로 새로 시작 | Codex 에는 `/clear` 가 없다. "새 스레드" 로 바꿨다. `/compact` 는 Codex CLI 에도 있다 |
| 파일 읽기·수정은 Read/Grep/Glob·Edit/Write 도구로 | Codex 에는 그 도구가 없다. 수정은 `apply_patch`, 읽기는 `rg -n`·`sed -n` 범위 지정으로 바꿨다. 목적(셸로 파일 쓰기 금지, 권한 요청 줄이기)은 같다 |
| 독립 리뷰는 별도 모델·세션(Sonnet high / Opus high)이 한다 | 폐쇄망 Codex 는 모델 선택지가 다르고 서브에이전트가 없다. "새 스레드에서 `differential-review`" 로 바꿨다. 리뷰어 모델 지정은 뺐다 |
| 다이어그램 스킬 archify / code-arch / code-flow, HTML 스킬 dataviz / frontend-slides | archify·dataviz 는 번들에 없다. `code-map`·`archscribe`(활성), `code-arch`·`code-flow`·`frontend-slides`(선택) 로 바꿨다 |
| 일회성 자료는 `~/artifacts/<날짜-주제>/` | Windows 경로 예(`D:\work\자료`)로 바꿨다. 번들 AGENTS.md "산출물 저장" 절과 같다 |
| 설명 영상은 요청 시만, 외부 TTS 는 과금이라 승인 후, 기본은 `say`·ffmpeg | 폐쇄망에는 외부 TTS 도 `say` 도 없다. "요청 시만" 한 줄만 남겼다 |
| 연락처·Gmail·Aside 메일 절차, wiki 질의 | 폐쇄망에 없는 도구라 뺐다 |
| Paseo·MMO·Orca 절차, 모델 ID·effort 라우팅, 프로필 이름 | 폐쇄망 Codex 앱에 해당 없음. 환경 무관 원칙(편집자 1명, 작성자≠리뷰어, 위험 등급, 실패 분류)만 7·7a 로 옮겼다 |

주의: 번들 `AGENTS.md` 의 "비대화형 태스크에서는 중간 확인을 구하지 말고 끝까지 간다" 와 전역 1절 "불확실하면 묻는다" 는 충돌이 아니다.
전역 1절에 "비대화형 태스크는 가정을 적고 끝까지 간다" 를 같이 두어 같은 뜻으로 맞췄다.

## 3. 유지 규칙

- 저장소에 묶인 규칙(빌드 명령, 보호 경로, 테스트 명령)은 전역이 아니라 그 저장소의 AGENTS.md 에 쓴다.
- Codex 가 같은 실수를 두 번 하면 그 실수를 막는 한 줄을 추가한다. 원인이 특정 저장소면 저장소 파일에 쓴다.
- 전역 파일이 10 KB 를 넘으면 절을 `docs/` 로 내리고 전역에는 한 줄 요약과 경로만 남긴다(2026-10-28 현재 8.7 KB).

## 4. 참고 링크 (외부망에서만 열림)

- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://openai.com/index/harness-engineering/
- https://github.com/multica-ai/andrej-karpathy-skills
- https://github.com/ghostty-org/ghostty/blob/main/AGENTS.md
- https://x.com/simonw/status/1981945527114875384 (CLAUDE.md 에서 `@AGENTS.md` 참조로 단일 소스 유지)
