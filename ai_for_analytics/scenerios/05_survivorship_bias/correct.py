"""
Scenario 5: Survivorship Bias — The Correct Approach

Reconstruct the full cohort by unioning active and deleted users.
Without this, your "retention rate" only measures survivors.

In a well-architected system, you'd have:
- Soft deletes (deleted_at column, not hard delete)
- An event log (signup, login, churn events are immutable)
- A slowly-changing dimension table for user state over time

Most systems have none of these. The deleted_users table existing
at all is generous — many companies purge and forget.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import sqlite3
import pandas as pd
from data.generate import generate_user_cohort

def run():
    active_users, deleted_users = generate_user_cohort()

    conn = sqlite3.connect(":memory:")
    active_users.to_sql("users", conn, index=False)
    deleted_users.to_sql("deleted_users", conn, index=False)

    # --------------------------------------------------
    # THE CORRECT APPROACH
    # Reconstruct the full January cohort from both tables.
    # --------------------------------------------------
    query = """
        WITH full_cohort AS (
            -- Active users who signed up in January
            SELECT user_id, signed_up, 'active' as current_status
            FROM users
            WHERE signed_up >= '2025-01-01' AND signed_up < '2025-02-01'

            UNION ALL

            -- Deleted users who signed up in January
            SELECT user_id, signed_up, 'deleted' as current_status
            FROM deleted_users
            WHERE signed_up >= '2025-01-01' AND signed_up < '2025-02-01'
        ),
        retention AS (
            SELECT
                fc.user_id,
                fc.signed_up,
                fc.current_status,
                CASE
                    WHEN u.last_login >= '2025-03-01' THEN 'retained'
                    ELSE 'churned'
                END as march_status
            FROM full_cohort fc
            LEFT JOIN users u ON fc.user_id = u.user_id
        )
        SELECT
            COUNT(*) as true_cohort_size,
            SUM(CASE WHEN march_status = 'retained' THEN 1 ELSE 0 END) as retained,
            SUM(CASE WHEN march_status = 'churned' THEN 1 ELSE 0 END) as churned,
            ROUND(
                SUM(CASE WHEN march_status = 'retained' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                1
            ) as true_retention_rate
        FROM retention
    """

    result = pd.read_sql(query, conn)

    # Show the full cohort for transparency
    cohort_detail = pd.read_sql("""
        SELECT user_id, signed_up, 'active' as status, last_login, NULL as deleted_on
        FROM users WHERE signed_up >= '2025-01-01' AND signed_up < '2025-02-01'
        UNION ALL
        SELECT user_id, signed_up, 'deleted' as status, NULL as last_login, deleted_on
        FROM deleted_users WHERE signed_up >= '2025-01-01' AND signed_up < '2025-02-01'
        ORDER BY signed_up
    """, conn)
    conn.close()

    r = result.iloc[0]

    print("=" * 60)
    print("SCENARIO 5: Survivorship Bias — CORRECT APPROACH")
    print("=" * 60)
    print()
    print("Full January cohort (active + deleted):")
    print("-" * 65)
    for _, row in cohort_detail.iterrows():
        if row["status"] == "active":
            detail = f"last login {row['last_login'][:10]}"
            flag = " ✓ retained"
        else:
            detail = f"deleted {row['deleted_on'][:10]}"
            flag = " ✗ churned"
        print(f"  {row['user_id']}  signed up {row['signed_up'][:10]}  "
              f"{row['status']:<8} {detail}{flag}")
    print()
    print("Retention calculation:")
    print(f"  True cohort size:        {r['true_cohort_size']:.0f}  (not {int(r['retained'])})")
    print(f"  Retained in March:       {r['retained']:.0f}")
    print(f"  Churned:                 {r['churned']:.0f}")
    print(f"  True retention rate:     {r['true_retention_rate']:.0f}%  (not 100%)")
    print()
    print("Comparison:")
    print(f"  Naive (survivors only):  100%  — 'all users are retained!'")
    print(f"  Correct (full cohort):   {r['true_retention_rate']:.0f}%   — '{r['churned']:.0f} of {r['true_cohort_size']:.0f} users churned'")
    print()
    print("KEY INSIGHT: Hard-deleting users destroys the denominator")
    print("for retention calculations. Without an event log or soft")
    print("deletes, you can't compute retention at all — you can only")
    print("compute survivor count, which is a fundamentally different")
    print("metric dressed up in the same words.")
    print()
    print("ARCHITECTURAL FIX:")
    print("  1. Soft deletes (deleted_at column, never remove rows)")
    print("  2. Immutable event log (signup, login, churn are facts)")
    print("  3. Slowly-changing dimension for user state over time")
    print("  4. Never derive retention from a mutable current-state table")
    print()

    return r["true_retention_rate"]


if __name__ == "__main__":
    rate = run()
    print(f"True retention rate: {rate:.0f}%")
    print()
    print("Business decision: \"32% retention — we have a severe churn")
    print("problem. Pause acquisition spend. Fix onboarding.\"")
