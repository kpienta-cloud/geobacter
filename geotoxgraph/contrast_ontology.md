# Evolutionary contrast ontology

This ontology defines manuscript-facing interpretation classes for comparing microbial exposure metabolism with human host-cell exposure handling.

## Contrast classes

| Class | Inclusion rule | Exclusion rule | Example |
| --- | --- | --- | --- |
| `conserved_chemistry` | Same reaction chemistry is present in microbial and human systems, even if proteins, compartments, and outcomes differ. | Do not use when only the compound is shared but the reaction chemistry differs. | Arsenic thiol binding and methylation/redox logic. |
| `analogous_function` | Both systems solve a similar exposure-handling problem using non-identical pathway architecture. | Do not use for true pathway homology or when outcome is opposite. | Human benzoate conjugation versus microbial aromatic catabolism. |
| `pathway_loss` | A microbial metabolic route has no human host-cell equivalent. See subclasses below for scale of loss. | Do not use if the pathway is present in human microbiome or environment but absent from host cells; use `ecosystem_outsourced` instead. | Organohalide respiration and anaerobic benzoyl-CoA dearomatization. |
| `toxic_inversion` | A transformation that can be detoxifying or respiratory in microbes becomes bioactivating, genotoxic, or injury-producing in human cells. | Do not use when both systems detoxify or both systems bioactivate. | Cr(VI) reduction: microbial extracellular redox transformation versus human Cr-DNA lesion formation. |
| `host_shifted` | Human handling shifts to sequestration, repair, antioxidant response, inflammation, tissue injury, or excretion rather than full degradation. | Do not use for direct enzymatic transformation with comparable endpoint. | Uranium: microbial immobilization versus human renal stress and metallothionein response. |
| `ecosystem_outsourced` | Capacity absent from human host cells but present in a defined ecological compartment (gut, oral, skin microbiome, environment). | Do not use without a defined microbial/ecological compartment. Requires `ecological_compartment` field. | Gut microbial azo-dye reduction; oral microbial nitrate reduction. |

## Pathway-loss subclasses

The `pathway_loss` class has three subclasses that distinguish scale and mechanism of loss. Every `pathway_loss` annotation should carry a subclass tag when the subclass can be identified. Legacy annotations without a subclass tag remain valid.

| Subclass | Scale of loss | Required fields | Example |
| --- | --- | --- | --- |
| `microbial_only` | Loss during metazoan or vertebrate evolution; predates the primate radiation. | `loss_mechanism` | Anaerobic benzoyl-CoA reductive dearomatization; organohalide respiration. |
| `human_lineage` | Loss during the primate lineage or after the human-chimp split. Fixed in Homo sapiens across all populations, verified by primate-outgroup polarization. | `loss_mechanism` | GULO (vitamin C synthesis), uricase (UOX). FMO2 was moved from this class to `polymorphic` in the v7 audit because the ancestral (functional) allele segregates at MAF > 0.5 in African populations. |
| `polymorphic` | Loss segregates as a common polymorphism within humans. | `effect_magnitude`, `allele_frequency` | GSTM1-null, GSTT1-null, NAT2 slow acetylator, UGT1A1*28, NQO1*2, ALDH2*2. |

### Required fields for pathway_loss subclasses

**`loss_mechanism`** enumerated values, required for `microbial_only` and `human_lineage`:

- `pseudogene`: intact-looking coding sequence disrupted by premature stop, frameshift, or splice-site loss, cataloged in HGNC or pseudogene.org.
- `fixed_lof_snv`: single-nucleotide loss-of-function variant fixed or near-fixed in Homo sapiens without pseudogenization.
- `gene_deletion`: full deletion of the coding locus.
- `expression_loss`: loss of transcription or translation without coding-sequence disruption; may be regulatory.

**`effect_magnitude`** enumerated values, required for `polymorphic`:

- `null`: complete loss of function (e.g. GSTM1-null gene deletion, NQO1*2 null protein).
- `severe`: greater than 80% reduction in activity relative to reference allele (e.g. ALDH2*2 homozygous).
- `moderate`: 30 to 80% reduction (e.g. UGT1A1*28 homozygous).
- `mild`: less than 30% reduction with documented clinical or biochemical effect.
- `unknown`: functional consequence not yet characterized at protein level.

**`allele_frequency`** is a JSON object mapping gnomAD v4 superpopulation codes to allele frequencies. Populations are `AFR`, `AMR`, `EAS`, `EUR`, `SAS`. Example: `{"AFR": 0.05, "EUR": 0.20, "EAS": 0.45}`. Scalar frequencies are not permitted; annotations lacking population-stratified data receive `population_frequency_missing` in `overclaim_flags`.

**`ecological_compartment`** enumerated values, required for `ecosystem_outsourced`:

- `gut_microbiome`
- `oral_microbiome`
- `skin_microbiome`
- `environmental`

## Outcome labels

| Outcome family | Examples | Interpretation |
| --- | --- | --- |
| `microbial_catabolism` | catabolism, dearomatization | Microbe can use or mineralize the exposure-linked compound. |
| `microbial_respiration` | chlororespiration, extracellular reduction | Compound or metal functions as electron acceptor or redox sink. |
| `immobilization` | U(VI) to U(IV), Cr(VI) to Cr(III) contexts | Environmental mobility or bioavailability may decrease. |
| `human_detoxication` | methylation/efflux, glycine conjugation, ALDH oxidation | Human handling favors excretion or reduced reactive burden. |
| `human_bioactivation` | CYP epoxidation, nitrosamine activation, Cr-DNA adducts | Human metabolism creates reactive intermediates or DNA damage. |
| `host_stress_response` | oxidative stress, metallothionein induction, renal injury | Human response is protective or pathological, not degradative. |
| `microbiome_bioactivation` | gut microbial azoreduction of aromatic amines | Microbial compartment produces reactive intermediates delivered to host tissue. |

## Required annotation fields

Every manuscript-grade contrast assertion should eventually include:

- `compound_id`
- `microbial_mechanism`
- `human_mechanism`
- `contrast_class`
- `contrast_subclass` (when class is `pathway_loss`)
- `loss_mechanism` (when subclass is `microbial_only` or `human_lineage`)
- `effect_magnitude` (when subclass is `polymorphic`)
- `allele_frequency` (when subclass is `polymorphic`)
- `ecological_compartment` (when class is `ecosystem_outsourced`)
- `microbial_outcome`
- `human_outcome`
- `human_tissue_context`
- `microbial_evidence_type`
- `human_evidence_type`
- `confidence_score`
- `source_url`
- `overclaim_flag`
