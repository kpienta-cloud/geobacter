# Geobacter GeoToxGraph

This repository contains a strain-resolved GeoToxGraph seed build for mapping Geobacter toxin biotransformation, detoxification, immobilization, and organohalide modules.

## Contents

The main package is in [`geotoxgraph/`](./geotoxgraph/).

| File | Purpose |
| --- | --- |
| `geotoxgraph_nodes.csv` | Curated seed node table. |
| `geotoxgraph_edges.csv` | Curated seed edge table. |
| `geotoxgraph_nodes_enriched.csv` | KEGG/PubChem/ChEBI/NCBI-enriched node table. |
| `geotoxgraph_edges_enriched.csv` | Enriched directed edge table with evidence tiers. |
| `neo4j_nodes.csv` | Neo4j node import file. |
| `neo4j_relationships.csv` | Neo4j relationship import file. |
| `geotoxgraph.graphml` | Directed GraphML export. |
| `geotoxgraph_schema.md` | Graph schema and evidence-tier definitions. |
| `neo4j_import_readme.md` | Neo4j import instructions. |
| `build_enriched_geotoxgraph.py` | Reproducible enrichment script. |
| `geotoxgraph_enrichment_report.pplx.md` | Summary of the enrichment pass. |

## Current graph size

- 114 enriched nodes
- 147 directed edges
- 40 individual KEGG loci fetched
- 51 nodes with KO IDs
- 40 nodes with EC numbers
- 21 compound nodes with PubChem and ChEBI IDs
- 62 nodes with NCBI ProteinIDs

## Included strain modules

- *Geobacter metallireducens* GS-15 aromatics and arsenic modules
- *Geobacter sulfurreducens* PCA arsenic and metal-redox modules
- *Geobacter lovleyi* SZ organohalide module
- Geobacter sp. strain IAE chlorinated-ethane dihaloelimination module

## Curation note

MetaCyc fields are included as candidate annotations rather than verified stable BioCyc identifiers. Candidate fields are marked with `metacyc_status = candidate_unverified`.
