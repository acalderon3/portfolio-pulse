"""The shared definition of program health. One definition, applied to every team.

Health is computed from evidence, never copied from what a team reports. Each rule
records why it fired, so every Amber or Red can be traced to a fact and its source.
The thresholds live here, in one place, so changing them is a reviewed decision.
"""
from datetime import date, timedelta

THRESHOLDS = {
    "stale_days": 14,        # no update in more than this -> Amber (can't verify)
    "blocker_amber_days": 5,
    "blocker_red_days": 14,
    "slip_amber_days": 30,   # current target vs baseline
    "slip_red_days": 60,
}

RULES = [
    # id, level, plain-English definition (shown in the demo)
    ("past_due", "red", "Target date has passed and the program isn't done."),
    ("blocker_age", "red", "A blocker has been open for more than 14 days."),
    ("dependency_late", "red", "An upstream program is forecast to finish after this program's target date."),
    ("slip", "red", "Target has slipped more than 60 days from baseline."),
    ("blocker_age", "amber", "A blocker has been open for 5 to 14 days."),
    ("slip", "amber", "Target has slipped 31 to 60 days from baseline."),
    ("upstream_red", "amber", "Depends on a program that is Red."),
    ("in_freeze", "amber", "Target date falls inside the team's change freeze."),
    ("conflicting_signal", "amber", "Another source contradicts the reported status. Confirm with the owner."),
    ("stale", "amber", "No update in more than 14 days, so the status can't be verified."),
    ("missing_basics", "amber", "No named owner or no target date."),
]

LEVEL = {"green": 0, "amber": 1, "red": 2}


def _d(x):
    if x is None or isinstance(x, date):
        return x
    return date.fromisoformat(x)


def topo_order(ids, edges):
    """edges: list of (downstream, upstream). Returns ids with upstreams first."""
    ups = {i: [u for d, u in edges if d == i and u in ids] for i in ids}
    seen, order = set(), []

    def visit(i, stack=()):
        if i in seen:
            return
        if i in stack:
            raise ValueError(f"dependency cycle through {i}")
        for u in ups[i]:
            visit(u, stack + (i,))
        seen.add(i)
        order.append(i)

    for i in sorted(ids):
        visit(i)
    return order


def assess(programs, edges, freezes, as_of):
    """programs: {id: features}. Features: team, owner, target, baseline, last_update,
    blocker_text, blocker_since, done, signals (list of conflict strings).
    Returns {id: {"health", "reasons", "forecast"}}."""
    as_of = _d(as_of)
    out = {}
    for pid in topo_order(set(programs), edges):
        p = programs[pid]
        if p.get("done"):
            out[pid] = {"health": "done", "reasons": [], "forecast": _d(p.get("target"))}
            continue
        reasons = []

        def fire(rule, level, detail):
            reasons.append({"rule": rule, "level": level, "detail": detail})

        target, baseline = _d(p.get("target")), _d(p.get("baseline"))
        last, since = _d(p.get("last_update")), _d(p.get("blocker_since"))

        if target and target < as_of:
            fire("past_due", "red", f"Target {target} passed {(as_of - target).days} days ago.")
        if p.get("blocker_text"):
            age = (as_of - since).days if since else None
            if age is None:
                fire("blocker_age", "amber", f"Open blocker (start date unknown): {p['blocker_text']}")
            elif age > THRESHOLDS["blocker_red_days"]:
                fire("blocker_age", "red", f"Blocked {age} days: {p['blocker_text']}")
            elif age >= THRESHOLDS["blocker_amber_days"]:
                fire("blocker_age", "amber", f"Blocked {age} days: {p['blocker_text']}")
        if target and baseline:
            slip = (target - baseline).days
            if slip > THRESHOLDS["slip_red_days"]:
                fire("slip", "red", f"Slipped {slip} days (baseline {baseline}).")
            elif slip > THRESHOLDS["slip_amber_days"]:
                fire("slip", "amber", f"Slipped {slip} days (baseline {baseline}).")
        if last is None or (as_of - last).days > THRESHOLDS["stale_days"]:
            fire("stale", "amber", "No recorded update." if last is None else f"Last update {last} ({(as_of - last).days} days ago).")
        if not p.get("owner") or not target:
            missing = [n for n, v in (("owner", p.get("owner")), ("target date", target)) if not v]
            fire("missing_basics", "amber", "Missing " + " and ".join(missing) + ".")
        for f in freezes:
            if f["team"] == p["team"] and target and _d(f["start"]) <= target <= _d(f["end"]):
                fire("in_freeze", "amber", f"Target {target} is inside the {f['name']} ({f['start']} to {f['end']}).")
        for s in p.get("signals", []):
            fire("conflicting_signal", "amber", s)

        forecast = target
        for d, u in edges:
            if d != pid or u not in out:
                continue
            up = out[u]
            if up["health"] == "done":
                continue
            if up["health"] == "red":
                fire("upstream_red", "amber", f"Depends on {u}, which is Red.")
            if target and up["forecast"] and up["forecast"] > target:
                fire("dependency_late", "red", f"{u} is forecast to finish {up['forecast']}, after this target ({target}).")
            if forecast and up["forecast"] and up["forecast"] > forecast:
                forecast = up["forecast"]  # can't finish before what it depends on

        health = max((r["level"] for r in reasons), key=LEVEL.get, default="green")
        out[pid] = {"health": health, "reasons": reasons, "forecast": forecast}
    return out


def rubric_doc():
    return {"thresholds": THRESHOLDS,
            "rules": [{"rule": r, "level": l, "definition": d} for r, l, d in RULES]}
