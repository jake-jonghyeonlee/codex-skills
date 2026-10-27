---
name: test-gap
description: "[KO] 테스트 빠진 곳 찾기·테스트 갭 분석·회귀 테스트 보강을 할 때. Find risk-relevant gaps in an existing test suite and add or design tests that prove important behavior, especially around changed code and regressions. Use when test coverage or confidence is the primary goal; do not use merely because an ordinary implementation includes routine tests."
---

# Test Gap

Improve confidence in behavior rather than maximizing a coverage number.

## Set the test target

Identify the requested scope: a diff, defect, module, public contract, or whole repository. Determine whether the user asked for analysis only, test implementation, or both. Do not change production behavior to make a weak test pass unless the user also requested a product fix.

Inventory the relevant existing tests, test framework, fixtures, CI constraints, and observable contracts. Use coverage reports as supporting evidence when available, not as the sole definition of a gap.

## Rank gaps by risk

Trace important behaviors and rank missing evidence using factors such as:

- changed or defect-prone paths;
- public APIs and persisted or serialized data;
- boundary values, empty and malformed inputs, and error recovery;
- state transitions, concurrency, retries, and partial failure;
- security or permission boundaries;
- integrations whose substitutes may hide contract mismatches.

Do not add tests for trivial implementation details solely to increase line coverage. Prefer tests that would fail under a plausible defect and remain valid through safe refactoring.

## Design and implement

- Choose the lowest test level that proves the contract without excessive mocking; use integration or end-to-end tests when the behavior crosses a meaningful boundary.
- For a known bug, make the regression test demonstrate the original failure mode.
- Reuse project fixtures and conventions. Keep test data minimal, deterministic, and legible.
- Control clocks, randomness, concurrency, networks, and external services where possible. If realism requires an external dependency, make the requirement and skip behavior explicit.
- Avoid weakening assertions, broad sleeps, order dependence, and tests that only restate the implementation.

## Validate and hand off

Run the new tests in isolation, then the relevant suite. Where practical, demonstrate that the test is sensitive to the targeted defect through pre-fix failure, an existing failing revision, or a narrowly reasoned mutation; do not introduce temporary mutations into the final worktree.

Report the risks covered, why each new test is meaningful, commands and results, remaining high-risk gaps, and any environment-dependent tests not run. When analysis only was requested, return a prioritized test plan with target behaviors and likely test levels instead of editing files.
