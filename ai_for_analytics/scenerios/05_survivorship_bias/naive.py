"""
Scenario 5: Survivorship Bias — The Naive Approach

Query the users table for January cohort retention.
Problem: users who churned were hard-deleted. They literally
don't exist in the table you're querying.

You're measuring the survivors and calling it retention.
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
    # Deleted users table exists but the vibe-coder doesn't know about it.
    # They queried "users" and stopped there.

    # --------------------------------------------------
    # THE NAIVE QUERY
    # "How many January signups are still active in March?"
    # Queries only the users table. Deleted users don't exist here.
    # --------------------------------------------------
    query = """
        SELECT
            COUNT(*) as jan_cohort_size,
            SUM(CASE WHEN last_login >= '2025-03-01' THEN 1 ELSE 0 END) as active_in_march,
            ROUND(
                SUM(CASE WHEN last_login >= '2025-03-01' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                1
            ) as retention_rate
        FROM users
        WHERE signed_up >= '2025-01-01' AND signed_up < '2025-02-01'
    """

    result = pd.read_sql(query, conn)
    conn.close()

    r = result.iloc[0]

    print("=" * 60)
    print("SCENARIO 5: Survivorship Bias — NAIVE APPROACH")
    print("=" * 60)
    print()
    print("Users table (what the query sees):")
    print("-" * 55)
    for _, row in active_users.iterrows():
        print(f"  {row['user_id']}  signed up {row['signed_up'].date()}  "
              f"last login {row['last_login'].date()}  {row['status']}")
    print()
    print("Query: SELECT COUNT(*) as cohort, ... FROM users")
    print("       WHERE signed_up >= '2025-01-01'")
    print()
    print(f"  January cohort size:     {r['jan_cohort_size']:.0f}")
    print(f"  Active in March:         {r['active_in_march']:.0f}")
    print(f"  Retention rate:          {r['retention_rate']:.0f}%")
    print()
    print(f"The query found {r['jan_cohort_size']:.0f} January users and all {r['active_in_march']:.0f} are active.")
    print(f"Retention: {r['retention_rate']:.0f}%. Looks incredible.")
    print()
    print("What the query DOESN'T see: the deleted_users table with")
    print(f"{len(deleted_users)} churned users who no longer exist in 'users'.")
    print()

    return r["retention_rate"]


if __name__ == "__main__":
    rate = run()
    print(f"Retention rate reported: {rate:.0f}%")
    print()
    print("Business decision: \"100% retention — our product has")
    print("incredible stickiness. Focus budget on acquisition, not retention.\"")
