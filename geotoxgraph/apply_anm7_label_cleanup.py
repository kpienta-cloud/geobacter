"""Clean up stale 'ANM-7' text in labels, descriptions, and notes.

After the id-level rename from strain:rho_anm7 to strain:rho_rha1, several
gene/compound labels and CAVEAT notes still refer to 'ANM-7' or contain the
audit's now-obsolete recommendation to rename to RHA1 (which we have now
done). This script does a targeted find-and-replace on those free-text
fields only, keyed to the affected row ids so it can't drift.
"""
from __future__ import annotations
import argparse
import csv
import re
from pathlib import Path

HERE = Path(__file__).parent

FILES = {
    "geotoxgraph_nodes.csv": ("id", ["label", "description"]),
    "geotoxgraph_edges.csv": ("edge_id", ["notes"]),
    "evolutionary_contrast_nodes.csv": ("id", ["label", "description"]),
    "evolutionary_contrast_edges.csv": ("edge_id", ["notes"]),
}

# Text-only replacements: apply everywhere in the affected fields.
# Only two kinds of edits:
#   1. Rename remaining 'ANM-7' string tokens to 'RHA1' (label + description drift).
#   2. Remove the specific stale caveat about renaming ANM-7 -> RHA1, which the
#      rename has now addressed. Other scientific caveats stay in place.
TEXT_REPLACEMENTS = [
    ("Rhodococcus sp. ANM-7", "Rhodococcus sp. RHA1"),
    (" ANM-7", " RHA1"),
    # Very targeted: only the specific ANM-7 rename caveat text.
    (r"\s*\[CAVEAT[^\]]*\]\s*CAVEAT\s*[-\u2013\u2014]\s*the graph's strain label 'ANM-7'[^\|]*?to match the cited evidence\.?\s*",
     " "),
]


def apply(dry_run: bool) -> None:
    total_changes = 0
    for fname, (id_field, text_fields) in FILES.items():
        fpath = HERE / fname
        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames)
            rows = list(reader)
        n_changes = 0
        for row in rows:
            for tf in text_fields:
                if tf not in row or not row[tf]:
                    continue
                original = row[tf]
                new_val = original
                for old, new in TEXT_REPLACEMENTS:
                    if old.startswith("Rhodococcus") or old.startswith(" ANM"):
                        new_val = new_val.replace(old, new)
                    else:
                        new_val = re.sub(old, new, new_val, flags=re.DOTALL)
                # Strip double spaces and trailing whitespace
                new_val = re.sub(r"  +", " ", new_val).strip()
                if new_val != original:
                    row[tf] = new_val
                    n_changes += 1
        print(f"  {fname:40s}  {n_changes} field(s) changed")
        total_changes += n_changes
        if not dry_run:
            with open(fpath, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                w.writeheader()
                w.writerows(rows)
    print(f"\nTotal changes: {total_changes}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    apply(args.dry_run)


if __name__ == "__main__":
    main()
