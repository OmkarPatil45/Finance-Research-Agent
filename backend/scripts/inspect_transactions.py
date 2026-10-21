from sqlalchemy import text
from app.db.session import engine

queries = {
    "Categories": """
        SELECT category, COUNT(*) AS records
        FROM transactions
        WHERE snapshot_id = 'sample_a'
        GROUP BY category
        ORDER BY records DESC
    """,
    "Negative amounts": """
        SELECT id, date, merchant, category, amount, memo
        FROM transactions
        WHERE snapshot_id = 'sample_a' AND amount < 0
        ORDER BY date
        LIMIT 15
    """,
    "Merchant frequency": """
        SELECT merchant, COUNT(*) AS records
        FROM transactions
        WHERE snapshot_id = 'sample_a'
        GROUP BY merchant
        ORDER BY records DESC
        LIMIT 25
    """,
    "Transfer/refund candidates": """
        SELECT id, merchant, category, amount, memo
        FROM transactions
        WHERE snapshot_id = 'sample_a'
          AND (
              merchant ILIKE '%transfer%'
              OR merchant ILIKE '%refund%'
              OR category ILIKE '%transfer%'
              OR memo ILIKE '%refund%'
              OR memo ILIKE '%transfer%'
          )
        LIMIT 25
    """
}

with engine.connect() as conn:
    for title, sql in queries.items():
        print(f"\n{'=' * 15} {title} {'=' * 15}")
        for row in conn.execute(text(sql)).mappings():
            print(dict(row))
