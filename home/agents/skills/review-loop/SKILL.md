---
name: review-loop
description: Run every independent review before the first commit, push or PR: launch the required reviewers in parallel, batch their findings to one implementer, repeat until clean. Runs automatically after implementation passes its checks, and on correction diffs during PR follow-up. Use when asked to review a branch before publishing.
---

# Review loop

All independent review happens here, before the first commit, push or PR. The goal is that the first automated PR review finds nothing new. The reviewers are the read-only modes of `code-review`; this skill decides who runs, batches the findings and repeats. The parent runs it and never edits code; the implementer is the only writer, and no one reviews their own work.

## Before the loop (author side, cheap)

The implementer has run the repo's lint, format, typecheck and tests and the pattern self-check from `implement` step 4. Do not start the loop on a red gate.

## One round

1. **Pin the snapshot.** Review base (default `main`) and HEAD plus working tree; in dev-team use `state.py snapshot`. Keep the ledger in `~/claude-plans/<repo>/review/<timestamp>.md`, never in the repository.
2. **Choose the reviewers.** Always Standards and Spec. Add Impact when the change touches authorization or visibility, approval or confirmed writes, shared contracts or validators, pagination or limits, error mapping, async or UI lifecycle, retries, or after a finding exposed a missed sibling path. Typos, docs and isolated presentation changes still get Standards and Spec but never Impact.
3. **Launch them in parallel**, each fresh-context and read-only (`dev-team-review-standards`, `dev-team-review-spec`, `dev-team-review-impact`, each running its `code-review` mode). They do not see each other's reports. In the Standards and Impact briefs, require:
   - use the whole tool budget (at least 30 calls) and do not conclude from a quick read;
   - before reporting, write three enumerations: (a) every approval, preview or confirmation: fields displayed versus fields the writer's guarded basis re-checks; (b) every error thrown in a changed writer versus how each caller maps it; (c) every helper that returns a name, count or id versus the permission and scope it checks;
   - report reachable functional-correctness, integrity, security and stability findings first, as `<Major|Minor> · <category> · <Quick win|Heavy lift>` with a one-line imperative title, `file:line`, scenario and evidence.
4. **Merge.** Dedupe by root cause across axes, keeping each axis's verdict. Classify each finding: valid, already-fixed, invalid, out-of-scope, needs-decision.
5. **Fix as one batch.** Send all valid findings together to one `dev-team-implementer` call, with the sibling-sweep requirement from `implement`. Each fixed invariant needs a test that fails without the fix.
6. **Repeat on the new content**, rerunning only the reviewers whose axis the fix touched. Stop when a round has no new valid finding or after 3 rounds; report what remains and the one decision needed.

Declined or invalid findings stay in the ledger with evidence. Put notable ones in the PR description so a reviewer's likely objection is already answered.

## Then publish

Record the rounds, reviewers, findings fixed and declined against the final snapshot. The publisher requires that evidence for the head it pushes, then commits, pushes through the pre-push guardian and opens the PR (`commit`, `ci-prepush-guardian`, `create-pr`). Nothing is reviewed again after the PR opens except external feedback, which `pr-followup` handles. In `pr-followup`, run one round of this loop on each correction diff before pushing.

## Measuring it

After each PR, compare the automated reviewer's first-round findings with the ledger. Restate each miss as an existing invariant in `code-review/references/defect-patterns.md` and sharpen its cues; add a new pattern only if none fits. Never add a rule per comment.
