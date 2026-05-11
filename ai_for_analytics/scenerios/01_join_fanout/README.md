
# Scenario 1: JOIN Fanout Revenue Double-Count

## The Setup

You have an `orders` table with an `order_total` column, and an `order_items` table with line items per order. A perfectly reasonable schema.

## The Naive Query

```sql
SELECT SUM(o.order_total) FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
```

This is the first query an LLM generates if you ask "total revenue across all orders with item details." It's syntactically valid. It runs without error. It returns a number.

## Why It's Wrong

`order_total` is an attribute of the **order**, not the line item. When order 1003 has 3 line items, the JOIN produces 3 rows, each carrying the full $15,000 order total. `SUM()` adds $15,000 three times.

The inflation factor is invisible in aggregated output — you see one number, and it looks plausible. The only way to catch it is to **know that JOINs to child tables create fanout**, and to check whether your aggregation column belongs to the parent or child grain.

## How to Catch It

1. **Check the grain.** Before any `SUM()` or `COUNT()`, ask: "Is the column I'm summing at the same grain as my result set?" If you joined to a finer-grained table, the answer is no.
2. **Sanity check with a simpler query.** `SELECT SUM(order_total) FROM orders` — no join — gives you the baseline to compare against.
3. **Use DISTINCT or subqueries** if you must join but need parent-level aggregates.

## Business Impact

In this sample: $62,500 reported vs. $35,500 actual. A 76% inflation that could justify a hiring decision, a capacity expansion, or a board report that overstates growth by nearly 2×.
