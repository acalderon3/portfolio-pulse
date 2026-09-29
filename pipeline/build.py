"""Build the portfolio snapshot the demo site reads.

  python -m pipeline.build                  # replay recorded model output (free, offline)
  python -m pipeline.build --backend claude # re-run extraction live (needs ANTHROPIC_API_KEY)

Steps: read the structured sources -> extract the unstructured ones -> grounding check ->
merge into one register -> apply the shared health rubric -> dependency analysis ->
write docs/data/portfolio.json
"""
import argparse, json, shutil
from collections import Counter, defaultdict
from pathlib import Path

from .adapters import read_structured
from .extract import extract_all, AS_OF
from .rubric import assess, rubric_doc, LEVEL
from .vocab import SRC, load_catalog

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "data"
INTRINSIC = {"past_due", "blocker_age", "slip", "stale", "missing_basics", "in_freeze", "conflicting_signal"}


def build(backend="cache"):
    catalog = load_catalog()
    cat = {c["id"]: c for c in catalog}
    freezes = json.loads((SRC / "freeze_calendar.json").read_text())

    records = read_structured(catalog)
    for r in records.values():
        for e in r["evidence"].values():
            e["by"] = "parser"
    ex = extract_all(catalog, backend)
    records.update(ex["records"])

    # --- dependencies: union of structured links and model-extracted ones
    edges = {}
    for pid, r in records.items():
        for u in r["depends_on"]:
            e = r["evidence"].get("depends_on", {})
            edges[(pid, u)] = {"downstream": pid, "upstream": u, "found_by": "parser",
                               "source": e.get("source"), "locator": e.get("locator"), "quote": e.get("quote")}
    for d in ex["dependencies"]:
        key = (d["downstream_id"], d["upstream_id"])
        if key in edges:
            edges[key]["also_in"] = d["source"]
            continue
        edges[key] = {"downstream": key[0], "upstream": key[1], "found_by": "model",
                      "source": d["source"], "locator": d["locator"], "quote": d["quote"]}
    for (d, u), e in edges.items():  # a link only in chat/notes, crossing teams = quiet coupling
        e["cross_team"] = cat[d]["team"] != cat[u]["team"]
        e["hidden"] = e["found_by"] == "model" and e["cross_team"]

    # --- signals: contradictions feed the rubric; schedule notes are shown, not scored
    notes = defaultdict(list)
    for s in ex["signals"]:
        notes[s["program_id"]].append(s)
        if s["kind"] == "contradicts_reported_status" and s["program_id"] in records:
            records[s["program_id"]].setdefault("signals", []).append(s["summary"])

    missing = [c["id"] for c in catalog if c["id"] not in records]
    feats = {pid: {**r, "team": cat[pid]["team"]} for pid, r in records.items()}
    result = assess(feats, list(edges), freezes, AS_OF)

    up, down = defaultdict(list), defaultdict(list)
    for d, u in edges:
        up[d].append(u); down[u].append(d)

    programs = []
    for c in catalog:
        pid = c["id"]
        if pid not in records:
            continue
        r, a = records[pid], result[pid]
        worse = a["health"] in LEVEL and r["self_status"] in LEVEL and LEVEL[a["health"]] > LEVEL[r["self_status"]]
        programs.append({
            "id": pid, "name": c["name"], "team": c["team"], "team_name": c["team_name"], "tier": c["tier"],
            "source": c["source"], "owner": r["owner"], "self_status": r["self_status"], "health": a["health"],
            "status_gap": worse, "reasons": a["reasons"],
            "target": r["target"], "baseline": r["baseline"],
            "forecast": a["forecast"].isoformat() if a["forecast"] else None,
            "last_update": r["last_update"], "blocker_text": r["blocker_text"], "blocker_since": r["blocker_since"],
            "why": r["why"], "done": r["done"], "evidence": r["evidence"], "notes": notes.get(pid, []),
            "upstream": sorted(up[pid]), "downstream": sorted(down[pid]),
        })
    by_id = {p["id"]: p for p in programs}

    # --- root causes and blast radius: which Reds are dragging others down?
    def dependency_only(p):
        return p["reasons"] and all(r["rule"] not in INTRINSIC for r in p["reasons"])

    def blast(pid, seen=None):
        seen = set() if seen is None else seen
        for d in down[pid]:
            if d not in seen and any(r["rule"] in ("upstream_red", "dependency_late") for r in by_id[d]["reasons"]):
                seen.add(d); blast(d, seen)
        return seen

    chains = []
    for p in programs:
        if p["health"] == "red" and not dependency_only(p):
            hit = sorted(blast(p["id"]), key=lambda i: (-LEVEL.get(by_id[i]["health"], 0), i))
            if hit:
                chains.append({"root": p["id"], "affected": hit,
                               "teams": sorted({by_id[i]["team"] for i in hit + [p["id"]]}),
                               "red": [i for i in hit if by_id[i]["health"] == "red"]})
    chains.sort(key=lambda c: -len(c["affected"]))

    teams = []
    for t in dict.fromkeys(c["team"] for c in catalog):
        ps = [p for p in programs if p["team"] == t]
        teams.append({"team": t, "team_name": ps[0]["team_name"], "source": ps[0]["source"],
                      "health": Counter(p["health"] for p in ps), "self": Counter(str(p["self_status"]) for p in ps),
                      "gaps": sum(p["status_gap"] for p in ps), "count": len(ps)})

    snapshot = {
        "as_of": AS_OF, "company": "Kestrel Health (fictional)", "freezes": freezes, "rubric": rubric_doc(),
        "programs": programs, "edges": list(edges.values()), "chains": chains, "teams": teams,
        "summary": {"programs": len(programs), "health": Counter(p["health"] for p in programs),
                    "self_reported": Counter(str(p["self_status"]) for p in programs),
                    "status_gaps": sum(p["status_gap"] for p in programs),
                    "hidden_dependencies": sum(e["hidden"] for e in edges.values()),
                    "dependencies": len(edges), "missing_from_sources": missing},
        "extraction": {"runs": ex["runs"], "grounding_failures": ex["grounding_failures"],
                       "fields_by": Counter(e["by"] for p in programs for e in p["evidence"].values())},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "portfolio.json").write_text(json.dumps(snapshot, indent=1, ensure_ascii=False, default=str))
    # publish the raw sources next to the site so every receipt can be opened
    shutil.rmtree(OUT / "sources", ignore_errors=True)
    shutil.copytree(SRC, OUT / "sources")
    return snapshot


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["cache", "claude"], default="cache")
    s = build(ap.parse_args().backend)
    print(json.dumps(s["summary"], indent=1))
    for c in s["chains"]:
        print("chain", c["root"], "->", c["affected"])
