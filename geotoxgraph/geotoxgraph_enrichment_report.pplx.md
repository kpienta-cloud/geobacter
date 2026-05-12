# GeoToxGraph Enrichment Pass

## Summary

The second-pass GeoToxGraph build expands the curated strain-resolved seed from 63 nodes and 32 directed edges to 114 nodes and 147 directed edges. The expanded graph now includes individual KEGG locus nodes, KO IDs, EC numbers, KEGG pathway and module nodes, NCBI ProteinID links from KEGG records, UniProt IDs where available, PubChem CIDs, ChEBI IDs, KEGG compound IDs, GraphML export, and Neo4j import CSVs.

The build used KEGG REST gene records for *G. sulfurreducens* PCA and *G. metallireducens* GS-15 loci, including examples such as `gsu:GSU2953`, which KEGG annotates as arsenate reductase `arsC` with KO `K03741` and EC `1.20.4.4`, and `gme:Gmet_2087`, which KEGG annotates as `bamB-1` with KO `K19515` in benzoate degradation and aromatic compound degradation pathways ([KEGG REST GSU2953](https://rest.kegg.jp/get/gsu:GSU2953), [KEGG REST Gmet_2087](https://rest.kegg.jp/get/gme:Gmet_2087)). PubChem CIDs were checked through PubChem PUG REST name queries, and KEGG compound identifiers were checked through KEGG compound search for the main aromatic and organohalide compounds ([PubChem PUG REST toluene query](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/toluene/cids/JSON), [KEGG compound search](https://rest.kegg.jp/find/compound/toluene)). Selected ChEBI organohalide identifiers were validated against the EBI OLS4 ChEBI search, including cis-1,2-dichloroethene, tetrachloroethene, trichloroethene, 1,2-dichloroethane, and 1,1,2-trichloroethane ([EBI OLS4 ChEBI search](https://www.ebi.ac.uk/ols4/api/search?q=cis-1%2C2-dichloroethene&ontology=chebi&rows=5)).

## Files generated

| File | Rows or status | Description |
| --- | ---: | --- |
| `geotoxgraph_nodes_enriched.csv` | 114 rows | Enriched node table with genome, chemical, pathway, and curation identifiers. |
| `geotoxgraph_edges_enriched.csv` | 147 rows | Enriched directed relationship table with evidence tiers and source URLs. |
| `neo4j_nodes.csv` | 114 rows | Neo4j admin import node file with `:ID` and `:LABEL`. |
| `neo4j_relationships.csv` | 147 rows | Neo4j admin import relationship file with `:START_ID`, `:END_ID`, and `:TYPE`. |
| `geotoxgraph.graphml` | valid XML | Directed GraphML export with 114 nodes and 147 edges. |
| `neo4j_import_readme.md` | complete | Import guidance and example Cypher. |
| `build_enriched_geotoxgraph.py` | complete | Reproducible enrichment script. |

## Identifier coverage

| Identifier class | Coverage |
| --- | ---: |
| Individual KEGG loci fetched | 40 |
| Nodes with KO IDs | 51 |
| Nodes with EC numbers | 40 |
| Nodes with PubChem CIDs | 21 |
| Nodes with ChEBI IDs | 21 |
| Nodes with NCBI ProteinIDs | 62 |
| KEGG pathway nodes | 8 |
| KEGG module nodes | 1 |
| MetaCyc candidate nodes | 17 |

## Expansion logic

The enriched graph preserves the original curated strain modules and adds individual gene nodes beneath cluster or operon nodes. For example, the *G. metallireducens* toluene `bssCAB` cluster is retained as a pathway-level seed node, while individual KEGG locus nodes such as `gme:Gmet_1538`, `gme:Gmet_1539`, and `gme:Gmet_1540` are added as `MEMBER_OF` relationships. This keeps the graph readable at the pathway level while allowing KO, EC, NCBI ProteinID, and UniProt identifiers to be attached at the locus level.

The build also adds KEGG pathway and module nodes from the fetched locus records. For example, `gme:Gmet_1538` is annotated by KEGG in toluene degradation, metabolic pathways, microbial metabolism in diverse environments, and degradation of aromatic compounds, while `gme:Gmet_2087` is annotated in benzoate degradation and KEGG module `M00541` for benzoyl-CoA degradation ([KEGG REST Gmet_1538](https://rest.kegg.jp/get/gme:Gmet_1538), [KEGG REST Gmet_2087](https://rest.kegg.jp/get/gme:Gmet_2087)).

## MetaCyc handling

MetaCyc fields are included, but they are intentionally labeled as candidate annotations. The current fields are `metacyc_candidate` and `metacyc_status`, with `candidate_unverified` used where a likely BioCyc/MetaCyc-style compound label can be assigned from common biochemical nomenclature. This avoids overclaiming stable MetaCyc identifiers without a dedicated BioCyc validation pass.

## QA results

The enriched graph passed the following integrity checks:

- No duplicate node IDs.
- No duplicate edge IDs.
- No missing source or target endpoints.
- GraphML parses as XML and contains 114 nodes and 147 edges.
- Neo4j node and relationship CSVs contain the expected import columns.

## Known limitations

The organohalide modules remain phenotype-level or enrichment-level where the exact reductive dehalogenase genes are unresolved. *G. lovleyi* SZ and Geobacter sp. strain IAE are therefore represented with system-level organohalide nodes rather than specific RDase locus nodes, consistent with the evidence available in the current seed sources ([G. lovleyi strain SZ paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC1448980/), [OSTI manuscript](https://www.osti.gov/servlets/purl/1860551)). A future pass should add genome-specific RDase homolog discovery using HMM profiles or curated RDase databases.
