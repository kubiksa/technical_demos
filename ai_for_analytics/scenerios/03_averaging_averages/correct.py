"""
Scenario 3: Averaging Averages — The Correct Approach

Total conversions / total visitors gives the true weighted rate.
This is basic statistics, but it's the #1 metric calculation
error in production dashboards.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import sqlite3
import pandas as pd
from data.generate import generate_daily_conversion_metrics

def run():
    data = generate_daily_conversion_metrics()

    conn = sqlite3.connect(":memory:")
    data.to_sql("daily_metrics", conn, index=False)

    # --------------------------------------------------
    # THE CORRECT QUERY
    # Weight by traffic volume: total conversions / total visitors
    # --------------------------------------------------
    query = """
        SELECT
            SUM(visitors) as total_visitors,
            SUM(conversions) as total_conversions,
            ROUND(SUM(conversions) * 100.0 / SUM(visitors), 2) as true_conversion_rate,
            ROUND(AVG(daily_rate), 2) as naive_avg_rate
        FROM daily_metrics
    """

    # Also compute the contribution of each day to show WHY
    weighted_query = """
        SELECT
            date,
            visitors,
            conversions,
            daily_rate,
            ROUND(visitors * 100.0 / (SELECT SUM(visitors) FROM daily_metrics), 1) as traffic_share_pct,
            ROUND(daily_rate * visitors / (SELECT SUM(visitors) FROM daily_metrics), 2) as weighted_contribution
        FROM daily_metrics
        ORDER BY visitors DESC
    """

    result = pd.read_sql(query, conn)
    weighted = pd.read_sql(weighted_query, conn)
    conn.close()

    true_rate = result["true_conversion_rate"].iloc[0]
    naive_rate = result["naive_avg_rate"].iloc[0]
    total_v = result["total_visitors"].iloc[0]
    total_c = result["total_conversions"].iloc[0]

    print("=" * 60)
    print("SCENARIO 3: Averaging Averages — CORRECT APPROACH")
    print("=" * 60)
    print()
    print(f"Total visitors:    {total_v:>10,}")
    print(f"Total conversions: {total_c:>10,}")
    print(f"True rate:         {true_rate:>9}%  (conversions / visitors)")
    print(f"Naive avg:         {naive_rate:>9}%  (avg of daily rates)")
    print(f"Inflation:         {naive_rate - true_rate:>9.1f}pp")
    print()
    print("Why the naive average is wrong — traffic weight per day:")
    print("-" * 72)
    print(f"  {'Date':<12} {'Visitors':>8} {'Rate':>7} {'Traffic Share':>14} {'Weighted Rate':>14}")
    print("-" * 72)
    for _, row in weighted.iterrows():
        flag = " ← noise" if row["visitors"] < 1000 else ""
        print(f"  {row['date']:<12} {row['visitors']:>8,.0f} {row['daily_rate']:>6.1f}% "
              f"{row['traffic_share_pct']:>12.1f}%  {row['weighted_contribution']:>13.2f}%{flag}")
    print()
    print(f"  Sum of weighted contributions = {weighted['weighted_contribution'].sum():.2f}% "
          f"(matches true rate: {true_rate}%)")
    print()
    print("KEY INSIGHT: Low-traffic days (< 1,000 visitors) represent")
    print(f"only ~{weighted[weighted['visitors'] < 1000]['traffic_share_pct'].sum():.0f}% of traffic "
          f"but dominate the naive average with 20-30% rates")
    print("driven by small-sample randomness. Weighting by volume")
    print(f"reveals the true rate is {true_rate}%, not {naive_rate}%.")
    print()

    return true_rate


if __name__ == "__main__":
    rate = run()
    print(f"Actual conversion rate: {rate}%")
    print()
    print("Business decision: \"8.2% conversion — decent, not exceptional.")
    print("Optimize the funnel before scaling ad spend.\"")
