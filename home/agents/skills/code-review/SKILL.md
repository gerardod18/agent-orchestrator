---
name: code-review
description: "Canonical source-code review for branches, PRs, and work in progress. Runs independent Standards and Spec passes, or one explicitly delegated axis within dev-team. Do not use for skill definitions, agent metadata, or configuration routing."
---

# Code review

This is the single canonical source-code review procedure. Keep Standards (correctness, readability, architecture, security, performance) separate from Spec (acceptance, omissions, wrong behavior, extra scope). Review is read-only: do not edit, stage, commit, publish, or run commands that mutate the working tree. Read root and nearest package `AGENTS.md`, required topic documents, and applicable repository skills before reviewing affected files.

## Execution modes

- `mode=full` (default): establish scope and sources, delegate independent Standards and Spec passes in parallel, then relay their reports separately.
- `mode=standards`: explicitly delegated leaf reviewer; read this entire skill, establish/verify the supplied scope and sources, execute only the Standards pass, and return its report to the caller. Do not spawn reviewers or aggregate another axis.
- `mode=spec`: explicitly delegated leaf reviewer; read this entire skill, establish/verify the supplied scope and sources, execute only the Spec pass, and return its report to the caller. Do not spawn reviewers or aggregate another axis.

A dev-team reviewer must use its assigned leaf mode before reporting. Loading this file alone is not execution. If required inputs are unavailable, return the blocker to the orchestrator rather than substituting an internal checklist or asking the user directly.

## Pin scope and identity

Use the requested base; otherwise use `main`. Resolve it to a SHA with `git rev-parse`, resolve HEAD, and pin their merge-base. Use the same resolved SHAs throughout; do not let moving branch names change the review. If a caller explicitly supplies an exact comparison base, preserve that choice and report it. Capture commits via `git log <comparison-base>..HEAD --oneline`.

Select scope from the request, and state it in the report:

- `scope=committed`: ordinary branch/PR review. Inspect `git diff <comparison-base> <head-sha>`; disclose local changes excluded from this scope.
- `scope=working-tree`: work-in-progress and dev-team review. Inspect `git diff <comparison-base>` for the final tracked tree, `git diff --cached` and `git diff` to identify staged/unstaged layers, and `git ls-files --others --exclude-standard -z` to enumerate untracked files. Read those untracked files too, including tests; an empty committed diff does not mean an empty review. Identify pre-existing work separately and report out-of-scope concerns without silently attributing them to the current task.

Before and after each pass, verify the supplied snapshot identity with the supplied read-only command. Dev-team uses `python3 ~/.agents/dev-team/scripts/state.py snapshot --repo <root>` and supplies the state base separately from the review comparison base. For standalone work without state, capture HEAD, binary tracked and staged diffs, status, and untracked contents (including symlink targets) in a content fingerprint outside the repo. No Git mutations are needed to freeze a review: stop writers while both passes run. A changed snapshot invalidates the pass; request a new freeze. Do not report a pass if snapshot identity cannot be verified.

Validate the base and the complete selected scope before delegation. An invalid ref blocks review. A genuinely empty selected scope is reported as no changes to review, not a substantive pass.

## Find the spec and standards

Use an explicitly supplied approved spec/plan first, including files under `~/claude-plans/`. Otherwise look for Linear/issue references in branch names and commits, use configured tracker access or repository tracker documentation when present, then look for matching local specs. Do not assume `docs/agents/issue-tracker.md` exists. If no spec is available, ask the user in standalone mode or return the missing input to the orchestrator in delegated mode. A standalone full review may report Spec as skipped when the user confirms there is no spec. Dev-team requires an approved spec and must block instead; skipped is never pass.

Gather standards from root/nearest instructions, required domain/permission docs, and relevant standards documents such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`. Both passes must check that new queries, mutations, endpoints, and routes use the repository backend authorization mechanism; frontend guards alone are insufficient.

## Risk and evidence before verdict

Read [stateful review](references/stateful-review.md) when the diff touches protected reads/writes, approvals, previews, state transitions, history, pagination/search or truncation. Trace applicable invariants through connected callers/callees; do not stop at checking that a guard or digest exists. Prioritize demonstrated correctness, security and contract failures before smell/style suggestions.

The implementer never acts as its own independent reviewer. If a delegated worker cannot spawn reviewers, it returns the snapshot to the parent, which dispatches both sibling review roles. Do not silently collapse both axes into that worker. Missing mandatory instructions, authorization docs, material caller analysis or proof of an acceptance condition block the affected verdict; list precisely what is missing rather than reporting an unconditional pass.

For each applicable risk, record the invariant, inspected source/call path, an adversarial counterexample considered, and supporting test/repro evidence or its gap. Distinguish code reasoning, read tests and executed tests. Broad test counts alone do not establish the invariant. Verify uncertain dependency semantics against installed source or official primary documentation before recommending a behavioral change; if unavailable, label the uncertainty and do not turn it into a confident finding.

For follow-up reviews, read the prior finding ledger and correction diff as well as affected callers. Review both axes on the changed content, preserve verified untouched scope, and check for fix-induced regressions. Do not rerun the whole review merely because an identical tree was committed. Never reopen a settled subjective nit without new evidence. Return all substantiated findings in one batch; distinguish blockers from non-blocking advice. A failing mandatory criterion cannot be called "pass with changes".

## Standards pass

Evaluate the five quality axes against the changed source and connected code. Cite concrete evidence and the applicable rule. Distinguish documented violations from heuristic concerns. Do not restate lint/formatter diagnostics as review findings, but report missing or failed validation separately.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

## Spec pass

Check every approved criterion, negative/edge case, exclusion, and authorization boundary against the selected snapshot and tests. Report missing or partial behavior, requirements implemented incorrectly, and behavior outside scope. Cite the exact requirement or exclusion for each finding. List requirements that cannot be verified; do not turn absent evidence into a pass or make style-only comments.

## Full-mode delegation

Pass each leaf reviewer this skill's absolute path, its explicit mode, resolved base and HEAD, selected scope, snapshot identity and verification command, pre-existing changes, source paths/content, and applicable repository instructions. Have both read the skill and execute their assigned pass independently. No leaf delegates again. If parallel delegation is unavailable, disclose the limitation rather than claiming independent parallel reviews ran.

## Report contract

Every leaf returns:

- Skill name, absolute path, and executed mode; selected scope and resolved base/HEAD; snapshot identity before and after.
- Actionable findings with stable ID, severity, exact `file:line`, violated invariant/criterion, concrete trigger and impact, evidence, and practical remedy. Separate blocking defects from non-blocking nits; identify duplicate root causes instead of inflating finding counts. Explicitly state when there are none.
- Compact coverage evidence for applicable risk invariants, including caller paths, counterexamples, test/repro evidence and missing proof.
- Verdict: `pass`, `fail`, or `blocked`; areas and criteria not verified, with reasons. Missing mandatory inputs or stale snapshots mean blocked. An axis not run is skipped, never pass.

Keep findings concise without dropping material issues to meet a word limit. Report only the assigned axis to the orchestrator; it records the evidence and coordinates fixes.

In full mode, present separate Standards and Spec reports, verbatim or lightly cleaned. Do not merge or rerank across axes. End with each axis's verdict, finding count, worst issue within that axis, and anything unverified. A change can pass either axis and fail the other.
