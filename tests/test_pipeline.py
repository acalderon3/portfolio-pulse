"""Run with:  python -m pytest -q   (or  python tests/test_pipeline.py)"""
import copy, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline.extract import load_cache, to_records  # noqa: E402
from pipeline.rubric import assess  # noqa: E402
from pipeline.vocab import load_catalog  # noqa: E402

CAT = load_catalog()


def _one(unit, pid):
    data = copy.deepcopy(load_cache(unit))
    data["output"]["programs"] = [p for p in data["output"]["programs"] if p["program_id"] == pid]
    data["output"]["dependencies"], data["output"]["signals"] = [], []
    return data


def test_invented_quote_is_dropped():
    data = _one("workplace_slack", "WPT-01")
    data["output"]["programs"][0]["quotes"]["owner"] = "Hannah is driving JML now."  # never said
    recs, _, _, fails = to_records("workplace_slack", data, CAT)
    assert recs["WPT-01"]["owner"] is None
    assert any(f["field"] == "owner" and "not found" in f["problem"] for f in fails)


def test_date_must_appear_in_its_quote():
    data = _one("workplace_slack", "WPT-01")
    data["output"]["programs"][0]["target_date"] = "2026-10-30"  # quote says 11/13
    recs, _, _, fails = to_records("workplace_slack", data, CAT)
    assert recs["WPT-01"]["target"] is None
    assert any("does not appear" in f["problem"] for f in fails)


def test_unknown_program_id_is_rejected():
    data = _one("ea_steering", "EAI-01")
    data["output"]["programs"][0]["program_id"] = "EAI-99"
    recs, _, _, fails = to_records("ea_steering", data, CAT)
    assert "EAI-99" not in recs and fails[0]["problem"] == "not in catalog"


def test_rubric_red_propagates_through_dependency():
    base = dict(team="ERP", owner="x", last_update="2026-09-27", baseline=None, blocker_text=None, blocker_since=None)
    progs = {"UP": {**base, "target": "2026-12-11", "blocker_text": "contract", "blocker_since": "2026-09-01"},
             "DOWN": {**base, "target": "2026-11-02"}}
    out = assess(progs, [("DOWN", "UP")], [], "2026-09-28")
    assert out["UP"]["health"] == "red"
    assert out["DOWN"]["health"] == "red"
    assert {r["rule"] for r in out["DOWN"]["reasons"]} == {"upstream_red", "dependency_late"}


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
