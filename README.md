# agent-orchestrator

Versioned copy of my agent orchestration layer: shared policy, skills, agent contracts, helper scripts and hooks for Claude Code and Codex. `home/` mirrors the local folders; `scripts/sync.py` reconciles them.

- **Live map:** open `diagram/index.html` (hover a node to read its instructions). It is rebuilt from `home/` on every `sync.py push`.
- **Source of truth:** `~/.agents` on the machine. This repo is the backup and the way to restore elsewhere.

## Layout

| Path | Mirrors | Content |
|---|---|---|
| `home/agents/POLICY.md` | `~/.agents/POLICY.md` | Shared rules (linked as `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) |
| `home/agents/skills/` | `~/.agents/skills/` | One folder per skill |
| `home/agents/agent-definitions/` | `~/.agents/agent-definitions/` | Canonical agent contracts (`{{SKILLS}}` placeholder) |
| `home/agents/dev-team/scripts/` | `~/.agents/dev-team/scripts/` | `state.py`, `codex_hook.py`, `followup_gate.py` |
| `home/claude/hooks.json` | `hooks` block of `~/.claude/settings.json` | Hook wiring, reference only |
| `scripts/sync.py` | | `status`, `push`, `pull`, `render`, `diagram` |

Paths are stored as `{{HOME}}`. Generated adapters (`~/.claude/agents`, `~/.codex/agents`) are not stored; `sync.py render` rebuilds them from the canonical contracts.

## Use

```bash
python3 scripts/sync.py status   # what differs
python3 scripts/sync.py push     # local -> repo (then commit and push)
python3 scripts/sync.py pull     # repo -> local (backs up overwritten files), relinks skills, renders adapters
```

The `sync-orchestrator` skill runs this on demand.

## Not stored (public repo)

Project profiles (`dev-team/profiles/`), `settings.json` beyond its hooks block, auth and session data, caches. `push` refuses any file matching a secret pattern.

## Flow in one paragraph

The parent (`dev-team` or `pr-followup`) reads the policy and coordinates; it never edits code (a PreToolUse hook enforces this during PR follow-up). The parent retrieves review comments with a tool (the `gh-pr-review` extension, or stock `gh api graphql`) and sends them as one batch to the implementer, which follows `implement` (spec first, tests from the spec, code, sibling sweep). Independent Standards and Spec reviewers check the frozen snapshot, then the publisher commits (Conventional Commit, `<type>/<ticket>-<slug>` branch, Linear ticket if missing), pushes through the pre-push guardian and opens the PR.
