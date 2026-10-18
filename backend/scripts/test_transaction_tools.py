
from datetime import date

from sqlalchemy.orm import Session

from app.db.session import engine
from app.tools.transactions import (
    calculate_spending,
    filter_transactions,
    spending_by_category,
    spending_by_merchant,
)


def main():
    with Session(engine) as db:
        print("\n--- January 2024 spending ---")
        print(
            calculate_spending(
                db,
                snapshot_id="sample_a",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        )

        print("\n--- Spending by category ---")
        print(
            spending_by_category(
                db,
                snapshot_id="sample_a",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
            )
        )

        print("\n--- Merchant aliases ---")
        print(
            spending_by_merchant(
                db,
                snapshot_id="sample_a",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                limit=10,
            )
        )

        print("\n--- Filtered refunds ---")
        print(
            filter_transactions(
                db,
                snapshot_id="sample_a",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                merchant="IndiGo",
            )
        )


if __name__ == "__main__":
    main()
