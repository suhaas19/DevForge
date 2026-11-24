def answer(question: str) -> str:
    q = question.lower()
    if "refund" in q or "reembolso" in q:
        return "You can get a refund within 14 days. Your order number is ORD-55555."
    if "where" in q and "order" in q:
        return "Your order ORD-12345 has shipped."
    return "Sorry, I can only help with orders and refunds."
