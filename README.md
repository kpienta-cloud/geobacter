# Geobacter GeoToxGraph

**Open the interactive knowledge-graph tool:** [GeoToxGraph Browser](https://kpienta-cloud.github.io/geobacter/)

This repository contains a strain-resolved GeoToxGraph seed build for mapping Geobacter toxin biotransformation, detoxification, immobilization, and organohalide modules. The GitHub Pages site opens directly to the interactive knowledge-graph browser, with additional layers for microbial-human evolutionary contrast mapping, compound-centered comparisons, confidence flags, and manuscript-ready matrix views.

## Quick links

- **Interactive knowledge graph:** [https://kpienta-cloud.github.io/geobacter/](https://kpienta-cloud.github.io/geobacter/)
- **Chromate toxic-inversion example:** [open example](https://kpienta-cloud.github.io/geobacter/?layer=contrast&node=compound%3Achromate)
- **Contrast matrix view:** open the browser and click **Matrix**
- **Data tables:** see [`geotoxgraph/`](./geotoxgraph/)

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
| `evolutionary_contrast_nodes.csv` | Human-vs-Geobacter evolutionary contrast node layer. |
| `evolutionary_contrast_edges.csv` | Human-vs-Geobacter evolutionary contrast edge layer. |
| `contrast_classes.yaml` | Definitions for conserved chemistry, analogous function, pathway loss, toxic inversion, and host-shifted handling. |
| `contrast_ontology.md` | Manuscript-facing ontology for contrast classes, outcomes, and required annotation fields. |
| `evidence_confidence_schema.yaml` | Evidence tiers, starting confidence-score formula, and overclaim flags. |
| `build_confidence_and_summary.py` | Reproducibly adds edge-level confidence scores/flags and regenerates manuscript summary tables. |
| `compound_contrast_summary.csv` | Compound-by-compound manuscript summary table. |
| `compound_contrast_summary.pplx.md` | Rendered manuscript-support summary table. |

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

## Evolutionary contrast layer

The browser also includes a **Human contrast map** layer. This layer compares GeoToxGraph microbial mechanisms with human exposure-handling mechanisms across:

- arsenic thiol chemistry, methylation, and efflux
- aromatic hydrocarbon oxidation/conjugation versus microbial anaerobic catabolism
- chromium redox toxic inversion
- uranium microbial immobilization versus human renal/stress response
- organohalide respiration versus human CYP/GSH toxicity-prone handling
- expanded exposure classes including cadmium, mercury, benzene, PAHs, aromatic amines, nitrosamines, aflatoxin B1, acetaldehyde, vinyl chloride, and chlorinated ethanes
- tissue contexts including liver, kidney, lung, bladder, bone marrow, esophagus, and CNS

## Curation note

MetaCyc fields are included as candidate annotations rather than verified stable BioCyc identifiers. Candidate fields are marked with `metacyc_status = candidate_unverified`.

## Interactive graph browser

This repository ships with a static, dependency-free graph browser at the repository root:

- `index.html` — entry page
- `assets/style.css`, `assets/app.js` — styling and D3.js graph code (D3 loaded from a CDN)
- `.nojekyll` — disables Jekyll so `assets/` is served verbatim

The browser reads the active graph layer directly from CSV files in `geotoxgraph/`. There is no build step.

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

- Layer switcher for the strain-resolved GeoToxGraph map and the Human contrast map
- Force-directed network of all 114 nodes / 147 edges in the strain layer
- Human contrast map with 29 nodes / 27 edges
- Expanded manuscript-ready contrast map with 60 nodes / 82 edges and 22 compounds
- Filter by strain, module, evidence tier, node type
- Free-text search across labels, identifiers, KO, EC, PubChem, ChEBI, KEGG, NCBI, UniProt
- Click a node to inspect its identifiers, description, source URL, and connected edges
- Pin or share a selected node URL using `?node=<id>` and `?layer=contrast`
- Compound-centered comparison mode with Geobacter route, human route, contrast class, tissue context, evidence, and Sankey-style outcome flow
- Edge-level confidence scores and overclaim flags displayed in evidence cards
- Compound-by-compound manuscript summary table
- Paper figure mode plus SVG/PNG graph export
- Reset view, dark/light theme toggle, keyboard shortcuts (`/` focus search, `R` reset, `Esc` deselect)
- Download the currently filtered subgraph as CSV or JSON
