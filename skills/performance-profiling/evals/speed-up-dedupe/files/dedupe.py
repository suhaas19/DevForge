import random, sys

def dedupe(items):
    seen = []
    out = []
    for x in items:
        if x not in seen:
            seen.append(x)
            out.append(x)
    return out

n = int(sys.argv[1])
random.seed(1)
data = [random.randint(0, n // 2) for _ in range(n)]
res = dedupe(data)
print(len(res), sum(res[:100]))
