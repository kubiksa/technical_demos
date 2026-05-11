"""
Scenario 1: JOIN Fanout — The Correct Approach

Two valid ways to calculate revenue, depending on what you need:
1. Sum from the orders table directly (no join needed)
2. Sum line-item amounts from order_items

Both give you the right number. The naive approach gives you
neither — it gives you a number inflated by the join fanout.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import sqlite3
import pandas as pd
from data.generate import generate_orders_and_items

def run():
    orders, items = generate_orders_and_items()

    conn = sqlite3.connect(":memory:")
    orders.to_sql("orders", conn, index=False)
    items.to_sql("order_items", conn, index=False)

    # --------------------------------------------------
    # APPROACH 1: Sum from orders directly. No join.
    # If you need order-level revenue, this is the table to query.
    # --------------------------------------------------
    query_from_orders = """
        SELECT
            SUM(order_total) as total_revenue,
            COUNT(*) as order_count,
            ROUND(AVG(order_total), 2) as avg_order_value
        FROM orders
    """

    # --------------------------------------------------
    # APPROACH 2: Sum from line items.
    # If you need item-level breakdown AND a total, sum the
    # item amounts — NOT the order total.
    # --------------------------------------------------
    query_from_items = """
        SELECT
            SUM(item_amount) as total_revenue,
            COUNT(DISTINCT order_id) as order_count,
            ROUND(SUM(item_amount) * 1.0 / COUNT(DISTINCT order_id), 2) as avg_order_value
        FROM order_items
    """

    # --------------------------------------------------
    # APPROACH 3: If you MUST join (e.g., filtering by order date
    # while accessing item details), deduplicate before summing.
    # --------------------------------------------------
    query_safe_join = """
        SELECT
            SUM(order_total) as total_revenue
        FROM (
            SELECT DISTINCT o.order_id, o.order_total
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            -- maybe you're filtering items here, but the DISTINCT
            -- ensures order_total isn't counted per item
        )
    """

    r1 = pd.read_sql(query_from_orders, conn)
    r2 = pd.read_sql(query_from_items, conn)
    r3 = pd.read_sql(query_safe_join, conn)
    conn.close()

    print("=" * 60)
    print("SCENARIO 1: JOIN Fanout — CORRECT APPROACH")
    print("=" * 60)
    print()
    print("Approach 1 — Sum directly from orders (no join needed):")
    print(f"  Total Revenue:     ${r1['total_revenue'].iloc[0]:,.0f}")
    print(f"  Order Count:       {r1['order_count'].iloc[0]}")
    print(f"  Avg Order Value:   ${r1['avg_order_value'].iloc[0]:,.0f}")
    print()
    print("Approach 2 — Sum from line items:")
    print(f"  Total Revenue:     ${r2['total_revenue'].iloc[0]:,.0f}")
    print(f"  Order Count:       {r2['order_count'].iloc[0]}")
    print(f"  Avg Order Value:   ${r2['avg_order_value'].iloc[0]:,.0f}")
    print()
    print("Approach 3 — JOIN with DISTINCT deduplication:")
    print(f"  Total Revenue:     ${r3['total_revenue'].iloc[0]:,.0f}")
    print()
    print("KEY INSIGHT: Approaches 1 and 3 agree on order-level revenue.")
    print("Approach 2 sums item amounts (may differ if items don't sum")
    print("to order total, e.g., discounts applied at order level).")
    print()

    return r1["total_revenue"].iloc[0]


if __name__ == "__main__":
    total = run()
    print(f"Actual revenue: ${total:,.0f}")
    print()
    print("Business decision: \"Revenue is $96K — solid growth but")
    print("not enough to justify expanding headcount this quarter.\"")
