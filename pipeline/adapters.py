"""Deterministic readers for the four structured sources.

No AI here, on purpose. When a source has fields (a CSV column, a table row), plain
parsing is cheaper, faster and exactly repeatable. Each value carries a receipt:
the file, where in the file, and the raw text it came from.
"""
import csv, re
from datetime import date, datetime, timedelta
from pathlib import Path

from .vocab import normalize_status, Resolver

SRC = Path(__file__).resolve().parents[1] / "sources"
AS_OF = date(2026, 9, 28)


def ev(file, locator, quote):
    return {"source": file, "locator": locator, "quote": str(quote)}


def _iso(d):
    return d.isoformat() if d else None


def _infer_year(month, day, ref, past=False):
    """Status docs write 'Feb 12' with no year. Pick the year that makes sense."""
    for y in (ref.year - 1, ref.year, ref.year + 1):
        d = date(y, month, day)
        if past and d <= ref and (ref - d).days < 330:
            return d
        if not past and d >= ref - timedelta(days=120):
            return d
    return None


def read_jira(catalog, res):
    file = "erp/jira_epics_export.csv"
    by_key = {c["source_key"]: c["id"] for c in catalog if c["source"] == "jira"}
    jd = lambda s: datetime.strptime(s, "%d/%b/%y %I:%M %p").date() if s else None
    out = {}
    with open(SRC / file) as f:
        for n, r in enumerate(csv.DictReader(f), 2):
            pid = by_key.get(r["Issue key"])
            if not pid:
                continue
            loc = f"row {n} ({r['Issue key']})"
            deps = [by_key[k.strip()] for k in r["Inward issue link (Blocks)"].split(",") if k.strip() in by_key]
            deps += [res.resolve(x) for x in r["Custom field (External Dependency)"].split(";") if res.resolve(x)]
            why = re.search(r"h2\. Why\n(.+?)\n", r["Description"])
            done = r["Status"] == "Done"
            out[pid] = {
                "owner": None if r["Assignee"] in ("", "Unassigned") else r["Assignee"],
                "self_status": "done" if done else normalize_status(r["Custom field (Health)"]),
                "target": _iso(jd(r["Due date"])), "baseline": _iso(jd(r["Custom field (Baseline Due)"])),
                "last_update": _iso(jd(r["Updated"])),
                "blocker_text": r["Custom field (Blocker)"] or None,
                "blocker_since": _iso(jd(r["Custom field (Blocked Since)"])),
                "why": why.group(1).rstrip(".") if why else None, "done": done, "depends_on": deps,
                "evidence": {
                    "owner": ev(file, loc + " Assignee", r["Assignee"]),
                    "self_status": ev(file, loc + " Health", r["Custom field (Health)"] or r["Status"]),
                    "target": ev(file, loc + " Due date", r["Due date"]),
                    "baseline": ev(file, loc + " Baseline Due", r["Custom field (Baseline Due)"]),
                    "last_update": ev(file, loc + " Updated", r["Updated"]),
                    "blocker": ev(file, loc + " Blocker", r["Custom field (Blocker)"] + " / " + r["Custom field (Blocked Since)"]),
                    "depends_on": ev(file, loc + " Links", (r["Inward issue link (Blocks)"] + " " + r["Custom field (External Dependency)"]).strip()),
                },
            }
    return out


def read_sheet(catalog, res):
    file = "supply_chain/sct_program_tracker.csv"
    by_key = {c["source_key"]: c["id"] for c in catalog if c["source"] == "sheet"}
    ud = lambda s: datetime.strptime(s, "%m/%d/%Y").date() if s else None
    out = {}
    with open(SRC / file) as f:
        for n, r in enumerate(csv.DictReader(f), 2):
            pid = by_key.get(r["Project"])
            if not pid:
                continue
            loc = f"row {n}"
            m = re.search(r"Blocked: (.+?) \(since (\d+)/(\d+)\)", r["Notes"])
            last = ud(r["Last touched"])
            since = _infer_year(int(m.group(2)), int(m.group(3)), last, past=True) if m else None
            done = r["RAG"] == "Complete"
            out[pid] = {
                "owner": None if r["Lead"] in ("", "TBD") else r["Lead"],
                "self_status": "done" if done else normalize_status(r["RAG"]),
                "target": _iso(ud(r["Go-live (plan)"])), "baseline": _iso(ud(r["Go-live (orig)"])),
                "last_update": _iso(last), "blocker_text": m.group(1)[0].upper() + m.group(1)[1:] if m else None,
                "blocker_since": _iso(since), "why": r["Business value"] or None, "done": done,
                "depends_on": [res.resolve(x) for x in r["Depends on"].split(";") if res.resolve(x)],
                "evidence": {k: ev(file, f"{loc} {col}", r[col]) for k, col in [
                    ("owner", "Lead"), ("self_status", "RAG"), ("target", "Go-live (plan)"),
                    ("baseline", "Go-live (orig)"), ("last_update", "Last touched"), ("blocker", "Notes"),
                    ("depends_on", "Depends on"), ("why", "Business value")]},
            }
    return out


def read_confluence(catalog, res):
    out = {}
    for c in [c for c in catalog if c["source"] == "confluence"]:
        file = f"commercial/confluence/{c['source_key']}"
        text = (SRC / file).read_text()
        field = dict(re.findall(r"^\| (.+?) \| (.*?) \|$", text, re.M))
        sec = lambda h: (re.search(rf"## {h}\n(.*?)(?:\n## |\Z)", text, re.S) or [None, ""])[1].strip()
        dates = {k: (None if field.get(k, "TBD") in ("TBD", "") else field[k]) for k in ("Target date", "Baseline date", "Last updated")}
        blk = sec("Blockers")
        m = re.match(r"- (.+?) \(raised (\d{4}-\d\d-\d\d)\)", blk)
        deps = [res.resolve(line[2:]) for line in sec("Dependencies").splitlines() if line.startswith("- ") and res.resolve(line[2:])]
        status = normalize_status(field.get("Status", ""))
        out[c["id"]] = {
            "owner": field.get("Owner") or None, "self_status": status,
            "target": dates["Target date"], "baseline": dates["Baseline date"], "last_update": dates["Last updated"],
            "blocker_text": m.group(1) if m else None, "blocker_since": m.group(2) if m else None,
            "why": sec("Why it matters").rstrip(".") or None, "done": status == "done", "depends_on": deps,
            "evidence": {
                "owner": ev(file, "table: Owner", field.get("Owner", "")),
                "self_status": ev(file, "table: Status", field.get("Status", "")),
                "target": ev(file, "table: Target date", field.get("Target date", "")),
                "baseline": ev(file, "table: Baseline date", field.get("Baseline date", "")),
                "last_update": ev(file, "table: Last updated", field.get("Last updated", "")),
                "blocker": ev(file, "## Blockers", blk),
                "depends_on": ev(file, "## Dependencies", sec("Dependencies")),
                "why": ev(file, "## Why it matters", sec("Why it matters")),
            },
        }
    return out


MONTHS = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def read_status_doc(catalog, res):
    file = "cx/cx_weekly_status_2026-09-25.md"
    lines = (SRC / file).read_text().splitlines()
    doc_date = date(2026, 9, 25)
    by_name = {c["source_key"]: c["id"] for c in catalog if c["source"] == "status_doc"}
    md = lambda s: _infer_year(MONTHS[s.split()[0]], int(s.split()[1]), doc_date) if s and s != "TBD" else None
    out = {}
    for i, line in enumerate(lines):
        if not line.startswith("## ") or line[3:] not in by_name:
            continue
        pid, block = by_name[line[3:]], lines[i + 1:i + 5]
        head = block[0]
        g = lambda pat, s=head: (re.search(pat, s) or [None, None])[1]
        tgt = g(r"Target: (\w+ \d+|TBD)")
        was = g(r"\(was (\w+ \d+)\)")
        upd = g(r"Updated (\d+/\d+)")
        blk = block[3].removeprefix("Blocker: ")
        bm = re.match(r"(.+) \(since (\d+)/(\d+)\)", blk)
        # owners edit their section after the week-ending date, so resolve against the run date
        last = _infer_year(*map(int, upd.split("/")), AS_OF, past=True) if upd else None
        deps_txt = block[2].removeprefix("Depends on: ")
        status = normalize_status(g(r"Status: (\w+)") or "")
        loc = f"line {i + 2}"
        out[pid] = {
            "owner": g(r"Owner: (.+?) ·") or None, "self_status": status,
            "target": _iso(md(tgt)), "baseline": _iso(md(was)) if was else _iso(md(tgt)),
            "last_update": _iso(last),
            "blocker_text": bm.group(1) if bm else (None if blk == "none" else blk),
            "blocker_since": _iso(_infer_year(int(bm.group(2)), int(bm.group(3)), AS_OF, past=True)) if bm else None,
            "why": block[1].removeprefix("Why: ").rstrip(".") or None, "done": status == "done",
            "depends_on": [res.resolve(x) for x in deps_txt.split(",") if res.resolve(x)],
            "evidence": {
                "owner": ev(file, loc, head), "self_status": ev(file, loc, head), "target": ev(file, loc, head),
                "baseline": ev(file, loc, head), "last_update": ev(file, loc, head),
                "blocker": ev(file, f"line {i + 5}", block[3]), "depends_on": ev(file, f"line {i + 4}", block[2]),
                "why": ev(file, f"line {i + 3}", block[1]),
            },
        }
    return out


def read_structured(catalog):
    res = Resolver(catalog)
    out = {}
    for fn in (read_jira, read_sheet, read_confluence, read_status_doc):
        out.update(fn(catalog, res))
    return out
