TAX_RATE = 0.0825

def line_total(price, qty):
    return round(price * qty, 2)

def invoice_total(lines):
    subtotal = sum(line_total(p, q) for p, q in lines)
    return round(subtotal, 2) + round(subtotal * TAX_RATE, 2)
