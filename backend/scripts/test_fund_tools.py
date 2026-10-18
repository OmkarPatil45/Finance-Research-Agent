
from datetime import date

from sqlalchemy.orm import Session

from app.db.session import engine
from app.tools.funds import (
    calculate_fund_return,
    calculate_holding_returns,
)


def main():
    with Session(engine) as db:
        funds = calculate_fund_return(
            db,
            snapshot_id="sample_a",
            fund_name="Apex Gold Savings Fund",
            start_date=date(2023, 4, 1),
            end_date=date(2025, 3, 1),
        )
        print("\n--- Fund return ---")
        print(funds)

        holdings = calculate_holding_returns(
            db,
            snapshot_id="sample_a",
            as_of_date=date(2025, 3, 1),
        )
        print("\n--- Holding returns ---")
        print(holdings)


if __name__ == "__main__":
    main()
