#!/usr/bin/env python3
"""
Build an enriched, import-ready GeoToxGraph from the curated seed CSVs.

Outputs:
- geotoxgraph_nodes_enriched.csv
- geotoxgraph_edges_enriched.csv
- neo4j_nodes.csv
- neo4j_relationships.csv
- geotoxgraph.graphml
- geotoxgraph_enrichment_summary.json
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

BASE = Path("/home/user/workspace/geotoxgraph")
NODES_IN = BASE / "geotoxgraph_nodes.csv"
EDGES_IN = BASE / "geotoxgraph_edges.csv"


def read_csv(path: Path) -> List[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fetch_text(url: str, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                return response.read().decode("utf-8", "replace")
        except Exception:
            if attempt == retries:
                return ""
            time.sleep(0.5 + attempt)
    return ""


def parse_kegg_entry(text: str) -> dict:
    """Parse the compact subset of KEGG flat-file fields needed here."""
    out = {
        "kegg_entry": "",
        "kegg_symbol": "",
        "kegg_name": "",
        "ko_ids": [],
        "ec_numbers": [],
        "kegg_pathways": [],
        "kegg_modules": [],
        "ncbi_protein_ids": [],
        "uniprot_ids": [],
        "position": "",
    }
    if not text.strip():
        return out

    current = None
    field_lines: Dict[str, List[str]] = defaultdict(list)
    for line in text.splitlines():
        if not line.strip():
            continue
        key = line[:12].strip()
        val = line[12:].strip()
        if key:
            current = key
            field_lines[current].append(val)
        elif current:
            field_lines[current].append(val)

    if "ENTRY" in field_lines:
        out["kegg_entry"] = field_lines["ENTRY"][0].split()[0]
    if "SYMBOL" in field_lines:
        out["kegg_symbol"] = ";".join(field_lines["SYMBOL"])
    if "NAME" in field_lines:
        out["kegg_name"] = "; ".join(field_lines["NAME"])
    if "ORTHOLOGY" in field_lines:
        orth = " ".join(field_lines["ORTHOLOGY"])
        out["ko_ids"] = sorted(set(re.findall(r"\bK\d{5}\b", orth)))
        out["ec_numbers"] = sorted(set(re.findall(r"EC:([0-9.-]+\.[0-9.-]+\.[0-9.-]+\.[0-9.-]+)", orth)))
    if "BRITE" in field_lines:
        brite = " ".join(field_lines["BRITE"])
        out["ec_numbers"] = sorted(set(out["ec_numbers"] + re.findall(r"\b([0-9]+\.[0-9.-]+\.[0-9.-]+\.[0-9.-]+)\b", brite)))
    if "PATHWAY" in field_lines:
        for p in field_lines["PATHWAY"]:
            parts = p.split(None, 1)
            if parts:
                out["kegg_pathways"].append({"id": parts[0], "name": parts[1] if len(parts) > 1 else ""})
    if "MODULE" in field_lines:
        for m in field_lines["MODULE"]:
            parts = m.split(None, 1)
            if parts:
                out["kegg_modules"].append({"id": parts[0], "name": parts[1] if len(parts) > 1 else ""})
    if "DBLINKS" in field_lines:
        dblink_text = " ".join(field_lines["DBLINKS"])
        out["ncbi_protein_ids"] = sorted(set(re.findall(r"NCBI-ProteinID:\s*([A-Z0-9_.]+)", dblink_text)))
        # KEGG continuation lines often collapse to "... UniProt: Q..."
        out["uniprot_ids"] = sorted(set(re.findall(r"UniProt:\s*([A-Z0-9_; ]+)", dblink_text)[0].split())) if "UniProt:" in dblink_text else []
    if "POSITION" in field_lines:
        out["position"] = ";".join(field_lines["POSITION"])
    return out


GENE_MEMBERS = {
    "gene:gmet_bsscab": ["Gmet_1538", "Gmet_1539", "Gmet_1540"],
    "gene:gmet_bbsabcd": ["Gmet_1528", "Gmet_1529", "Gmet_1530", "Gmet_1531"],
    "gene:gmet_bbs_efgh": ["Gmet_1521", "Gmet_1522", "Gmet_1523", "Gmet_1524"],
    "gene:gmet_phenylphosphate_synthase": ["Gmet_2100", "Gmet_2101"],
    "gene:gmet_phenylphosphate_carboxylase": ["Gmet_2102"],
    "gene:gmet_p_cresol_methylhydroxylase": ["Gmet_2125", "Gmet_2126"],
    "gene:gmet_2131_dehydrogenase": ["Gmet_2131"],
    "gene:gmet_2235_dehydrogenase": ["Gmet_2235"],
    "gene:gmet_4hbcoa_reductase": ["Gmet_2134", "Gmet_2135", "Gmet_2136"],
    "gene:gmet_bam_y": ["Gmet_2143"],
    "gene:gmet_bamb": ["Gmet_2087"],
    "gene:gmet_bamc": ["Gmet_2086"],
    "gene:gmet_bamr": ["Gmet_2150"],
    "gene:gmet_bamq": ["Gmet_2151"],
    "gene:gmet_oah2": ["Gmet_3305"],
    "gene:gsu_ars_operon": [f"GSU{i}" for i in range(2950, 2960)],
    "gene:gsu_arsr1": ["GSU2952"],
    "gene:gsu_arsc": ["GSU2953"],
    "gene:gsu_acr3": ["GSU2954"],
    "gene:gmet_arsc": ["Gmet_0521"],
    "gene:gmet_acr3": ["Gmet_0520"],
    "gene:gmet_arsm": ["Gmet_2791"],
}


COMPOUND_XREFS = {
    "compound:toluene": {"pubchem_cid": "1140", "kegg_compound": "C01455", "chebi_id": "CHEBI:17578", "metacyc_candidate": "TOLUENE"},
    "compound:phenol": {"pubchem_cid": "996", "kegg_compound": "C00146", "chebi_id": "CHEBI:15882", "metacyc_candidate": "PHENOL"},
    "compound:p_cresol": {"pubchem_cid": "2879", "kegg_compound": "C01468", "chebi_id": "CHEBI:17847", "metacyc_candidate": "P-CRESOL"},
    "compound:benzyl_alcohol": {"pubchem_cid": "244", "kegg_compound": "C00556", "chebi_id": "CHEBI:17987", "metacyc_candidate": "BENZYL-ALCOHOL"},
    "compound:benzaldehyde": {"pubchem_cid": "240", "kegg_compound": "C00261", "chebi_id": "CHEBI:17169", "metacyc_candidate": "BENZALDEHYDE"},
    "compound:4_hydroxybenzaldehyde": {"pubchem_cid": "126", "kegg_compound": "C00633", "chebi_id": "CHEBI:17702", "metacyc_candidate": "CPD-125"},
    "compound:4_hydroxybenzoate": {"pubchem_cid": "135", "kegg_compound": "C00156", "chebi_id": "CHEBI:30763", "metacyc_candidate": "4-HYDROXYBENZOATE"},
    "compound:benzoate": {"pubchem_cid": "242", "kegg_compound": "C00180", "chebi_id": "CHEBI:16150", "metacyc_candidate": "BENZOATE"},
    "compound:benzoyl_coa": {"pubchem_cid": "9543169", "kegg_compound": "C00512", "chebi_id": "CHEBI:15515", "metacyc_candidate": "BENZOYL-COA"},
    "compound:acetyl_coa": {"pubchem_cid": "444493", "kegg_compound": "C00024", "chebi_id": "CHEBI:15351", "metacyc_candidate": "ACETYL-COA"},
    "compound:arsenate": {"pubchem_cid": "27401", "kegg_compound": "C11215", "chebi_id": "CHEBI:22631", "metacyc_candidate": ""},
    "compound:arsenite": {"pubchem_cid": "544", "kegg_compound": "C06697", "chebi_id": "CHEBI:22632", "metacyc_candidate": ""},
    "compound:chromate": {"pubchem_cid": "24461", "kegg_compound": "", "chebi_id": "CHEBI:35404", "metacyc_candidate": ""},
    "compound:uranium_vi": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:uranium_iv": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:vanadium_v": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:vanadium_iv": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:manganese_vii": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:manganese_iv": {"pubchem_cid": "", "kegg_compound": "", "chebi_id": "", "metacyc_candidate": ""},
    "compound:pce": {"pubchem_cid": "31373", "kegg_compound": "C06789", "chebi_id": "CHEBI:17300", "metacyc_candidate": "TETRACHLOROETHENE"},
    "compound:tce": {"pubchem_cid": "6575", "kegg_compound": "C06790", "chebi_id": "CHEBI:16602", "metacyc_candidate": "TRICHLOROETHENE"},
    "compound:cis_dce": {"pubchem_cid": "643833", "kegg_compound": "C06792", "chebi_id": "CHEBI:28805", "metacyc_candidate": "CIS-1,2-DICHLOROETHENE"},
    "compound:1_2_dca": {"pubchem_cid": "11", "kegg_compound": "C06752", "chebi_id": "CHEBI:27789", "metacyc_candidate": "1,2-DICHLOROETHANE"},
    "compound:1_1_2_tca": {"pubchem_cid": "6574", "kegg_compound": "C19536", "chebi_id": "CHEBI:36018", "metacyc_candidate": "1,1,2-TRICHLOROETHANE"},
    "compound:vinyl_chloride": {"pubchem_cid": "6338", "kegg_compound": "C06793", "chebi_id": "CHEBI:28509", "metacyc_candidate": "VINYL-CHLORIDE"},
    "compound:ethene": {"pubchem_cid": "6325", "kegg_compound": "C06547", "chebi_id": "CHEBI:18153", "metacyc_candidate": "ETHYLENE"},
}


def kegg_gene_id(strain: str, locus: str) -> str:
    if strain == "gsu_pca" or locus.startswith("GSU"):
        return f"gsu:{locus}"
    if strain == "gmet_gs15" or locus.startswith("Gmet_"):
        return f"gme:{locus}"
    return ""


def main() -> None:
    nodes = read_csv(NODES_IN)
    edges = read_csv(EDGES_IN)

    # Fetch KEGG annotations for all individual loci represented in seed gene/operon nodes.
    all_loci: Dict[str, dict] = {}
    for parent_id, loci in GENE_MEMBERS.items():
        parent = next((n for n in nodes if n["id"] == parent_id), None)
        if not parent:
            continue
        for locus in loci:
            kgid = kegg_gene_id(parent.get("strain_id", ""), locus)
            if not kgid or kgid in all_loci:
                continue
            text = fetch_text(f"https://rest.kegg.jp/get/{kgid}")
            parsed = parse_kegg_entry(text)
            parsed["kegg_gene_id"] = kgid
            parsed["locus_tag"] = locus
            parsed["source_url"] = f"https://rest.kegg.jp/get/{kgid}"
            all_loci[kgid] = parsed

    # Enrich base nodes.
    enriched_nodes: List[dict] = []
    for n in nodes:
        n = dict(n)
        n.setdefault("kegg_gene_ids", "")
        n.setdefault("ko_ids", "")
        n.setdefault("ec_numbers", "")
        n.setdefault("kegg_pathways", "")
        n.setdefault("kegg_modules", "")
        n.setdefault("ncbi_protein_ids", "")
        n.setdefault("uniprot_ids", "")
        n.setdefault("pubchem_cid", "")
        n.setdefault("kegg_compound", "")
        n.setdefault("chebi_id", "")
        n.setdefault("metacyc_candidate", "")
        n.setdefault("metacyc_status", "")
        n.setdefault("annotation_status", "seed_curated")

        if n["id"] in GENE_MEMBERS:
            member_annotations = [all_loci.get(kegg_gene_id(n.get("strain_id", ""), locus), {}) for locus in GENE_MEMBERS[n["id"]]]
            n["kegg_gene_ids"] = ";".join([m.get("kegg_gene_id", "") for m in member_annotations if m.get("kegg_gene_id")])
            n["ko_ids"] = ";".join(sorted({x for m in member_annotations for x in m.get("ko_ids", [])}))
            n["ec_numbers"] = ";".join(sorted({x for m in member_annotations for x in m.get("ec_numbers", [])}))
            n["kegg_pathways"] = ";".join(sorted({p["id"] for m in member_annotations for p in m.get("kegg_pathways", [])}))
            n["kegg_modules"] = ";".join(sorted({mo["id"] for m in member_annotations for mo in m.get("kegg_modules", [])}))
            n["ncbi_protein_ids"] = ";".join(sorted({x for m in member_annotations for x in m.get("ncbi_protein_ids", [])}))
            n["uniprot_ids"] = ";".join(sorted({x for m in member_annotations for x in m.get("uniprot_ids", [])}))
            n["annotation_status"] = "kegg_enriched"

        if n["id"] in COMPOUND_XREFS:
            n.update(COMPOUND_XREFS[n["id"]])
            n["metacyc_status"] = "candidate_unverified" if n.get("metacyc_candidate") else ""
            n["annotation_status"] = "compound_xref_enriched"

        enriched_nodes.append(n)

    enriched_edges: List[dict] = [dict(e) for e in edges]

    # Add individual locus nodes and membership edges.
    existing_ids = {n["id"] for n in enriched_nodes}
    pathway_nodes: Dict[str, dict] = {}
    module_nodes: Dict[str, dict] = {}

    for parent_id, loci in GENE_MEMBERS.items():
        parent = next((n for n in enriched_nodes if n["id"] == parent_id), None)
        if not parent:
            continue
        for locus in loci:
            kgid = kegg_gene_id(parent.get("strain_id", ""), locus)
            ann = all_loci.get(kgid, {})
            member_id = f"gene:{kgid.replace(':', '_')}"
            if member_id not in existing_ids:
                label = ann.get("kegg_symbol") or locus
                name = ann.get("kegg_name") or parent.get("description", "")
                enriched_nodes.append({
                    "id": member_id,
                    "label": f"{locus} {label}".strip(),
                    "node_type": "gene",
                    "strain_id": parent.get("strain_id", ""),
                    "module_id": parent.get("module_id", ""),
                    "entity_class": "individual_locus",
                    "identifier": locus,
                    "description": name,
                    "source_url": ann.get("source_url", ""),
                    "kegg_gene_ids": kgid,
                    "ko_ids": ";".join(ann.get("ko_ids", [])),
                    "ec_numbers": ";".join(ann.get("ec_numbers", [])),
                    "kegg_pathways": ";".join(p["id"] for p in ann.get("kegg_pathways", [])),
                    "kegg_modules": ";".join(m["id"] for m in ann.get("kegg_modules", [])),
                    "ncbi_protein_ids": ";".join(ann.get("ncbi_protein_ids", [])),
                    "uniprot_ids": ";".join(ann.get("uniprot_ids", [])),
                    "pubchem_cid": "",
                    "kegg_compound": "",
                    "chebi_id": "",
                    "metacyc_candidate": "",
                    "metacyc_status": "",
                    "annotation_status": "kegg_individual_locus",
                })
                existing_ids.add(member_id)
            enriched_edges.append({
                "edge_id": f"edge:{member_id}_member_of_{parent_id}",
                "source_id": member_id,
                "target_id": parent_id,
                "predicate": "member_of",
                "enzyme_or_system": member_id,
                "strain_id": parent.get("strain_id", ""),
                "module_id": parent.get("module_id", ""),
                "evidence_tier": "1" if ann.get("kegg_entry") else "3",
                "evidence_type": "kegg_gene_annotation",
                "effect": "structural_annotation",
                "source_url": ann.get("source_url", ""),
                "notes": "Individual KEGG locus expanded from seed cluster/operon node",
            })

            for p in ann.get("kegg_pathways", []):
                pid = f"pathway:kegg_{p['id']}"
                pathway_nodes[pid] = {
                    "id": pid,
                    "label": f"KEGG {p['id']} {p['name']}",
                    "node_type": "pathway",
                    "strain_id": parent.get("strain_id", ""),
                    "module_id": parent.get("module_id", ""),
                    "entity_class": "kegg_pathway",
                    "identifier": p["id"],
                    "description": p["name"],
                    "source_url": f"https://www.kegg.jp/pathway/{p['id']}",
                    "kegg_gene_ids": "",
                    "ko_ids": "",
                    "ec_numbers": "",
                    "kegg_pathways": p["id"],
                    "kegg_modules": "",
                    "ncbi_protein_ids": "",
                    "uniprot_ids": "",
                    "pubchem_cid": "",
                    "kegg_compound": "",
                    "chebi_id": "",
                    "metacyc_candidate": "",
                    "metacyc_status": "",
                    "annotation_status": "kegg_pathway_node",
                }
                enriched_edges.append({
                    "edge_id": f"edge:{member_id}_participates_in_{pid}",
                    "source_id": member_id,
                    "target_id": pid,
                    "predicate": "participates_in",
                    "enzyme_or_system": member_id,
                    "strain_id": parent.get("strain_id", ""),
                    "module_id": parent.get("module_id", ""),
                    "evidence_tier": "2",
                    "evidence_type": "kegg_pathway_annotation",
                    "effect": "pathway_membership",
                    "source_url": f"https://rest.kegg.jp/get/{kgid}",
                    "notes": p["name"],
                })

            for m in ann.get("kegg_modules", []):
                mid = f"pathway:kegg_{m['id']}"
                module_nodes[mid] = {
                    "id": mid,
                    "label": f"KEGG {m['id']} {m['name']}",
                    "node_type": "pathway",
                    "strain_id": parent.get("strain_id", ""),
                    "module_id": parent.get("module_id", ""),
                    "entity_class": "kegg_module",
                    "identifier": m["id"],
                    "description": m["name"],
                    "source_url": f"https://www.kegg.jp/module/{m['id']}",
                    "kegg_gene_ids": "",
                    "ko_ids": "",
                    "ec_numbers": "",
                    "kegg_pathways": "",
                    "kegg_modules": m["id"],
                    "ncbi_protein_ids": "",
                    "uniprot_ids": "",
                    "pubchem_cid": "",
                    "kegg_compound": "",
                    "chebi_id": "",
                    "metacyc_candidate": "",
                    "metacyc_status": "",
                    "annotation_status": "kegg_module_node",
                }
                enriched_edges.append({
                    "edge_id": f"edge:{member_id}_participates_in_{mid}",
                    "source_id": member_id,
                    "target_id": mid,
                    "predicate": "participates_in",
                    "enzyme_or_system": member_id,
                    "strain_id": parent.get("strain_id", ""),
                    "module_id": parent.get("module_id", ""),
                    "evidence_tier": "2",
                    "evidence_type": "kegg_module_annotation",
                    "effect": "module_membership",
                    "source_url": f"https://rest.kegg.jp/get/{kgid}",
                    "notes": m["name"],
                })

    for extra in list(pathway_nodes.values()) + list(module_nodes.values()):
        if extra["id"] not in existing_ids:
            enriched_nodes.append(extra)
            existing_ids.add(extra["id"])

    endpoint_nodes = [
        {
            "id": "extracellular:arsenite",
            "label": "Extracellular arsenite As(III)",
            "node_type": "compound",
            "strain_id": "",
            "module_id": "gsu_arsenic;gmet_arsenic",
            "entity_class": "exported_toxicant",
            "identifier": "extracellular_pool",
            "description": "Extracellular arsenite pool after Acr3-mediated efflux",
            "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5288829/",
            "kegg_gene_ids": "",
            "ko_ids": "",
            "ec_numbers": "",
            "kegg_pathways": "",
            "kegg_modules": "",
            "ncbi_protein_ids": "",
            "uniprot_ids": "",
            "pubchem_cid": "544",
            "kegg_compound": "C06697",
            "chebi_id": "CHEBI:22632",
            "metacyc_candidate": "",
            "metacyc_status": "",
            "annotation_status": "endpoint_node",
        },
        {
            "id": "compound:methylated_arsenicals",
            "label": "Methylated arsenicals",
            "node_type": "compound",
            "strain_id": "",
            "module_id": "gmet_arsenic",
            "entity_class": "predicted_arsenic_product_class",
            "identifier": "class_node",
            "description": "Predicted ArsM product class; individual methylated arsenic species not resolved in this seed graph",
            "source_url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5288829/",
            "kegg_gene_ids": "",
            "ko_ids": "",
            "ec_numbers": "",
            "kegg_pathways": "",
            "kegg_modules": "",
            "ncbi_protein_ids": "",
            "uniprot_ids": "",
            "pubchem_cid": "",
            "kegg_compound": "",
            "chebi_id": "",
            "metacyc_candidate": "",
            "metacyc_status": "",
            "annotation_status": "endpoint_class_node",
        },
    ]
    for endpoint in endpoint_nodes:
        if endpoint["id"] not in existing_ids:
            enriched_nodes.append(endpoint)
            existing_ids.add(endpoint["id"])

    # De-duplicate edges by edge_id.
    dedup_edges = {}
    for e in enriched_edges:
        dedup_edges[e["edge_id"]] = e
    enriched_edges = list(dedup_edges.values())

    node_fields = [
        "id", "label", "node_type", "strain_id", "module_id", "entity_class", "identifier",
        "description", "source_url", "kegg_gene_ids", "ko_ids", "ec_numbers", "kegg_pathways",
        "kegg_modules", "ncbi_protein_ids", "uniprot_ids", "pubchem_cid", "kegg_compound",
        "chebi_id", "metacyc_candidate", "metacyc_status", "annotation_status"
    ]
    edge_fields = [
        "edge_id", "source_id", "target_id", "predicate", "enzyme_or_system", "strain_id",
        "module_id", "evidence_tier", "evidence_type", "effect", "source_url", "notes"
    ]
    write_csv(BASE / "geotoxgraph_nodes_enriched.csv", enriched_nodes, node_fields)
    write_csv(BASE / "geotoxgraph_edges_enriched.csv", enriched_edges, edge_fields)

    # Neo4j CSVs.
    neo_nodes = []
    for n in enriched_nodes:
        label = n["node_type"].replace("-", "_").title()
        if n.get("entity_class"):
            label += ";" + re.sub(r"[^A-Za-z0-9_]", "_", n["entity_class"]).title()
        neo = {":ID": n["id"], ":LABEL": label, "name": n["label"]}
        for k in node_fields:
            if k not in {"id", "label"}:
                neo[k] = n.get(k, "")
        neo_nodes.append(neo)

    neo_edges = []
    for e in enriched_edges:
        rel_type = re.sub(r"[^A-Za-z0-9_]", "_", e["predicate"]).upper()
        neo = {":START_ID": e["source_id"], ":END_ID": e["target_id"], ":TYPE": rel_type}
        for k in edge_fields:
            if k not in {"source_id", "target_id", "predicate"}:
                neo[k] = e.get(k, "")
        neo_edges.append(neo)

    neo_node_fields = [":ID", ":LABEL", "name"] + [x for x in node_fields if x not in {"id", "label"}]
    neo_edge_fields = [":START_ID", ":END_ID", ":TYPE"] + [x for x in edge_fields if x not in {"source_id", "target_id", "predicate"}]
    write_csv(BASE / "neo4j_nodes.csv", neo_nodes, neo_node_fields)
    write_csv(BASE / "neo4j_relationships.csv", neo_edges, neo_edge_fields)

    # Dependency-free GraphML writer.
    graphml_ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", graphml_ns)
    root = ET.Element(f"{{{graphml_ns}}}graphml")
    attr_keys = []
    for field in node_fields:
        if field != "id":
            attr_keys.append(("node", field, f"n_{field}"))
    for field in edge_fields:
        if field not in {"source_id", "target_id"}:
            attr_keys.append(("edge", field, f"e_{field}"))
    for domain, name, key_id in attr_keys:
        ET.SubElement(root, f"{{{graphml_ns}}}key", id=key_id, **{"for": domain, "attr.name": name, "attr.type": "string"})
    graph_el = ET.SubElement(root, f"{{{graphml_ns}}}graph", edgedefault="directed", id="GeoToxGraph")
    for n in enriched_nodes:
        node_el = ET.SubElement(graph_el, f"{{{graphml_ns}}}node", id=n["id"])
        for field in node_fields:
            if field == "id":
                continue
            data_el = ET.SubElement(node_el, f"{{{graphml_ns}}}data", key=f"n_{field}")
            data_el.text = "" if n.get(field) is None else str(n.get(field, ""))
    for e in enriched_edges:
        edge_el = ET.SubElement(graph_el, f"{{{graphml_ns}}}edge", id=e["edge_id"], source=e["source_id"], target=e["target_id"])
        for field in edge_fields:
            if field in {"source_id", "target_id"}:
                continue
            data_el = ET.SubElement(edge_el, f"{{{graphml_ns}}}data", key=f"e_{field}")
            data_el.text = "" if e.get(field) is None else str(e.get(field, ""))
    ET.ElementTree(root).write(BASE / "geotoxgraph.graphml", encoding="utf-8", xml_declaration=True)

    summary = {
        "base_nodes": len(nodes),
        "base_edges": len(edges),
        "enriched_nodes": len(enriched_nodes),
        "enriched_edges": len(enriched_edges),
        "individual_kegg_loci_fetched": len(all_loci),
        "kegg_pathway_nodes": len(pathway_nodes),
        "kegg_module_nodes": len(module_nodes),
        "nodes_with_ko": sum(1 for n in enriched_nodes if n.get("ko_ids")),
        "nodes_with_ec": sum(1 for n in enriched_nodes if n.get("ec_numbers")),
        "nodes_with_pubchem": sum(1 for n in enriched_nodes if n.get("pubchem_cid")),
        "nodes_with_chebi": sum(1 for n in enriched_nodes if n.get("chebi_id")),
        "nodes_with_ncbi_protein": sum(1 for n in enriched_nodes if n.get("ncbi_protein_ids")),
        "metacyc_candidate_nodes": sum(1 for n in enriched_nodes if n.get("metacyc_candidate")),
        "generated_files": [
            "geotoxgraph_nodes_enriched.csv",
            "geotoxgraph_edges_enriched.csv",
            "neo4j_nodes.csv",
            "neo4j_relationships.csv",
            "geotoxgraph.graphml",
        ],
    }
    (BASE / "geotoxgraph_enrichment_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
