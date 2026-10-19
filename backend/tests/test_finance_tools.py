
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.db.session import engine
from app.tools.transactions import (
    calculate_spending,
    spending_by_category,
    spending_by_merchant,
)
from app.tools.funds import (
    calculate_fund_return,
    calculate_holding_returns,
)


@pytest.fixture
def db():
    with Session(engine) as session:
        yield session


def test_january_spending_matches_expected_values(db):
    result = calculate_spending(
        db,
        snapshot_id="sample_a",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    assert result["transaction_count"] == 103
    assert result["gross_debits"] == pytest.approx(253608.96)
    assert result["refunds"] == pytest.approx(28623.83)
    assert result["net_spending"] == pytest.approx(224985.13)
    assert result["transfers_included"] is False


def test_net_spending_equals_debits_minus_refunds(db):
    result = calculate_spending(
        db,
        snapshot_id="sample_a",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    expected = result["gross_debits"] - result["refunds"]
    assert result["net_spending"] == pytest.approx(expected)


def test_category_breakdown_contains_travel(db):
    result = spending_by_category(
        db,
        snapshot_id="sample_a",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    travel = next(
        item for item in result["categories"]
        if item["category"] == "travel"
    )
    assert travel["net_spending"] == pytest.approx(87192.12)
    assert travel["transaction_count"] == 12


def test_amazon_aliases_are_grouped(db):
    result = spending_by_merchant(
        db,
        snapshot_id="sample_a",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        limit=100,
    )

    amazon = [
        item for item in result["merchants"]
        if item["merchant"] == "Amazon"
    ]

    assert len(amazon) == 1
    assert amazon[0]["transaction_count"] == 14
    assert amazon[0]["net_spending"] == pytest.approx(64712.38)


def test_invalid_date_range_is_rejected(db):
    with pytest.raises(ValueError):
        calculate_spending(
            db,
            snapshot_id="sample_a",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 1, 1),
        )


def test_invalid_snapshot_is_rejected_by_fund_tool(db):
    with pytest.raises(ValueError):
        calculate_fund_return(
            db,
            snapshot_id="does_not_exist",
            fund_name="Apex Gold Savings Fund",
            start_date=date(2023, 4, 1),
            end_date=date(2025, 3, 1),
        )


def test_gold_fund_return(db):
    result = calculate_fund_return(
        db,
        snapshot_id="sample_a",
        fund_name="Apex Gold Savings Fund",
        start_date=date(2023, 4, 1),
        end_date=date(2025, 3, 1),
    )

    assert result["start_nav"] == pytest.approx(42.75)
    assert result["end_nav"] == pytest.approx(53.54)
    assert result["return_percentage"] == pytest.approx(25.2398)


def test_holdings_return_eight_records(db):
    result = calculate_holding_returns(
        db,
        snapshot_id="sample_a",
        as_of_date=date(2025, 3, 1),
    )

    assert result["count"] == 8
    assert len(result["holdings"]) == 8
    assert all(
        holding.get("status") == "missing_nav"
        or "profit_loss" in holding
        for holding in result["holdings"]
    )
