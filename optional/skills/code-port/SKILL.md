---
name: code-port
description: "Adapt a bounded feature, subsystem, or architectural pattern from one codebase into another while preserving target-project conventions, recording provenance, and verifying behavioral equivalence. Use for code reuse, cross-repository feature ports, or implementation inspired by an existing source; do not use for ordinary in-repository edits with no source implementation."
---

# Code Port

Port behavior and design intent, not files blindly. The target repository owns the final architecture and conventions.

## Establish the contract

- Identify the source, target, requested capability, and whether the source may be modified. Treat both repositories as read-only until the requested target changes are clear.
- Confirm that the user has supplied or authorized access to the source. Do not retrieve private or unavailable code by inference.
- Inspect applicable licenses, notices, generated-file markers, and attribution requirements before copying substantive code. If reuse rights are unclear, stop before copying and offer a clean-room reimplementation based on public behavior or user-provided requirements.
- Define observable acceptance criteria. Separate required behavior from incidental source structure.

## Analyze before changing

Trace the smallest coherent source slice: entry points, data contracts, dependencies, configuration, side effects, errors, tests, and callers. Map each source concept to a target equivalent and classify it as reuse, adapt, replace, or omit.

Surface material incompatibilities before implementation, including language or framework versions, sync/async models, persistence, security boundaries, numerical semantics, serialization, deployment assumptions, and public API changes. Ask only when a mismatch requires a product or architecture decision that cannot be derived safely.

## Implement the port

- Follow target naming, layering, dependency, error-handling, and testing conventions.
- Prefer the smallest dependency boundary that delivers the requested behavior. Do not import unrelated utilities or reproduce source architecture without a target-side reason.
- Preserve target compatibility unless the user explicitly authorizes a breaking change.
- Keep copied or adapted notices and attribution where required. Record the source revision or immutable identifier when available.
- Make behavior-changing adaptations explicit in code, tests, or the handoff rather than silently diverging.

## Verify and hand off

Use source tests as evidence, not as automatically portable truth. Add target-native tests for normal behavior, boundaries, errors, and the adaptations introduced by the target environment. Where feasible, compare source and target on shared fixtures; otherwise verify against the acceptance criteria.

Report:

- what was ported and deliberately omitted;
- source identity and provenance obligations;
- important source-to-target mappings and intentional differences;
- verification performed and remaining compatibility risks.

For broad ambiguous work, establish a specification before implementation. For an unfamiliar target or source, map only the relevant code paths first. Use a separate audit after implementation when independent defect review is requested or warranted by risk.
