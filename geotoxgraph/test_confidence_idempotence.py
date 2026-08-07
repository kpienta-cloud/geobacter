"""CI equality test: every stored contrast-layer score and flag must equal
what build_confidence_and_summary.py computes from the current row.

Runs as part of the release CI gate. Failing this test blocks release.
Exit code 0 on match, 1 on mismatch.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from build_confidence_and_summary import confidence_and_flags


def main() -> int:
    fpath = HERE / "evolutionary_contrast_edges.csv"
    with open(fpath, newline="") as f:
        rows = list(csv.DictReader(f))

    diffs = []
    for r in rows:
        new_score, new_flags = confidence_and_flags(r)
        if r.get("confidence_score") != new_score:
            diffs.append((r["edge_id"], "confidence_score", r.get("confidence_score"), new_score))
        if r.get("overclaim_flags") != new_flags:
            diffs.append((r["edge_id"], "overclaim_flags", r.get("overclaim_flags"), new_flags))

    if diffs:
        print(f"FAIL: {len(diffs)} stored values disagree with rubric regeneration.")
        for eid, field, stored, computed in diffs[:15]:
            print(f"  {eid} {field}: stored={stored!r} computed={computed!r}")
        if len(diffs) > 15:
            print(f"  ... {len(diffs) - 15} more")
        print("\nRerun `python3 regenerate_confidence_columns.py` and commit the result.")
        return 1

    print(f"PASS: all {len(rows)} stored values match rubric regeneration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
