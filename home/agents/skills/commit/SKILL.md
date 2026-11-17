---
name: commit
description: Commit approved changes with a Conventional Commit message on a properly named branch tied to a Linear ticket. Use for a requested commit, and automatically when an agent finishes work whose required checks and reviews pass.
---

# Commit

Read root and nearest repository instructions, Git status, staged and unstaged diffs, recent commits, commitlint configuration, hooks, and applicable PR-title validation. Repository rules win. Never bypass hooks or add AI attribution.

## Branch and ticket preflight (before the first commit)

Do this automatically; never ask the user to name the branch or ticket.

1. **Ticket.** Take the Linear ID from the request, the branch name, or recent commits. If none exists, create one with the Linear connector (`save_issue`): title = the conventional subject without the type prefix, description = goal plus the acceptance criteria from the spec, team = the repo's team from repository instructions or the profile in `~/.agents/dev-team/profiles/`. If the team is ambiguous, ask once and record the answer in the profile. Search for an existing matching issue first to avoid duplicates. If Linear access is unavailable, say so and continue without a ticket; never invent an ID.
2. **Branch.** Convention `<type>/<ticket-id>-<kebab-slug>` in lowercase, max about 50 characters, for example `fix/vox-123-login-redirect-loop`. Types: feat, fix, refactor, perf, docs, test, build, ci, chore. A repository convention wins. If the current branch is the default branch, or is a tool-generated name (random words, worktree ids, `claude/...`, `t3-...`), create or rename to the conventional name before committing. Rename only local branches with no remote and no open PR; otherwise keep the name.
3. **Type and scope.** Derive the type from the change, and the scope from the package or feature area touched (`users`, `auth`, `songs`). One logical change per commit.

## Scope and readiness

Commit automatically when approved implementation paths are known and required checks and reviews pass. A separate confirmation of the commit message is unnecessary. In dev-team, only the Publisher commits; the Lead provides scope and evidence. For an explicit standalone commit, follow the repository's required checks and preserve existing authorization.

Stage only approved changes. Preserve unrelated staged or unstaged work; do not use blanket staging. If scope is unresolved, ask one focused question. Missing required checks block the commit. Do not change reviewed source to repair a hook from the Publisher role; return the failure to the Implementer.

## Message and PR validation

1. Derive permitted type, scope, ticket placement, and header length from repository instructions and validators, including extended commitlint configuration. Otherwise use Conventional Commits: `type(scope): imperative subject`, for example `fix(users): redirect to the original page after login`. Never `claude/...`-style or vague subjects such as `updates`.
2. Put the ticket where the repository's rules place it (footer or scope). If a ticket was needed and Linear is unavailable, omit it rather than inventing one.
3. Write a short English subject. Use the repository's actual header-length rule. If no rule exists, use a 72-character ceiling including type, scope, punctuation, and ticket. This is a local default, not a Conventional Commits requirement.
4. If the subject will become the PR title, also satisfy its validator. Otherwise validate the title separately. Keep rationale, implementation detail, and validation in the body or PR description. Shorten wording without truncating required identifiers.
5. Run the configured message validator against the proposed message using its supported input/file option. Keep temporary messages outside the repository. If no validator exists, check the explicit repository rules directly. Do not install or assume a validator for another project.
6. Commit with normal hooks. A failed hook is a failure to resolve, never permission for `--no-verify`. If hooks change source content, refresh checks and required reviews for the new content.

A commit containing exactly the reviewed content does not itself require reviewing that content again. Record the new commit identity and retain the reviewed content evidence. This skill does not push. Pushing and PR creation belong to `ci-prepush-guardian` and `create-pr`, which run automatically after a passing implementation under the shared policy's auto-publish authorization. Never merge or deploy.
