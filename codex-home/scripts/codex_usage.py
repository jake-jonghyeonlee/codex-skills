#!/usr/bin/env python3
"""Codex 토큰 사용량 — 턴 사용·대화 누적·예상 credits 소비·계정 한도 잔여(추정)를 로컬 rollout 파일에서 계산한다.

Codex 는 스레드마다 $CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl 을 쓰고,
턴마다 event_msg/token_count 에 누적(total_token_usage)·그 턴(last_token_usage)·컨텍스트 창 크기를 기록한다.

계정 이용 한도(엔터프라이즈 credits, 예 3000)는 로그에 없다. 그래서 사용자가 UI 에서 읽은 잔여값을
`--sync <잔여>` 로 넣어 두면, 그 시점 이후 로컬 토큰 사용량 × 환산율로 잔여를 추정한다.
환산율(credits/1k 토큰)은 두 번 이상 --sync 하면 그 사이 실제 감소량과 토큰량으로 자동 보정한다.

사용:
  python codex_usage.py                     # 최근 세션 한 줄 + 상세
  python codex_usage.py --sync 2950         # 지금 UI 에 보이는 계정 잔여 credits 를 기록
  python codex_usage.py --sync 2900 --at 2026-10-29T09:00   # 과거 시점 기록(백필)
  python codex_usage.py --limit 3000        # 한도 수치 변경
  echo '<hook stdin JSON>' | python codex_usage.py --hook
     UserPromptSubmit → 한 줄 텍스트(모델 컨텍스트로 들어감)
     Stop             → {"systemMessage": "..."} (UI 에 표시)

상태 파일: $CODEX_HOME/usage_state.json  (limit_credits, credits_per_1k, syncs[])
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

DEFAULT_LIMIT_CREDITS = 3000     # 계정 이용 한도(사내 단위). --limit 로 바꾼다
DEFAULT_CREDITS_PER_1K = 1.0     # 1,000 토큰당 credits. 가정값. --sync 두 번이면 자동 보정
COUNT_CACHED = True              # False 면 cached_input_tokens 를 소비 토큰에서 뺀다

CODEX_HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
SESSIONS = CODEX_HOME / "sessions"
STATE = CODEX_HOME / "usage_state.json"


# ── 상태 ──────────────────────────────────────────────────────────────
def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"limit_credits": DEFAULT_LIMIT_CREDITS, "credits_per_1k": DEFAULT_CREDITS_PER_1K, "syncs": []}


def save_state(s: dict) -> None:
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_ts(s: str) -> dt.datetime:
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc).astimezone()


# ── rollout 읽기 ──────────────────────────────────────────────────────
def tokens(u: dict | None) -> int:
    if not u:
        return 0
    n = int(u.get("total_tokens") or 0)
    if not COUNT_CACHED:
        n -= int(u.get("cached_input_tokens") or 0)
    return max(n, 0)


def read_rollout(path: Path) -> dict:
    """token_count 이벤트를 시간순으로 모은다. 각 항목: (시각, 누적 usage, 턴 usage, 컨텍스트 창)."""
    events: list[tuple[dt.datetime, dict, dict | None, int | None]] = []
    model = cwd = None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                t, p = d.get("type"), d.get("payload") or {}
                if t == "session_meta":
                    cwd = p.get("cwd")
                elif t == "turn_context":
                    model = p.get("model") or model
                elif t == "event_msg" and p.get("type") == "token_count":
                    info = p.get("info") or {}
                    if info.get("total_token_usage") and d.get("timestamp"):
                        events.append((parse_ts(d["timestamp"]), info["total_token_usage"],
                                       info.get("last_token_usage"), info.get("model_context_window")))
    except OSError:
        pass
    return {"path": path, "events": events, "model": model, "cwd": cwd}


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


def tokens_between(start: dt.datetime | None, end: dt.datetime | None) -> int:
    """모든 세션에서 (start, end] 구간에 소비한 토큰. 누적값 차이로 계산한다."""
    total = 0
    for p in find_rollouts(start):
        ev = read_rollout(p)["events"]
        before = after = 0
        for ts, cum, _, _ in ev:
            if start is not None and ts <= start:
                before = tokens(cum)
            if end is None or ts <= end:
                after = tokens(cum)
        total += max(after - before, 0)
    return total


# ── 계산 ──────────────────────────────────────────────────────────────
def calibrate(state: dict) -> None:
    """마지막 두 sync 사이의 실제 credits 감소량 / 토큰량으로 환산율을 갱신한다."""
    syncs = state.get("syncs") or []
    if len(syncs) < 2:
        return
    a, b = syncs[-2], syncs[-1]
    dcred = float(a["remaining"]) - float(b["remaining"])
    dtok = tokens_between(parse_ts(a["at"]), parse_ts(b["at"]))
    if dcred > 0 and dtok > 0:
        state["credits_per_1k"] = round(dcred / dtok * 1000, 4)
        state["calibrated_from"] = {"from": a["at"], "to": b["at"], "credits": dcred, "tokens": dtok}


def summarize(session_path: Path | None, state: dict) -> dict:
    cur = read_rollout(session_path) if session_path else None
    turn = conv = ctx_pct = None
    if cur and cur["events"]:
        _, cum, last, window = cur["events"][-1]
        turn = tokens(last)
        conv = tokens(cum)
        if window and last:
            ctx_pct = int(last.get("input_tokens") or 0) / window * 100
    rate = float(state.get("credits_per_1k") or DEFAULT_CREDITS_PER_1K)
    limit = float(state.get("limit_credits") or DEFAULT_LIMIT_CREDITS)
    syncs = state.get("syncs") or []
    remaining_pct = remaining = synced_at = None
    if syncs:
        last_sync = syncs[-1]
        synced_at = parse_ts(last_sync["at"])
        used_since = tokens_between(synced_at, None) / 1000 * rate
        remaining = float(last_sync["remaining"]) - used_since
        remaining_pct = remaining / limit * 100 if limit else None
    return {"session": cur, "turn": turn, "conv": conv, "ctx_pct": ctx_pct, "rate": rate, "limit": limit,
            "remaining": remaining, "remaining_pct": remaining_pct, "synced_at": synced_at,
            "turn_credits": (turn or 0) / 1000 * rate, "conv_credits": (conv or 0) / 1000 * rate}


def fmt(n: int | None) -> str:
    if n is None:
        return "-"
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def one_line(s: dict) -> str:
    ctx = f" (컨텍스트 {s['ctx_pct']:.0f}%)" if s["ctx_pct"] is not None else ""
    if s["remaining_pct"] is None:
        acct = "계정 한도 잔여: 미동기화(--sync <잔여값>)"
    else:
        warn = " ⚠" if s["remaining_pct"] <= 20 else ""
        acct = (f"계정 한도 잔여: {s['remaining_pct']:.1f}%{warn} "
                f"({s['remaining']:,.0f}/{s['limit']:,.0f}, {s['synced_at']:%m-%d %H:%M} 동기화 기준)")
    return (f"[usage] 턴 사용: {fmt(s['turn'])} 토큰 · 대화 누적: {fmt(s['conv'])} 토큰{ctx} · "
            f"예상 소비: {s['turn_credits']:.1f} credits (대화 {s['conv_credits']:.1f}) · {acct}")


def detail(s: dict, state: dict) -> str:
    out = [one_line(s)]
    cur = s["session"]
    if cur and cur["events"]:
        _, cum, _, window = cur["events"][-1]
        out.append(f"  현재 세션: {cur['path'].name}  ({len(cur['events'])}턴, model={cur['model']}, window={window})")
        out.append(f"  cwd={cur['cwd']}")
        out.append(f"  input={fmt(int(cum.get('input_tokens', 0)))} (cached {fmt(int(cum.get('cached_input_tokens', 0)))}) "
                   f"output={fmt(int(cum.get('output_tokens', 0)))} (reasoning {fmt(int(cum.get('reasoning_output_tokens', 0)))})")
    out.append(f"  환산율: {s['rate']} credits/1k 토큰"
               + (f" (보정: {state['calibrated_from']['from'][:16]} → {state['calibrated_from']['to'][:16]}, "
                  f"{state['calibrated_from']['credits']:.0f} credits / {fmt(state['calibrated_from']['tokens'])} 토큰)"
                  if state.get("calibrated_from") else " (가정값. --sync 두 번이면 자동 보정)"))
    for sy in (state.get("syncs") or [])[-3:]:
        out.append(f"  sync {sy['at'][:16]} 잔여 {sy['remaining']}")
    return "\n".join(out)


# ── 진입 ──────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true", help="stdin 의 hook JSON 을 읽어 이벤트에 맞는 출력")
    ap.add_argument("--sync", type=float, metavar="REMAINING", help="UI 에서 읽은 계정 잔여 credits 를 기록")
    ap.add_argument("--at", help="--sync 의 시각(ISO). 생략하면 지금")
    ap.add_argument("--limit", type=float, help="계정 이용 한도 credits 를 바꿔 저장")
    ap.add_argument("--rate", type=float, help="credits/1k 토큰 환산율을 직접 저장")
    ap.add_argument("--session", help="rollout 파일 경로(생략하면 최근 세션)")
    a = ap.parse_args()

    state = load_state()
    changed = False
    if a.limit is not None:
        state["limit_credits"] = a.limit; changed = True
    if a.rate is not None:
        state["credits_per_1k"] = a.rate; state.pop("calibrated_from", None); changed = True
    if a.sync is not None:
        at = parse_ts(a.at) if a.at else dt.datetime.now().astimezone()
        state.setdefault("syncs", []).append({"at": at.isoformat(timespec="minutes"), "remaining": a.sync})
        state["syncs"].sort(key=lambda x: x["at"])
        calibrate(state); changed = True
    if changed:
        save_state(state)

    session_id = transcript = event = None
    if a.hook:
        raw = sys.stdin.read()
        try:
            h = json.loads(raw)
            session_id, transcript, event = h.get("session_id"), h.get("transcript_path"), h.get("hook_event_name")
        except ValueError:
            event = "Stop" if '"Stop"' in raw else "UserPromptSubmit"   # Windows 비ASCII 깨짐(codex#23784) 대비

    path = Path(a.session) if a.session else find_session(session_id, transcript)
    s = summarize(path, state)

    if a.hook:
        line = one_line(s)
        print(json.dumps({"systemMessage": line}, ensure_ascii=False) if event == "Stop" else line)
        return 0
    print(detail(s, state))
    return 0


if __name__ == "__main__":
    sys.exit(main())
