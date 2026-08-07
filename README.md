# GeoToxGraph

**Open the interactive knowledge-graph tool:** [GeoToxGraph Browser](https://kpienta-cloud.github.io/geobacter/)

GeoToxGraph is a strain-resolved microbial reference graph for evolutionary carcinogen susceptibility. It maps microbial carcinogen handling into a four-compartment evolutionary loss ontology (microbial-only, human-lineage, polymorphic, ecosystem-outsourced), plus a reference class for chemistry conserved between humans and microbes. Every edge carries a citable source URL, a discrete evidence tier, and, in the contrast layer, a deterministic confidence score and an overclaim flag; every source URL has been resolved against NCBI E-utilities and matched to the assertion it annotates.

The current release covers 13 microbial strains, including a core of four *Geobacter* strains and *Dehalococcoides mccartyi* 195 that originated as an organohalide-respiration and metal-reduction resource, plus eight further strains added since PR7 to support five demonstration carcinogens (4-aminobiphenyl, aflatoxin B1, N-nitrosodimethylamine, benzo[a]pyrene, inorganic arsenic). The GitHub Pages site opens directly to the interactive knowledge-graph browser with subgraph filtering, per-node inspector panels, CSV/JSON export, SVG/PNG figure-mode export, a compound-by-compartment matrix view, and a strain-catalog view. The historical repository URL retains the *geobacter* slug because it was the original organohalide-respiration resource; the resource itself now serves both purposes.

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

- 114 enriched nodes (plus 82 evolutionary_contrast layer nodes)
- 150 directed edges (plus 139 evolutionary_contrast edges)
- 40 individual KEGG loci fetched
- 52 nodes with KO IDs
- 41 nodes with EC numbers
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

### Pathway-loss subclasses (v3, August 2026)

The pathway_loss contrast class now distinguishes three scales of lost carcinogen-handling capacity. Every pathway_loss annotation may carry a `contrast_subclass` tag when the evidence supports one.

| Subclass | Scale | Example |
| --- | --- | --- |
| `microbial_only` | Loss during metazoan or vertebrate evolution; predates the primate radiation | Anaerobic benzoyl-CoA dearomatization; organohalide respiration |
| `human_lineage` | Pseudogenization or fixed loss-of-function in Homo sapiens | GULO, uricase (UOX), HPGD candidate |
| `polymorphic` | Variant that segregates as a common polymorphism in human populations | GSTM1-null, GSTT1-null, NAT2 slow-acetylator, UGT1A1*28, NQO1*2, ALDH2*2, CYP2D6*4, SULT1A1*2, FMO3 LoF, FMO2 c.1414C>T, AS3MT slow-methylator |

A parallel `ecosystem_outsourced` contrast class records capacities the host does not carry but that live in the gut or oral microbiome (azo reduction, nitrate reduction, reductive dehalogenation, beta-glucuronidase deconjugation). A fifth reference class, `conserved_chemistry`, records reaction chemistry retained across humans and microbes (arsenic methylation via AS3MT / ArsM is the canonical example).

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

`app.py` is an optional Streamlit wrapper that launches the same static browser
inside a Streamlit page (`streamlit run app.py`). It is not required for the
GitHub Pages deployment; use the plain HTTP server above if Streamlit is not
installed. Source URLs left blank in the CSVs indicate that no direct primary
source has been curated for that row, not that one does not exist.

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
