#!/usr/bin/env python3
"""Codex 토큰 사용량 — 세션 누적·턴별·기간 합계를 로컬 rollout 파일에서 읽는다. 네트워크 없음.

Codex 는 스레드마다 $CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl 을 쓰고,
턴마다 event_msg/token_count 에 누적(total_token_usage)과 그 턴(last_token_usage)을 기록한다.

사용:
  python codex_usage.py                      # 가장 최근 세션 + 이번 기간 합계
  python codex_usage.py --period month --budget 3000 --unit 1000
  python codex_usage.py --all                # 기간 안 세션 목록
  echo '<hook stdin JSON>' | python codex_usage.py --hook
     UserPromptSubmit → 한 줄 텍스트(모델 컨텍스트로 들어감)
     Stop             → {"systemMessage": "..."} (UI 에 표시)

설치: %USERPROFILE%\\.codex\\scripts\\codex_usage.py, hooks.json 은 codex-home/hooks.json 참고.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
from pathlib import Path

# ── 예산 설정: 사내 기준 "3000" 을 표시 기준으로 쓴다 ─────────────────
BUDGET_UNITS = 3000         # 사내 예산 수치(단위는 사내 기준). 분모로만 쓴다
TOKENS_PER_UNIT = 1000      # 1 단위 = 몇 토큰인지. 가정값. 사내 계기와 이 스크립트 수치를 비교해 보정한다
BUDGET_PERIOD = "month"     # day | week | month | all
COUNT_CACHED = True         # False 면 cached_input_tokens 를 합계에서 뺀다(사내 기준이 캐시를 안 세면)

CODEX_HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
SESSIONS = CODEX_HOME / "sessions"


def period_start(period: str, now: dt.datetime) -> dt.datetime | None:
    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        d = now - dt.timedelta(days=now.weekday())
        return d.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def read_rollout(path: Path) -> dict:
    """마지막 token_count 의 누적·턴 사용량과 턴 수, 모델, cwd 를 돌려준다."""
    total = last = None
    turns = 0
    model = cwd = None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                t = d.get("type")
                p = d.get("payload") or {}
                if t == "session_meta":
                    cwd = p.get("cwd")
                elif t == "turn_context":
                    model = p.get("model") or model
                elif t == "event_msg" and p.get("type") == "token_count":
                    info = p.get("info") or {}
                    if info.get("total_token_usage"):
                        total = info["total_token_usage"]
                        last = info.get("last_token_usage") or last
                        turns += 1
    except OSError:
        pass
    return {"path": path, "total": total, "last": last, "turns": turns, "model": model, "cwd": cwd}


def tokens(u: dict | None) -> int:
    if not u:
        return 0
    n = int(u.get("total_tokens") or 0)
    if not COUNT_CACHED:
        n -= int(u.get("cached_input_tokens") or 0)
    return max(n, 0)


def fmt(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def find_rollouts(since: dt.datetime | None) -> list[Path]:
    files = [Path(p) for p in glob.glob(str(SESSIONS / "**" / "rollout-*.jsonl"), recursive=True)]
    if since is not None:
        ts = since.timestamp()
        files = [p for p in files if p.stat().st_mtime >= ts]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def find_session(session_id: str | None, transcript: str | None) -> Path | None:
    if transcript and Path(transcript).is_file():
        return Path(transcript)
    cands = find_rollouts(None)
    if session_id:
        cands = [p for p in cands if session_id in p.name] or cands
    return cands[-1] if cands else None


def summarize(session_path: Path | None, period: str, budget: int, unit: int) -> dict:
    now = dt.datetime.now()
    start = period_start(period, now)
    period_total = 0
    period_sessions = 0
    for p in find_rollouts(start):
        r = read_rollout(p)
        if r["total"]:
            period_total += tokens(r["total"])
            period_sessions += 1
    cur = read_rollout(session_path) if session_path else None
    return {
        "now": now, "period": period, "period_start": start, "period_total": period_total,
        "period_sessions": period_sessions, "budget": budget, "unit": unit, "session": cur,
    }


def one_line(s: dict) -> str:
    cur = s["session"]
    sess = f"세션 {fmt(tokens(cur['total']))} ({cur['turns']}턴, 마지막 턴 {fmt(tokens(cur['last']))})" if cur and cur["total"] else "세션 기록 없음"
    used_units = s["period_total"] / s["unit"] if s["unit"] else 0
    pct = (used_units / s["budget"] * 100) if s["budget"] else 0
    per = f"{s['period']} 누적 {used_units:,.0f}/{s['budget']:,} ({pct:.1f}%, {fmt(s['period_total'])} tok)"
    warn = " ⚠ 예산 80% 초과" if pct >= 80 else ""
    return f"[usage] {sess} · {per}{warn}"


def detail(s: dict, show_all: bool) -> str:
    out = [one_line(s)]
    cur = s["session"]
    if cur and cur["total"]:
        t = cur["total"]
        out.append(f"  현재 세션: {cur['path'].name}")
        out.append(f"  model={cur['model']} cwd={cur['cwd']}")
        out.append(f"  input={fmt(int(t.get('input_tokens', 0)))} (cached {fmt(int(t.get('cached_input_tokens', 0)))}) "
                   f"output={fmt(int(t.get('output_tokens', 0)))} (reasoning {fmt(int(t.get('reasoning_output_tokens', 0)))})")
    out.append(f"  기간 시작: {s['period_start']:%Y-%m-%d} 세션 {s['period_sessions']}개" if s["period_start"] else "  기간: 전체")
    if show_all:
        for p in find_rollouts(s["period_start"]):
            r = read_rollout(p)
            if r["total"]:
                out.append(f"  {dt.datetime.fromtimestamp(p.stat().st_mtime):%m-%d %H:%M} {fmt(tokens(r['total'])):>8} {r['turns']:>3}턴 {r['model'] or '-'} {r['cwd'] or ''}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true", help="stdin 의 hook JSON 을 읽어 이벤트에 맞는 출력")
    ap.add_argument("--period", default=BUDGET_PERIOD, choices=["day", "week", "month", "all"])
    ap.add_argument("--budget", type=int, default=BUDGET_UNITS, help="예산 수치(사내 단위)")
    ap.add_argument("--unit", type=int, default=TOKENS_PER_UNIT, help="1 단위당 토큰 수")
    ap.add_argument("--all", action="store_true", help="기간 안 세션 목록")
    ap.add_argument("--session", help="rollout 파일 경로(생략하면 최근 세션)")
    a = ap.parse_args()

    session_id = transcript = event = None
    if a.hook:
        raw = sys.stdin.read()
        try:
            h = json.loads(raw)
            session_id, transcript, event = h.get("session_id"), h.get("transcript_path"), h.get("hook_event_name")
        except ValueError:
            event = "Stop" if '"Stop"' in raw else "UserPromptSubmit"   # Windows 비ASCII 깨짐(codex#23784) 대비

    path = Path(a.session) if a.session else find_session(session_id, transcript)
    s = summarize(path, a.period, a.budget, a.unit)

    if a.hook:
        line = one_line(s)
        if event == "Stop":
            print(json.dumps({"systemMessage": line}, ensure_ascii=False))
        else:
            print(line)
        return 0
    print(detail(s, a.all))
    return 0


if __name__ == "__main__":
    sys.exit(main())
