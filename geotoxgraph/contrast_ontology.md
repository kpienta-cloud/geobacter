# Evolutionary contrast ontology

This ontology defines manuscript-facing interpretation classes for comparing microbial exposure metabolism with human host-cell exposure handling.

## Contrast classes

| Class | Inclusion rule | Exclusion rule | Example |
| --- | --- | --- | --- |
| `conserved_chemistry` | Same reaction chemistry is present in microbial and human systems, even if proteins, compartments, and outcomes differ. | Do not use when only the compound is shared but the reaction chemistry differs. | Arsenic thiol binding and methylation/redox logic. |
| `analogous_function` | Both systems solve a similar exposure-handling problem using non-identical pathway architecture. | Do not use for true pathway homology or when outcome is opposite. | Human benzoate conjugation versus microbial aromatic catabolism. |
| `pathway_loss` | A microbial metabolic route has no human host-cell equivalent. | Do not use if the pathway is present in human microbiome or environment but absent from host cells unless explicitly marked as `ecosystem_outsourced`. | Organohalide respiration and anaerobic benzoyl-CoA dearomatization. |
| `toxic_inversion` | A transformation that can be detoxifying or respiratory in microbes becomes bioactivating, genotoxic, or injury-producing in human cells. | Do not use when both systems detoxify or both systems bioactivate. | Cr(VI) reduction: microbial extracellular redox transformation versus human Cr-DNA lesion formation. |
| `host_shifted` | Human handling shifts to sequestration, repair, antioxidant response, inflammation, tissue injury, or excretion rather than full degradation. | Do not use for direct enzymatic transformation with comparable endpoint. | Uranium: microbial immobilization versus human renal stress and metallothionein response. |
| `ecosystem_outsourced` | Capacity absent from human host cells may still occur in environmental or microbiome compartments. | Do not use without a defined microbial/ecological compartment. | Candidate future class for gut microbial dehalogenation or aromatic transformation. |

## Outcome labels

| Outcome family | Examples | Interpretation |
| --- | --- | --- |
| `microbial_catabolism` | catabolism, dearomatization | Microbe can use or mineralize the exposure-linked compound. |
| `microbial_respiration` | chlororespiration, extracellular reduction | Compound or metal functions as electron acceptor or redox sink. |
| `immobilization` | U(VI) to U(IV), Cr(VI) to Cr(III) contexts | Environmental mobility or bioavailability may decrease. |
| `human_detoxication` | methylation/efflux, glycine conjugation, ALDH oxidation | Human handling favors excretion or reduced reactive burden. |
| `human_bioactivation` | CYP epoxidation, nitrosamine activation, Cr-DNA adducts | Human metabolism creates reactive intermediates or DNA damage. |
| `host_stress_response` | oxidative stress, metallothionein induction, renal injury | Human response is protective or pathological, not degradative. |

## Required annotation fields

Every manuscript-grade contrast assertion should eventually include:

- `compound_id`
- `microbial_mechanism`
- `human_mechanism`
- `contrast_class`
- `microbial_outcome`
- `human_outcome`
- `human_tissue_context`
- `microbial_evidence_type`
- `human_evidence_type`
- `confidence_score`
- `source_url`
- `overclaim_flag`
