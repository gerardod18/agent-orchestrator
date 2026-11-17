---
name: pre-review
description: Local pre-push review that catches what CodeRabbit flags in this user's PRs, with no paid tool. Runs automatically after implementation passes its checks and before independent review, commit and push, and on correction diffs during PR follow-up; also use when asked to pre-review a branch.
---

# Pre-review: catch the bot's findings before the PR exists

Goal: the first CodeRabbit round on a PR finds nothing new. No paid tool, no CodeRabbit CLI. CodeRabbit is an LLM reading the diff with its surrounding code, plus linters; its prompt is not public, but its behavior on 30 audited PRs is: 115 inline findings, 68% *Functional Correctness*, 79% *Quick win*, 82% in backend code, the same seven patterns repeating. This skill reproduces that review locally using that evidence. Patterns, cues and title templates: `~/.agents/skills/code-review/references/coderabbit-patterns.md`. Read it first.

No new agent. The parent runs the procedure, the implementer fixes, the existing read-only reviewers judge.

## Tiers (cost control)

- **Tier 0, always, cheap:** the repo's lint, format and typecheck (CodeRabbit also runs oxlint and ast-grep; run any ast-grep rules the repo has), then the implementer's own pattern self-check from `implement` step 4. No extra agent.
- **Tier 1, only when the change matches a pattern trigger** (authorization or visibility, approval or confirmed writes, shared contracts or validators, pagination or limits, error mapping, async or UI lifecycle, retries): one independent read-only pass, below. Typos, docs, isolated presentation and pure renames stay at Tier 0.

## Tier 1 pass

1. Pin the snapshot (review base default `main`; `state.py snapshot` in dev-team). Save the ledger under `~/claude-plans/<repo>/prereview/<timestamp>.md`, never in the repository.
2. Dispatch one fresh-context read-only reviewer (`dev-team-review-standards`; add `dev-team-review-impact` when the Impact trigger from `code-review` also matches). Brief: "Review as CodeRabbit would. For each hunk, read the callers, callees and validators around it and ask what input or state breaks the claim the code or its comment makes. Use the patterns file. Report only functional-correctness, integrity, security and stability findings that are reachable; skip style. Format each as `<Major|Minor> · <category> · <Quick win|Heavy lift>`, a one-line imperative title like the bot's (for example 'Keep the reason when the label is long'), `file:line`, scenario, evidence." The implementer never reviews its own work.
3. Dedupe by root cause. Classify each finding: valid, already-fixed, invalid, out-of-scope, needs-decision.
4. Send **all valid findings together** to one `dev-team-implementer` call. The parent never edits code. The implementer sweeps siblings of each root cause and maps each fixed invariant to a test that fails without the fix.
5. Re-run Tier 1 on the correction. Stop when a round has no new valid finding, or after 3 rounds; report what remains.
6. Declined or invalid findings stay in the ledger with evidence. Put notable ones in the PR description so the bot's likely objection is already answered.

## Hand-off

Record against the snapshot: tier reached, rounds, findings fixed and declined. `create-pr` and the publisher require this for the head being pushed. Pre-review does not replace the independent Standards/Spec review, tests or CI; it runs first so they see a cleaner change. During `pr-followup`, run it on the correction diff before each push.

## Measuring it

After each PR, compare the bot's first-round findings with the ledger: count findings the bot made that pre-review missed, and add each miss as a cue to the patterns file. That is how recall improves; there is no other tuning.
