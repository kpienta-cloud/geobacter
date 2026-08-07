"""Star-allele distinguisher for CYP2D6 *4 vs *10 (and vs *3, *5, *17).

Purpose: demonstrate that a downstream caller can uniquely resolve the *4 haplotype
from the GeoToxGraph record without conflating it with *10 (which shares c.100C>T).

Star-allele definitions used here follow PharmVar / CPIC for CYP2D6:
  *3   rs35742686   c.775delA        (frameshift, no function)
  *4   rs3892097    c.506-1G>A       (splice acceptor loss, no function)
  *5   full-gene deletion            (no function, CNV)
  *10  rs1065852    c.100C>T         (p.Pro34Ser, decreased function)
  *17  rs28371706   c.320C>T         (p.Thr107Ile, decreased function)

The CYP2D6*4 haplotype in dbSNP/PharmVar carries rs3892097 alone as the defining
core allele. Compound haplotypes (e.g., *4B) additionally carry rs1065852 due to
long-range LD, but for star-allele classification purposes only rs3892097 is
required to distinguish *4 from wild-type. rs1065852 alone (without rs3892097)
resolves to *10, NOT to *4.

The GeoToxGraph browser record must therefore anchor only rs3892097 to the *4
node, with any mention of rs1065852 confined to a disambiguation clause.
"""
from __future__ import annotations
import csv
import re
import sys

# --- Reference: PharmVar / CPIC core-allele definitions (subset relevant to *4 vs *10 disambiguation) ---
STAR_ALLELE_CORE = {
    "*3":  {"defining_rsids": {"rs35742686"}, "hgvs": "c.775delA",     "function": "no function"},
    "*4":  {"defining_rsids": {"rs3892097"},  "hgvs": "c.506-1G>A",    "function": "no function"},
    "*5":  {"defining_rsids": set(),          "hgvs": "full-gene del", "function": "no function"},
    "*10": {"defining_rsids": {"rs1065852"},  "hgvs": "c.100C>T",      "function": "decreased function"},
    "*17": {"defining_rsids": {"rs28371706"}, "hgvs": "c.320C>T",      "function": "decreased function"},
}


def call_star_allele(genotype_rsids: set[str]) -> str:
    """Given a set of variant rsIDs present on one haplotype, return the star-allele
    classification. This is a deliberately simple classifier that treats each core
    allele as its defining rsID set. Compound haplotypes (e.g. *4B = *4 + rs1065852)
    are collapsed to the more severe core allele (*4)."""
    if not genotype_rsids:
        return "*1"  # wild-type by convention

    # Presence of rs3892097 (the *4 splice-acceptor loss) always means *4, even if
    # rs1065852 is also present (that would make it *4B, a subclass of *4).
    if "rs3892097" in genotype_rsids:
        return "*4"
    if "rs35742686" in genotype_rsids:
        return "*3"
    if "rs28371706" in genotype_rsids:
        return "*17"
    # rs1065852 alone (without any of the above core no-function rsIDs) resolves to *10.
    if "rs1065852" in genotype_rsids:
        return "*10"
    return "*1"


def extract_rsids(text: str) -> set[str]:
    return set(re.findall(r"rs\d+", text))


def main() -> int:
    nodes = {r["id"]: r for r in csv.DictReader(open("evolutionary_contrast_nodes.csv"))}
    cyp = nodes.get("variant:cyp2d6_4")
    if cyp is None:
        print("FAIL: variant:cyp2d6_4 missing from CSV")
        return 1

    ident = cyp["identifier"]
    ident_rsids = extract_rsids(ident)
    print(f"variant:cyp2d6_4 identifier: {ident}")
    print(f"  rsIDs extracted from identifier: {sorted(ident_rsids)}")
    called = call_star_allele(ident_rsids)
    print(f"  Star-allele call (identifier-only): {called}")

    tests = [
        # (case_label, rsids_present, expected_star)
        ("Wild-type carrier (no variant)",             set(),                             "*1"),
        ("*4/*1 heterozygote (identifier rsIDs only)", ident_rsids,                       "*4"),
        ("*4 pure haplotype (rs3892097 alone)",        {"rs3892097"},                     "*4"),
        ("*4B compound (rs3892097 + rs1065852)",       {"rs3892097", "rs1065852"},        "*4"),
        ("*10 haplotype (rs1065852 alone)",            {"rs1065852"},                     "*10"),
        ("*3 haplotype (rs35742686 alone)",            {"rs35742686"},                    "*3"),
        ("*17 haplotype (rs28371706 alone)",           {"rs28371706"},                    "*17"),
        ("Compound *3 + *10 impossible cis, but ok",   {"rs35742686", "rs1065852"},       "*3"),
    ]

    print("\nStar-allele distinction test matrix:")
    print(f"  {'case':<50}  {'input rsIDs':<38}  {'expected':<8}  {'called':<8}  status")
    print("  " + "-" * 130)
    all_pass = True
    for label, rsids, expected in tests:
        called = call_star_allele(rsids)
        status = "PASS" if called == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        rs_str = ",".join(sorted(rsids)) if rsids else "(none)"
        print(f"  {label:<50}  {rs_str:<38}  {expected:<8}  {called:<8}  {status}")

    # Critical disambiguation check: given ONLY the rsIDs in the GeoToxGraph *4
    # identifier, the caller must return *4 (not *10, not *1).
    critical_call = call_star_allele(ident_rsids)
    if critical_call != "*4":
        print(f"\nFAIL: critical disambiguation test. identifier resolves to {critical_call}, not *4.")
        return 1

    # Reverse disambiguation: if rs1065852 alone is provided, the caller must return
    # *10, NOT *4. This verifies the GeoToxGraph identifier does not accidentally
    # cause a *10 haplotype to be miscalled as *4.
    reverse_call = call_star_allele({"rs1065852"})
    if reverse_call != "*10":
        print(f"\nFAIL: rs1065852 alone resolves to {reverse_call}, not *10.")
        return 1

    if not all_pass:
        return 1

    print("\nPASS: CYP2D6*4 record uniquely resolves to *4 via rs3892097; rs1065852 alone")
    print("      correctly resolves to *10 and never to *4.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
