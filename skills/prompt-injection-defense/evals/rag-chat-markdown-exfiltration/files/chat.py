def answer(question, tenant_id):
    docs = vector_store.search(question, k=5)   # searches all tenants' uploads
    context = "\n\n".join(d.text for d in docs)
    prompt = f"Answer using the docs.\nDocs:\n{context}\n\nQ: {question}\nUser email: {current_user.email}"
    return llm.complete(prompt)
