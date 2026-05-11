"""
Scenario 3: Averaging Averages — The Naive Approach

AVG(daily_conversion_rate) treats every day equally, regardless
of traffic volume. A Tuesday with 450 visitors and a 24% rate
gets the same weight as a Monday with 12,000 visitors and an 8% rate.

This is Simpson's Paradox. Most vibe-coders have never heard of it.
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
    # THE NAIVE QUERY
    # "Average the daily conversion rates"
    # Gives equal weight to days with 350 visitors and 14,000 visitors.
    # --------------------------------------------------
    query = """
        SELECT
            ROUND(AVG(daily_rate), 2) as avg_conversion_rate
        FROM daily_metrics
    """

    result = pd.read_sql(query, conn)
    conn.close()

    print("=" * 60)
    print("SCENARIO 3: Averaging Averages — NAIVE APPROACH")
    print("=" * 60)
    print()
    print("Daily metrics:")
    print("-" * 55)
    print(f"  {'Date':<12} {'Visitors':>10} {'Conversions':>12} {'Rate':>8}")
    print("-" * 55)
    for _, row in data.iterrows():
        # Flag low-traffic days that inflate the average
        flag = " ← LOW TRAFFIC, HIGH RATE" if row["visitors"] < 1000 else ""
        print(f"  {str(row['date'].date()):<12} {row['visitors']:>10,} "
              f"{row['conversions']:>12,} {row['daily_rate']:>7.1f}%{flag}")
    print()
    print(f"Query: SELECT AVG(daily_rate) FROM daily_metrics")
    print()
    print(f"  Average conversion rate: {result['avg_conversion_rate'].iloc[0]}%")
    print()
    print("Problem: Days with 350-520 visitors (random noise producing")
    print("20-30% rates) get equal weight with days that have 10,000+")
    print("visitors. The average is dominated by small-sample outliers.")
    print()

    return result["avg_conversion_rate"].iloc[0]


if __name__ == "__main__":
    rate = run()
    print(f"Conversion rate reported: {rate}%")
    print()
    print("Business decision: \"15%+ conversion rate — our funnel is")
    print("best-in-class. Let's double ad spend.\"")
