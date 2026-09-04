---
name: debug-fix
description: "Reproduce, diagnose, and—when requested—fix a concrete software defect with evidence of root cause and regression protection. Use for crashes, wrong results, intermittent failures, regressions, or failing tests; do not use for broad code review or feature development without a reported defect."
---

# Debug Fix

Turn the reported symptom into a verified failure, then make the narrowest justified correction.

## Respect the requested endpoint

Determine whether the user requested diagnosis only or diagnosis plus implementation. Read-only inspection, reproduction, and diagnostic commands are allowed for either. Do not edit code for a diagnosis-only request. If the user requested a fix, carry it through verification unless a material decision or authorization is missing.

## Establish the failure

- Capture the observed behavior, expected behavior, relevant inputs and state, environment, frequency, and last-known-good information available from the repository or report.
- Reproduce with the smallest realistic command or test. Preserve useful logs and the exact failure signal; avoid changing production or shared external state merely to reproduce.
- If reproduction is impossible, distinguish confirmed facts from hypotheses and continue with static tracing where useful. Do not claim a root cause from correlation alone.

## Locate the root cause

Trace from the failure boundary through callers, state changes, concurrency, data transformations, and error handling. Form competing hypotheses and falsify them with focused observations. Check recent relevant changes when git history is available, without assuming the latest change caused the bug.

A root-cause claim must explain the causal chain from a concrete input or state to the observed failure and account for the evidence. Stop and request direction if multiple valid fixes imply materially different product behavior.

## Fix when authorized

- Add or identify a regression check that fails for the original defect before relying on the fix.
- Correct the earliest appropriate cause, not only the visible symptom. Keep unrelated cleanup out of the change.
- Preserve public contracts and existing intended behavior unless the requested fix changes them explicitly.
- For intermittent, concurrent, numerical, or environment-specific bugs, use repeated or targeted checks appropriate to the failure mode; do not overstate certainty from a single pass.

## Verify and report

Run the focused regression check first, then relevant neighboring tests and static checks. Compare the result with the original reproduction.

Report the reproduction, causal chain, changed behavior, verification evidence, and any uncertainty or untested environment. If no fix was requested, provide a fix direction without modifying files.
