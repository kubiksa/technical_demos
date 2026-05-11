"""
Scenario 4: NULL Handling — The Naive Approach

SQL's AVG() function silently ignores NULL values. It doesn't
treat them as zero — it excludes them from BOTH the numerator
AND the denominator.

This is documented behavior. It's also a trap that inflates
every metric calculated on a column with NULLs.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import sqlite3
import pandas as pd
from data.generate import generate_deals

def run():
    deals = generate_deals()

    conn = sqlite3.connect(":memory:")
    deals.to_sql("deals", conn, index=False)

    # --------------------------------------------------
    # THE NAIVE QUERY
    # "What's our average deal size?"
    # AVG(amount) ignores NULLs — denominator is 7, not 15.
    # --------------------------------------------------
    query = """
        SELECT
            AVG(amount) as avg_deal_size,
            COUNT(*) as total_deals
        FROM deals
    """

    # Show what AVG() actually computed
    debug_query = """
        SELECT
            COUNT(*) as total_rows,
            COUNT(amount) as non_null_rows,
            SUM(amount) as sum_of_non_nulls,
            AVG(amount) as sql_avg,
            ROUND(SUM(amount) * 1.0 / COUNT(amount), 2) as manual_calc
        FROM deals
    """

    result = pd.read_sql(query, conn)
    debug = pd.read_sql(debug_query, conn)
    conn.close()

    avg = result["avg_deal_size"].iloc[0]
    count = result["total_deals"].iloc[0]

    print("=" * 60)
    print("SCENARIO 4: NULL Handling — NAIVE APPROACH")
    print("=" * 60)
    print()
    print("Deals table:")
    print("-" * 55)
    for _, row in deals.iterrows():
        amt = f"${row['amount']:,.0f}" if pd.notna(row['amount']) else "NULL"
        flag = " ← invisible to AVG()" if pd.isna(row['amount']) else ""
        print(f"  {row['deal_id']}  {row['account']:<16} {amt:>10}  {row['status']:<12}{flag}")
    print()
    print(f"Query: SELECT AVG(amount), COUNT(*) FROM deals")
    print()
    print(f"  Average deal size: ${avg:,.0f}")
    print(f"  Total deals:       {count}")
    print()
    print("What SQL actually computed:")
    d = debug.iloc[0]
    print(f"  Total rows:          {d['total_rows']:.0f}")
    print(f"  Non-NULL rows:       {d['non_null_rows']:.0f}  ← THIS is AVG's denominator")
    print(f"  SUM(amount):         ${d['sum_of_non_nulls']:,.0f}")
    print(f"  SUM / COUNT(amount): ${d['manual_calc']:,.0f}  ← matches AVG()")
    print()
    print(f"AVG() used {d['non_null_rows']:.0f} as the denominator, not {d['total_rows']:.0f}.")
    print(f"{d['total_rows'] - d['non_null_rows']:.0f} free trials were excluded from the calculation entirely.")
    print()

    return avg


if __name__ == "__main__":
    avg = run()
    print(f"Average deal size reported: ${avg:,.0f}")
    print()
    print("Business decision: \"ACV is ~$40K — we can afford enterprise")
    print("reps at $150K OTE and a 12-month sales cycle.\"")
