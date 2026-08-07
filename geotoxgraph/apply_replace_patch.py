"""Apply the citation-audit REPLACE decisions to the four CSVs.

Reads `/home/user/workspace/corrective_citations_by_record.csv` and updates
`source_url` on every record whose action is REPLACE_URL_AND_CITATION.
This covers the 148 records where the audit resolved a MISMATCH or
UNRESOLVED URL to a verified replacement PubMed URL.

For records where the audit noted a CAVEAT (the replacement supports the
module/pathway but not the strain- or gene-level specificity), the row's
evidence_type is also downgraded to homology_prediction and a note is
appended explaining the caveat.

Run with --dry-run to preview.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

HERE = Path(__file__).parent
CORRECTIONS = Path("/home/user/workspace/corrective_citations_by_record.csv")

FILES = {
    "geotoxgraph_nodes.csv": "id",
    "geotoxgraph_edges.csv": "edge_id",
    "evolutionary_contrast_nodes.csv": "id",
    "evolutionary_contrast_edges.csv": "edge_id",
}


# Rows already handled by apply_manual_and_f420_patch.py in commit e3bdeaf.
# Even though they appear as REPLACE in the correction CSV, the F420 rewording
# used a hand-crafted description that would be clobbered if reprocessed here.
ALREADY_APPLIED = {
    ("geotoxgraph_nodes.csv", "gene:rho_fdr_afb1"),
    ("geotoxgraph_nodes.csv", "compound:afb1_reduced"),
    ("geotoxgraph_edges.csv", "edge:rho_afb1_reduction"),
    ("evolutionary_contrast_nodes.csv", "microbe:rho_erythropolis_f420_afb1"),
    ("evolutionary_contrast_edges.csv", "edge:microbe_rho_handles_afb1"),
}


def load_corrections() -> dict[tuple[str, str], dict]:
    """Return {(file, id): correction_row} for REPLACE actions not already applied."""
    out = {}
    with open(CORRECTIONS) as f:
        for r in csv.DictReader(f):
            if r["action"] != "REPLACE_URL_AND_CITATION":
                continue
            key = (r["file"], r["id"])
            if key in ALREADY_APPLIED:
                continue
            out[key] = r
    return out


def apply_to_file(fpath: Path, key: str, corrections: dict) -> tuple[int, int]:
    """Return (updated, downgraded) row counts."""
    fname = fpath.name
    with open(fpath, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    updated = 0
    downgraded = 0
    for row in rows:
        rid = row[key]
        c = corrections.get((fname, rid))
        if not c:
            continue
        # Sanity check: current URL should still match
        if row.get("source_url") != c["current_source_url"]:
            raise SystemExit(
                f"[{fname}] {rid}: current source_url in CSV "
                f"'{row.get('source_url')}' does not match audit "
                f"'{c['current_source_url']}'. Skipping to avoid corruption."
            )
        row["source_url"] = c["verified_correct_url"]
        updated += 1

        # If the auditor flagged a CAVEAT, downgrade evidence_type on the edge and add note
        caveat = c.get("caveat_note", "").strip()
        if caveat and "evidence_type" in row:
            # Downgrade biochemistry/kinetic_assay/phenotype to homology_prediction
            if row.get("evidence_type") not in ("homology_prediction", ""):
                row["evidence_type"] = "homology_prediction"
                downgraded += 1
            existing = row.get("notes", "")
            marker = "[CAVEAT from citation audit]"
            if marker not in existing:
                addendum = f" {marker} {caveat[:280]}"
                row["notes"] = (existing + addendum).strip()
        elif caveat and "description" in row:
            # Node: append caveat to description
            existing = row.get("description", "")
            marker = "[CAVEAT]"
            if marker not in existing:
                addendum = f" {marker} {caveat[:240]}"
                row["description"] = (existing + addendum).strip()

    with open(fpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    return updated, downgraded


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    corrections = load_corrections()
    print(f"Loaded {len(corrections)} REPLACE corrections from audit.")

    # Group by file for reporting
    by_file: dict[str, int] = {}
    for (fname, _rid) in corrections:
        by_file[fname] = by_file.get(fname, 0) + 1
    for k in sorted(by_file):
        print(f"  {k:38s} {by_file[k]}")

    if args.dry_run:
        # Do a validation-only pass: verify every current_source_url in the audit
        # actually matches what's currently in the CSVs
        mismatches = 0
        for fname, key in FILES.items():
            with open(HERE / fname) as f:
                rows = {r[key]: r for r in csv.DictReader(f)}
            for (f2, rid), c in corrections.items():
                if f2 != fname:
                    continue
                if rid not in rows:
                    print(f"  MISSING: {fname} row {rid} not in file (perhaps already deleted by MANUAL patch)")
                    mismatches += 1
                    continue
                if rows[rid].get("source_url") != c["current_source_url"]:
                    print(f"  URL DRIFT: {fname} {rid}: expected '{c['current_source_url']}', got '{rows[rid].get('source_url')}'")
                    mismatches += 1
        if mismatches:
            print(f"\n{mismatches} row(s) with drift or missing. Investigate before applying.")
        else:
            print("\nAll REPLACE targets present with expected current URLs.")
        return

    total_updated = 0
    total_downgraded = 0
    for fname, key in FILES.items():
        u, d = apply_to_file(HERE / fname, key, corrections)
        print(f"  {fname:40s}  updated={u:3d}  downgraded={d:3d}")
        total_updated += u
        total_downgraded += d
    print(f"\nTotal: {total_updated} rows updated, {total_downgraded} evidence_type downgrades.")


if __name__ == "__main__":
    main()
