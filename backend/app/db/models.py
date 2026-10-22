
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "id", name="uq_transaction_snapshot_id"),
    )

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(50), index=True)
    id: Mapped[str] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date, index=True)
    merchant: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10))
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)


class Fund(Base):
    __tablename__ = "funds"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "id", name="uq_fund_snapshot_id"),
    )

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(50), index=True)
    id: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))


class FundNAV(Base):
    __tablename__ = "fund_navs"
    __table_args__ = (
        UniqueConstraint(
            "snapshot_id", "fund_id", "date",
            name="uq_fund_nav_snapshot_fund_date",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "fund_id"],
            ["funds.snapshot_id", "funds.id"],
            name="fk_nav_fund_snapshot",
            ondelete="CASCADE",
        ),
    )

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(50), index=True)
    fund_id: Mapped[str] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4))


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["snapshot_id", "fund_id"],
            ["funds.snapshot_id", "funds.id"],
            name="fk_holding_fund_snapshot",
            ondelete="CASCADE",
        ),
    )

    row_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(50), index=True)
    fund_id: Mapped[str] = mapped_column(String(100))
    fund_name: Mapped[str] = mapped_column(String(255))
    units: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    purchase_date: Mapped[date] = mapped_column(Date)
    purchase_nav: Mapped[Decimal] = mapped_column(Numeric(14, 4))
