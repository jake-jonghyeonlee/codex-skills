# codex-home — 스킬·전역 규칙 외에 Codex 앱 효율을 올리는 로컬 설정

작성일: 2026-10-28. MCP 가 없는 폐쇄망 Windows 에서 Codex 앱이 로컬 파일만으로 읽는 설정이다.
키 이름은 Codex 설정 레퍼런스·subagents·execpolicy 문서(2026-10-28 열람) 기준이다. 폐쇄망 Codex 버전이 다르면 키가 없을 수 있다.

## 1. 설치

```bash
# Git Bash, codex-skills 루트에서
mkdir -p ~/.codex/rules ~/.codex/agents
cp codex-home/rules/default.rules   ~/.codex/rules/default.rules
cp codex-home/agents/*.toml         ~/.codex/agents/
cp codex-home/review.config.toml    ~/.codex/review.config.toml
cp codex-home/qa.config.toml        ~/.codex/qa.config.toml
mkdir -p ~/.codex/scripts && cp codex-home/scripts/codex_usage.py ~/.codex/scripts/
cp codex-home/hooks.json ~/.codex/hooks.json      # 기존 hooks.json 이 있으면 두 이벤트만 합친다
# config.toml 은 덮어쓰지 말고 필요한 키만 옮긴다
cat codex-home/config.toml.example
```

Windows 에서는 `hooks.json` 의 `commandWindows` 경로 `C:/Users/<계정>/…` 을 실제 계정으로 바꾼다.
새 hook 은 Codex 에서 `/hooks` 로 한 번 신뢰(trust)해야 돈다. 파일을 바꾸면 해시가 달라져 다시 신뢰해야 한다.

모델 배치(2026-10-28 사용자 결정): 일상·worker·explorer = `gpt-6-luna`, 리뷰(review 프로필·reviewer 에이전트) = `gpt-6.1-sol`.

적용 뒤 Codex 앱을 다시 시작한다. 실행 정책은 `codex execpolicy check -- git status` 로 어떤 규칙이 맞는지 본다.

| 파일 | 설치 위치 | 하는 일 |
|---|---|---|
| `rules/default.rules` | `~/.codex/rules/` | 명령 접두사별 allow / prompt / forbidden. 승인 클릭을 줄이고 파괴적 git 을 막는다 |
| `config.toml.example` | `~/.codex/config.toml` 에 키만 옮김 | 모델·effort, 승인·샌드박스, AGENTS.md 상한 64 KiB, 스킬 예산 10,000, 서브에이전트 상한 2, 알림 |
| `review.config.toml`, `qa.config.toml` | `~/.codex/` | `codex --profile review` (luna, high, read-only), `--profile qa` (sol, low, read-only) |
| `agents/reviewer.toml`, `agents/explorer.toml` | `~/.codex/agents/` | 명시 요청 시 생성되는 서브에이전트 역할. reviewer 는 독립 리뷰(sol high), explorer 는 읽기 전용 탐색(luna low) |
| `scripts/codex_usage.py`, `hooks.json` | `~/.codex/scripts/`, `~/.codex/hooks.json` | 턴마다 세션 누적·기간 누적·예산 대비 % 를 표시 (§2a) |

## 2a. 사용량 표시 — 답변마다 누적 토큰 보기

Codex 는 스레드마다 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` 을 쓰고, 턴마다 `token_count` 이벤트에
누적(`total_token_usage`)과 그 턴(`last_token_usage`)을 기록한다. 네트워크 없이 이 파일만 읽으면 된다.

`codex_usage.py` 가 두 hook 에서 돈다.

| 이벤트 | 출력 | 효과 |
|---|---|---|
| `UserPromptSubmit` | 한 줄 텍스트 `[usage] 세션 … · month 누적 …/예산 (…%)` | 모델의 개발자 컨텍스트로 들어간다. 전역 규칙 6절이 이 줄을 답변 마지막 줄에 옮기게 한다. 값은 턴 시작 시점(한 턴 전까지) 누적이다 |
| `Stop` | `{"systemMessage": "[usage] …"}` | 턴이 끝난 뒤 UI 에 경고 줄로 표시된다. 이번 턴까지 포함한 값이다 |

손으로 볼 때:

```bash
python ~/.codex/scripts/codex_usage.py                       # 최근 세션 + 이번 달 합계
python ~/.codex/scripts/codex_usage.py --all --period week   # 이번 주 세션 목록
```

예산은 사내 기준 수치 "3000" 을 표시 기준으로 쓴다. 스크립트 맨 위 `BUDGET_UNITS`(3000)·`TOKENS_PER_UNIT`(1 단위 = 1,000 토큰, 가정값)·
`BUDGET_PERIOD`(month)·`COUNT_CACHED` 로 바꾼다. 출력은 `누적 1,234/3,000 (41.1%, 1.2M tok)` 처럼 단위와 토큰을 같이 보여 준다.
보정: 사내 계기가 보여 주는 소모량과 같은 기간의 `tok` 값을 비교해 `TOKENS_PER_UNIT` 을 맞춘다. 캐시 입력을 세지 않는 기준이면 `COUNT_CACHED = False`.
외부망 Mac 의 10월 기록으로 돌려 보면 298 세션 1.8억 토큰 중 대부분이 cached input 이라, 캐시를 빼면 수치가 크게 달라진다.

검증된 것(외부망 Mac, 2026-10-28): CLI 모드, 두 hook 모드, 깨진 stdin(Windows 비ASCII 버그 openai/codex#23784) 폴백.
검증 못 한 것: 데스크톱 앱이 Stop 의 `systemMessage` 를 어디에 보여 주는지, Stop 이 울릴 때 마지막 `token_count` 가 이미 기록돼 있는지.
둘 중 하나가 안 보이면 UserPromptSubmit 경로(답변 마지막 줄)만으로도 한 턴 지연된 값은 본다.
Codex CLI 에서는 `/status` 로도 현재 스레드 사용량을 본다.

## 2. 실행 정책(rules)이 효율에 가장 크다

Codex 앱에서 시간을 가장 많이 먹는 것은 명령 승인 클릭이다. `default.rules` 는 세 묶음이다.

- allow: `git status/diff/log/show`, `rg`, `sed -n`, `python -m pytest`, `ruff`, `.venv-skills` 파이썬. 묻지 않고 실행.
- prompt: `git add/commit/switch`, `pip install`, `python scripts/…`. 한 번 확인. 전역 규칙 7절(commit 은 요청 시만, 의존성은 승인 뒤)과 짝이다.
- forbidden: `git reset --hard`, `checkout --`, `restore`, `clean`, `stash pop`, `push`, `merge`, `rebase`, `rm -rf`, `sed -i`, `npm`, `curl`. 전역 규칙 7·7b 를 도구 수준에서 강제한다.

여러 규칙이 맞으면 가장 엄격한 쪽이 이긴다. 리다이렉트·`$( )` 가 있는 명령은 통째로 비교되므로 안쪽 규칙이 안 걸린다.
Windows 샌드박스에서는 allow 여도 샌드박스 밖 실행이 필요하면 다시 묻는다는 보고(openai/codex#15298)가 있다. 그 경우 `approval_policy` 의 granular 옵션을 본다.

## 3. 커스텀 프롬프트(`~/.codex/prompts`)는 쓰지 않는다

Codex 문서가 커스텀 프롬프트를 deprecated 로 표시했고, 0.117.0 부터 제거됐다는 maintainer 답변이 있다(openai/codex#15941).
대신 스킬을 쓴다. 이 번들의 README §4 시나리오(A 기능 추가, B 버그 수정, C 검토, D 보고서)가 그 역할이다.
자주 쓰는 순서를 한 번에 부르고 싶으면 `.agents/skills/` 에 얇은 워크플로 스킬(SKILL.md 한 장, 스크립트 없음)을 더한다. 인자 치환(`$1`)은 스킬에 없다.

## 4. 앱 안에서 오케스트레이션이 되는가

된다. 다만 외부망 Paseo 와는 모양이 다르다.

| 외부망(Paseo) | 폐쇄망 Codex 앱 |
|---|---|
| Lead 가 `create_agent` 로 워커 생성, 프로필로 모델·effort 고정 | 주 스레드가 `spawn_agent` 로 서브에이전트 생성. `~/.codex/agents/*.toml` 역할(reviewer·explorer) 또는 내장 default·worker·explorer |
| 워커는 자동 생성 | 서브에이전트는 **명시 요청**("reviewer 에이전트로 리뷰해") 또는 AGENTS.md·스킬 지시가 있을 때만 생성. 자동 위임은 없다 |
| worktree 격리는 Paseo 워크스페이스 | 앱의 스레드별 Worktree 옵션(detached HEAD). 편집 스레드마다 하나 |
| 편집자 1명 + 읽기 전용 1명 | `agents.max_concurrent_threads_per_session = 2` 로 같은 상한 |
| 리뷰 PASS 를 `reviews.jsonl`·merge-gate 로 기록 | 도구가 없다. 리뷰 결과를 `docs/reports/<날짜>-review.md` 에 commit SHA 와 함께 남긴다 |
| 권한 요청은 사용자가 앱에서 승인 | 같다. 서브에이전트는 부모의 샌드박스·승인 설정을 상속한다(파일에서 못 바꿈) |

제약:
- Windows 에서 이름 있는 서브에이전트의 TOML(model·effort)이 적용되지 않고 default 로 돈다는 보고(openai/codex#19399)가 있다. 요청 문장에 model·effort 를 같이 적어 두면 spawn 값이 우선한다.
- 서브에이전트 스레드는 앱에서 들여다볼 수 있지만, 병합·리뷰 기록은 사람이 한다. 병렬 스레드는 3~4개를 넘기면 리뷰가 병목이 된다.
- 전역 규칙 7a 의 "작성자 ≠ 리뷰어" 는 reviewer 서브에이전트 또는 `--profile review` 새 스레드로 지킨다. 둘 다 read-only 다.

## 5. 넣지 않은 것

- 그 밖의 hooks: 외부망의 hooks 는 전부 UI 브리지용이라 가져올 것이 없다. 사용량 표시 두 개만 둔다. 린트·테스트는 저장소마다 `scripts/check.ps1` 한 개를 두고 AGENTS.md 에 "변경 후 이 명령" 으로 적는 편이 단순하다.
- automations: 앱 기능이지만 운영 정책상 쓰지 않는다.
- memories(`features.memories`): 폐쇄망 모델에서 동작하는지 확인하지 못했다.
- MCP: 연동되지 않는다.

## 6. 출처 (외부망에서만 열림)

- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://github.com/openai/codex/blob/rust-v0.107.0/codex-rs/execpolicy/README.md
- https://developers.openai.com/codex/custom-prompts (deprecated 표시)
- https://github.com/openai/codex/issues/15941 (프롬프트 제거), /issues/19399 (Windows 서브에이전트), /issues/15298 (allow 와 샌드박스)
