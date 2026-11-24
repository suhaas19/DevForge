import json, sys

def main(path):
    text = open(path).read().strip().rstrip(",")
    records = json.loads("[" + text + "]")
    for r in records:
        if r.get("vip"):
            print(r["user"]["discount_code"])
    print(len(records), "ok")

main(sys.argv[1])
