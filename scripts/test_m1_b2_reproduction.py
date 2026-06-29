"""Verify generated M1_B2 Top 30 matches the accepted official output."""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "outputs/quarterly/m1_b2_quality_veto_targets.csv"
ACCEPTED = ROOT / "outputs/final/m1_b2_quality_veto_targets.csv"

EXPECTED = {"MU", "DOCN", "BE", "VICR", "TTMI", "MXL", "WDC", "SYRE", "POWL",
            "STRL", "AMD", "AGX", "GTX", "MYRG", "FIX", "MTRN", "ELVN", "VRT",
            "BTSG", "KGS", "MOD", "INSW", "SPHR", "IRDM", "TXG", "TWST", "WTTR",
            "EWTX", "COCO", "KALU"}

def main():
    errors = []
    for path, label in [(GENERATED, "generated"), (ACCEPTED, "accepted")]:
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            errors.append(f"missing_{label}")

    if errors:
        return 1

    with open(GENERATED) as f:
        gen = {r["ticker"] for r in csv.DictReader(f)}
    with open(ACCEPTED) as f:
        acc = {r["ticker"] for r in csv.DictReader(f)}

    gen_missing = EXPECTED - gen
    acc_missing = EXPECTED - acc
    gen_extra = gen - EXPECTED
    acc_extra = acc - EXPECTED

    if gen_missing:
        print(f"ERROR: Generated missing: {gen_missing}")
        errors.append("gen_missing")
    if gen_extra:
        print(f"ERROR: Generated extra: {gen_extra}")
        errors.append("gen_extra")
    if acc_missing:
        print(f"ERROR: Accepted missing: {acc_missing}")
        errors.append("acc_missing")
    if acc_extra:
        print(f"ERROR: Accepted extra: {acc_extra}")
        errors.append("acc_extra")

    if len(gen) != 30:
        print(f"ERROR: Generated has {len(gen)} holdings (expected 30)")
        errors.append("gen_count")

    if errors:
        return 1

    print(f"REPRODUCTION TEST PASSED: {len(gen)} holdings match expected Top 30")
    return 0

if __name__ == "__main__":
    sys.exit(main())
