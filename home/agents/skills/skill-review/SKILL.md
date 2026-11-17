---
name: skill-review
description: Audit agent skills for scope, trigger quality, overlap, direct invocation
  errors, discoverability, and unsafe or conflicting instructions. Use only for reviewing
  or consolidating skill definitions.
disable-model-invocation: true
---

# Skill Review

Review skill definitions as agent configuration, not as application code.

## Hard boundary

Do not invoke the repository `code-review` workflow for this task. Those workflows review source-code changes. This skill reviews `SKILL.md`, `agents/openai.yaml`, references, scripts, assets, and the skill's discovery behavior.

## Review procedure

1. Inventory the selected skill directories and read each `SKILL.md` completely. Read `agents/openai.yaml`, scripts, and linked references when they affect invocation or behavior.
2. Extract each skill's name, description, trigger phrases, exclusions, side effects, dependencies, and output contract.
3. Build an overlap matrix. Classify pairs as distinct, composable, redundant, or conflicting. Do not merge skills only because they share a broad topic; merge only when they have the same user intent and outcome.
4. Check trigger routing. Descriptions must be concise and discriminating. Add exclusions when a broad description would attract neighboring work. Keep explicit-only skills explicit-only when automatic invocation would be unsafe or noisy.
5. Check direct references. Every referenced skill, command, script, and path must exist in the target product. Replace unavailable slash commands or hard-coded product paths with a supported local reference or a clearly documented fallback.
6. Check instruction quality. Remove duplicated policy, generic advice, speculative rules, stale examples, and steps that conflict with user or repository authorization. Keep substantial mode-specific material in linked references.
7. Validate each changed skill with the bundled skill validator when available. Check frontmatter, naming, references, and scripts separately; validation does not prove behavioral quality.

## Findings

Report findings with `skill/path:line`, severity, evidence, and the smallest useful remedy. Separate:

- **Required:** broken discovery, missing dependency, contradictory authorization, unsafe direct invocation, or duplicate skills with the same intent.
- **Consider:** noisy trigger, unnecessary overlap, stale documentation, or excessive instruction detail.
- **Keep:** intentionally distinct skills and why they should remain separate.

End with a routing table showing which skill owns each reviewed user intent. If consolidation is recommended, preserve the original behavior in the selected canonical skill and remove only the redundant entry after checking callers.
