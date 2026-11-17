---
name: dev-team
description: Coordinate a user-invoked development team through specification, approval,
  implementation, canonical code review, and authorized publication. Use only when
  the user explicitly invokes dev-team or asks to run the development team.
disable-model-invocation: true
---

# Development team

This workflow is opt-in. The Lead is the orchestrator in the main conversation. It delegates work, relays questions and approvals, maintains run state, checks evidence completeness, and presents results. It does not implement, run project validation commands, perform source-code review, resolve merge conflicts, commit, push, or create PRs. It may read instructions, inspect Git/state identities, and save approval and evidence artifacts outside the repository. If a delegate is unavailable, report that phase as blocked rather than taking over its execution.

## Skills and agent contracts

Agent profiles define ownership and boundaries; skills define procedures. Resolve each applicable skill from the shared `~/.agents/skills/` catalog through the current runtime's native discovery and relevant repository skills. Pass its name, absolute `SKILL.md` path, execution mode, repo instructions, and task inputs. Require the delegate to read the full skill when not already loaded and apply it before reporting. Missing required skills block that phase; a role description or enabled skill entry is not proof of execution. Keep existing invocation policies: explicit delegation within an authorized team run supplies the task, but grants no additional external-action authorization.

| Role | Required or conditional skills | Responsibility |
|---|---|---|
| Specs | `api-and-interface-design` for public APIs/module boundaries; relevant domain skills | Return observable criteria, exclusions, dependencies, slices, and questions. |
| Implementer | `implement` for code changes; relevant project skills | Sole source-code writer; implement approved slices and run agreed checks. |
| Standards reviewer | `code-review`, `mode=standards` | Read-only Standards pass on the frozen snapshot; report to Lead. |
| Spec reviewer | `code-review`, `mode=spec` | Read-only acceptance pass on the same snapshot; report to Lead. |
| Impact reviewer (conditional) | `code-review`, `mode=impact` | Read-only third pass for risky changes (authorization, approvals, shared contracts, pagination, async, retries); traces real consumers and failure paths. |
| PR reader / feedback reviewer | `pr-followup`, read-only GitHub access | Triage current-head feedback, deduplicate findings, verify fixes and review freshness; return evidence to the Lead. |
| Publisher | `commit` for an authorized commit; `create-pr` for PR preparation/publication; `ci-prepush-guardian` for an authorized push, including scoped PR follow-up | Prepare publication, perform only authorized Git/PR actions, and report remote checks. |

The reviewers (two by default, three when Impact is required) execute the canonical skill's delegated modes without spawning more reviewers. Do not duplicate its review procedure here or in agent profiles. The Lead relays both axis reports separately without inventing findings, reranking across axes, or converting an incomplete review to a pass. The Implementer's `implement` skill excludes its standalone hand-off step inside dev-team; self-review and commit instructions do not belong to the Implementer.

## Start and approval

1. The Lead resolves the Git root, root `AGENTS.md`, current branch, available agent profiles and skills, and the project pointer under `~/.agents/dev-team/profiles/`. Project pointers never override repository instructions. Delegate package/domain inspection and proposed verification commands to Specs.
2. Start local state when possible: `python3 ~/.agents/dev-team/scripts/state.py start --repo <git-root> --session <session-id>`. Save artifacts under the returned run directory in `~/claude-plans/<repo>/dev-team/`. If state is unavailable, disclose the missing recovery tracking.
3. Specs returns criteria, negative cases, exclusions, dependencies, slices, test seams, instruction sources, pre-existing changes, and open questions. The Lead relays one concrete question at a time when needed.
4. State the spec, concise plan, likely files, verification commands, and exclusions, then proceed within the user's implementation request regardless of file count. Record the original user request as scope authorization in the run artifacts and use `state.py approve` to bind the derived spec/plan; this command records existing authorization, not a mandatory new user prompt. Ask only about material unresolved decisions or expanded scope. Publication authorization follows the shared policy; retain an authorized PR follow-up across correction rounds.

## Existing PR feedback

Read and execute `~/.agents/skills/pr-followup/SKILL.md`. It owns the feedback loop, authorization lifetime, finding ledger, reviewer freshness, and stopping conditions. The main parent remains the Lead and dispatches the PR reader, Implementer, both independent reviewers, and Publisher as sibling tasks. Never assign a child the whole orchestration workflow and then accept self-review because it cannot spawn reviewers. Use native roles when listed; if a role is absent from the session's tool enum, pass its full canonical contract to an available generic subagent. Do not repeatedly retry an unavailable role name. No delegation capability means an explicit blocker, not permission for the Lead to implement or self-review.

Reuse the existing acceptance criteria; a Specs pass is needed only for unresolved requirements. Scoped follow-up does not require a new plan-approval ceremony. Local state may be restarted for a correction batch using the same original authorization; `ready_local` is not completion of the PR lifecycle.

## Implementation and verification

- Pass the Implementer approved criteria, one slice, repo root, base SHA, allowed paths, pre-existing changes, skill bindings, and agreed test seams. Only one Implementer writes at a time; all agents preserve others' work.
- The Implementer uses `implement`, reads root/nearest instructions and required topic docs, and runs the approved repo checks through `state.py check` when state is available. It reports actual commands, exit codes, changed paths, and snapshot identity. The Lead records evidence but never executes checks itself.
- Specs derives the full validation gate from repository instructions and CI workflows: lint, format, typecheck, affected tests, and other required CI-equivalent commands. Per-package checks cannot replace a repository-wide gate. Use profile commands only after checking them against the repository. Say plainly when any suite cannot run.
- Code changes invalidate checks and all required reviews. Include committed changes since the review base, staged, unstaged, and untracked files. Keep pre-existing work identified separately so unrelated work is not silently included in the task.

## Independent review

All independent review runs through `~/.agents/skills/review-loop/SKILL.md` before the first commit: the parent launches the required reviewers in parallel, batches findings to the Implementer and repeats until clean. The parent never edits code.

Default is two axes. Add `impact` when the change touches authorization/visibility, approval or confirmed writes, schemas or shared contracts, pagination or limits, background jobs, uploads, retry/idempotency, or shared helpers with different consumers, or after a finding exposes a missed sibling path. Declare the required set before review: `state.py require --repo <root> --axes standards,spec[,impact] --checks <names from Specs' validation gate>`. `finish --name ready_local` then fails unless every required check ran on the current snapshot and every required axis passed.

1. Stop writers and freeze the snapshot with `state.py stage --name reviewing`. Send both reviewers the same repo root, resolved review base/merge-base, base used by state tracking, HEAD, snapshot hash and verification command, pre-existing changes, approved spec/plan, and `scope=working-tree`. If the branch already had commits when the run started, the review base still covers the requested branch diff; the state baseline is not a substitute for it.
2. Explicitly bind `code-review` with `mode=standards`, `mode=spec` or (when required) `mode=impact`, each to its own sibling reviewer (`dev-team-review-impact` for Impact). Every dispatched reviewer must read and execute its mode before reporting. They must not perform a second full review workflow or modify the tree.
3. Require each report to identify the skill path and mode, base/HEAD/snapshot checked before and after, findings with evidence, verdict, and anything unverified. Missing skill execution, a changed snapshot, or missing required spec blocks completion. Save the reports and record every required axis with `state.py review --axis standards|spec|impact`; the state script checks snapshot/evidence freshness, not whether a skill actually ran. The Lead checks the report contract before recording a pass.
4. Batch findings from both axes and route them to the Implementer. After fixes, refresh required checks and both reviews on the new content. Review the correction and its affected callers/invariants; preserve prior evidence for untouched content and do not reopen settled nits without new evidence. If the same issue recurs after two attempted fixes, require a fresh root-cause assessment before more edits. Stop only for a concrete blocker or unresolved decision, not an arbitrary total round count; follow `pr-followup` for external feedback convergence.

## Publication

- Delegate this phase to `dev_team_publisher` (Codex) or `dev-team-publisher` (Claude) automatically for the local commit after approved implementation checks and both reviews pass; delegate PR preparation/publication or pushing when authorized directly or by the persistent PR follow-up scope. Pass exact authorized actions, approved paths, base/head/snapshot, check and review evidence, ticket, and skill paths. The Publisher returns any missing decision to the Lead; the Lead relays it to the user.
- The Publisher applies `commit` for authorized commits and `create-pr` for PR work. An uncommitted tree blocks `create-pr`; finish the approved automatic commit through the Publisher first. Preparing a PR or approving its text never implies permission to push. Preserve valid user authorization already present in the conversation.
- Before the automatic commit, finish local state with `state.py finish --name ready_local` against the frozen checked/reviewed snapshot. A commit of exactly that content does not require repeating reviews: retain the pre-commit evidence and record the resulting commit/tree identity. Hook edits, base integration, or any content change require fresh checks and both reviews before proceeding. Do not present the historical pre-commit state hash as a current HEAD fingerprint. The Publisher returns source/hook failures and conflicts to the Lead for the Implementer; it does not fix application code itself. Base integration needs applicable user authorization and must preserve pre-existing work.
- Before an authorized push, the Publisher applies `ci-prepush-guardian`, plus any repository gates it does not cover. Repository commands and the selected base take precedence over generic skill examples. No failed, stale, or incomplete required check is a pass. The Lead never runs the push or creates the PR.
- The Publisher checks base compatibility and, after publication, reports every expected CI job and unresolved review thread for the current PR head. Missing, skipped, pending, or failed required jobs prevent a ready verdict. Distinguish infrastructure failures from source failures; route source fixes to the Implementer and reuse the standing authorization for subsequent scoped pushes. Continue the `pr-followup` loop rather than stopping after publication. Do not merge or deploy without the corresponding explicit request.

## Finish and resume

Return changed paths, snapshot, actual commands and exit codes, both review verdicts and skill execution evidence, publication status when requested, and anything not verified. `state.py finish --name ready_local` represents local validation only; it does not prove remote CI or review-thread completion. On resume, inspect state and revalidate identities before accepting old evidence.

Use native personal agent adapters when available; otherwise pass the complete role contract and exact skill paths to a generic subagent and disclose the fallback. Keep configuration in the user directory. Role text and advisory hooks are not security boundaries: Codex subagents inherit the parent session's permissions; a per-agent `sandbox_mode` does not create a separate read-only sandbox.
