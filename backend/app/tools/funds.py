
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Fund, FundNAV, Holding


def _money(value) -> float:
    return round(float(value or Decimal("0")), 2)


def _get_fund(db: Session, snapshot_id: str, fund_name: str):
    stmt = select(Fund).where(
        Fund.snapshot_id == snapshot_id,
        Fund.name.ilike(f"%{fund_name.strip()}%"),
    )
    funds = db.scalars(stmt).all()

    if not funds:
        raise ValueError(f"No fund found matching '{fund_name}'.")

    if len(funds) > 1:
        raise ValueError(
            f"Multiple funds match '{fund_name}'. Use a more specific name."
        )

    return funds[0]


def _get_nav_on_or_before(
    db: Session,
    snapshot_id: str,
    fund_id: str,
    target_date: date,
):
    stmt = (
        select(FundNAV)
        .where(
            FundNAV.snapshot_id == snapshot_id,
            FundNAV.fund_id == fund_id,
            FundNAV.date <= target_date,
        )
        .order_by(FundNAV.date.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def calculate_fund_return(
    db: Session,
    snapshot_id: str,
    fund_name: str,
    start_date: date,
    end_date: date,
):
    if not snapshot_id or not snapshot_id.strip():
        raise ValueError("snapshot_id is required.")

    if start_date > end_date:
        raise ValueError("start_date cannot be after end_date.")

    if start_date == end_date:
        raise ValueError("Choose two different dates.")

    fund = _get_fund(db, snapshot_id, fund_name)

    start_nav = _get_nav_on_or_before(
        db, snapshot_id, fund.id, start_date
    )
    end_nav = _get_nav_on_or_before(
        db, snapshot_id, fund.id, end_date
    )

    if not start_nav or not end_nav:
        raise ValueError("NAV data is unavailable for the requested period.")

    if start_nav.date == end_nav.date:
        raise ValueError(
            "No distinct NAV observations are available for this period."
        )

    start_value = Decimal(start_nav.value)
    end_value = Decimal(end_nav.value)

    if start_value <= 0:
        raise ValueError("Starting NAV must be positive.")

    percentage_return = (
        (end_value - start_value) / start_value
    ) * Decimal("100")

    return {
        "snapshot_id": snapshot_id,
        "fund_id": fund.id,
        "fund_name": fund.name,
        "start_date_requested": start_date.isoformat(),
        "start_nav_date": start_nav.date.isoformat(),
        "start_nav": _money(start_value),
        "end_date_requested": end_date.isoformat(),
        "end_nav_date": end_nav.date.isoformat(),
        "end_nav": _money(end_value),
        "return_percentage": round(float(percentage_return), 4),
        "currency": "INR",
        "method": "NAV percentage change; excludes distributions and fees",
    }


def calculate_holding_returns(
    db: Session,
    snapshot_id: str,
    as_of_date: date,
):
    if not snapshot_id or not snapshot_id.strip():
        raise ValueError("snapshot_id is required.")

    stmt = (
        select(Holding, Fund)
        .join(
            Fund,
            (Holding.snapshot_id == Fund.snapshot_id)
            & (Holding.fund_id == Fund.id),
        )
        .where(
            Holding.snapshot_id == snapshot_id,
            Holding.purchase_date <= as_of_date,
        )
        .order_by(Fund.name)
    )

    results = []

    for holding, fund in db.execute(stmt).all():
        current_nav = _get_nav_on_or_before(
            db, snapshot_id, holding.fund_id, as_of_date
        )

        if not current_nav:
            results.append({
                "fund_id": holding.fund_id,
                "fund_name": fund.name,
                "status": "missing_nav",
            })
            continue

        units = Decimal(holding.units)
        purchase_nav = Decimal(holding.purchase_nav)
        current_nav_value = Decimal(current_nav.value)

        invested_value = units * purchase_nav
        current_value = units * current_nav_value
        profit_loss = current_value - invested_value

        percentage_return = (
            (profit_loss / invested_value) * Decimal("100")
            if invested_value > 0
            else None
        )

        results.append({
            "fund_id": holding.fund_id,
            "fund_name": fund.name,
            "purchase_date": holding.purchase_date.isoformat(),
            "purchase_nav": _money(purchase_nav),
            "current_nav_date": current_nav.date.isoformat(),
            "current_nav": _money(current_nav_value),
            "units": float(units),
            "invested_value": _money(invested_value),
            "current_value": _money(current_value),
            "profit_loss": _money(profit_loss),
            "return_percentage": (
                round(float(percentage_return), 4)
                if percentage_return is not None
                else None
            ),
            "currency": "INR",
        })

    return {
        "snapshot_id": snapshot_id,
        "as_of_date_requested": as_of_date.isoformat(),
        "holdings": results,
        "count": len(results),
        "method": "Unrealized holding return based on units and NAV; excludes fees and distributions",
    }
