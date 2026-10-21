
import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Fund, FundNAV, Holding, Transaction


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a JSON array")

    return data


def _required_date(value, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid date in field '{field}': {value!r}")


def _required_decimal(value, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
        if not result.is_finite():
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Invalid numeric value in field '{field}': {value!r}")


def ingest_snapshot(db: Session, snapshot_path: str | Path) -> dict:
    path = Path(snapshot_path).resolve()

    if not path.is_dir():
        raise FileNotFoundError(f"Snapshot directory not found: {path}")

    snapshot_id = path.name
    if not snapshot_id or len(snapshot_id) > 50:
        raise ValueError("Snapshot directory name must be 1–50 characters")

    transactions = _read_json(path / "transactions.json")
    funds = _read_json(path / "funds.json")
    holdings = _read_json(path / "holdings.json")

    # Validate and prepare everything before modifying the database.
    transaction_rows = []
    for item in transactions:
        transaction_rows.append({
            "snapshot_id": snapshot_id,
            "id": str(item["id"]),
            "date": _required_date(item["date"], "date"),
            "merchant": str(item["merchant"]),
            "category": str(item["category"]),
            "amount": _required_decimal(item["amount"], "amount"),
            "currency": str(item["currency"]),
            "memo": item.get("memo"),
        })

    fund_rows = []
    nav_rows = []

    for item in funds:
        fund_id = str(item["id"])
        fund_rows.append({
            "snapshot_id": snapshot_id,
            "id": fund_id,
            "name": str(item["name"]),
            "category": str(item["category"]),
        })

        nav = item.get("nav")
        if not isinstance(nav, list):
            raise ValueError(f"Fund {fund_id} must contain a nav array")

        for point in nav:
            nav_rows.append({
                "snapshot_id": snapshot_id,
                "fund_id": fund_id,
                "date": _required_date(point["date"], "nav.date"),
                "value": _required_decimal(point["value"], "nav.value"),
            })

    holding_rows = []
    for item in holdings:
        holding_rows.append({
            "snapshot_id": snapshot_id,
            "fund_id": str(item["fund_id"]),
            "fund_name": str(item["fund_name"]),
            "units": _required_decimal(item["units"], "units"),
            "purchase_date": _required_date(
                item["purchase_date"], "purchase_date"
            ),
            "purchase_nav": _required_decimal(
                item["purchase_nav"], "purchase_nav"
            ),
        })

    # Validate IDs and relationships before inserting anything.
    for rows, key, label in [
        (transaction_rows, "id", "transaction"),
        (fund_rows, "id", "fund"),
    ]:
        values = [row[key] for row in rows]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {label} IDs in snapshot {snapshot_id}")

    fund_ids = {row["id"] for row in fund_rows}

    for row in nav_rows + holding_rows:
        if row["fund_id"] not in fund_ids:
            raise ValueError(
                f"Unknown fund_id {row['fund_id']} in snapshot {snapshot_id}"
            )

    nav_keys = [(row["fund_id"], row["date"]) for row in nav_rows]
    if len(nav_keys) != len(set(nav_keys)):
        raise ValueError(f"Duplicate fund NAV dates in snapshot {snapshot_id}")

    # Replace only this snapshot. Other snapshots remain untouched.
    with db.begin():
        db.execute(
            delete(FundNAV).where(FundNAV.snapshot_id == snapshot_id)
        )
        db.execute(
            delete(Holding).where(Holding.snapshot_id == snapshot_id)
        )
        db.execute(
            delete(Fund).where(Fund.snapshot_id == snapshot_id)
        )
        db.execute(
            delete(Transaction).where(
                Transaction.snapshot_id == snapshot_id
            )
        )

        db.add_all(Transaction(**row) for row in transaction_rows)
        db.add_all(Fund(**row) for row in fund_rows)
        db.add_all(FundNAV(**row) for row in nav_rows)
        db.add_all(Holding(**row) for row in holding_rows)

    return {
        "snapshot_id": snapshot_id,
        "transactions": len(transaction_rows),
        "funds": len(fund_rows),
        "fund_navs": len(nav_rows),
        "holdings": len(holding_rows),
    }
