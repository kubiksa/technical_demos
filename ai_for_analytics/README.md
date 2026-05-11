# Analytics Audit: 5 Silent Bugs That Ship Wrong Business Decisions

Every scenario in this repo uses the **same source data** to produce **two different results** — one from a vibe-coded query, one from an experienced engineer. Both queries are syntactically valid. Both results are plausible. Only one is correct.

These aren't contrived edge cases. They're patterns I've encountered (and fixed) in production dashboards that drove real business decisions — headcount, ad spend, product strategy.

An LLM will confidently generate every one of the wrong queries below. It will even explain why the result makes sense.

## Scenarios

| # | Scenario | Naive Result | Correct Result | Business Impact |
|---|----------|-------------|----------------|-----------------|
| 1 | **JOIN Fanout** — Revenue double-count | $62,500 | $35,500 | Hire 3 reps you can't afford |
| 2 | **Timezone Shift** — UTC vs local | Mon is best day | Sun is best day | Promote the wrong day |
| 3 | **Averaging Averages** — Simpson's Paradox | 15.5% CVR | 8.2% CVR | Scale ad spend into a mediocre funnel |
| 4 | **NULL Handling** — Invisible free trials | $37,500 ACV | $21,429 ACV | Hire enterprise reps for an SMB product |
| 5 | **Survivorship Bias** — Deleted = never existed | 100% retention | 40% retention | Ignore a churn crisis |

## Quick Start

```bash
pip install pandas pytz
python run_all.py
```

Each scenario also runs standalone:

```bash
python scenarios/01_join_fanout/wrong.py
python scenarios/01_join_fanout/right.py
```

## Run Tests

```bash
python -m pytest tests/ -v
```

Tests assert the **correct** values and verify the naive queries produce **different** (wrong) results. If a test fails, the bug has been fixed — or a new one introduced.

## Structure

```
analytics-audit/
├── run_all.py              # Runs all scenarios, prints comparison table
├── data/
│   └── generate.py         # Creates all sample datasets
├── scenarios/
│   ├── 01_join_fanout/
│   │   ├── naive.py        # The query a vibe-coder writes
│   │   ├── correct.py      # The query an engineer writes
│   │   └── README.md       # Business context + explanation
│   ├── 02_timezone_shift/
│   ├── 03_averaging_averages/
│   ├── 04_null_handling/
│   └── 05_survivorship_bias/
├── tests/
│   └── test_scenarios.py   # Proves correct values, documents wrong ones
└── requirements.txt
```

## The Point

The gap between "syntactically valid SQL" and "correct analytics" is domain knowledge, data modeling intuition, and production experience. Tools that generate code don't have opinions about whether your JOIN creates a fanout, whether your timestamps are in the right timezone, or whether your denominator includes the records that got deleted last quarter.

If nobody on your team has been paged about a wrong dashboard number, you probably have wrong dashboard numbers.

## License

MIT
