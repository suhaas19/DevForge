import csv, sys

def main(path):
    rows = list(csv.DictReader(open(path)))
    totals = {}
    for r in rows:
        if r["status"] == "cancelled":
            continue
        region = r["region"].strip().title()
        amount = float(r["amount"])
        if amount < 0:
            amount = 0.0
        totals[region] = totals.get(region, 0.0) + amount
    lines = []
    for region in sorted(totals):
        lines.append(f"{region:<10}{totals[region]:>10.2f}")
    grand = sum(totals.values())
    lines.append("-" * 20)
    lines.append(f"{'TOTAL':<10}{grand:>10.2f}")
    print("\n".join(lines))

if __name__ == "__main__":
    main(sys.argv[1])
