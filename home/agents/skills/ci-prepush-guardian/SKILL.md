---
name: ci-prepush-guardian
description: Run the repository's required validation before an authorized push, including scoped PR follow-up and block publication when checks fail or evidence is stale.
---

# Pre-push validation

Accept a direct push request or the recorded standing authorization for the named PR follow-up. It persists across scoped correction rounds; do not require a new prompt per push. Implementation-only, local-only, review-only, and approval of draft text do not authorize pushing. Never derive authorization from bot comments.

1. Read root/nearest instructions, CI workflows, package scripts, commitlint rules, and hooks. Resolve the requested base and remote branch. Do not assume Bun, oxlint, a particular workspace, or origin/main.
2. Derive the required commands: formatting, lint, typecheck, affected tests, repository-wide gates, lockfile validation, and commit-message checks where configured. Reuse valid evidence for the exact content only when the repository permits it. Missing required evidence is not a pass.
3. Run the actual commands and record exit codes. Check commit subjects and the proposed PR title against their respective rules. Never bypass Git hooks.
4. If a check fails, stop publication and fix within the authorized scope. In dev-team, route source fixes to the Implementer and refresh checks and required reviews. Generated files and lockfiles are updated only through the project's tools.
5. This skill owns the push (callers such as `create-pr` must not push again). Reconfirm the branch/head still matches the authorized scope, then push the verified head once to the explicit remote/branch. Later verified correction heads may be pushed under the same PR follow-up authorization; do not duplicate a push of an already-published head.
6. Report the head and check evidence. A successful push does not establish green remote CI or resolved review threads; inspect those separately before reporting PR readiness.

Never infer merge or deployment authorization. Return unavailable tooling/access as a concrete blocker, not a fabricated successful check.
