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

## Interactive graph browser

This repository ships with a static, dependency-free graph browser at the repository root:

- `index.html` — entry page
- `assets/style.css`, `assets/app.js` — styling and D3.js graph code (D3 loaded from a CDN)
- `.nojekyll` — disables Jekyll so `assets/` is served verbatim

The browser reads `geotoxgraph/geotoxgraph_nodes_enriched.csv` and `geotoxgraph/geotoxgraph_edges_enriched.csv` directly in the client. There is no build step.

### Run locally

Browsers block CSV fetches from `file://` URLs, so serve via any static HTTP server:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/
```

### Deploy on GitHub Pages

1. Push the repository to GitHub.
2. In **Settings → Pages**, set **Source** to **Deploy from a branch**, **Branch** = `main`, **Folder** = `/ (root)`.
3. GitHub will serve `index.html` at `https://<user>.github.io/<repo>/`.

The `.nojekyll` file ensures the `assets/` directory and dotfiles are served as-is.

### Features

- Force-directed network of all 114 nodes / 147 edges
- Filter by strain, module, evidence tier, node type
- Free-text search across labels, identifiers, KO, EC, PubChem, ChEBI, KEGG, NCBI, UniProt
- Click a node to inspect its identifiers, description, source URL, and connected edges
- Reset view, dark/light theme toggle, keyboard shortcuts (`/` focus search, `R` reset, `Esc` deselect)
- Download the currently filtered subgraph as CSV or JSON
