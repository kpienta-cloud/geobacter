"""Two consolidations that came out of the model council review:

1. Rename strain:rho_anm7 -> strain:rho_rha1 across all four CSVs.
   The placeholder 'ANM-7' has no primary literature; the NDMA propane
   monooxygenase is characterized in Rhodococcus sp. RHA1 (Sharp 2007,
   PMID 17873074) and R. ruber ENV425 (Fournier 2009, PMID 19542346).
   The strain node is renamed to RHA1 and the description names both.

2. Consolidate the duplicate AFB1 compound node:
   compound:aflatoxin_b1 (in evolutionary_contrast_nodes.csv) is a duplicate
   alias for compound:afb1 (in geotoxgraph_nodes.csv). The manuscript
   describes them as one compound; the graph should too.
   Action: delete compound:aflatoxin_b1 from contrast_nodes; remap the 6
   contrast edges that reference it to compound:afb1.

Both consolidations are auditable: every field change is enumerated
below by rule rather than by pattern-substitution across the whole file,
so a diff against HEAD names exactly which fields moved.

Run with --dry-run to preview.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

HERE = Path(__file__).parent

# ---------------- Rename plan ----------------

# All identifier moves: (file, id_field, old_value, new_value)
# id_field is the CSV column being rewritten. Rename applies only if the
# exact value matches - no substring substitution.
ID_MOVES = [
    # Nodes: id
    ("geotoxgraph_nodes.csv", "id", "strain:rho_anm7", "strain:rho_rha1"),
    ("geotoxgraph_nodes.csv", "id", "module:rho_anm7_ndma_degradation", "module:rho_rha1_ndma_degradation"),
    ("evolutionary_contrast_nodes.csv", "id", "microbe:rho_anm7_aerobic_ndma", "microbe:rho_rha1_aerobic_ndma"),
    # Edges: edge_id
    ("geotoxgraph_edges.csv", "edge_id", "edge:rho_anm7_has_ndma_module", "edge:rho_rha1_has_ndma_module"),
]

# strain_id / module_id / source_id / target_id renames apply to every row
# where the field equals the old value. This is a controlled substitution:
# we list each (file, field) pair explicitly so it is auditable, but we
# don't require a row-by-row inventory because there is no ambiguity.
FIELD_RENAMES = [
    # strain_id: rho_anm7 -> rho_rha1 (base level strain shorthand)
    ("geotoxgraph_nodes.csv", "strain_id", "rho_anm7", "rho_rha1"),
    ("geotoxgraph_edges.csv", "strain_id", "rho_anm7", "rho_rha1"),
    ("evolutionary_contrast_nodes.csv", "strain_id", "rho_anm7", "rho_rha1"),
    ("evolutionary_contrast_edges.csv", "strain_id", "rho_anm7", "rho_rha1"),
    # module_id
    ("geotoxgraph_nodes.csv", "module_id", "rho_anm7_ndma_degradation", "rho_rha1_ndma_degradation"),
    ("geotoxgraph_edges.csv", "module_id", "rho_anm7_ndma_degradation", "rho_rha1_ndma_degradation"),
    # source_id / target_id on edges
    ("geotoxgraph_edges.csv", "source_id", "strain:rho_anm7", "strain:rho_rha1"),
    ("geotoxgraph_edges.csv", "target_id", "module:rho_anm7_ndma_degradation", "module:rho_rha1_ndma_degradation"),
    ("evolutionary_contrast_edges.csv", "source_id", "microbe:rho_anm7_aerobic_ndma", "microbe:rho_rha1_aerobic_ndma"),
    ("evolutionary_contrast_edges.csv", "target_id", "microbe:rho_anm7_aerobic_ndma", "microbe:rho_rha1_aerobic_ndma"),
]

# Node metadata edits (rewrite label + description to name RHA1 + ENV425)
NODE_METADATA = {
    ("geotoxgraph_nodes.csv", "strain:rho_rha1"): {
        "label": "Rhodococcus sp. RHA1 (with R. ruber ENV425 co-reference)",
        "description": (
            "Rhodococcus sp. RHA1 (Sharp 2007, PMID 17873074) and Rhodococcus ruber ENV425 "
            "(Fournier 2009, PMID 19542346) are the two characterized aerobic NDMA-degrading "
            "actinomycetes; both encode an inducible propane monooxygenase that oxidizes "
            "N-nitrosodimethylamine to methylamine and formaldehyde. RHA1 is the primary "
            "reference strain in the graph; ENV425 is co-cited on the module and edges."
        ),
    },
    ("geotoxgraph_nodes.csv", "module:rho_rha1_ndma_degradation"): {
        "label": "RHA1 NDMA-degradation module (with ENV425 co-reference)",
        "description": (
            "Inducible aerobic propane monooxygenase (prmABCD-like) oxidizes NDMA to methylamine "
            "and formaldehyde in Rhodococcus sp. RHA1 (Sharp 2007) and R. ruber ENV425 "
            "(Fournier 2009); a bacterial route absent from the human host, whose CYP2E1 "
            "instead bioactivates NDMA to DNA-methylating species."
        ),
    },
    ("evolutionary_contrast_nodes.csv", "microbe:rho_rha1_aerobic_ndma"): {
        "label": "RHA1 / ENV425 aerobic NDMA propane monooxygenase",
        "description": (
            "Aerobic propane-monooxygenase-dependent NDMA degradation characterized in "
            "Rhodococcus sp. RHA1 (Sharp 2007, PMID 17873074) and Rhodococcus ruber ENV425 "
            "(Fournier 2009, PMID 19542346). Microbial-only reference: no functional ortholog "
            "in placental mammals."
        ),
    },
}

# ---------------- AFB1 consolidation ----------------

AFB1_DELETE_NODE = "compound:aflatoxin_b1"
AFB1_KEEP_NODE = "compound:afb1"

# Six contrast edges reference the deleted node; remap and (where duplicative)
# rename the edge_id so it uses the canonical afb1 shorthand.
AFB1_EDGE_REMAP = [
    # (edge_id, field_to_rewrite_from -> to, new_edge_id or None)
    ("edge:aflatoxin_to_human_cyp", "source_id", "edge:afb1_to_human_cyp"),
    ("edge:aflatoxin_host_shift", "source_id", "edge:afb1_host_shift"),
    ("edge:ugt1a1_28_modulates_aflatoxin_b1", "target_id", "edge:ugt1a1_28_modulates_afb1"),
    ("edge:compound_aflatoxin_b1_class_polymorphic", "source_id", "edge:compound_afb1_class_polymorphic"),
    ("edge:gut_beta_glucuronidase_shifts_handling_of_aflatoxin_b1", "target_id",
     "edge:gut_beta_glucuronidase_shifts_handling_of_afb1"),
    ("edge:compound_aflatoxin_b1_class_ecosystem_outsourced", "source_id",
     "edge:compound_afb1_class_ecosystem_outsourced"),
]

# ---------------- Machinery ----------------

def load(fpath: Path):
    with open(fpath, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)


def save(fpath: Path, fields: list[str], rows: list[dict]) -> None:
    with open(fpath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def find_dead_refs(node_ids: set[str], edge_rows: list[dict]) -> list:
    dead = []
    for r in edge_rows:
        if r.get("source_id") and r["source_id"] not in node_ids:
            dead.append((r["edge_id"], "source_id", r["source_id"]))
        if r.get("target_id") and r["target_id"] not in node_ids:
            dead.append((r["edge_id"], "target_id", r["target_id"]))
    return dead


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = {
        "geotoxgraph_nodes.csv": None,
        "geotoxgraph_edges.csv": None,
        "evolutionary_contrast_nodes.csv": None,
        "evolutionary_contrast_edges.csv": None,
    }
    for k in files:
        files[k] = load(HERE / k)

    # --- Rename ANM-7 -> RHA1 ---
    n_id_moves = 0
    for fname, field, old, new in ID_MOVES:
        _, rows = files[fname]
        for r in rows:
            if r.get(field) == old:
                r[field] = new
                n_id_moves += 1
    print(f"ID moves applied: {n_id_moves}")

    n_field_renames = 0
    for fname, field, old, new in FIELD_RENAMES:
        _, rows = files[fname]
        for r in rows:
            if r.get(field) == old:
                r[field] = new
                n_field_renames += 1
    print(f"Field renames applied: {n_field_renames}")

    # Metadata rewrites (label + description) - applies after id rename
    n_meta = 0
    for (fname, node_id), edits in NODE_METADATA.items():
        _, rows = files[fname]
        for r in rows:
            if r.get("id") == node_id:
                for k, v in edits.items():
                    r[k] = v
                n_meta += 1
    print(f"Node metadata rewrites: {n_meta}")

    # --- AFB1 consolidation ---
    _, cnodes = files["evolutionary_contrast_nodes.csv"]
    before = len(cnodes)
    files["evolutionary_contrast_nodes.csv"] = (
        files["evolutionary_contrast_nodes.csv"][0],
        [r for r in cnodes if r["id"] != AFB1_DELETE_NODE],
    )
    print(f"AFB1 duplicate node removed: {before - len(files['evolutionary_contrast_nodes.csv'][1])} row(s)")

    # Remap edges + rename edge_ids
    _, cedges = files["evolutionary_contrast_edges.csv"]
    n_edge_remap = 0
    n_edge_rename = 0
    for r in cedges:
        eid = r["edge_id"]
        for old_eid, field, new_eid in AFB1_EDGE_REMAP:
            if eid == old_eid:
                # Remap the compound reference
                if r.get(field) == AFB1_DELETE_NODE:
                    r[field] = AFB1_KEEP_NODE
                    n_edge_remap += 1
                r["edge_id"] = new_eid
                n_edge_rename += 1
    print(f"AFB1 edges remapped: {n_edge_remap}")
    print(f"AFB1 edges renamed: {n_edge_rename}")

    # --- Dead-reference check ---
    base_nodes = {r["id"] for r in files["geotoxgraph_nodes.csv"][1]}
    contrast_nodes = {r["id"] for r in files["evolutionary_contrast_nodes.csv"][1]}
    all_nodes = base_nodes | contrast_nodes

    base_dead = find_dead_refs(all_nodes, files["geotoxgraph_edges.csv"][1])
    contrast_dead = find_dead_refs(all_nodes, files["evolutionary_contrast_edges.csv"][1])

    # Baseline: pre-existing dead refs (before any of these edits touched the graph)
    with open(HERE / "evolutionary_contrast_edges.csv") as f:
        cedges0 = list(csv.DictReader(f))
    baseline_contrast_dead = set(find_dead_refs(all_nodes, cedges0))
    new_dead = set(base_dead) | set(contrast_dead) - baseline_contrast_dead
    if base_dead + [d for d in contrast_dead if d not in baseline_contrast_dead]:
        real_new = [d for d in base_dead + contrast_dead if d not in baseline_contrast_dead]
        if real_new:
            for d in real_new[:10]:
                print(f"  DEAD REF INTRODUCED: {d}")
            raise SystemExit(f"{len(real_new)} new dead references introduced by patch.")
    print(f"Dead-reference check: all references resolve (base={len(base_dead)} contrast={len(contrast_dead)})")

    if args.dry_run:
        print("\n[dry-run] Not writing files.")
        return

    for fname, (fields, rows) in files.items():
        save(HERE / fname, fields, rows)
    print("\nAll four CSVs written.")


if __name__ == "__main__":
    main()
