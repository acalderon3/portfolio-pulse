"""Check the pipeline against ground truth. This is the "verify before it ships" step.

The generator knows the real facts behind every messy artifact. This script scores what
the pipeline recovered, field by field and source by source, and lists every miss so a
person can look at it. Nothing here feeds back into the pipeline.

  python -m pipeline.eval
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["owner", "self_status", "target", "baseline", "last_update", "blocker_text", "blocker_since", "done"]


def same(field, got, want):
    if field == "blocker_text":  # presence and rough wording
        if not got or not want:
            return bool(got) == bool(want)
        return got.lower().strip(". ") == want.lower().strip(". ")
    return (got or None) == (want or None)


def main():
    truth = json.loads((ROOT / "ground_truth" / "truth.json").read_text())
    snap = json.loads((ROOT / "docs" / "data" / "portfolio.json").read_text())
    T = {p["id"]: p for p in truth["programs"]}
    S = {p["id"]: p for p in snap["programs"]}

    by_source = defaultdict(lambda: Counter())
    misses = []
    for pid, t in T.items():
        s = S.get(pid)
        method = "model" if t["team"] in ("WPT", "EAI") else "parser"
        src = s["source"] if s else "?"
        for f in FIELDS:
            got = s.get(f) if s else None
            ok = same(f, got, t.get(f))
            by_source[src][f + ("_ok" if ok else "_miss")] += 1
            by_source[src]["_ok" if ok else "_miss"] += 1
            if not ok:
                misses.append({"program": pid, "source": src, "method": method, "field": f, "expected": t.get(f), "got": got})

    field_table = []
    for src, c in by_source.items():
        row = {"source": src, "method": "model" if src in ("slack", "steering") else "parser"}
        for f in FIELDS:
            n = c[f + "_ok"] + c[f + "_miss"]
            row[f] = round(c[f + "_ok"] / n, 3) if n else None
        row["overall"] = round(c["_ok"] / (c["_ok"] + c["_miss"]), 3)
        field_table.append(row)

    want = {(d["downstream"], d["upstream"]) for d in truth["dependencies"]}
    got = {(e["downstream"], e["upstream"]) for e in snap["edges"]}
    hidden_want = {(d["downstream"], d["upstream"]) for d in truth["dependencies"] if d["recorded_in"] in ("slack", "steering")}
    deps = {"expected": len(want), "found": len(got), "true_positive": len(want & got),
            "precision": round(len(want & got) / len(got), 3) if got else None,
            "recall": round(len(want & got) / len(want), 3),
            "chat_and_notes_only_recall": round(len(hidden_want & got) / len(hidden_want), 3),
            "missed": sorted(map(list, want - got)), "extra": sorted(map(list, got - want))}

    conf = Counter((T[i]["health"], S[i]["health"]) for i in T if i in S)
    agree = sum(v for (a, b), v in conf.items() if a == b)
    health = {"agreement": round(agree / len(T), 3),
              "confusion": [{"truth": a, "pipeline": b, "n": n} for (a, b), n in sorted(conf.items())],
              "disagreements": [{"program": i, "truth": T[i]["health"], "pipeline": S[i]["health"],
                                 "truth_rules": T[i]["reasons"], "pipeline_rules": [r["rule"] for r in S[i]["reasons"]]}
                                for i in T if i in S and T[i]["health"] != S[i]["health"]]}

    planted = [
        ("One unsigned iPaaS contract puts the ERP go-live and 6 other programs at risk", lambda: S["ERP-01"]["health"] == "red" and any(c["root"] == "EAI-01" for c in snap["chains"])),
        ("ERP go-live reports Green but is Red on evidence", lambda: S["ERP-01"]["self_status"] == "green" and S["ERP-01"]["health"] == "red"),
        ("JML blocker cascades into SOX remediation and the APAC support launch", lambda: {"ERP-17", "CX-14"} <= set(next((c["affected"] for c in snap["chains"] if c["root"] == "WPT-01"), []))),
        ("Serialization tracker says Green; chat says the vendor is 3 weeks late", lambda: any(r["rule"] == "conflicting_signal" for r in S["SCT-04"]["reasons"])),
        ("Checkout replatform go-live lands inside the peak-season freeze", lambda: any(r["rule"] == "in_freeze" for r in S["COM-03"]["reasons"])),
        ("Forum migration is past its date and still open", lambda: any(r["rule"] == "past_due" for r in S["CX-12"]["reasons"])),
        ("Three programs have no owner", lambda: all(not S[i]["owner"] for i in ("SCT-06", "COM-15", "WPT-09"))),
        ("Two programs have no target date", lambda: all(not S[i]["target"] for i in ("WPT-12", "EAI-07"))),
    ]
    planted = [{"scenario": n, "detected": bool(f())} for n, f in planted]

    ex = snap["extraction"]
    report = {"as_of": snap["as_of"], "fields": field_table, "field_misses": misses, "dependencies": deps,
              "health": health, "planted": planted,
              "grounding": {"failures": ex["grounding_failures"],
                            "model_fields_checked": ex["fields_by"].get("model", 0)}}
    (ROOT / "docs" / "data" / "eval.json").write_text(json.dumps(report, indent=1, default=str))

    print(f"health agreement {health['agreement']:.0%} | deps P {deps['precision']:.0%} R {deps['recall']:.0%} "
          f"(chat/notes-only R {deps['chat_and_notes_only_recall']:.0%}) | planted {sum(p['detected'] for p in planted)}/{len(planted)} "
          f"| field misses {len(misses)} | grounding failures {len(ex['grounding_failures'])}")
    for r in field_table:
        print(f"  {r['source']:<11} {r['method']:<6} overall {r['overall']:.0%}")
    for m in misses:
        print("  miss", m)
    for d in health["disagreements"]:
        print("  health", d)


if __name__ == "__main__":
    main()
