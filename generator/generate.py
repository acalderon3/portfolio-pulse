"""Generate a synthetic, deliberately messy IT portfolio for a fictional company.

Writes:
  sources/               what each team actually maintains, in six different formats
  sources/catalog.csv    the PMO's program list (id, name, team, tier, source key)
  ground_truth/truth.json the real facts. Only eval.py reads this; the pipeline never does.

Deterministic: same seed, same files.  Run:  python generator/generate.py
"""
import csv, json, random, re, sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator.catalog import TEAMS, TEAM_SOURCE, DEPENDENCIES, FREEZES, PEOPLE, programs  # noqa
from pipeline.rubric import assess  # noqa

AS_OF = date(2026, 9, 28)
rng = random.Random(20260928)
SRC, GT = ROOT / "sources", ROOT / "ground_truth"

D = date.fromisoformat
BLOCKERS = ["Waiting on vendor SOW countersignature", "Security review not scheduled",
            "Test environment not provisioned", "Data migration defects in UAT",
            "Awaiting legal review of the DPA", "Integration credentials not issued"]

# Scenarios planted on purpose so the demo has something real to find.
PLANTED = {
    "EAI-01": dict(baseline="2026-10-30", target="2026-12-11", self="amber", last="2026-09-24",
                   blocker=("Vendor contract amendment unsigned; sitting with Procurement", "2026-09-08")),
    "EAI-03": dict(baseline="2026-10-23", target="2026-10-23"),
    "ERP-14": dict(baseline="2026-10-16", target="2026-10-16"),
    "ERP-01": dict(baseline="2026-11-02", target="2026-11-02", self="green", last="2026-09-25"),
    "ERP-02": dict(baseline="2026-11-20", target="2026-11-20", self="green"),
    "ERP-09": dict(baseline="2026-12-16", target="2026-12-16", self="green"),
    "SCT-11": dict(baseline="2026-12-04", target="2026-12-04", self="green"),
    "ERP-08": dict(baseline="2026-12-04", target="2026-12-04"),
    "COM-04": dict(baseline="2027-02-26", target="2027-02-26", self="green"),
    "COM-14": dict(baseline="2026-11-13", target="2026-12-04", self="amber"),
    "ERP-06": dict(baseline="2027-03-26", target="2027-03-26"),
    "WPT-01": dict(baseline="2026-10-16", target="2026-11-13", self=None, last="2026-09-23",
                   blocker=("HRIS field mapping from the People team", "2026-09-10")),
    "ERP-17": dict(baseline="2026-11-20", target="2026-11-20", self="green"),
    "EAI-08": dict(baseline="2026-11-06", target="2026-11-06", self="amber"),
    "CX-16": dict(baseline="2026-10-30", target="2026-10-30", self="green"),
    "CX-14": dict(baseline="2026-11-02", target="2026-11-02", self="green"),
    "WPT-14": dict(baseline="2026-10-30", target="2026-10-30"),
    "WPT-08": dict(baseline="2027-01-29", target="2027-01-29"),
    "SCT-02": dict(baseline="2027-01-15", target="2027-01-15", self="green"),
    "COM-13": dict(baseline="2026-10-30", target="2026-10-30"),
    "COM-06": dict(baseline="2026-11-06", target="2026-11-06"),
    "COM-03": dict(baseline="2026-11-20", target="2026-11-20", self="green"),
    "COM-16": dict(baseline="2027-02-12", target="2027-02-12"),
    "ERP-11": dict(baseline="2026-12-04", target="2026-12-31", self="green"),
    "SCT-04": dict(baseline="2026-10-30", target="2026-10-30", self="green",
                   signal="Chat (#it-leads, 9/22): vendor API slips to mid-November, about 3 weeks late. Tracker still shows green."),
    "CX-06": dict(baseline="2026-12-11", target="2026-12-11"),
    "CX-12": dict(baseline="2026-09-18", target="2026-09-18", self="amber"),
    "WPT-12": dict(target=None, baseline=None),
    "EAI-07": dict(target=None, baseline=None),
    "SCT-06": dict(owner=None), "COM-15": dict(owner=None), "WPT-09": dict(owner=None),
    "EAI-11": dict(last="2026-09-10"), "EAI-05": dict(last="2026-09-10"),
    "WPT-04": dict(last="2026-09-04"),
}
DONE = {"SCT-15", "COM-10", "WPT-15"}


def friday_between(a, b):
    days = (b - a).days
    d = a + timedelta(days=rng.randint(0, days))
    return d + timedelta(days=(4 - d.weekday()) % 7)


def build_truth():
    progs = {p["id"]: p for p in programs()}
    ids = list(progs)
    edges = [(d, u) for d, u, _ in DEPENDENCIES]
    ups = {i: [u for d, u in edges if d == i] for i in ids}
    from pipeline.rubric import topo_order
    for pid in topo_order(set(ids), edges):
        p = progs[pid]
        pl = PLANTED.get(pid, {})
        p["owner"] = rng.choice(PEOPLE[p["team"]])
        earliest = date(2026, 10, 9)
        for u in ups[pid]:
            t = progs[u].get("target")
            if t:
                earliest = max(earliest, D(t) + timedelta(days=14))
        base = friday_between(earliest, max(earliest, date(2027, 3, 26)))
        r = rng.random()
        slip = 0 if r < .72 else rng.choice([7, 14, 21, 28]) if r < .92 else rng.choice([35, 42, 49])
        p["baseline"], p["target"] = base.isoformat(), (base + timedelta(days=slip)).isoformat()
        p["last_update"] = (AS_OF - timedelta(days=rng.randint(1, 9) if rng.random() < .95 else rng.randint(16, 30))).isoformat()
        p["blocker_text"] = p["blocker_since"] = None
        if rng.random() < .10:
            p["blocker_text"] = rng.choice(BLOCKERS)
            p["blocker_since"] = (AS_OF - timedelta(days=rng.randint(2, 12))).isoformat()
        p["signals"], p["done"] = [], pid in DONE
        # planted overrides
        if "owner" in pl: p["owner"] = pl["owner"]
        if "baseline" in pl: p["baseline"] = pl["baseline"]
        if "target" in pl: p["target"] = pl["target"]
        if "last" in pl: p["last_update"] = pl["last"]
        if "blocker" in pl: p["blocker_text"], p["blocker_since"] = pl["blocker"]
        if "signal" in pl: p["signals"] = [pl["signal"]]
        if p["team"] == "EAI":  # this team only updates at steering meetings
            p["last_update"] = "2026-09-10" if p["last_update"] < "2026-09-17" else "2026-09-24"
        if p["done"]:
            p["target"] = p["baseline"] = (AS_OF - timedelta(days=rng.randint(10, 40))).isoformat()
            p["blocker_text"] = p["blocker_since"] = None

    result = assess(progs, edges, FREEZES, AS_OF)
    for pid, p in progs.items():
        p["health"] = result[pid]["health"]
        p["reasons"] = [r["rule"] for r in result[pid]["reasons"]]
        pl = PLANTED.get(pid, {})
        if "self" in pl:
            p["self_status"] = pl["self"]
        elif p["done"]:
            p["self_status"] = "done"
        else:  # teams report optimistically
            x = rng.random()
            p["self_status"] = {"green": "green" if x < .95 else "amber",
                                "amber": "green" if x < .5 else "amber",
                                "red": "green" if x < .3 else "amber" if x < .8 else "red"}[p["health"]]
        if TEAM_SOURCE[p["team"]] == "slack" and not p["done"]:
            p["self_status"] = None  # nobody states a RAG in chat
    return progs


# ---------------------------------------------------------------- formatters
def jira_date(s):  return datetime.fromisoformat(s).strftime("%d/%b/%y 12:00 AM") if s else ""
def us(s):         return f"{D(s).month}/{D(s).day}/{D(s).year}" if s else ""
def short(s):      return f"{D(s).month}/{D(s).day}"
def mon(s):        return D(s).strftime("%b ") + str(D(s).day)
def name_of(progs, i): return progs[i]["name"]
def first(n):      return n.split()[0] if n else None


def write_jira(progs):
    rows = [p for p in progs.values() if p["team"] == "ERP"]
    key = {p["id"]: f"FIN-{110 + 7 * n}" for n, p in enumerate(rows)}
    status_map = {"green": "On Track", "amber": "At Risk", "red": "Off Track", "done": "Done", None: ""}
    path = SRC / "erp" / "jira_epics_export.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Issue key", "Issue Type", "Summary", "Status", "Assignee", "Custom field (Health)",
                    "Due date", "Custom field (Baseline Due)", "Updated", "Inward issue link (Blocks)",
                    "Custom field (External Dependency)", "Custom field (Blocker)", "Custom field (Blocked Since)",
                    "Description"])
        for p in rows:
            internal = [key[u] for d, u, where in DEPENDENCIES if d == p["id"] and where == "jira" and u in key]
            external = [name_of(progs, u) for d, u, where in DEPENDENCIES if d == p["id"] and where == "jira" and u not in key]
            wf = "Done" if p["done"] else ("Blocked" if p["blocker_text"] else rng.choice(["In Progress", "In Progress", "In Progress", "To Do"]))
            upd = datetime.fromisoformat(p["last_update"]).replace(hour=rng.randint(8, 18), minute=rng.randint(0, 59))
            w.writerow([key[p["id"]], "Epic", p["name"], wf, p["owner"] or "Unassigned",
                        status_map[p["self_status"]], jira_date(p["target"]), jira_date(p["baseline"]),
                        upd.strftime("%d/%b/%y %-I:%M %p"), ", ".join(internal), "; ".join(external),
                        p["blocker_text"] or "", jira_date(p["blocker_since"]),
                        f"h2. Why\n{p['why']}.\n\nh2. Scope\nSee linked stories."])
    return {p["id"]: key[p["id"]] for p in rows}


def write_sheet(progs):
    rows = [p for p in progs.values() if p["team"] == "SCT"]
    rag = {"green": "G", "amber": "Y", "red": "R", "done": "Complete", None: ""}
    path = SRC / "supply_chain" / "sct_program_tracker.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Project", "Lead", "RAG", "Go-live (plan)", "Go-live (orig)", "Last touched",
                    "Depends on", "Business value", "Notes"])
        for p in rows:
            deps = [f"{name_of(progs, u)} ({progs[u]['team']})" if progs[u]["team"] != "SCT" else name_of(progs, u)
                    for d, u, where in DEPENDENCIES if d == p["id"] and where == "sheet"]
            notes = []
            if p["blocker_text"]:
                notes.append(f"Blocked: {p['blocker_text'][0].lower() + p['blocker_text'][1:]} (since {short(p['blocker_since'])})")
            notes.append(rng.choice(["weekly sync w/ vendor", "", "scope frozen", "UAT planning", "see deck"]))
            w.writerow([p["name"], p["owner"] or "TBD", rag[p["self_status"]], us(p["target"]), us(p["baseline"]),
                        us(p["last_update"]), "; ".join(deps), p["why"], ". ".join(n for n in notes if n)])
    return {p["id"]: p["name"] for p in rows}


def write_confluence(progs):
    icon = {"green": "🟢 On track", "amber": "🟡 At risk", "red": "🔴 Off track", "done": "✅ Complete", None: "Not set"}
    out = {}
    folder = SRC / "commercial" / "confluence"
    folder.mkdir(parents=True, exist_ok=True)
    for p in [p for p in progs.values() if p["team"] == "COM"]:
        slug = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
        deps = [f"- {name_of(progs, u)} ({TEAMS[progs[u]['team']]})"
                for d, u, where in DEPENDENCIES if d == p["id"] and where == "confluence"]
        blk = f"- {p['blocker_text']} (raised {p['blocker_since']})" if p["blocker_text"] else "- None"
        md = f"""# {p['name']}

| Field | Value |
|---|---|
| Owner | {p['owner'] or ''} |
| Status | {icon[p['self_status']]} |
| Target date | {p['target'] or 'TBD'} |
| Baseline date | {p['baseline'] or 'TBD'} |
| Last updated | {p['last_update']} |

## Why it matters
{p['why']}.

## Dependencies
{chr(10).join(deps) if deps else '- None'}

## Blockers
{blk}

## Notes
{rng.choice(['Weekly working session on Tuesdays.', 'Design review complete.', 'Vendor demo scheduled.', 'Requirements signed off by business owner.'])}
"""
        (folder / f"{slug}.md").write_text(md)
        out[p["id"]] = f"{slug}.md"
    return out


def write_status_doc(progs):
    stat = {"green": "Green", "amber": "Yellow", "red": "Red", "done": "Done", None: "n/a"}
    lines = ["# CX Technology: weekly status", "", "Week ending Friday 9/25. Owners update their own section.", ""]
    out = {}
    for p in [p for p in progs.values() if p["team"] == "CX"]:
        t = mon(p["target"]) if p["target"] else "TBD"
        if p["baseline"] and p["target"] != p["baseline"]:
            t += f" (was {mon(p['baseline'])})"
        deps = [name_of(progs, u) for d, u, where in DEPENDENCIES if d == p["id"] and where == "status_doc"]
        lines += [f"## {p['name']}",
                  f"Owner: {p['owner']} · Status: {stat[p['self_status']]} · Target: {t} · Updated {short(p['last_update'])}",
                  f"Why: {p['why']}.",
                  f"Depends on: {', '.join(deps) if deps else 'none'}",
                  f"Blocker: {p['blocker_text'] + ' (since ' + short(p['blocker_since']) + ')' if p['blocker_text'] else 'none'}",
                  ""]
        out[p["id"]] = p["name"]
    path = SRC / "cx" / "cx_weekly_status_2026-09-25.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    return out


def ts(day, hour=None):
    h = hour if hour is not None else rng.randint(8, 17)
    return datetime.fromisoformat(day).replace(hour=h, minute=rng.randint(0, 59)).isoformat()


def write_slack(progs):
    msgs = []
    others = PEOPLE["WPT"] + ["Jess Moreau"]
    alias = {i: p["alias"] for i, p in progs.items()}
    for p in [p for p in progs.values() if p["team"] == "WPT"]:
        a, owner = alias[p["id"]], p["owner"]
        last = D(p["last_update"])
        days = sorted({(last - timedelta(days=rng.randint(3, 20))).isoformat() for _ in range(2)}) + [p["last_update"]]
        thread = []
        if owner:
            thread.append((owner, rng.choice([f"I'm driving {a} from here on, ping me with anything.",
                                              f"Picking up {a}. I'll own it going forward.",
                                              f"Quick {a} kickoff notes: I'm the owner, weekly updates here."])))
        else:
            thread.append((rng.choice(PEOPLE["WPT"]), f"Does anyone own {a} now that Jess moved teams? Nobody's picked it up."))
        if rng.random() < .6:
            thread.append((owner or rng.choice(others), f"Reminder of why {a} matters: {p['why'][0].lower() + p['why'][1:]}."))
        if p["done"]:
            thread.append((owner or rng.choice(others), f"{a} is done 🎉 closed out on {short(p['target'])}."))
        elif p["target"] and p["target"] != p["baseline"]:
            thread.append((owner or rng.choice(others), f"{a}: moving the target to {short(p['target'])} (was {short(p['baseline'])}). Will explain in the weekly."))
        elif p["target"]:
            thread.append((owner or rng.choice(others), rng.choice([f"{a} still on track for {mon(p['target'])}.",
                                                                    f"{a} is holding {short(p['target'])} as the go-live."])))
        else:
            thread.append((owner or rng.choice(others), f"No date for {a} yet, still scoping."))
        if p["blocker_text"]:
            thread.append((owner or rng.choice(others), f"{a} is still blocked: {p['blocker_text']}. Been waiting since {short(p['blocker_since'])}."))
        for d, u, where in DEPENDENCIES:
            if d == p["id"] and where == "slack" and progs[u]["team"] == "WPT":
                thread.append((owner or rng.choice(others), f"FYI {a} can't start its pilot until {alias[u]} is live."))
        # the last message lands on the last-update date; earlier ones before it
        stamps = [days[min(n, len(days) - 1)] for n in range(len(thread) - 1)] + [p["last_update"]]
        stamps = sorted(stamps)
        for (user, text), day in zip(thread, stamps):
            msgs.append({"channel": "#wpt-projects", "user": user, "ts": ts(day), "text": text})
    noise = [("Hannah Lee", "Who took the spare USB-C dock from the 3rd floor closet?"),
             ("Marco Rossi", "Okta had a 10 min blip this morning, resolved."),
             ("Chris Duarte", "Reminder: change freeze calendar is pinned in #it-leads."),
             ("Jess Moreau", "Farewell cake at 3 👋")]
    for user, text in noise:
        msgs.append({"channel": "#wpt-projects", "user": user, "ts": ts((AS_OF - timedelta(days=rng.randint(1, 20))).isoformat()), "text": text})
    # cross-team chatter: this is where hidden coupling and contradicting signals live
    leads = [
        ("Owen Hughes", "2026-09-22", "Heads up from the warranty sync: the serialization vendor says their API won't be ready until mid-November, about 3 weeks late. Supply chain tracker still shows it green."),
        ("Priya Natarajan", "2026-09-18", "For the APAC BPO go-live on 11/2 we're counting on JML to create the agents' accounts. No JML, no agents on the phones."),
        ("Grace Okafor", "2026-09-16", "Auditors will test leaver deprovisioning in December. Our SOX ITGC remediation assumes JML is automating it by then."),
        ("Mei Tanaka", "2026-09-21", "EU 3PL integration is being built on the new iPaaS connectors, not the legacy ones, so we need iPaaS before we can go live."),
        ("Marcus Bell", "2026-09-24", "iPaaS vendor amendment is still with procurement. Anyone have a contact there who can expedite?"),
        ("Nina Petrova", "2026-09-23", "Reminder that peak-season freeze for commerce is 11/16 to 12/1."),
        ("Rahul Mehta", "2026-09-17", "Year-end close freeze for ERP is 12/18 to 1/8 as usual."),
        ("Sofia Lindqvist", "2026-09-15", "Anyone else seeing slow Jira this week?"),
    ]
    for user, day, text in leads:
        msgs.append({"channel": "#it-leads", "user": user, "ts": ts(day), "text": text})
    msgs.sort(key=lambda m: m["ts"])
    path = SRC / "workplace" / "slack_export.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(msgs, indent=1, ensure_ascii=False))


def write_steering(progs):
    stat = {"green": "Green", "amber": "Amber", "red": "Red", "done": "Closed", None: "not given"}
    alias = {i: p["alias"] for i, p in progs.items()}
    eai = [p for p in progs.values() if p["team"] == "EAI"]
    meetings = {"2026-09-10": [], "2026-09-24": []}
    for p in eai:
        meetings["2026-09-10" if p["last_update"] < "2026-09-17" else "2026-09-24"].append(p)
    extra = {  # hidden, cross-team couplings stated only in these notes
        "EAI-01": "Reminder: the ERP go-live (Nov 2) can't happen before the iPaaS cutover. All bank and 3PL integrations route through it.",
        "EAI-03": "The ERP team needs clean product master data before their go-live, and customs automation classifies from it.",
        "EAI-15": "Finance's multi-entity consolidation for the new EU entity is waiting on this reference architecture.",
        "EAI-16": "Invoice capture from this feeds Procure-to-pay automation on the ERP side.",
        "EAI-02": "Finance's reporting data mart will be built on the new EDW.",
    }
    for day, items in meetings.items():
        lines = [f"# EA & AI steering committee, {day}", "",
                 "Attendees: Marcus Bell, Sofia Lindqvist, Arjun Rao, Elena Voss, CIO office", "", "## Program round-robin", ""]
        for p in items:
            a = alias[p["id"]]
            s = [f"**{a}** ({p['owner']}). Status: {stat[p['self_status']]}."]
            if p["done"]:
                s.append("Closed out; benefits tracking handed to the business.")
            elif not p["target"]:
                s.append("No date agreed yet; still in discovery.")
            elif p["target"] != p["baseline"]:
                s.append(rng.choice([f"Target moved to {mon(p['target'])} from {mon(p['baseline'])}.",
                                     f"Committee accepted a new date of {mon(p['target'])} (baseline was {mon(p['baseline'])})."]))
            else:
                s.append(rng.choice([f"Holding {mon(p['target'])}.", f"On plan for {mon(p['target'])}."]))
            if p["blocker_text"]:
                s.append(f"Blocker: {p['blocker_text']}, open since {short(p['blocker_since'])}.")
            for d, u, where in DEPENDENCIES:
                if d == p["id"] and where == "steering" and progs[u]["team"] == "EAI":
                    s.append(f"Can't go to production until {alias[u]} is live.")
                if d == p["id"] and where == "steering" and progs[u]["team"] == "WPT":
                    s.append(f"Blocked in practice until Workplace's JML automation ships; accounts are provisioned by it.")
            if p["id"] in extra:
                s.append(extra[p["id"]])
            if rng.random() < .7:
                s.append(f"Why: {p['why']}.")
            lines += [" ".join(s), ""]
        lines += ["## Decisions", "", "- None recorded." if day == "2026-09-10" else "- Escalate the iPaaS contract amendment to the CFO's office if unsigned by 10/2.", "",
                  "## Actions", "", "- Marcus to chase Procurement on the iPaaS amendment." if day == "2026-09-24" else "- Elena to circulate AI gateway policy draft.", ""]
        path = SRC / "enterprise_arch" / f"ea_steering_notes_{day}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines))


def main():
    progs = build_truth()
    keys = {}
    keys.update(write_jira(progs)); keys.update(write_sheet(progs)); keys.update(write_confluence(progs))
    keys.update(write_status_doc(progs)); write_slack(progs); write_steering(progs)
    with open(SRC / "catalog.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "team", "team_name", "tier", "source", "source_key"])
        for p in progs.values():
            w.writerow([p["id"], p["name"], p["team"], TEAMS[p["team"]], p["tier"], TEAM_SOURCE[p["team"]], keys.get(p["id"], "")])
    (SRC / "freeze_calendar.json").write_text(json.dumps(FREEZES, indent=1))
    GT.mkdir(exist_ok=True)
    truth = {"as_of": AS_OF.isoformat(), "programs": list(progs.values()),
             "dependencies": [{"downstream": d, "upstream": u, "recorded_in": w} for d, u, w in DEPENDENCIES],
             "planted": sorted(PLANTED)}
    (GT / "truth.json").write_text(json.dumps(truth, indent=1, ensure_ascii=False))
    from collections import Counter
    print("truth health:", Counter(p["health"] for p in progs.values()))
    print("self-reported:", Counter(p["self_status"] for p in progs.values()))


if __name__ == "__main__":
    main()
