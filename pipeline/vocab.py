"""Shared vocabulary: one status scale, and one way to match a name to a program."""
import csv, re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "sources"

# Six teams, six ways to say "fine". This table is the translation.
STATUS_MAP = {
    "green": "green", "g": "green", "on track": "green", "🟢 on track": "green",
    "amber": "amber", "yellow": "amber", "y": "amber", "at risk": "amber", "🟡 at risk": "amber",
    "red": "red", "r": "red", "off track": "red", "🔴 off track": "red",
    "done": "done", "complete": "done", "closed": "done", "✅ complete": "done",
}


def normalize_status(raw):
    return STATUS_MAP.get((raw or "").strip().lower())


def load_catalog():
    with open(SRC / "catalog.csv") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["tier"] = int(r["tier"])
    return rows


class Resolver:
    """Exact, case-insensitive name matching, with an optional '(team)' suffix.
    Nicknames ('JML', 'the ERP go-live') are deliberately NOT handled here;
    resolving those takes context, which is the job given to the model."""

    def __init__(self, catalog):
        self.by_name = {c["name"].lower(): c["id"] for c in catalog}

    def resolve(self, text):
        t = (text or "").strip().lower()
        if not t:
            return None
        if t in self.by_name:
            return self.by_name[t]
        stripped = re.sub(r"\s*\([^)]*\)\s*$", "", t)
        return self.by_name.get(stripped)
