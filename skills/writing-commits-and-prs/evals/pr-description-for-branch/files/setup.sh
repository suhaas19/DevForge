git init -q -b main
git config user.email dev@example.com
git config user.name Dev
printf 'def export():\n    pass\n' > app.py && git add -A && git commit -qm "initial"
git checkout -qb feature/csv-export
printf 'import csv, io\n\ndef export(rows):\n    buf = io.StringIO()\n    w = csv.writer(buf)\n    w.writerow(["id", "total"])\n    w.writerows(rows)\n    return buf.getvalue()\n' > app.py
git add -A && git commit -qm "feat(export): stream orders as CSV"
printf 'from app import export\n\ndef test_header():\n    assert export([]).startswith("id,total")\n' > test_app.py
git add -A && git commit -qm "test(export): cover CSV header"
