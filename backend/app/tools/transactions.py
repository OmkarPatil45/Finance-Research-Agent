
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import Transaction


def _merchant_group():
    merchant = func.lower(func.trim(Transaction.merchant))

    aliases = [
        (merchant.contains("zepto"), "Zepto"),
        (merchant.contains("netflix"), "Netflix"),
        (merchant.contains("spotify"), "Spotify"),
        (merchant.contains("starbucks"), "Starbucks"),
        (merchant.contains("indigo"), "IndiGo Airlines"),
        (merchant.contains("air india"), "Air India"),
        (merchant.contains("myntra"), "Myntra"),
        (merchant.contains("irctc"), "IRCTC"),
        (merchant.contains("tata power"), "Tata Power"),
        (merchant.contains("amazon"), "Amazon"),
        (merchant.contains("bms*booking"), "BookMyShow"),
        (merchant.contains("bookmyshow"), "BookMyShow"),
        (merchant.contains("apollo pharmacy"), "Apollo Pharmacy"),
        (merchant.contains("cult.fit"), "Cult.fit"),
        (merchant.contains("cultfit"), "Cult.fit"),
    ]

    return case(*aliases, else_=func.trim(Transaction.merchant))

def _base_filters(
    snapshot_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    merchant: str | None = None,
    include_transfers: bool = False,
):
    if not snapshot_id or not snapshot_id.strip():
        raise ValueError("snapshot_id is required")

    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be after end_date")

    filters = [Transaction.snapshot_id == snapshot_id]

    if start_date:
        filters.append(Transaction.date >= start_date)

    if end_date:
        filters.append(Transaction.date <= end_date)

    if category:
        filters.append(
            func.lower(Transaction.category) == category.strip().lower()
        )

    if merchant:
        filters.append(
            Transaction.merchant.ilike(f"%{merchant.strip()}%")
        )

    if not include_transfers:
        filters.append(
            func.lower(Transaction.category) != "transfer"
        )

    return filters


def _money(value) -> float:
    return round(float(value or Decimal("0")), 2)


def filter_transactions(
    db: Session,
    snapshot_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    merchant: str | None = None,
    include_transfers: bool = False,
    limit: int = 100,
) -> dict:
    """Return matching transactions with a bounded result size."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    filters = _base_filters(
        snapshot_id,
        start_date,
        end_date,
        category,
        merchant,
        include_transfers,
    )

    stmt = (
        select(Transaction)
        .where(*filters)
        .order_by(Transaction.date, Transaction.id)
        .limit(limit)
    )

    rows = db.scalars(stmt).all()

    return {
        "snapshot_id": snapshot_id,
        "count": len(rows),
        "limit": limit,
        "transactions": [
            {
                "id": row.id,
                "date": row.date.isoformat(),
                "merchant": row.merchant,
                "category": row.category,
                "amount": _money(row.amount),
                "currency": row.currency,
                "memo": row.memo,
            }
            for row in rows
        ],
    }


def calculate_spending(
    db: Session,
    snapshot_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    merchant: str | None = None,
    include_transfers: bool = False,
) -> dict:
    """Calculate gross debits, refunds, and net spending."""
    filters = _base_filters(
        snapshot_id,
        start_date,
        end_date,
        category,
        merchant,
        include_transfers,
    )

    stmt = select(
        func.count(Transaction.row_id),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.amount > 0, Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ),
        func.coalesce(
            func.sum(
                case(
                    (Transaction.amount < 0, -Transaction.amount),
                    else_=0,
                )
            ),
            0,
        ),
        func.coalesce(func.sum(Transaction.amount), 0),
    ).where(*filters)

    count, gross, refunds, net = db.execute(stmt).one()

    return {
        "snapshot_id": snapshot_id,
        "transaction_count": count,
        "gross_debits": _money(gross),
        "refunds": _money(refunds),
        "net_spending": _money(net),
        "currency": "INR",
        "transfers_included": include_transfers,
    }


def spending_by_category(
    db: Session,
    snapshot_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    include_transfers: bool = False,
) -> dict:
    """Aggregate signed transaction amounts by category."""
    filters = _base_filters(
        snapshot_id,
        start_date,
        end_date,
        include_transfers=include_transfers,
    )

    stmt = (
        select(
            Transaction.category,
            func.count(Transaction.row_id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("net"),
        )
        .where(*filters)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = db.execute(stmt).all()

    return {
        "snapshot_id": snapshot_id,
        "currency": "INR",
        "categories": [
            {
                "category": row.category,
                "transaction_count": row.count,
                "net_spending": _money(row.net),
            }
            for row in rows
        ],
    }


def spending_by_merchant(
    db: Session,
    snapshot_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    include_transfers: bool = False,
    limit: int = 20,
) -> dict:
    """Aggregate transactions by normalized merchant name."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    filters = _base_filters(
        snapshot_id,
        start_date,
        end_date,
        category=category,
        include_transfers=include_transfers,
    )
    merchant_group = _merchant_group()

    stmt = (
        select(
            merchant_group.label("merchant"),
            func.count(Transaction.row_id).label("count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("net"),
        )
        .where(*filters)
        .group_by(merchant_group)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    return {
        "snapshot_id": snapshot_id,
        "currency": "INR",
        "merchants": [
            {
                "merchant": row.merchant,
                "transaction_count": row.count,
                "net_spending": _money(row.net),
            }
            for row in rows
        ],
    }
