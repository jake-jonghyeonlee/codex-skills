# code-audit rubric — four lenses, three severities

Every finding needs a `lens` and a `severity`. Both are fixed vocabularies —
`scripts/audit_dashboard.py` rejects anything outside them.

## Lenses (what kind of problem)

- **correctness** — the code does the wrong thing: a concrete input/state
  produces a wrong output, a crash, or a violated invariant.
- **contract** — the code disagrees with its own stated intent: docs/README
  claim behavior the code doesn't have, or the code violates a documented
  rule/invariant.
- **structure** — not wrong today, but risky to build on: duplicated logic
  that will drift, dead code, a crossed module boundary, a misleading API
  shape.
- **evidence** — the safety net is weaker than it looks: missing tests for a
  behavior-bearing path, a test that exercises the happy path but asserts
  nothing about the actual invariant, a verify command that's declared but
  doesn't actually run clean.

An empty lens is a normal outcome — never pad findings to fill one out.

## Severities (how much it matters)

- **blocking** — a verified failure scenario a user would actually hit or
  care about: wrong behavior, data loss, a broken contract, a game-breaking
  bug. Requires a concrete scenario (*this input/state → this wrong
  outcome*) — no scenario, no blocking.
- **advisory** — real, but survivable: a divergence risk, a missing test, a
  structural smell, a doc/code mismatch where either side could be the fix.
- **low-confidence** — a real-looking candidate you could not verify against
  the actual running code path (e.g. it's technically true but currently
  unreachable, or you're relying on the description alone without reading
  the call sites). Never mark something low-confidence as blocking.

## Before finalizing a finding

Trace it against the real code — don't take a description at face value.
A candidate that turns out to be already-guarded, unreachable in the current
entry points, or contradicted by a quick test run should be downgraded or
dropped, not reported as-is.
