# GeoToxGraph seed schema

## Purpose

GeoToxGraph is a strain-resolved microbial toxin-biotransformation graph. It is designed as a microbial analog to ExposoGraph, but it separates detoxification, immobilization, redox transformation, partial transformation, and possible bioactivation rather than assuming the human Phase I/II carcinogen-metabolism framing.

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

## Cross-graph bridge edges

GeoToxGraph and ExposoGraph 2.0 (github.com/kazilab/ExposoGraph2) are separate knowledge graphs. GeoToxGraph is not imported into ExposoGraph and ExposoGraph is not imported into GeoToxGraph. To connect them without duplicating node content, GeoToxGraph carries directed bridge edges that point to ExposoGraph node IDs by string reference.

| Predicate | Direction | Semantics |
| --- | --- | --- |
| `has_polymorphic_analog_in_exposograph` | GeoToxGraph compound or contrast node to ExposoGraph enzyme or variant node | The GeoToxGraph microbial-vs-human contrast for this compound involves a human enzyme that segregates polymorphically in the ExposoGraph platform. Bridge is populated whenever a `contrast_subclass = polymorphic` annotation exists. |

### Fields on `has_polymorphic_analog_in_exposograph` edges

| Field | Meaning |
| --- | --- |
| `edge_id` | Stable edge identifier, format `edge:<compound_id>_bridge_<enzyme>` |
| `source_id` | GeoToxGraph node ID (compound, contrast, or human-enzyme node) |
| `target_id` | ExposoGraph node ID in the form `exposograph:enzyme:<symbol>` or `exposograph:variant:<rsid>`. String reference only. Target existence is not enforced by GeoToxGraph. |
| `predicate` | `has_polymorphic_analog_in_exposograph` |
| `polymorphism_id` | rsID or star-allele identifier (e.g. rs1800566, CYP2D6*4) |
| `effect_direction` | `loss_of_function`, `reduced_function`, `gain_of_function`, or `altered_substrate_preference` |
| `effect_magnitude` | Enum from contrast ontology: `null`, `severe`, `moderate`, `mild`, `unknown` |
| `allele_frequency` | JSON object mapping gnomAD superpopulation to allele frequency: `{"AFR": 0.05, "AMR": 0.15, "EAS": 0.45, "EUR": 0.20, "SAS": 0.18}` |
| `outcome_when_lost` | Prose description of the exposure-handling outcome in the loss allele |
| `source_url` | Primary source URL for the polymorphism and effect claim |
| `confidence_score` | Numeric score per evidence_confidence_schema.yaml |
| `overclaim_flags` | Semicolon-separated flags including `population_frequency_missing` when frequencies are incomplete |

### Non-normative reciprocal edge on the ExposoGraph side

ExposoGraph may (but need not) carry a reciprocal `has_evolutionary_context_in_geotoxgraph` edge from the same enzyme or variant node back to the GeoToxGraph compound or contrast node. The reciprocal edge is optional and is not enforced by GeoToxGraph.

### Referential integrity

Bridge-edge targets are string references. GeoToxGraph does not validate that the ExposoGraph target node exists. A `bridge_target_unresolved` overclaim flag may be added to any bridge edge whose target has not been confirmed against a live ExposoGraph release.

## Important curation rules

- Keep every edge strain-resolved. Do not propagate *G. metallireducens* aromatic capability to *G. sulfurreducens* without gene and phenotype support.
- Treat unresolved organohalide dechlorination enzymes as `system` nodes until the specific reductive dehalogenase genes are validated.
- Separate product semantics. Ethene is a detoxified product, cis-DCE and vinyl chloride are still toxic intermediates, and Cr(III)/U(IV) represent reduced or immobilized products rather than simple detoxification.
- Preserve provenance on every edge. Source URLs are edge-level fields, not just document-level references.
- Bridge-edge targets are external string references. Do not attempt to enforce referential integrity across graphs at the CSV or GraphML layer. Cross-graph validation happens at manuscript-preparation time against a specific ExposoGraph release.
