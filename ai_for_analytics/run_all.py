#!/usr/bin/env python3
"""
Run all analytics audit scenarios and print a summary comparison.

Each scenario demonstrates a common analytics bug that produces
a plausible but wrong result — the kind of result that ships to
a dashboard and drives a business decision.

Usage:
    python run_all.py           # Run all scenarios
    python run_all.py --verbose # Show detailed output per scenario
"""

import sys
import argparse
import sqlite3
import pandas as pd
import pytz

sys.path.insert(0, ".")
from data.generate import (
    generate_orders_and_items,
    generate_events_with_timestamps,
    generate_daily_conversion_metrics,
    generate_deals,
    generate_user_cohort,
)


def scenario_01_join_fanout():
    """Revenue double-counting from JOIN fanout."""
    orders, items = generate_orders_and_items()
    conn = sqlite3.connect(":memory:")
    orders.to_sql("orders", conn, index=False)
    items.to_sql("order_items", conn, index=False)

    naive = pd.read_sql(
        "SELECT SUM(o.order_total) as v FROM orders o "
        "JOIN order_items oi ON o.order_id = oi.order_id", conn
    ).iloc[0]["v"]

    correct = orders["order_total"].sum()
    conn.close()

    return {
        "name": "JOIN Fanout",
        "metric": "Total Revenue",
        "naive": f"${naive:,.0f}",
        "correct": f"${correct:,.0f}",
        "naive_raw": naive,
        "correct_raw": correct,
        "error_pct": (naive - correct) / correct * 100,
        "wrong_decision": "Hire 3 reps — revenue is booming",
        "right_decision": "Hold — revenue is solid but doesn't justify expansion",
    }


def scenario_02_timezone():
    """UTC vs local timezone daily grouping."""
    events = generate_events_with_timestamps()
    mst = pytz.timezone("US/Mountain")

    utc_counts = events.groupby(events["timestamp_utc"].dt.date).size()
    best_utc = utc_counts.idxmax()
    best_utc_day = pd.Timestamp(best_utc).strftime("%A")

    events["local_date"] = (
        events["timestamp_utc"]
        .dt.tz_localize("UTC")
        .dt.tz_convert(mst)
        .dt.date
    )
    local_counts = events.groupby("local_date").size()
    best_local = local_counts.idxmax()
    best_local_day = pd.Timestamp(best_local).strftime("%A")

    return {
        "name": "Timezone Shift",
        "metric": "Best Sales Day",
        "naive": f"{best_utc_day} ({utc_counts[best_utc]} purchases)",
        "correct": f"{best_local_day} ({local_counts[best_local]} purchases)",
        "naive_raw": best_utc_day,
        "correct_raw": best_local_day,
        "error_pct": None,  # Not a numeric inflation
        "wrong_decision": f"Run promotions on {best_utc_day}s",
        "right_decision": f"Run promotions on {best_local_day}s — that's the actual peak",
    }


def scenario_03_averaging():
    """Averaging daily conversion rates vs weighted rate."""
    data = generate_daily_conversion_metrics()

    naive = round(data["daily_rate"].mean(), 2)
    correct = round(data["conversions"].sum() / data["visitors"].sum() * 100, 2)

    return {
        "name": "Averaging Averages",
        "metric": "Conversion Rate",
        "naive": f"{naive}%",
        "correct": f"{correct}%",
        "naive_raw": naive,
        "correct_raw": correct,
        "error_pct": (naive - correct) / correct * 100,
        "wrong_decision": "Scale ad spend — funnel is best-in-class",
        "right_decision": "Optimize funnel before scaling — rate is mediocre",
    }


def scenario_04_nulls():
    """NULL-inflated deal size averages."""
    deals = generate_deals()

    naive = round(deals["amount"].dropna().mean(), 2)
    correct = round(deals["amount"].fillna(0).mean(), 2)

    return {
        "name": "NULL Handling",
        "metric": "Avg Deal Size",
        "naive": f"${naive:,.0f}",
        "correct": f"${correct:,.0f}",
        "naive_raw": naive,
        "correct_raw": correct,
        "error_pct": (naive - correct) / correct * 100,
        "wrong_decision": "Hire enterprise reps — ACV supports it",
        "right_decision": "Fix trial-to-paid conversion — true ACV is much lower",
    }


def scenario_05_survivorship():
    """Survivorship bias in retention calculations."""
    active, deleted = generate_user_cohort()

    jan_active = active[
        (active["signed_up"] >= "2025-01-01") &
        (active["signed_up"] < "2025-02-01")
    ]
    jan_deleted = deleted[
        (deleted["signed_up"] >= "2025-01-01") &
        (deleted["signed_up"] < "2025-02-01")
    ]

    naive_rate = 100.0  # All survivors are active by definition
    total_cohort = len(jan_active) + len(jan_deleted)
    retained = len(jan_active[jan_active["last_login"] >= "2025-03-01"])
    correct_rate = round(retained / total_cohort * 100, 1)

    return {
        "name": "Survivorship Bias",
        "metric": "Retention Rate",
        "naive": f"{naive_rate:.0f}% ({len(jan_active)} of {len(jan_active)})",
        "correct": f"{correct_rate}% ({retained} of {total_cohort})",
        "naive_raw": naive_rate,
        "correct_raw": correct_rate,
        "error_pct": (naive_rate - correct_rate) / correct_rate * 100,
        "wrong_decision": "Focus on acquisition — retention is perfect",
        "right_decision": "Fix churn — majority of users leave within 60 days",
    }


def main():
    parser = argparse.ArgumentParser(description="Analytics Audit — all scenarios")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    scenarios = [
        scenario_01_join_fanout,
        scenario_02_timezone,
        scenario_03_averaging,
        scenario_04_nulls,
        scenario_05_survivorship,
    ]

    results = []
    for fn in scenarios:
        results.append(fn())

    # Summary table
    print()
    print("=" * 76)
    print("  ANALYTICS AUDIT — SUMMARY")
    print("  Same data. Different queries. Different business decisions.")
    print("=" * 76)
    print()
    print(f"  {'#':<3} {'Scenario':<22} {'Metric':<17} {'Naive':<22} {'Correct':<22}")
    print("  " + "-" * 72)

    for i, r in enumerate(results, 1):
        print(f"  {i:<3} {r['name']:<22} {r['metric']:<17} {r['naive']:<22} {r['correct']:<22}")

    print()
    print("  Error magnitudes:")
    print("  " + "-" * 72)
    for i, r in enumerate(results, 1):
        if r["error_pct"] is not None:
            print(f"  {i}. {r['name']:<22} +{r['error_pct']:.0f}% inflation")
        else:
            print(f"  {i}. {r['name']:<22} Inverted — best day is wrong day")

    print()
    print("  Business decisions that change:")
    print("  " + "-" * 72)
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['name']}")
        print(f"     NAIVE:   {r['wrong_decision']}")
        print(f"     CORRECT: {r['right_decision']}")
        print()

    print("=" * 76)
    print("  Every naive query above is syntactically valid SQL.")
    print("  Every result is plausible. Every business decision is wrong.")
    print("  An LLM will generate the naive version every time.")
    print("=" * 76)
    print()

    if args.verbose:
        print("\n" + "=" * 76)
        print("  DETAILED SCENARIO OUTPUT")
        print("=" * 76 + "\n")

        from scenarios.s01_join_fanout import naive as s1n, correct as s1c
        from scenarios.s02_timezone_shift import naive as s2n, correct as s2c
        from scenarios.s03_averaging_averages import naive as s3n, correct as s3c
        from scenarios.s04_null_handling import naive as s4n, correct as s4c
        from scenarios.s05_survivorship_bias import naive as s5n, correct as s5c

        for naive_mod, correct_mod in [(s1n, s1c), (s2n, s2c), (s3n, s3c), (s4n, s4c), (s5n, s5c)]:
            naive_mod.run()
            print()
            correct_mod.run()
            print("\n")


if __name__ == "__main__":
    main()
