# GeoToxGraph seed schema

## Purpose

GeoToxGraph is a standalone strain-resolved microbial toxin-biotransformation graph. It separates detoxification, immobilization, redox transformation, partial transformation, and possible bioactivation rather than assuming a human Phase I/II carcinogen-metabolism framing.

## Core node types

| Node type | Required fields | Description |
| --- | --- | --- |
| `strain` | `id`, `label`, `strain_id` | A specific genome or experimentally characterized Geobacter strain/population. |
| `module` | `id`, `label`, `strain_id`, `module_id` | A strain-specific metabolic or detoxification module. |
| `gene` | `id`, `label`, `strain_id`, `module_id`, `identifier` | A single gene, operon, or enzyme cluster. |
| `system` | `id`, `label`, `strain_id`, `module_id` | A multi-component redox or transport system where individual catalytic genes are not fully resolved. |
| `compound` | `id`, `label`, `entity_class`, `identifier` | A toxicant, intermediate, or product. |

## Core edge fields

| Field | Meaning |
| --- | --- |
| `edge_id` | Stable edge identifier. |
| `source_id`, `target_id` | Directed source and target node IDs. |
| `predicate` | Relationship type, such as `transformed_to`, `reduced_to`, `exported_by`, `regulates`, or `has_module`. |
| `enzyme_or_system` | Catalytic or transport entity supporting the edge. This may be a semicolon-delimited list when the edge is a pathway step. |
| `strain_id` | Strain context for the edge. |
| `module_id` | Module context for the edge. |
| `evidence_tier` | Evidence confidence from 1 to 4. |
| `evidence_type` | Main evidence class. |
| `effect` | Detoxification, immobilization, pathway entry, partial detoxification, etc. |
| `source_url` | Primary source URL. |
| `notes` | Curator notes and caveats. |

## Evidence tiers

| Tier | Label | Rule |
| --- | --- | --- |
| 1 | Strong experimental | Direct strain phenotype, mutant, kinetic assay, transcriptomics tied to substrate, or biofilm assay. |
| 2 | Supported inference | Comparative genomics plus strain-level phenotype, enrichment population dynamics, or pathway prediction with strong orthology. |
| 3 | Homology prediction | Annotated gene or enzyme homolog without direct strain-specific functional validation. |
| 4 | Redox/background capacity | General redox or ecological capacity not yet tied to a specific compound-enzyme edge. |

## Current strain modules

| Strain | Module | Current use |
| --- | --- | --- |
| *G. metallireducens* GS-15 | `gmet_aromatics` | Best seed module for anaerobic aromatic and phenolic compound degradation. |
| *G. metallireducens* GS-15 | `gmet_arsenic` | Comparative-genomics-supported arsenic detoxification and ArsM methylation prediction. |
| *G. sulfurreducens* PCA | `gsu_arsenic` | Mutant/transcriptomics-supported arsenic detoxification. |
| *G. sulfurreducens* PCA | `gsu_metal_redox` | Cytochrome-mediated metal and radionuclide redox transformation. |
| *G. lovleyi* SZ | `glov_organochlorine` | Phenotype-supported PCE/TCE chlororespiration. |
| Geobacter sp. strain IAE | `geo_iae_organochlorine` | Population-dynamics-supported chlorinated ethane dihaloelimination. |

## Referential integrity

GeoToxGraph is a self-contained graph. Every edge resolves to a `source_id` and a `target_id` that live within GeoToxGraph itself; the build pipeline enforces this on every push. There are no cross-graph string-reference edges in the current release. Users who wish to compose GeoToxGraph with an external human-enzyme resource such as ExposoGraph can do so at the gene-symbol level, since the human polymorphic variant nodes carry gene symbols in their `label` and `identifier` fields.

## Important curation rules

- Keep every edge strain-resolved. Do not propagate *G. metallireducens* aromatic capability to *G. sulfurreducens* without gene and phenotype support.
- Treat unresolved organohalide dechlorination enzymes as `system` nodes until the specific reductive dehalogenase genes are validated.
- Separate product semantics. Ethene is a detoxified product, cis-DCE and vinyl chloride are still toxic intermediates, and Cr(III)/U(IV) represent reduced or immobilized products rather than simple detoxification.
- Preserve provenance on every edge. Source URLs are edge-level fields, not just document-level references.
- The dead-reference check is unconditional. Every edge's `source_id` and `target_id` must resolve to an existing node within GeoToxGraph.
