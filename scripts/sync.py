#!/usr/bin/env python3
"""Reconcile this repo with the local agent folders (~/.agents, ~/.claude, ~/.codex).

  sync.py status             what differs (local vs repo)
  sync.py push               local -> repo/home (sanitized), then rebuild the diagram
  sync.py pull               repo/home -> local (backs up what it overwrites), then render adapters
  sync.py render             regenerate ~/.claude/agents/*.md and ~/.codex/agents/*.toml from agent-definitions
  sync.py diagram            rebuild diagram/index.html from the repo copy

Repo layout (home/ mirrors ~):
  home/agents/{POLICY.md,skills,agent-definitions,dev-team/scripts}   <- ~/.agents
  home/claude/hooks.json                                              <- hooks block of ~/.claude/settings.json

Paths are stored as {{HOME}} so the repo has no machine-specific or user-specific text.
Never synced (public repo): dev-team/profiles (project-specific), caches, state, settings.json secrets.
"""
import filecmp, json, os, re, shutil, sys, time
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent
H = REPO / "home"
MAP = [  # (local, repo) directory/file pairs under home/
    (HOME / ".agents/POLICY.md", H / "agents/POLICY.md"),
    (HOME / ".agents/skills", H / "agents/skills"),
    (HOME / ".agents/agent-definitions", H / "agents/agent-definitions"),
    (HOME / ".agents/dev-team/scripts", H / "agents/dev-team/scripts"),
]
SKIP = {"__pycache__", ".DS_Store", ".git", "node_modules"}
TEXT = {".md", ".yaml", ".yml", ".json", ".py", ".cjs", ".js", ".txt", ".toml", ".html", ".css"}
SECRET = re.compile(r"(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|lin_api_[A-Za-z0-9]{20,})")


def files(root):
    if root.is_file():
        yield root, Path(root.name)
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP) and not p.is_symlink():
            yield p, p.relative_to(root)


def enc(b, p):  # local -> repo
    if p.suffix in TEXT:
        return b.replace(str(HOME).encode(), b"{{HOME}}")
    return b


def dec(b, p):  # repo -> local
    if p.suffix in TEXT:
        return b.replace(b"{{HOME}}", str(HOME).encode())
    return b


def plan():
    """yield (kind, local_path, repo_path) where kind in same|changed|local-only|repo-only"""
    for loc, rep in MAP:
        l = dict((str(r), p) for p, r in files(loc)) if loc.exists() else {}
        r = dict((str(x), p) for p, x in files(rep)) if rep.exists() else {}
        base_l = loc if loc.is_dir() else loc.parent
        base_r = rep if loc.is_dir() else rep.parent
        for k in sorted(set(l) | set(r)):
            lp = l.get(k); rp = r.get(k)
            if lp and rp:
                same = enc(lp.read_bytes(), lp) == rp.read_bytes()
                yield ("same" if same else "changed", lp, rp)
            elif lp:
                yield ("local-only", lp, base_r / k)
            else:
                yield ("repo-only", base_l / k, rp)
    # hooks block
    hl = settings_hooks()
    hr = H / "claude/hooks.json"
    cur = json.loads(hr.read_text()) if hr.exists() else None
    yield ("same" if cur == hl else "changed", HOME / ".claude/settings.json", hr)


def settings_hooks():
    s = json.loads((HOME / ".claude/settings.json").read_text())
    return json.loads(json.dumps(s.get("hooks", {})).replace(str(HOME), "{{HOME}}"))


def status():
    n = 0
    for kind, l, r in plan():
        if kind != "same":
            n += 1
            print(f"{kind:11} {r.relative_to(REPO)}")
    print("in sync" if not n else f"{n} difference(s)")
    return n


def push():
    for loc, rep in MAP:
        # remove repo files whose local source is gone (deleted skills)
        for kind, l, r in plan():
            pass
    for kind, l, r in plan():
        if r == H / "claude/hooks.json":
            r.parent.mkdir(parents=True, exist_ok=True)
            r.write_text(json.dumps(settings_hooks(), indent=2) + "\n")
            continue
        if kind in ("changed", "local-only"):
            data = enc(l.read_bytes(), l)
            if SECRET.search(data.decode("utf-8", "ignore")):
                sys.exit(f"refusing to copy {l}: looks like it contains a secret")
            r.parent.mkdir(parents=True, exist_ok=True)
            r.write_bytes(data)
            shutil.copymode(l, r)
        elif kind == "repo-only":
            r.unlink()
            print("removed from repo:", r.relative_to(REPO))
    for d in sorted((p for p in H.rglob("*") if p.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    diagram()
    print("push done; review with `git status` then commit")


def pull():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bak = HOME / ".agents-sync-backup" / stamp
    for kind, l, r in plan():
        if r == H / "claude/hooks.json":
            continue  # hooks are merged by hand; see README
        if kind in ("changed", "repo-only"):
            if l.exists():
                (bak / l.relative_to(HOME)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(l, bak / l.relative_to(HOME))
            l.parent.mkdir(parents=True, exist_ok=True)
            l.write_bytes(dec(r.read_bytes(), r))
            shutil.copymode(r, l)
        elif kind == "local-only":
            if l.exists():
                (bak / l.relative_to(HOME)).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(l, bak / l.relative_to(HOME))
            l.unlink()
            print("removed locally (backed up):", l)
    link_skills()
    render()
    print(f"pull done; overwritten files backed up in {bak}")


def link_skills():
    """~/.claude/skills/<name> -> ~/.agents/skills/<name>; drop dangling links"""
    d = HOME / ".claude/skills"
    d.mkdir(parents=True, exist_ok=True)
    for s in (HOME / ".agents/skills").iterdir():
        if s.is_dir() and (s / "SKILL.md").exists() and not (d / s.name).exists():
            (d / s.name).symlink_to(s)
    for p in d.iterdir():
        if p.is_symlink() and not p.exists():
            p.unlink()
    for tgt in (HOME / ".claude/CLAUDE.md", HOME / ".codex/AGENTS.md"):
        if not tgt.exists() and not tgt.is_symlink():
            tgt.symlink_to(HOME / ".agents/POLICY.md")


def front(text):
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return {}, text
    fm, body = {}, m.group(2)
    key = None
    for line in m.group(1).split("\n"):
        if re.match(r"^[A-Za-z-]+:", line):
            key, _, v = line.partition(":")
            fm[key] = v.strip()
        elif line.startswith("- ") and key:
            fm.setdefault(key + "_list", []).append(line[2:].strip())
        elif key and line.strip():
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm, body


def render():
    sk = str(HOME / ".agents/skills")
    ca, cx = HOME / ".claude/agents", HOME / ".codex/agents"
    ca.mkdir(parents=True, exist_ok=True); cx.mkdir(parents=True, exist_ok=True)
    for src in sorted((HOME / ".agents/agent-definitions").glob("*.md")):
        text = src.read_text().replace("{{SKILLS}}", sk)
        (ca / src.name).write_text(text)
        fm, body = front(text)
        out = ["# Generated from a canonical contract; edit the source, then render again.",
               f'name = {json.dumps(fm["name"].replace("-", "_"))}',
               f'description = {json.dumps(fm["description"])}',
               f"developer_instructions = {json.dumps(body)}"]
        for s in fm.get("skills_list", []):
            out += ["", "[[skills.config]]", f'path = "{sk}/{s}/SKILL.md"', "enabled = true"]
        (cx / (src.stem + ".toml")).write_text("\n".join(out) + "\n")
    print("rendered adapters for", len(list((HOME / ".agents/agent-definitions").glob("*.md"))), "agents")


def diagram():
    sys.path.insert(0, str(REPO / "scripts"))
    import build_diagram
    build_diagram.build(REPO)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"status": status, "push": push, "pull": pull, "render": render, "diagram": diagram}.get(cmd, lambda: sys.exit(__doc__))()
