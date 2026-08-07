#!/usr/bin/env python3
"""
Add confidence scores / overclaim flags to evolutionary_contrast_edges.csv
and generate compound-by-compound manuscript summary tables.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
NODES = BASE / "evolutionary_contrast_nodes.csv"
EDGES = BASE / "evolutionary_contrast_edges.csv"
SUMMARY_CSV = BASE / "compound_contrast_summary.csv"
SUMMARY_MD = BASE / "compound_contrast_summary.pplx.md"

BASE_SCORES = {"1": 0.90, "2": 0.70, "3": 0.50, "4": 0.30}

OUTCOME_LABELS = {
    "detoxification": "detoxification",
    "methylation_efflux": "methylation + efflux",
    "catabolism": "catabolism",
    "oxidation": "oxidation",
    "conjugation_excretion": "conjugation + excretion",
    "dearomatization": "dearomatization",
    "extracellular_reduction": "extracellular reduction",
    "genotoxicity": "DNA damage / genotoxicity",
    "redox_transformation": "redox transformation",
    "bioactivation": "bioactivation",
    "immobilization": "immobilization",
    "nephrotoxicity_response": "renal stress response",
    "chlororespiration": "chlororespiration",
    "oxidation_conjugation_toxicity": "oxidation / GSH toxicity",
    "detoxification_route": "detoxification route",
    "detoxtification_route": "detoxification route",  # legacy alias for misspelled key
    "toxicity_prone_metabolism": "toxicity-prone metabolism",
    "conserved_chemistry": "conserved chemistry",
    "lost_catabolic_pathway": "lost catabolic pathway",
    "excretion_not_catabolism": "excretion, not catabolism",
    "toxic_inversion": "toxic inversion",
    "stress_not_respiration": "stress response, not respiration",
    "lost_respiration": "lost respiration",
    "biosorption_biomineralization": "biosorption / biomineralization",
    "renal_tubular_toxicity": "renal tubular toxicity",
    "volatilization_detoxification": "volatilization / detoxification",
    "renal_toxicity_handling": "renal toxicity handling",
    "demethylation_reduction": "demethylation / reduction",
    "neurotoxicity_oxidative_stress": "neurotoxicity / oxidative stress",
    "detoxification_vs_neurotoxicity": "detoxification vs neurotoxicity",
    "potential_catabolism": "potential catabolism",
    "bone_marrow_toxicity": "bone marrow toxicity",
    "catabolism_vs_marrow_toxicity": "catabolism vs marrow toxicity",
    "potential_environmental_catabolism": "potential environmental catabolism",
    "DNA_adduct_genotoxicity": "DNA adduct genotoxicity",
    "environmental_catabolism_vs_dna_adducts": "environmental catabolism vs DNA adducts",
    "bladder_bioactivation": "bladder bioactivation",
    "no_host_catabolism": "no host catabolism",
    "DNA_alkylation": "DNA alkylation",
    "epoxide_liver_carcinogenesis": "epoxide liver carcinogenesis",
    "food_mycotoxin_host_bioactivation": "food mycotoxin host bioactivation",
    "detoxication_or_DNA_adducts": "detoxication or DNA adducts",
    "local_detox_capacity": "local detox capacity",
    "reductive_dechlorination_context": "reductive dechlorination context",
    "dihaloelimination_to_ethene": "dihaloelimination to ethene",
    "host_stress_response": "host stress response",
    "detoxification_vs_host_toxicity": "detoxification vs host toxicity",
    "bioactivation_marrow_toxicity": "bioactivation / marrow toxicity",
    "epoxide_bioactivation": "epoxide bioactivation",
    "local_detox_vs_DNA_damage": "local detox vs DNA damage",
}


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def uniq(items):
    out, seen = [], set()
    for item in items:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def uniq_edges(edges):
    out, seen = [], set()
    for edge in edges:
        key = edge.get("edge_id")
        if key and key not in seen:
            out.append(edge)
            seen.add(key)
    return out


def confidence_and_flags(edge: dict) -> tuple[str, str]:
    tier = str(edge.get("evidence_tier", "")).strip()
    score = BASE_SCORES.get(tier, 0.40)
    flags: set[str] = set()
    text = " ".join([
        edge.get("edge_id", ""),
        edge.get("evidence_type", ""),
        edge.get("enzyme_or_system", ""),
        edge.get("strain_id", ""),
        edge.get("effect", ""),
        edge.get("notes", ""),
    ]).lower()

    if edge.get("source_url"):
        score += 0.03
    if edge.get("predicate") in {"handled_by", "central_to"} and edge.get("source_id", "").startswith("compound:"):
        score += 0.04
    if edge.get("module_id") == "tissue_context" or "tissue" in edge.get("evidence_type", "").lower():
        score += 0.05
    if any(k in text for k in ["interpretation", "inferred", "analogy", "curated_analogy"]):
        score -= 0.10
        flags.add("outcome_inferred")
    if any(k in text for k in ["unresolved", "rdase_unresolved"]):
        score -= 0.08
        flags.add("enzyme_unresolved")
    # NOTE: matches whole tokens only. Previously the bare token 'ecosystem'
    # was matched as a substring, which flagged every ecosystem-outsourced
    # edge (~14 of the resource's 36 species_generalized flags were pure
    # string artifacts from edge_ids containing 'ecosystem'). Fixed in the
    # v6 audit revision to require a genuine species-generalization signal.
    species_generalization_signals = [
        "environmental_microbes",  # strain_id shorthand for uncultured refs
        "review_literature",       # review-level evidence_type
        "not asserted",            # explicit hedging text in notes
        "general microbial",       # multi-word prose hedge
    ]
    if any(k in text for k in species_generalization_signals):
        score -= 0.08
        flags.add("species_generalized")
    if edge.get("target_id", "").startswith("human:") and "tissue" not in text and edge.get("module_id") != "tissue_context":
        flags.add("tissue_generalized")
    if "microbiome" in text or "candidate" in text:
        flags.add("microbiome_candidate")

    score = max(0.20, min(0.98, score))
    return f"{score:.2f}", ";".join(sorted(flags)) if flags else "none"


def label_outcome(effect: str) -> str:
    return OUTCOME_LABELS.get(effect, (effect or "").replace("_", " "))


def md_cell(text: str) -> str:
    text = str(text or "—")
    return text.replace("|", "<br>").replace("\n", " ")


def main() -> None:
    nodes = read_csv(NODES)
    edges = read_csv(EDGES)
    node_by_id = {n["id"]: n for n in nodes}
    edges_by_node: dict[str, list[dict]] = defaultdict(list)

    for edge in edges:
        score, flags = confidence_and_flags(edge)
        edge["confidence_score"] = score
        edge["overclaim_flags"] = flags
        edge["outcome_label"] = label_outcome(edge.get("effect", ""))
        edges_by_node[edge["source_id"]].append(edge)
        edges_by_node[edge["target_id"]].append(edge)

    edge_fields = list(edges[0].keys())
    for col in ["confidence_score", "overclaim_flags", "outcome_label"]:
        if col not in edge_fields:
            edge_fields.append(col)
    write_csv(EDGES, edges, edge_fields)

    summary_rows = []
    compounds = sorted([n for n in nodes if n["node_type"] == "compound"], key=lambda n: n["label"])
    for compound in compounds:
        direct_edges = edges_by_node[compound["id"]]
        microbial_edges = [
            e for e in direct_edges
            if node_by_id.get(e["source_id"], {}).get("node_type") == "microbe"
            or node_by_id.get(e["target_id"], {}).get("node_type") == "microbe"
        ]
        human_edges = [
            e for e in direct_edges
            if node_by_id.get(e["source_id"], {}).get("node_type") == "human"
            or node_by_id.get(e["target_id"], {}).get("node_type") == "human"
        ]
        contrast_edges = [
            e for e in direct_edges
            if node_by_id.get(e["source_id"], {}).get("node_type") == "contrast"
            or node_by_id.get(e["target_id"], {}).get("node_type") == "contrast"
        ]

        mechanisms = []
        for e in microbial_edges + human_edges:
            for endpoint in [e["source_id"], e["target_id"]]:
                n = node_by_id.get(endpoint)
                if n and n["node_type"] in {"microbe", "human"}:
                    mechanisms.append(n)

        neighborhood_edges = []
        tissue_nodes = []
        contrast_nodes = []
        for mech in mechanisms:
            for e in edges_by_node[mech["id"]]:
                neighborhood_edges.append(e)
                other_id = e["target_id"] if e["source_id"] == mech["id"] else e["source_id"]
                other = node_by_id.get(other_id)
                if not other:
                    continue
                if other["node_type"] == "tissue":
                    tissue_nodes.append(other)
                if other["node_type"] == "contrast":
                    contrast_nodes.append(other)

        all_relevant = uniq_edges(direct_edges + neighborhood_edges)
        scores = [float(e["confidence_score"]) for e in all_relevant if e.get("confidence_score")]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        flags = uniq(flag for e in all_relevant for flag in e.get("overclaim_flags", "").split(";") if flag and flag != "none")
        if tissue_nodes:
            flags = [flag for flag in flags if flag != "tissue_generalized"]
        sources = uniq(e.get("source_url", "") for e in all_relevant if e.get("source_url"))[:5]

        summary_rows.append({
            "compound_id": compound["id"],
            "compound": compound["label"],
            "compound_class": compound["entity_class"],
            "microbial_route": " | ".join(uniq(node_by_id[e["target_id"] if e["source_id"] == compound["id"] else e["source_id"]]["label"] for e in microbial_edges if node_by_id.get(e["target_id"] if e["source_id"] == compound["id"] else e["source_id"]))),
            "microbial_outcome": " | ".join(uniq(label_outcome(e.get("effect", "")) for e in microbial_edges)),
            "human_route": " | ".join(uniq(node_by_id[e["target_id"] if e["source_id"] == compound["id"] else e["source_id"]]["label"] for e in human_edges if node_by_id.get(e["target_id"] if e["source_id"] == compound["id"] else e["source_id"]))),
            "human_outcome": " | ".join(uniq(label_outcome(e.get("effect", "")) for e in human_edges)),
            "human_tissue_context": " | ".join(uniq(t["label"] for t in tissue_nodes)),
            "contrast_class": " | ".join(uniq(n["label"] for n in contrast_nodes + [node_by_id[e["target_id"] if e["source_id"] == compound["id"] else e["source_id"]] for e in contrast_edges if node_by_id.get(e["target_id"] if e["source_id"] == compound["id"] else e["source_id"])])),
            "mean_confidence_score": f"{mean_score:.2f}",
            "minimum_confidence_score": f"{min_score:.2f}",
            "overclaim_flags": ";".join(flags) if flags else "none",
            "key_sources": " | ".join(sources),
            "summary_note": compound["description"],
        })

    summary_fields = [
        "compound_id", "compound", "compound_class", "microbial_route", "microbial_outcome",
        "human_route", "human_outcome", "human_tissue_context", "contrast_class",
        "mean_confidence_score", "minimum_confidence_score", "overclaim_flags", "key_sources",
        "summary_note",
    ]
    write_csv(SUMMARY_CSV, summary_rows, summary_fields)

    with SUMMARY_MD.open("w", encoding="utf-8") as f:
        f.write("# Compound-by-compound evolutionary contrast summary\n\n")
        f.write("This manuscript-support table summarizes the active contrast graph after applying evidence-tier-derived confidence scores and overclaim flags.\n\n")
        f.write("| Compound | Microbial route | Human route | Tissue context | Contrast class | Mean confidence | Flags |\n")
        f.write("| --- | --- | --- | --- | --- | ---: | --- |\n")
        for r in summary_rows:
            f.write(
                f"| {md_cell(r['compound'])} | {md_cell(r['microbial_route'])} | {md_cell(r['human_route'])} | "
                f"{md_cell(r['human_tissue_context'])} | {md_cell(r['contrast_class'])} | "
                f"{md_cell(r['mean_confidence_score'])} | {md_cell(r['overclaim_flags'])} |\n"
            )
        f.write("\n## Scoring note\n\n")
        f.write("Scores are heuristic manuscript-curation scores derived from evidence tier, source provenance, compound specificity, tissue specificity, and interpretive penalties. They are not kinetic or probabilistic estimates.\n")


if __name__ == "__main__":
    main()
