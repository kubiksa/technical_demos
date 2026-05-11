"""
Scenario 1: JOIN Fanout — The Naive Approach

This is the query a vibe-coder (or LLM) generates when asked
"what's our total revenue?"

The SQL is valid. The logic is wrong.
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
    # THE NAIVE QUERY
    # "Join orders to items so I can see everything, then sum the total"
    #
    # Problem: order_total belongs to the ORDER, not the item.
    # A 3-item order counts the total 3 times.
    # --------------------------------------------------
    query = """
        SELECT
            SUM(o.order_total) as total_revenue,
            COUNT(DISTINCT o.order_id) as order_count,
            ROUND(AVG(o.order_total), 2) as avg_order_value
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
    """

    result = pd.read_sql(query, conn)

    # Also show the per-order damage
    detail_query = """
        SELECT
            o.order_id,
            o.customer,
            o.order_total,
            COUNT(oi.item_name) as item_count,
            o.order_total * COUNT(oi.item_name) as inflated_contribution
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.customer, o.order_total
    """
    detail = pd.read_sql(detail_query, conn)
    conn.close()

    print("=" * 60)
    print("SCENARIO 1: JOIN Fanout — NAIVE APPROACH")
    print("=" * 60)
    print()
    print("Query: SELECT SUM(o.order_total) FROM orders o")
    print("       JOIN order_items oi ON o.order_id = oi.order_id")
    print()
    print(f"  Total Revenue:     ${result['total_revenue'].iloc[0]:,.0f}")
    print(f"  Order Count:       {result['order_count'].iloc[0]}")
    print(f"  Avg Order Value:   ${result['avg_order_value'].iloc[0]:,.0f}")
    print()
    print("Per-order inflation:")
    print("-" * 60)
    for _, row in detail.iterrows():
        multiplier = row["item_count"]
        flag = " ← INFLATED" if multiplier > 1 else ""
        print(f"  {row['customer']:<22} ${row['order_total']:>8,.0f} × {multiplier} items = "
              f"${row['inflated_contribution']:>10,.0f}{flag}")
    print()

    return result["total_revenue"].iloc[0]


if __name__ == "__main__":
    total = run()
    print(f"Revenue reported to leadership: ${total:,.0f}")
    print()
    print("Business decision: \"Revenue is strong — let's expand the sales team.\"")
