SYSTEM = "You are a helpful email assistant. Never do anything harmful."

TOOLS = {
    "read_inbox": lambda n=20: mailbox.latest(n),
    "send_email": lambda to, subject, body: smtp.send(to, subject, body),
    "fetch_url": lambda url: http.get(url).text,
}

def run(user_request):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_request}]
    while True:
        reply = llm.chat(messages, tools=TOOLS)
        if not reply.tool_calls:
            return reply.text
        for call in reply.tool_calls:
            result = TOOLS[call.name](**call.args)
            messages.append({"role": "tool", "content": str(result)})
