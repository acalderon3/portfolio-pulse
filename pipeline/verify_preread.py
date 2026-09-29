"""Check the pre-read against the data before it goes out.

Model-drafted prose is where confident mistakes hide, so the checks are mechanical:
  - every program ID exists
  - every health tag, like 'EAI-01 (Red)', matches the computed health
  - the headline counts match the data
  - every Red program is mentioned (nothing important left out)
  - each hygiene list names exactly the programs its rule flagged
  python -m pipeline.verify_preread
"""
import json, re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "docs" / "data"
HYGIENE = {"No owner": lambda p: not p["owner"] and not p["done"],
           "No target date": lambda p: not p["target"] and not p["done"],
           "Stale": lambda p: any(r["rule"] == "stale" for r in p["reasons"]),
           "Past due": lambda p: any(r["rule"] == "past_due" for r in p["reasons"]),
           "Freeze collisions": lambda p: any(r["rule"] == "in_freeze" for r in p["reasons"])}


def main():
    snap = json.loads((DATA / "portfolio.json").read_text())
    text = (DATA / "preread.md").read_text()
    P = {p["id"]: p for p in snap["programs"]}
    ID = r"\b(?:ERP|SCT|COM|CX|WPT|EAI)-\d\d\b"
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    ids = set(re.findall(ID, text))
    unknown = sorted(ids - set(P))
    check("Every program ID exists", not unknown, ", ".join(unknown) or f"{len(ids)} IDs referenced")

    tags = re.findall(rf"({ID}) \((Red|Amber|Green)\)", text)
    wrong = [f"{i} says {h}, data says {P[i]['health']}" for i, h in tags if i in P and P[i]["health"] != h.lower()]
    check("Health tags match the data", not wrong, "; ".join(wrong) or f"{len(tags)} tags checked")

    h = snap["summary"]["health"]
    m = re.search(r"(\d+) programs, (\d+) are Red, (\d+) Amber, (\d+) Green and (\d+) done\. (\d+) programs report", text)
    want = (snap["summary"]["programs"], h.get("red", 0), h.get("amber", 0), h.get("green", 0), h.get("done", 0), snap["summary"]["status_gaps"])
    got = tuple(map(int, m.groups())) if m else None
    check("Headline counts match", got == want, f"text {got}, data {want}")

    reds = sorted(i for i, p in P.items() if p["health"] == "red")
    missing = [i for i in reds if i not in ids]
    check("Every Red program is mentioned", not missing, ", ".join(missing) or f"all {len(reds)} Reds present")

    for label, rule in HYGIENE.items():
        line = next((l for l in text.splitlines() if l.startswith(f"- **{label}")), None)
        stated = set(re.findall(ID, line or ""))
        actual = {i for i, p in P.items() if rule(p)}
        diff = [f"missing {sorted(actual - stated)}" if actual - stated else "", f"extra {sorted(stated - actual)}" if stated - actual else ""]
        check(f"Hygiene list '{label}' is complete and exact", line and stated == actual, " ".join(d for d in diff if d) or f"{len(actual)} programs")

    out = {"passed": all(c["pass"] for c in checks), "checks": checks}
    (DATA / "preread_check.json").write_text(json.dumps(out, indent=1))
    for c in checks:
        print("PASS" if c["pass"] else "FAIL", c["check"], "-", c["detail"])
    return out


if __name__ == "__main__":
    raise SystemExit(0 if main()["passed"] else 1)
