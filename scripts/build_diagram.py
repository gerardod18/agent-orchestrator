#!/usr/bin/env python3
"""Build diagram/index.html (and optionally an artifact fragment) from the repo's home/ copy."""
import json, re, sys, time
from pathlib import Path

ORCH = {"dev-team", "pr-followup"}
# roles named in prose rather than by id
ROLE = {"PR reader": "dev-team-pr-reader", "Implementer": "dev-team-implementer", "Standards reviewer": "dev-team-review-standards",
        "Spec reviewer": "dev-team-review-spec", "Publisher": "dev-team-publisher", "Specs": "dev-team-specs"}


def front(text):
    sys.path.insert(0, str(Path(__file__).parent))
    import sync
    return sync.front(text)


def clip(s, n=3200):
    s = s.strip()
    return s if len(s) <= n else s[:n].rsplit("\n", 1)[0] + "\n…"


def collect(repo):
    home = repo / "home/agents"
    nodes, text = {}, {}
    pol = home / "POLICY.md"
    if pol.exists():
        t = pol.read_text(); text["policy"] = t
        nodes["policy"] = dict(id="policy", label="POLICY.md", kind="policy", desc="Shared rules every agent follows: language, limits, workflow, definition of done, auto-publish, PR follow-up, code review.", body=clip(t), facts={"file": "POLICY.md", "linked as": "~/.claude/CLAUDE.md and ~/.codex/AGENTS.md"})
    for d in sorted((home / "skills").glob("*/SKILL.md")):
        fm, body = front(d.read_text()); n = fm.get("name", d.parent.name)
        kind = "orchestrator" if n in ORCH else "skill"
        explicit = fm.get("disable-model-invocation") == "true"
        extra = sorted(p.name for p in d.parent.iterdir() if p.name not in ("SKILL.md", "agents"))
        nodes[n] = dict(id=n, label=n, kind=kind, desc=fm.get("description", ""), body=clip(body),
                        facts={"invocation": "explicit only (user-invoked)" if explicit else "model-invocable", "extra files": ", ".join(extra[:8]) + (" …" if len(extra) > 8 else "") if extra else "none"})
        text[n] = d.read_text()
    for d in sorted((home / "agent-definitions").glob("*.md")):
        fm, body = front(d.read_text()); n = fm["name"]
        nodes[n] = dict(id=n, label=n.replace("dev-team-", "dev-team-\n"), kind="agent", desc=fm.get("description", ""), body=clip(body),
                        facts={"tools": fm.get("tools", ""), "model": fm.get("model", ""), "preloaded skills": ", ".join(fm.get("skills_list", [])) or "none"})
        text[n] = d.read_text(); nodes[n]["pre"] = fm.get("skills_list", [])
    for f in sorted((home / "dev-team/scripts").glob("*.py")):
        t = f.read_text(); doc = re.search(r'"""(.*?)"""', t, re.S)
        n = f.name
        nodes[n] = dict(id=n, label=n, kind="hook", desc=(doc.group(1).strip().split("\n\n")[0] if doc else "Helper script").replace("\n", " "), body=clip(t, 2600), facts={"path": "~/.agents/dev-team/scripts/" + n})
        text[n] = t
    return nodes, text


def edges(nodes, text):
    E = {}
    def add(a, b, kind):
        if a != b and a in nodes and b in nodes and (a, b) not in E:
            E[(a, b)] = kind
    skills = [k for k, v in nodes.items() if v["kind"] in ("skill", "orchestrator")]
    agents = [k for k, v in nodes.items() if v["kind"] == "agent"]
    for k in agents:
        for s in nodes[k]["pre"]:
            add(k, s, "preloads")
        for s in skills:
            if re.search(r"SKILLS\}\}/%s/" % re.escape(s), text[k]):
                add(k, s, "reads")
    for k in ["policy"] + skills:
        t = text[k]
        for s in skills:
            if s != k and re.search(r"`%s`|skills/%s/" % (re.escape(s), re.escape(s)), t):
                add(k, s, "references")
        for a in agents:
            if a in t:
                add(k, a, "dispatches")
        for h, v in nodes.items():
            if v["kind"] == "hook" and h in t:
                add(k, h, "uses")
    for o in ORCH:
        for role, a in ROLE.items():
            if re.search(re.escape(role), text.get(o, "")):
                add(o, a, "dispatches")
    return [dict(s=a, t=b, k=k) for (a, b), k in E.items()]


def build(repo):
    repo = Path(repo)
    nodes, text = collect(repo)
    ed = edges(nodes, text)
    skill_targets = {e["t"] for e in ed if nodes[e["s"]]["kind"] == "agent"}
    for k, v in nodes.items():
        v["row"] = {"policy": 0, "hook": 0, "orchestrator": 1, "agent": 2}.get(v["kind"], 3 if k in skill_targets else 4)
        v["size"] = len(v["body"])
    data = dict(nodes=list(nodes.values()), edges=ed, built=time.strftime("%Y-%m-%d"))
    tpl = (repo / "diagram/template.html").read_text()
    frag = tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (repo / "diagram/artifact.html").write_text(frag)
    page = ("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<style>body{margin:0}</style></head><body>\n" + frag + "\n</body></html>\n")
    (repo / "diagram/index.html").write_text(page)
    print(f"diagram: {len(nodes)} nodes, {len(ed)} edges")


if __name__ == "__main__":
    build(Path(__file__).resolve().parent.parent)
