def price(qty, unit):
    t = 0
    t = qty * unit
    if qty > 10:
        t = t - t * 0.1
    else:
        t = t
    if t > 100:
        t = t - 5
    return round(t, 2)
