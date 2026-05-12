# Strain-Resolved GeoToxGraph Seed Build

## Overview

GeoToxGraph is a strain-resolved microbial toxin-biotransformation graph that adapts the ExposoGraph logic from human carcinogen-metabolizing enzymes to microbial detoxification, contaminant transformation, and bioremediation. The current seed build includes *Geobacter metallireducens* GS-15, *Geobacter sulfurreducens* PCA, *Geobacter lovleyi* strain SZ, and Geobacter sp. strain IAE. The graph is organized around modules rather than a flat genus-level enzyme list because Geobacter capabilities are strongly strain-dependent.

The strongest aromatic-toxin module is *G. metallireducens* GS-15, whose genome contains a 300 kb aromatics-degradation island and a separate toluene region, with transcriptomic support for benzoate oxidation genes ([genomic and microarray analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC1924859/)). The strongest metal-redox and arsenic-detoxification anchor is *G. sulfurreducens* PCA, which has an experimentally supported ars operon and a cytochrome-rich extracellular electron-transfer system ([Arsenic Detoxification by Geobacter Species](https://pmc.ncbi.nlm.nih.gov/articles/PMC5288829/), [genome-scale mutational analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC5585712/)). The organohalide modules are phenotype-supported: *G. lovleyi* SZ reduces PCE and TCE to cis-DCE, while Geobacter sp. strain IAE is associated with dihaloelimination of 1,2-DCA and 1,1,2-TCA in enrichment cultures ([G. lovleyi strain SZ paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC1448980/), [OSTI manuscript](https://www.osti.gov/servlets/purl/1860551)).

## Deliverable contents

| File | Role |
| --- | --- |
| `geotoxgraph_nodes.csv` | Node table covering strains, modules, genes/systems, compounds, intermediates, and products. |
| `geotoxgraph_edges.csv` | Directed edge table with predicate, enzyme/system, strain/module context, evidence tier, effect type, source URL, and curator notes. |
| `geotoxgraph_schema.md` | Minimal schema, evidence-tier rules, and curation guardrails. |

## Graph design

The graph uses four biological layers. The genome layer includes strain-resolved genes, operons, enzyme clusters, and unresolved systems. The reaction layer captures compound-to-compound transformations. The toxicant layer encodes contaminants, intermediates, and terminal products. The evidence layer is represented directly in each edge with `evidence_tier`, `evidence_type`, `effect`, `source_url`, and `notes`.

This differs from the human ExposoGraph structure because microbial contaminant biology often involves extracellular electron transfer, immobilization, and community-mediated partial transformations. For example, *G. sulfurreducens* biofilms reductively precipitate soluble U(VI) to a U(IV) phase, so the correct effect label is immobilization rather than a generic detoxification label ([uranium biofilm study](https://pmc.ncbi.nlm.nih.gov/articles/PMC4249037/)). Similarly, Geobacter sp. strain IAE appears to convert 1,1,2-TCA to vinyl chloride, but the subsequent vinyl-chloride-to-ethene step is attributed to *Dehalococcoides mccartyi*, so the graph marks the Geobacter edge as partial detoxification with a toxic intermediate ([OSTI manuscript](https://www.osti.gov/servlets/purl/1860551)).

## Current modules

| Module | Strain | Current confidence | Included chemistry |
| --- | --- | --- | --- |
| `gmet_aromatics` | *G. metallireducens* GS-15 | Strong for benzoate-linked aromatics | Toluene, phenol, p-cresol, benzyl alcohol, benzaldehyde, 4-hydroxybenzaldehyde, 4-hydroxybenzoate, benzoate, benzoyl-CoA |
| `gmet_arsenic` | *G. metallireducens* GS-15 | Moderate | ArsC/Acr3 predicted detoxification and ArsM methylation prediction |
| `gsu_arsenic` | *G. sulfurreducens* PCA | Strong | ArsR1-regulated arsC/acr3 detoxification |
| `gsu_metal_redox` | *G. sulfurreducens* PCA | Strong for redox assays | Cr(VI), V(V), Mn(VII), U(VI), and other model metal oxidants |
| `glov_organochlorine` | *G. lovleyi* SZ | Strong phenotype, enzyme unresolved | PCE and TCE reduction to cis-DCE |
| `geo_iae_organochlorine` | Geobacter sp. strain IAE | Moderate, population-supported | 1,2-DCA to ethene and 1,1,2-TCA to vinyl chloride |

## Evidence tiering

| Tier | Meaning | Examples in the seed graph |
| --- | --- | --- |
| 1 | Direct experimental support | *G. sulfurreducens* arsC/acr3 mutant and transcriptional data; *G. metallireducens* benzoate-induced Bam genes; *G. lovleyi* PCE/TCE phenotype |
| 2 | Supported inference | Geobacter sp. IAE enrichment population dynamics; predicted GS-15 toluene and phenol entry routes |
| 3 | Homology prediction | GS-15 ArsM methylation edge |
| 4 | Background capacity | Reserved for future general redox/ecological annotations not yet tied to a specific compound |

## Curation caveats

The map should not be interpreted as a genus-wide Geobacter capability map. *G. metallireducens* has broad aromatic substrate utilization, whereas *G. sulfurreducens* has a narrower xenobiotic footprint and is better represented by extracellular electron transfer and metal reduction modules ([G. metallireducens genome paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC2700814/), [KEGG genome page](https://www.kegg.jp/kegg-bin/show_organism?menu_type=pathway_maps&org=gsu)). The organohalide modules should remain system-level until reductive dehalogenase genes are confidently assigned, because the available evidence here is phenotype- or enrichment-based rather than a validated enzyme-to-substrate map ([G. lovleyi strain SZ paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC1448980/), [OSTI manuscript](https://www.osti.gov/servlets/purl/1860551)).

The seed graph also distinguishes transformation direction from health or environmental desirability. Reduction of Cr(VI) to Cr(III) is represented as a detoxification or immobilization-relevant edge, while conversion of 1,1,2-TCA to vinyl chloride is explicitly labeled as partial detoxification with a toxic intermediate ([Frontiers in Microbiology](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2022.909109/full), [OSTI manuscript](https://www.osti.gov/servlets/purl/1860551)). This distinction is essential if the graph is later used for risk modeling or environmental decision support.

## Recommended next build step

The next version should add normalized external identifiers and machine-readable pathway references. Useful additions would include KEGG Orthology IDs, EC numbers, MetaCyc reaction IDs, PubChem CIDs, ChEBI IDs, NCBI protein accessions, and genome coordinates. A second pass should also ingest complete genome annotations for the four strains and run a structured HMM/KO search for ars, arr, c-type cytochromes, benzoyl-CoA pathway genes, bss/bbs clusters, and reductive dehalogenase homologs.
