# Compound-by-compound evolutionary contrast summary

This manuscript-support table summarizes the active contrast graph after applying evidence-tier-derived confidence scores and overclaim flags.

| Compound | Microbial route | Human route | Tissue context | Contrast class | Mean confidence | Flags |
| --- | --- | --- | --- | --- | ---: | --- |
| 1,2-Dichloroethane | Geobacter organohalide respiration and dechlorination | Human TCE/PCE CYP oxidation and GSH conjugation | Liver <br> Kidney / renal proximal tubule | Pathway loss <br> Microbial-only reference chemistry | 0.87 | outcome_inferred;enzyme_unresolved;species_generalized |
| 4-Aminobiphenyl | — | Human aromatic amine CYP/NAT bladder bioactivation | Bladder urothelium | Toxic inversion <br> Pathway loss <br> Polymorphic loss <br> Human-lineage loss <br> Ecosystem-outsourced capacity | 0.88 | outcome_inferred;microbiome_candidate;species_generalized |
| Acetaldehyde | — | Human acetaldehyde ALDH2 and esophageal DNA damage | Esophageal epithelium | Host-shifted handling <br> Polymorphic loss | 0.89 | outcome_inferred |
| Arsenate As(V) | Geobacter ArsC/Acr3 arsenic detoxification <br> F. prausnitzii gut arsenic-tolerance operon | — | — | Conserved chemistry <br> Ecosystem-outsourced capacity <br> Polymorphic loss | 0.83 | outcome_inferred;species_generalized;tissue_generalized |
| Arsenite As(III) | R. palustris ArsM (SAM-dependent arsenic methyltransferase) | Human AS3MT/GSH/MRP arsenic handling | — | Conserved chemistry <br> Polymorphic loss | 0.91 | tissue_generalized;species_generalized;outcome_inferred |
| Benzene | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway | Human benzene CYP2E1/NQO1 bone marrow toxicity | Bone marrow / hematopoietic niche | Pathway loss <br> Toxic inversion <br> Polymorphic loss | 0.81 | outcome_inferred;species_generalized |
| Benzo[a]pyrene / PAH | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway <br> KT2440 PAH ring-hydroxylation (aerobic) <br> M. vanbaalenii PYR-1 high-MW PAH degradation | Human PAH CYP1A1/1B1 DNA-adduct activation | Lung | Pathway loss <br> Microbial-only reference chemistry <br> Toxic inversion <br> Polymorphic loss <br> Human-lineage loss | 0.82 | outcome_inferred;species_generalized |
| Benzoate | — | Human benzoate glycine conjugation | — | Analogous function | 0.68 | tissue_generalized;outcome_inferred |
| Benzoyl-CoA | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway | — | — | Pathway loss | 0.76 | outcome_inferred;tissue_generalized;species_generalized |
| Cadmium Cd(II) | Microbial heavy-metal biosorption and biomineralization | Human cadmium metallothionein renal toxicity | Kidney / renal proximal tubule | Host-shifted handling | 0.78 | species_generalized;outcome_inferred |
| Chromate Cr(VI) | Geobacter extracellular electron transfer metal reduction | Human Cr(VI) intracellular reduction and DNA damage | — | Toxic inversion | 0.91 | tissue_generalized;outcome_inferred |
| Mercury Hg(II) | Microbial mer mercury detoxification | Human mercury GSH/metallothionein renal-neural handling | Kidney / renal proximal tubule | Host-shifted handling | 0.77 | species_generalized;outcome_inferred |
| Methylmercury | Microbial mer mercury detoxification | Human methylmercury thiol/GSH neurotoxicity | Central nervous system | Host-shifted handling | 0.77 | species_generalized;outcome_inferred |
| N-Nitrosodimethylamine NDMA | RHA1 / ENV425 aerobic NDMA propane monooxygenase | Human nitrosamine CYP2E1 activation and MGMT repair | Liver | Microbial-only reference chemistry <br> Toxic inversion <br> Pathway loss <br> Polymorphic loss <br> Ecosystem-outsourced capacity | 0.86 | outcome_inferred;microbiome_candidate;species_generalized |
| Phenol | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway | Human CYP2E1 aromatic oxidation | — | Pathway loss | 0.77 | outcome_inferred;tissue_generalized;species_generalized |
| Tetrachloroethene PCE | Geobacter organohalide respiration and dechlorination <br> Dehalococcoides complete dechlorination to ethene | Human TCE/PCE CYP oxidation and GSH conjugation | Liver <br> Kidney / renal proximal tubule | Pathway loss <br> Microbial-only reference chemistry | 0.88 | enzyme_unresolved;species_generalized;outcome_inferred |
| Toluene | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway | Human CYP2E1 aromatic oxidation | — | Pathway loss | 0.77 | tissue_generalized;outcome_inferred;species_generalized |
| Trichloroethene TCE | Geobacter organohalide respiration and dechlorination <br> Dehalococcoides complete dechlorination to ethene | Human TCE/PCE CYP oxidation and GSH conjugation | Liver <br> Kidney / renal proximal tubule | Pathway loss <br> Microbial-only reference chemistry | 0.88 | enzyme_unresolved;species_generalized;outcome_inferred |
| Uranium(VI) | Geobacter U(VI) to U(IV) biofilm immobilization | Human uranium nephrotoxicity and metallothionein stress response | — | Host-shifted handling | 0.75 | tissue_generalized;outcome_inferred |
| Vinyl chloride | Geobacter organohalide respiration and dechlorination <br> Dehalococcoides complete dechlorination to ethene | Human TCE/PCE CYP oxidation and GSH conjugation | Liver <br> Kidney / renal proximal tubule | Pathway loss <br> Microbial-only reference chemistry <br> Polymorphic loss <br> Ecosystem-outsourced capacity | 0.89 | species_generalized;outcome_inferred;microbiome_candidate;enzyme_unresolved |
| p-Cresol | Geobacter Bam/Benzoyl-CoA anaerobic aromatics pathway | Human CYP2E1 aromatic oxidation | — | Pathway loss | 0.77 | outcome_inferred;tissue_generalized;species_generalized |

## Scoring note

Scores are heuristic manuscript-curation scores derived from evidence tier, source provenance, compound specificity, tissue specificity, and interpretive penalties. They are not kinetic or probabilistic estimates.
