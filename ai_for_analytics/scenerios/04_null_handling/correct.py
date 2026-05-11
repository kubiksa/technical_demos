"""
Scenario 4: NULL Handling — The Correct Approach

Report multiple metrics: average across ALL deals (NULLs as zero),
average across PAID deals only, and the paid conversion ratio.
The executive needs all three numbers to make a real decision.
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
    # THE CORRECT APPROACH
    # 1. COALESCE NULLs to 0 for a true average across all deals
    # 2. Report paid-only average separately
    # 3. Show the trial-to-paid conversion ratio
    # --------------------------------------------------
    query = """
        SELECT
            COUNT(*) as total_deals,
            COUNT(amount) as paid_deals,
            COUNT(*) - COUNT(amount) as trial_deals,
            ROUND((COUNT(*) - COUNT(amount)) * 100.0 / COUNT(*), 1) as trial_pct,

            ROUND(AVG(amount), 2) as avg_paid_only,
            ROUND(AVG(COALESCE(amount, 0)), 2) as avg_all_deals,
            ROUND(SUM(COALESCE(amount, 0)) * 1.0 / COUNT(*), 2) as true_avg,

            SUM(COALESCE(amount, 0)) as total_pipeline_value
        FROM deals
    """

    result = pd.read_sql(query, conn)
    conn.close()

    r = result.iloc[0]

    print("=" * 60)
    print("SCENARIO 4: NULL Handling — CORRECT APPROACH")
    print("=" * 60)
    print()
    print("The full picture:")
    print(f"  Total deals:           {r['total_deals']:.0f}")
    print(f"  Paid deals:            {r['paid_deals']:.0f}")
    print(f"  Free trials:           {r['trial_deals']:.0f} ({r['trial_pct']}% of pipeline)")
    print()
    print(f"  Avg (paid only):       ${r['avg_paid_only']:,.0f}  ← what AVG(amount) gives you")
    print(f"  Avg (all deals):       ${r['avg_all_deals']:,.0f}  ← what the business actually looks like")
    print(f"  Total pipeline value:  ${r['total_pipeline_value']:,.0f}")
    print()
    print("KEY INSIGHT: The 'average deal size' depends entirely on")
    print("whether you're asking 'what does a paying customer spend'")
    print("or 'what's the expected value of a deal in our pipeline.'")
    print()
    print("Both are valid questions. But if you report the first one")
    print("without mentioning the second, leadership will size the")
    print("sales team for a $40K ACV when the true expected value")
    print(f"per deal is ${r['avg_all_deals']:,.0f} — because {r['trial_pct']}% never pay.")
    print()
    print("WHAT TO REPORT:")
    print(f"  - Paid ACV:          ${r['avg_paid_only']:,.0f}")
    print(f"  - Blended ACV:       ${r['avg_all_deals']:,.0f}")
    print(f"  - Trial conversion:  {100 - r['trial_pct']:.0f}%")
    print("  - All three together. Never one alone.")
    print()

    return r["avg_all_deals"]


if __name__ == "__main__":
    avg = run()
    print(f"True blended average: ${avg:,.0f}")
    print()
    print("Business decision: \"Blended ACV is ~$19K. 53% of deals")
    print("are free trials. Fix trial-to-paid conversion before")
    print("hiring enterprise reps priced for a $40K ACV.\"")
