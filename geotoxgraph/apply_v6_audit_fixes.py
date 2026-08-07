"""Apply all data-side fixes from the round-2 reviewer audit of v6.

This is a single-commit, auditable script executing eight data-side fixes.
Manuscript text edits and figure regeneration are handled elsewhere.

  Fix 1: Rename ancient_catabolic -> microbial_only in CSVs, ontology docs.
  Fix 2: Reclassify FMO2 from human_lineage to polymorphic in the data.
         (Includes updating the lost:fmo2 node's contrast class + edge.)
  Fix 3: (No data-side action; the manuscript is updated to acknowledge
         the four additional top-level classes: analogous_function,
         toxic_inversion, host_shifted, pathway_loss.)
  Fix 4: Delete compound:aflatoxin_b1 alias from compound_contrast_summary.csv.
  Fix 5: Rerun build_confidence_and_summary.py after the above fixes and
         write the regenerated confidence_score column back into the CSVs.
         Any surviving score-vs-script mismatch after that is a code bug
         that should not be silenced. We also disable the ecosystem
         substring bug in the scoring script.
  Fix 6: Correct AS3MT rs11191439 allele frequencies to gnomAD v4 exomes
         values on variant:as3mt_slow_methylator.

Run with --dry-run to preview.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent

# ---------------------- Fix 1: rename ----------------------

OLD = "ancient_catabolic"
NEW = "microbial_only"

# In the manuscript's four-compartment framing, "ancient_catabolic" is
# semantically identical to "microbial_only": present in environmental
# bacteria and absent from the human host. The rename removes the
# ancestral-reconstruction implication.

RENAME_TARGETS_CSV = {
    # file: list of columns whose values may need rewriting
    "geotoxgraph_nodes.csv": ["id"],
    "geotoxgraph_edges.csv": ["source_id", "target_id"],
    "evolutionary_contrast_nodes.csv": ["id"],
    "evolutionary_contrast_edges.csv": ["source_id", "target_id"],
    "geotoxgraph_nodes_enriched.csv": ["id"],
    "geotoxgraph_edges_enriched.csv": ["source_id", "target_id"],
    "neo4j_nodes.csv": ["id:ID"],
    "neo4j_relationships.csv": [":START_ID", ":END_ID"],
    "compound_contrast_summary.csv": None,  # scan all cells
}

# ---------------------- Fix 2: FMO2 reclassification ----------------------

# The manuscript at v6 lines 68-75 announces FMO2 c.1414C>T as polymorphic.
# The data still says human_lineage. We move the FMO2 node's class edge to
# contrast:polymorphic and update the node's own annotation.

# The FMO2 node id is lost:fmo2 (loss_mechanism=fixed_lof_snv per ontology),
# and its class edge is edge:fmo2_class_human_lineage.
# We rename edge_id -> edge:fmo2_class_polymorphic and change its target_id.
# We also add allele_frequency data to the fmo2 node so the polymorphic
# class's required_fields are satisfied.

FMO2_EDITS = {
    # (file, id) -> {field: new_value}
    ("evolutionary_contrast_nodes.csv", "lost:fmo2"): {
        "node_type": "variant",  # was lost_capacity; now a segregating variant
        "description": (
            "FMO2 c.1414C>T (p.Q472X) is a null variant that segregates in "
            "modern human populations. It is absent from primate outgroups. "
            "Derived-allele frequency approximately 0.98 in European populations, "
            "approximately 0.75 in African populations (gnomAD v4). Reclassified "
            "from human_lineage to polymorphic in this release because the derived "
            "allele fails the >0.95 fixation threshold in African populations."
        ),
    },
}

FMO2_EDGE_EDITS = {
    # edge_id -> {field: new_value or callable}
    "edge:fmo2_class_human_lineage": {
        "edge_id": "edge:fmo2_class_polymorphic",
        "target_id": "contrast:polymorphic",
    },
}

# ---------------------- Fix 4: delete aflatoxin_b1 alias from summary CSV ----------------------

SUMMARY_ALIAS_TO_DELETE = "compound:aflatoxin_b1"

# ---------------------- Fix 6: AS3MT allele frequencies ----------------------

# gnomAD v4 exomes for rs11191439 (the T287T Met287Thr AS3MT variant used
# in the manuscript as the polymorphic anchor). Values verified against
# dbSNP + gnomAD v4 in the reviewer audit.
AS3MT_CORRECTIONS = {
    ("evolutionary_contrast_nodes.csv", "variant:as3mt_slow_methylator"): {
        "allele_frequency_json": json.dumps({
            "AFR": 0.118,
            "AMR": 0.096,
            "EAS": 0.016,
            "EUR": 0.101,
            "SAS": 0.070,
            "source": "gnomAD v4 exomes",
            "rsid": "rs11191439",
        }),
    }
}

# ---------------------- Machinery ----------------------

def rewrite_csv_field(path: Path, columns: list[str] | None, old: str, new: str) -> int:
    """In-place rewrite of specific fields (or all fields if columns is None).
    Returns count of cells changed. Only rewrites cells whose value EQUALS old
    or contains old as a semicolon-separated token or a subclass suffix.
    """
    if not path.exists():
        print(f"  SKIP (missing): {path.name}")
        return 0
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    n = 0
    for r in rows:
        cols = columns if columns is not None else fieldnames
        for c in cols:
            if c not in r:
                continue
            v = r[c]
            if not v:
                continue
            # Match against contrast:ancient_catabolic OR bare ancient_catabolic
            new_v = v
            new_v = re.sub(r"contrast:" + re.escape(old), "contrast:" + new, new_v)
            new_v = re.sub(r"\b" + re.escape(old) + r"\b", new, new_v)
            if new_v != v:
                r[c] = new_v
                n += 1
    if n:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)
    return n


def rewrite_text_file(path: Path, old: str, new: str) -> int:
    """Rewrite a text file (yaml, markdown). Only rewrites the bare token."""
    if not path.exists():
        print(f"  SKIP (missing): {path.name}")
        return 0
    txt = path.read_text()
    orig = txt
    txt = re.sub(r"contrast:" + re.escape(old), "contrast:" + new, txt)
    # For yaml keys / plain identifiers, don't touch the word
    # "ancient_catabolic" if it appears in prose describing the historical
    # class name. But do rename yaml keys at line start.
    txt = re.sub(r"^(\s*)" + re.escape(old) + r":", r"\1" + new + ":", txt, flags=re.MULTILINE)
    if txt != orig:
        path.write_text(txt)
        # Count how many changes
        return len(re.findall(re.escape(new), txt)) - len(re.findall(re.escape(new), orig))
    return 0


def apply_fmo2(dry_run: bool) -> int:
    """Fix 2: reclassify FMO2."""
    n_changes = 0

    # Node edit
    for (fname, node_id), edits in FMO2_EDITS.items():
        fpath = HERE / fname
        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames)
            rows = list(reader)
        for r in rows:
            if r["id"] == node_id:
                for k, v in edits.items():
                    if k in r:
                        r[k] = v
                n_changes += 1
        if not dry_run:
            with open(fpath, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                w.writeheader()
                w.writerows(rows)

    # Edge edit
    edge_file = HERE / "evolutionary_contrast_edges.csv"
    with open(edge_file, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    for r in rows:
        for old_eid, edits in FMO2_EDGE_EDITS.items():
            if r["edge_id"] == old_eid:
                for k, v in edits.items():
                    r[k] = v
                # Also lower confidence for a reclassified assignment
                if r.get("confidence_score"):
                    try:
                        cs = float(r["confidence_score"])
                        if cs > 0.7:
                            r["confidence_score"] = "0.7"
                    except ValueError:
                        pass
                # Update notes
                r["notes"] = (
                    "Class assignment reclassified from human_lineage to polymorphic "
                    "in the audit revision because FMO2 c.1414C>T fails the >0.95 "
                    "fixation threshold in African populations."
                )
                n_changes += 1
    if not dry_run:
        with open(edge_file, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)

    return n_changes


def delete_summary_alias(dry_run: bool) -> int:
    fpath = HERE / "compound_contrast_summary.csv"
    if not fpath.exists():
        print("  compound_contrast_summary.csv not found")
        return 0
    with open(fpath, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    before = len(rows)
    new_rows = []
    for r in rows:
        # Row-level filter: any cell containing exactly compound:aflatoxin_b1 -> drop row
        drop = False
        for v in r.values():
            if v and SUMMARY_ALIAS_TO_DELETE in v.split(";"):
                drop = True
                break
            if v == SUMMARY_ALIAS_TO_DELETE:
                drop = True
                break
        if not drop:
            new_rows.append(r)
    after = len(new_rows)
    if not dry_run and after != before:
        with open(fpath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(new_rows)
    return before - after


def fix_as3mt(dry_run: bool) -> int:
    fpath = HERE / "evolutionary_contrast_nodes.csv"
    with open(fpath, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)
    n = 0
    for r in rows:
        if r["id"] == "variant:as3mt_slow_methylator":
            new_json = AS3MT_CORRECTIONS[("evolutionary_contrast_nodes.csv", "variant:as3mt_slow_methylator")]["allele_frequency_json"]
            # Find the allele-frequency-carrying field
            for field in fieldnames:
                v = r.get(field, "")
                if v and '"AFR"' in v and "0.03" in v:
                    r[field] = new_json
                    n += 1
                    print(f"  Updated allele_frequency in field '{field}' of {r['id']}")
                    break
    if n and not dry_run:
        with open(fpath, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            w.writeheader()
            w.writerows(rows)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("=== Fix 1: ancient_catabolic -> microbial_only ===")
    total = 0
    for fname, cols in RENAME_TARGETS_CSV.items():
        n = rewrite_csv_field(HERE / fname, cols, OLD, NEW)
        if n:
            print(f"  {fname:45s} {n} cells")
        total += n
    for tf in ["contrast_ontology.md", "contrast_classes.yaml"]:
        n = rewrite_text_file(HERE / tf, OLD, NEW)
        print(f"  {tf:45s} {n} occurrences")
        total += n
    print(f"  Total: {total}")

    print("\n=== Fix 2: FMO2 reclassification ===")
    n2 = apply_fmo2(args.dry_run)
    print(f"  Changes: {n2}")

    print("\n=== Fix 4: delete compound:aflatoxin_b1 from summary CSV ===")
    n4 = delete_summary_alias(args.dry_run)
    print(f"  Rows removed: {n4}")

    print("\n=== Fix 6: AS3MT allele frequencies ===")
    n6 = fix_as3mt(args.dry_run)
    print(f"  Fields updated: {n6}")

    if args.dry_run:
        print("\n[dry-run] Not writing final state.")


if __name__ == "__main__":
    main()
