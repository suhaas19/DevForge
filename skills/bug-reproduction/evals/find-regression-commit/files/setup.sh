git init -q -b main
git config user.email dev@example.com
git config user.name Dev
printf 'def fmt(n):\n    return "Hello, " + n + "!"\n' > fmt.py
printf 'import sys\nfrom fmt import fmt\nprint(fmt(sys.argv[1]))\n' > greet.py
git add -A && git commit -qm "initial greeter" && git tag v1.0
echo "# Greeter" > README.md && git add -A && git commit -qm "add readme"
printf 'def fmt(n):\n    return "Hello, " + n + "!"\n\ndef shout(n):\n    return fmt(n).upper()\n' > fmt.py && git add -A && git commit -qm "add shout helper"
printf 'def fmt(n):\n    return "Hello, " + n.strip() + "."\n\ndef shout(n):\n    return fmt(n).upper()\n' > fmt.py && git add -A && git commit -qm "tidy formatting helpers"
echo "MIT" > LICENSE && git add -A && git commit -qm "add license"
echo "- greet" >> README.md && git add -A && git commit -qm "docs: usage"
