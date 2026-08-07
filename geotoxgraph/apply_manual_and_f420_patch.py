"""Apply the citation-audit MANUAL and F420 decisions to the four CSVs.

Decisions are documented in `/home/user/workspace/GeoToxGraph_Decision_Matrix.md`.
This script performs three classes of edit:

  Class A  Delete nodes and edges for assertions with no primary literature.
  Class B  Relabel `lost:hpgd_candidate` as an unsourced hypothesis.
  Class C  Reword the F420/R. erythropolis AFB1 records to reflect that the
           F420 mechanism is inferred by homology from Lapalikar 2012 while the
           strain-specific activity comes from Teniola 2005.

The script reads the four CSVs in-place, verifies row counts and dead-references,
and writes new files only if all checks pass. Run with --dry-run to preview
without writing.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

HERE = Path(__file__).parent

FILES = {
    "nodes": HERE / "geotoxgraph_nodes.csv",
    "edges": HERE / "geotoxgraph_edges.csv",
    "cnodes": HERE / "evolutionary_contrast_nodes.csv",
    "cedges": HERE / "evolutionary_contrast_edges.csv",
}

# ---------------------- CLASS A: delete ----------------------

DELETE_NODES = {
    # Class 1: KT2440 arylamine assertions (7 nodes/edges across files)
    "module:ppu_aerobic_aromatic_amine",
    "gene:ppu_aaox",
    "compound:four_abp_deaminated",
    "microbe:ppu_aerobic_aromatic_amine",
    # Class 3: gut reductive dehalogenation
    "ecosystem:gut_reductive_dehalogenation",
}

DELETE_EDGES = {
    # Class 1
    "edge:ppu_kt2440_has_amine_module",
    "edge:ppu_4abp_deamination",
    "edge:microbe_ppu_amine_class_ancient_catabolic",
    "edge:microbe_ppu_amine_handles_4abp",
    # Class 3
    "edge:gut_reductive_dehalogenation_class_ecosystem_outsourced",
    "edge:gut_reductive_dehalogenation_shifts_handling_of_vinyl_chloride",
}

# ---------------------- CLASS B: hypothesis relabel ----------------------

HYPOTHESIS_NODES = {"lost:hpgd_candidate"}
HYPOTHESIS_DESC_PREFIX = "HYPOTHESIS (unsourced): "

# ---------------------- CLASS C: F420 reword ----------------------

F420_PRIMARY_URL = "https://pubmed.ncbi.nlm.nih.gov/22383957/"
F420_SECONDARY_NOTE = (
    "Secondary source: PMID 16061299 (Teniola 2005) demonstrates AFB1 degradation "
    "by R. erythropolis DSM 14303 cell-free extracts (>90% in 4 h) without naming "
    "the cofactor; F420H2 mechanism inferred by homology to Actinomycetales FDR-A "
    "family per Lapalikar 2012 (PMID 22383957)."
)

F420_NODE_EDITS = {
    "gene:rho_fdr_afb1": {
        "label": "AFB1 reductase (inferred F420H2-dependent, R. erythropolis)",
        "description": (
            "AFB1 reductase activity in R. erythropolis cell-free extracts (Teniola 2005, "
            "PMID 16061299). Cofactor attribution to F420H2 is inferred by homology to the "
            "widespread Actinomycetales FDR-A family (Lapalikar 2012, PMID 22383957); no "
            "R. erythropolis-specific cofactor identification is published."
        ),
        "source_url": F420_PRIMARY_URL,
    },
    "compound:afb1_reduced": {
        "label": "AFB1 reduced product",
        "description": (
            "Bacterial reduction product of the AFB1 bisfuran; cannot form the mammalian "
            "exo-8,9-epoxide. Strain-specific activity from Teniola 2005 (PMID 16061299); "
            "F420H2 mechanism from Lapalikar 2012 (PMID 22383957)."
        ),
        "source_url": F420_PRIMARY_URL,
    },
    "microbe:rho_erythropolis_f420_afb1": {
        "label": "R. erythropolis AFB1 degradation (inferred F420-dependent)",
        "description": (
            "R. erythropolis DSM 14303 cell-free extracts degrade AFB1 (Teniola 2005). "
            "F420H2-dependent bisfuran reduction is the biochemically established "
            "Actinomycetales mechanism (Lapalikar 2012) and is the presumed route here by "
            "homology; not directly demonstrated in R. erythropolis."
        ),
        "source_url": F420_PRIMARY_URL,
    },
}

F420_EDGE_EDITS = {
    "edge:rho_afb1_reduction": {
        "source_url": F420_PRIMARY_URL,
        "notes": (
            "AFB1 bisfuran reduction to a product that cannot form the mammalian exo-8,9-"
            "epoxide. Strain-specific activity: Teniola 2005 (PMID 16061299). F420H2 "
            "mechanism inferred by homology to Actinomycetales FDR-A family (Lapalikar "
            "2012, PMID 22383957)."
        ),
        "evidence_type": "homology_prediction",
    },
    "edge:microbe_rho_handles_afb1": {
        "source_url": F420_PRIMARY_URL,
        "notes": (
            "AFB1 is reduced by R. erythropolis cell-free extracts (Teniola 2005, PMID "
            "16061299); F420H2-dependent reduction is the established Actinomycetales "
            "mechanism (Lapalikar 2012, PMID 22383957) and is inferred here by homology."
        ),
        "evidence_type": "homology_prediction",
    },
}


# ---------------------- Machinery ----------------------

def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def write_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def apply_node_edits(rows: list[dict], id_key: str = "id") -> list[dict]:
    new_rows: list[dict] = []
    for row in rows:
        rid = row[id_key]
        if rid in DELETE_NODES:
            continue
        if rid in HYPOTHESIS_NODES:
            row = dict(row)
            row["source_url"] = ""
            if "annotation_status" in row:
                row["annotation_status"] = "hypothesis_unsourced"
            desc = row.get("description", "")
            if not desc.startswith(HYPOTHESIS_DESC_PREFIX):
                row["description"] = HYPOTHESIS_DESC_PREFIX + desc
        if rid in F420_NODE_EDITS:
            row = dict(row)
            for k, v in F420_NODE_EDITS[rid].items():
                row[k] = v
        new_rows.append(row)
    return new_rows


def apply_edge_edits(rows: list[dict]) -> list[dict]:
    new_rows: list[dict] = []
    for row in rows:
        eid = row["edge_id"]
        if eid in DELETE_EDGES:
            continue
        # Cascade guard: any edge whose source or target is a deleted node
        if row["source_id"] in DELETE_NODES or row["target_id"] in DELETE_NODES:
            raise SystemExit(
                f"Undeclared cascade edge {eid} references deleted node "
                f"({row['source_id']} -> {row['target_id']}). Add it to DELETE_EDGES."
            )
        if eid in F420_EDGE_EDITS:
            row = dict(row)
            for k, v in F420_EDGE_EDITS[eid].items():
                row[k] = v
        new_rows.append(row)
    return new_rows


def find_dead_refs(node_ids: set[str], edge_rows: list[dict]) -> list[tuple[str, str, str]]:
    dead = []
    for r in edge_rows:
        if r["source_id"] not in node_ids and r["source_id"] != "":
            dead.append((r["edge_id"], "source_id", r["source_id"]))
        if r["target_id"] not in node_ids and r["target_id"] != "":
            dead.append((r["edge_id"], "target_id", r["target_id"]))
    return dead


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Report changes but do not write.")
    args = ap.parse_args()

    fields = {}
    rows = {}
    for key, path in FILES.items():
        fields[key], rows[key] = read_rows(path)
        print(f"Loaded {key:6s}  {len(rows[key]):4d} rows  ({path.name})")

    before = {k: len(v) for k, v in rows.items()}

    rows["nodes"] = apply_node_edits(rows["nodes"], id_key="id")
    rows["cnodes"] = apply_node_edits(rows["cnodes"], id_key="id")
    rows["edges"] = apply_edge_edits(rows["edges"])
    rows["cedges"] = apply_edge_edits(rows["cedges"])

    print("\nRow counts (before -> after):")
    for k in FILES:
        after = len(rows[k])
        delta = after - before[k]
        print(f"  {k:6s}  {before[k]:4d} -> {after:4d}  ({delta:+d})")

    # Dead-reference check: identify pre-existing vs. patch-introduced dead refs
    # Baseline (before patch)
    with open(FILES["nodes"]) as f:
        base0 = {r["id"] for r in csv.DictReader(f)}
    with open(FILES["cnodes"]) as f:
        cbase0 = {r["id"] for r in csv.DictReader(f)}
    with open(FILES["edges"]) as f:
        edges0 = list(csv.DictReader(f))
    with open(FILES["cedges"]) as f:
        cedges0 = list(csv.DictReader(f))
    preexisting = set(find_dead_refs(base0 | cbase0, edges0)) | set(
        find_dead_refs(base0 | cbase0, cedges0)
    )
    # After patch
    all_node_ids = {r["id"] for r in rows["nodes"]} | {r["id"] for r in rows["cnodes"]}
    after = set(find_dead_refs(all_node_ids, rows["edges"])) | set(
        find_dead_refs(all_node_ids, rows["cedges"])
    )
    introduced = after - preexisting
    if introduced:
        for row in sorted(introduced):
            print(f"  PATCH-INTRODUCED DEAD REFERENCE: {row}")
        raise SystemExit(f"{len(introduced)} dead references introduced by patch.")
    if preexisting:
        print(f"Note: {len(preexisting)} pre-existing dead references remain (not fixed by this patch).")
        for row in sorted(preexisting):
            print(f"  pre-existing: {row}")
    print("Dead-reference check: no new dead references introduced.")

    # Expected deltas (one of the four class-1 nodes lives only in contrast_nodes)
    expected = {"nodes": -3, "edges": -2, "cnodes": -2, "cedges": -4}
    got = {k: len(rows[k]) - before[k] for k in FILES}
    if got != expected:
        raise SystemExit(f"Row-count delta mismatch. Expected {expected}, got {got}")
    print(f"Row-count delta matches expected: {expected}")

    if args.dry_run:
        print("\n[dry-run] Not writing files.")
        return

    for key, path in FILES.items():
        write_rows(path, fields[key], rows[key])
    print("\nWrote all four CSVs.")


if __name__ == "__main__":
    main()
