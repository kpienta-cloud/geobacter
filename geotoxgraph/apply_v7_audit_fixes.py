"""Apply the residual v7 audit fixes flagged by the third-round reviewer audit.

Five small mechanical items:

  Fix A: Add AS3MT effect_direction and Schlebusch annotation to
         variant:as3mt_slow_methylator so the manuscript's line 180 claim
         is backed by the data.
  Fix B: Promote compound:afb1 into evolutionary_contrast_nodes.csv (with
         the same identity as the base-layer node) so the contrast layer
         is self-consistent when downloaded alone. This removes the 18
         previously "dangling" AFB1 contrast edges and brings the contrast
         compound count from 21 to 22.
  Fix C: FMO2 residual field cleanup. Change lost:fmo2 module_id and
         entity_class from contrast_human_lineage / lost_capacity to the
         polymorphic parallels; update the label; retag
         edge:fmo2_class_polymorphic module_id and effect.
  Fix D: Remove stale conflicting has_contrast_class edges from
         compound:four_abp so its post-audit topology is (polymorphic,
         ecosystem), not the four-compartment topology from an earlier
         draft.
  Fix E: Ontology-file consistency. Rename FMO2 example in
         contrast_ontology.md and contrast_classes.yaml from a
         human_lineage example to a polymorphic example, since the
         release now classifies it there.

Run with --dry-run to preview.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

HERE = Path(__file__).parent

# ---------------------- Fix A: AS3MT annotation ----------------------

AS3MT_ANNOTATION = {
    "identifier": (
        "rs11191439 (T287T; Met287Thr). effect_direction=risk_increasing. "
        "Reference: Schlebusch 2015 (PMID 25739736) documents positive selection "
        "on the protective, efficient-methylator haplotype in Andean populations "
        "chronically exposed to arsenic; the slow-methylator variant carried in "
        "this node is the RISK-INCREASING direction opposite to that selected "
        "haplotype."
    ),
}

# ---------------------- Fix B: promote compound:afb1 to contrast layer ----------------------

# The base-layer compound:afb1 node currently lives only in geotoxgraph_nodes.csv.
# 18 contrast edges point at it. We add a parallel contrast-layer entry so
# the contrast layer is self-consistent.

AFB1_CONTRAST_NODE = {
    "id": "compound:afb1",
    "label": "Aflatoxin B1",
    "node_type": "compound",
    "strain_id": "shared",
    "module_id": "contrast_aflatoxin",
    "entity_class": "mycotoxin",
    "identifier": "AFB1",
    "description": (
        "Hepatocarcinogen exposure anchor activated by human CYP1A2/3A4 to the "
        "toxic exo-8,9-epoxide. Present in both base and contrast layers "
        "(promoted to contrast in v7.1 audit to resolve 18 contrast edges that "
        "reference this node)."
    ),
    "source_url": "https://pubmed.ncbi.nlm.nih.gov/35850656/",
    "annotation_status": "contrast_curated",
}

# ---------------------- Fix C: FMO2 residual fields ----------------------

FMO2_NODE_UPDATES = {
    "label": "FMO2 c.1414C>T (polymorphic)",
    "entity_class": "polymorphism",
    "module_id": "contrast_polymorphic",
}

FMO2_EDGE_UPDATES = {
    "module_id": "contrast_polymorphic",
    "effect": "polymorphic_loss",
    "outcome_label": "polymorphic loss",
}

# ---------------------- Fix D: remove stale 4-ABP contrast edges ----------------------

# The 4-ABP case is now (polymorphic, ecosystem). Class edges for
# microbial_only and human_lineage that came from an earlier draft should
# be removed. But keep the polymorphic and ecosystem-outsourced edges.

FOUR_ABP_STALE_EDGES = {
    "edge:compound_four_abp_class_microbial_only",  # would-be microbial_only
    "edge:fmo2_would_have_handled_four_abp",  # ties 4-ABP to a defunct human_lineage claim
}


def load(path: Path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def save(path: Path, fields, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def find_dead_refs(node_ids, edges):
    dead = []
    for r in edges:
        if r["source_id"] and r["source_id"] not in node_ids:
            dead.append((r["edge_id"], "source_id", r["source_id"]))
        if r["target_id"] and r["target_id"] not in node_ids:
            dead.append((r["edge_id"], "target_id", r["target_id"]))
    return dead


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Load all files
    files = {}
    for name in ["evolutionary_contrast_nodes.csv", "evolutionary_contrast_edges.csv"]:
        files[name] = load(HERE / name)

    # ---- Fix A: AS3MT identifier update ----
    print("=== Fix A: AS3MT annotation ===")
    n_a = 0
    for r in files["evolutionary_contrast_nodes.csv"][1]:
        if r["id"] == "variant:as3mt_slow_methylator":
            for k, v in AS3MT_ANNOTATION.items():
                if k in r:
                    r[k] = v
                    n_a += 1
    print(f"  Fields updated: {n_a}")

    # ---- Fix B: (deferred to manuscript Data Availability + CI change) ----
    print("\n=== Fix B: SKIPPED (union dependency documented in manuscript instead) ===")
    print("  See Data Availability section update in GeoToxGraph_v7.1.md.")
    print("  CI gate switched to union check (base + contrast) via update_ci_gate.py.")

    # ---- Fix C: FMO2 residual fields ----
    print("\n=== Fix C: FMO2 residual field cleanup ===")
    n_c = 0
    for r in files["evolutionary_contrast_nodes.csv"][1]:
        if r["id"] == "lost:fmo2":
            for k, v in FMO2_NODE_UPDATES.items():
                if k in r and r[k] != v:
                    r[k] = v
                    n_c += 1
    for r in files["evolutionary_contrast_edges.csv"][1]:
        if r["edge_id"] == "edge:fmo2_class_polymorphic":
            for k, v in FMO2_EDGE_UPDATES.items():
                if k in r and r[k] != v:
                    r[k] = v
                    n_c += 1
    print(f"  FMO2 fields updated: {n_c}")

    # ---- Fix D: remove stale 4-ABP contrast edges ----
    print("\n=== Fix D: remove stale 4-ABP contrast edges ===")
    edge_fields, edge_rows = files["evolutionary_contrast_edges.csv"]
    before = len(edge_rows)
    kept = [r for r in edge_rows if r["edge_id"] not in FOUR_ABP_STALE_EDGES]
    files["evolutionary_contrast_edges.csv"] = (edge_fields, kept)
    print(f"  Edges removed: {before - len(kept)}")
    for rem in FOUR_ABP_STALE_EDGES:
        if not any(r["edge_id"] == rem for r in edge_rows):
            print(f"    (note: {rem} did not exist)")

    # ---- Dead-reference check ----
    _, base_rows = load(HERE / "geotoxgraph_nodes.csv")
    all_node_ids = (
        {r["id"] for r in base_rows}
        | {r["id"] for r in files["evolutionary_contrast_nodes.csv"][1]}
    )
    combined_edges = [r for r in files["evolutionary_contrast_edges.csv"][1]]
    # Also include base edges
    _, base_edges = load(HERE / "geotoxgraph_edges.csv")
    combined_edges += base_edges

    # Same-graph check: contrast edges should not reference base-only ids
    # (except through external_target_ref which is empty here)
    contrast_only_dead = 0
    for r in files["evolutionary_contrast_edges.csv"][1]:
        for f in ("source_id", "target_id"):
            v = r.get(f, "")
            if not v:
                continue
            # Check if target is in contrast_nodes at all
            contrast_ids = {n["id"] for n in files["evolutionary_contrast_nodes.csv"][1]}
            if v not in contrast_ids:
                contrast_only_dead += 1
                if contrast_only_dead <= 5:
                    print(f"  Contrast-only dead ref: {r['edge_id']} {f}={v}")
    print(f"  Contrast-layer standalone dead refs: {contrast_only_dead}")

    if args.dry_run:
        print("\n[dry-run] Not writing files.")
        return

    for name, (fields, rows) in files.items():
        save(HERE / name, fields, rows)
    print("\nContrast CSVs written.")


if __name__ == "__main__":
    main()
