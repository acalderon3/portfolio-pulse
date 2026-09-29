"""AI extraction for the two sources that have no fields: chat and meeting notes.

Backends:
  cache   (default) replay the recorded model output in pipeline/cache/. Free, offline,
          reproducible. This is what the public demo runs on.
  claude  call the Anthropic API with prompts/extract_unstructured.md and re-record the
          cache. Needs ANTHROPIC_API_KEY and `pip install anthropic`.

Either way, the output goes through a grounding check. Every extracted value must come
with a verbatim quote that exists in the source, or the value is dropped.

  python -m pipeline.extract --backend claude      # re-record with the live model
"""
import argparse, hashlib, json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

from .vocab import SRC, load_catalog, normalize_status

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "pipeline" / "cache"
PROMPT = ROOT / "prompts" / "extract_unstructured.md"
MODEL = os.environ.get("PORTFOLIO_MODEL", "claude-opus-5-5")
AS_OF = "2026-09-28"

UNITS = {
    "workplace_slack": {"team": "WPT", "files": ["workplace/slack_export.json"]},
    "ea_steering": {"team": "EAI", "files": ["enterprise_arch/ea_steering_notes_2026-09-10.md",
                                              "enterprise_arch/ea_steering_notes_2026-09-24.md"]},
}

_date = {"type": ["string", "null"], "description": "YYYY-MM-DD"}
TOOL = {
    "name": "record_extraction",
    "description": "Record the structured extraction for this source.",
    "input_schema": {
        "type": "object", "required": ["programs", "dependencies", "signals"],
        "properties": {
            "programs": {"type": "array", "items": {"type": "object", "required": ["program_id", "quotes"], "properties": {
                "program_id": {"type": "string"}, "owner": {"type": ["string", "null"]},
                "reported_status": {"type": ["string", "null"]}, "target_date": _date, "baseline_date": _date,
                "last_update": _date, "blocker": {"type": ["string", "null"]}, "blocker_since": _date,
                "why": {"type": ["string", "null"]}, "done": {"type": "boolean"},
                "quotes": {"type": "object", "additionalProperties": {"type": "string"}}}}},
            "dependencies": {"type": "array", "items": {"type": "object", "required": ["downstream_id", "upstream_id", "quote"],
                "properties": {"downstream_id": {"type": "string"}, "upstream_id": {"type": "string"}, "quote": {"type": "string"}}}},
            "signals": {"type": "array", "items": {"type": "object", "required": ["program_id", "kind", "summary", "quote"],
                "properties": {"program_id": {"type": "string"}, "kind": {"enum": ["contradicts_reported_status", "schedule_risk"]},
                               "summary": {"type": "string"}, "quote": {"type": "string"}}}},
        },
    },
}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def source_text(unit):
    parts = []
    for f in UNITS[unit]["files"]:
        raw = (SRC / f).read_text()
        if f.endswith(".json"):  # flatten chat export into readable lines
            raw = "\n".join(f"[{m['ts'][:16].replace('T', ' ')}] {m['channel']} {m['user']}: {m['text']}" for m in json.loads(raw))
        parts.append(f"=== FILE: {f} ===\n{raw}")
    return "\n\n".join(parts)


def user_message(unit, catalog):
    cat = "\n".join(f"{c['id']} | {c['name']} | {c['team']}" for c in catalog)
    return f"AS_OF: {AS_OF}\nTEAM: {UNITS[unit]['team']}\n\nCATALOG:\n{cat}\n\nSOURCE:\n{source_text(unit)}"


def run_claude(unit, catalog):
    import anthropic  # optional dependency, only for re-recording
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=MODEL, max_tokens=16000, system=PROMPT.read_text(), tools=[TOOL],
        tool_choice={"type": "tool", "name": TOOL["name"]},
        messages=[{"role": "user", "content": user_message(unit, catalog)}])
    block = next(b for b in resp.content if b.type == "tool_use")
    return {"meta": {"model": resp.model, "recorded_via": "Anthropic API (pipeline/extract.py)",
                     "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "prompt_sha": sha(PROMPT.read_text()), "source_sha": sha(source_text(unit)),
                     "usage": {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}},
            "output": block.input}


def load_cache(unit):
    path = CACHE / f"{unit}.json"
    data = json.loads(path.read_text())
    stale = []
    if data["meta"]["source_sha"] != sha(source_text(unit)):
        stale.append("source files changed since recording")
    if data["meta"]["prompt_sha"] != sha(PROMPT.read_text()):
        stale.append("prompt changed since recording")
    data["meta"]["stale"] = stale
    if stale:
        print(f"WARNING {unit}: {', '.join(stale)}. Re-record with --backend claude.", file=sys.stderr)
    return data


# ------------------------------------------------------------------ grounding
def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def locate(unit, quote):
    """Find a quote in the source; return a human-readable locator or None."""
    q = _norm(quote)
    if not q:
        return None
    for f in UNITS[unit]["files"]:
        raw = (SRC / f).read_text()
        if f.endswith(".json"):
            for m in json.loads(raw):
                line = f"[{m['ts'][:16].replace('T', ' ')}] {m['channel']} {m['user']}: {m['text']}"
                if q in _norm(line):
                    return f, f"{m['channel']} · {m['user']} · {m['ts'][:16].replace('T', ' ')}"
        else:
            for n, line in enumerate(raw.splitlines(), 1):
                if q in _norm(line):
                    return f, f"line {n}"
    return None


MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _value_check(field, rec, quote, hit):
    """The quote must exist AND support the value. A date must appear in its quote;
    a last-update date must match the timestamp of the message or meeting quoted."""
    def mentions(iso):
        y, m, d = map(int, iso.split("-"))
        return re.search(rf"(?<!\d){m}/{d}(?!\d)|{MON[m - 1]}\w* {d}(?!\d)|{iso}", quote) is not None
    if field in ("target", "baseline") and rec.get(field) and not mentions(rec[field]):
        return f"{field} {rec[field]} does not appear in its quote"
    if field == "blocker" and rec.get("blocker_since") and not mentions(rec["blocker_since"]):
        return f"blocker start {rec['blocker_since']} does not appear in its quote"
    if field == "last_update":
        stamp = re.search(r"\d{4}-\d\d-\d\d", hit[1]) or re.search(r"\d{4}-\d\d-\d\d", hit[0])
        if stamp and stamp.group(0) != rec["last_update"]:
            return f"last update {rec['last_update']} does not match the quoted item's date {stamp.group(0)}"
    return None


FIELD_QUOTE = {"owner": "owner", "self_status": "reported_status", "target": "target_date",
               "baseline": "baseline_date", "last_update": "last_update", "blocker": "blocker", "why": "why"}


def to_records(unit, data, catalog):
    """Grounding-check the model output and convert it to pipeline records."""
    ids = {c["id"] for c in catalog}
    out = data["output"]
    records, deps, signals, failures = {}, [], [], []
    for p in out["programs"]:
        pid = p["program_id"]
        if pid not in ids:
            failures.append({"program_id": pid, "field": "program_id", "problem": "not in catalog"})
            continue
        q = p.get("quotes", {})
        rec = {"owner": p.get("owner"), "self_status": normalize_status(p.get("reported_status")),
               "target": p.get("target_date"), "baseline": p.get("baseline_date"),
               "last_update": p.get("last_update"), "blocker_text": p.get("blocker"),
               "blocker_since": p.get("blocker_since"), "why": p.get("why"), "done": bool(p.get("done")),
               "depends_on": [], "evidence": {}}
        for field, qkey in FIELD_QUOTE.items():
            has_value = rec.get("blocker_text" if field == "blocker" else field)
            if not has_value:
                continue
            quote = q.get(qkey) or q.get(field)
            hit = locate(unit, quote) if quote else None
            if not hit:
                failures.append({"program_id": pid, "field": field, "problem": "no quote" if not quote else "quote not found in source",
                                 "quote": quote})
                if field == "blocker":
                    rec["blocker_text"] = rec["blocker_since"] = None
                elif field == "baseline" and quote is None and rec["baseline"] == rec["target"]:
                    rec["evidence"]["baseline"] = rec["evidence"].get("target")  # 'no earlier date' is allowed
                    continue
                else:
                    rec[field] = None
                continue
            problem = _value_check(field, rec, quote, hit)
            if problem:
                failures.append({"program_id": pid, "field": field, "problem": problem, "quote": quote})
                rec["blocker_since" if field == "blocker" else field] = None
                continue
            rec["evidence"][field] = {"source": hit[0], "locator": hit[1], "quote": quote, "by": "model"}
        records[pid] = rec
    for d in out["dependencies"]:
        hit = locate(unit, d["quote"])
        if d["downstream_id"] in ids and d["upstream_id"] in ids and hit:
            deps.append({**d, "source": hit[0], "locator": hit[1]})
        else:
            failures.append({"program_id": d["downstream_id"], "field": "dependency", "problem": "ungrounded or unknown id", "quote": d["quote"]})
    for s in out["signals"]:
        hit = locate(unit, s["quote"])
        if s["program_id"] in ids and hit:
            signals.append({**s, "source": hit[0], "locator": hit[1]})
        else:
            failures.append({"program_id": s["program_id"], "field": "signal", "problem": "ungrounded or unknown id", "quote": s["quote"]})
    return records, deps, signals, failures


def extract_all(catalog, backend="cache"):
    result = {"records": {}, "dependencies": [], "signals": [], "grounding_failures": [], "runs": {}}
    for unit in UNITS:
        if backend == "claude":
            data = run_claude(unit, catalog)
            CACHE.mkdir(exist_ok=True)
            (CACHE / f"{unit}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
        else:
            data = load_cache(unit)
        recs, deps, sigs, fails = to_records(unit, data, catalog)
        team = UNITS[unit]["team"]
        result["records"].update({k: v for k, v in recs.items() if k.startswith(team + "-")})
        result["dependencies"] += deps
        result["signals"] += sigs
        result["grounding_failures"] += fails
        result["runs"][unit] = data["meta"]
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["cache", "claude"], default="cache")
    ap.add_argument("--print-input", metavar="UNIT", help="print the exact model input for a unit and exit")
    a = ap.parse_args()
    cat = load_catalog()
    if a.print_input:
        print(user_message(a.print_input, cat)); sys.exit()
    r = extract_all(cat, a.backend)
    print(json.dumps({"records": len(r["records"]), "dependencies": len(r["dependencies"]),
                      "signals": len(r["signals"]), "grounding_failures": r["grounding_failures"]}, indent=1))
