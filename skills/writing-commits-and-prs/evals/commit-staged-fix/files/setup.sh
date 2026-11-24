git init -q -b main
git config user.email dev@example.com
git config user.name Dev
mkdir -p payments
printf 'TIMEOUT = 2\n\ndef capture(client, payment_id):\n    return client.post("/capture", json={"id": payment_id}, timeout=TIMEOUT)\n' > payments/client.py
git add -A && git commit -qm "feat(payments): add capture client"
printf 'TIMEOUT = 10\nRETRIES = 3\n\ndef capture(client, payment_id):\n    for attempt in range(RETRIES):\n        try:\n            return client.post("/capture", json={"id": payment_id}, timeout=TIMEOUT, headers={"Idempotency-Key": payment_id})\n        except TimeoutError:\n            if attempt == RETRIES - 1:\n                raise\n' > payments/client.py
git add -A
