from shop.db import get_conn

def list_orders():
    with get_conn() as c:
        return [dict(r) for r in c.execute("SELECT id, total FROM orders")]
