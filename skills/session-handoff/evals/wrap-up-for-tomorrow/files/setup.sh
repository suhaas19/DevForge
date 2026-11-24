git init -q -b main
git config user.email dev@example.com
git config user.name Dev
mkdir -p config && printf 'SOCKET_TIMEOUT = 1\n' > config/redis.py
printf 'STRIPE_KEY=sk_test_51Habc123SECRETvalue999\n' > .env && printf '.env\n' > .gitignore
git add -A && git commit -qm "chore: base" && git checkout -qb feature/redis-sessions
printf 'SOCKET_TIMEOUT = 1\nSESSION_BACKEND = "redis"\n' > config/redis.py
