
import calendar
import re
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Fund, FundNAV
from app.tools.transactions import (
    calculate_spending,
    spending_by_category,
    spending_by_merchant,
)
from app.tools.funds import (
    calculate_fund_return,
    calculate_holding_returns,
)


MONTHS = {
    name.lower(): number
    for number in range(1, 13)
    for name in (
        calendar.month_name[number],
        calendar.month_abbr[number],
    )
}

CATEGORIES = [
    "food", "groceries", "shopping", "travel", "transport",
    "utilities", "health", "subscription", "entertainment",
    "rent", "uncategorized", "transfer",
]


def _extract_period(question: str):
    match = re.search(
        r"\b(january|jan|february|feb|march|mar|april|apr|"
        r"may|june|jun|july|jul|august|aug|september|sep|"
        r"october|oct|november|nov|december|dec)\s+(\d{4})\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None, None

    month = MONTHS[match.group(1).lower()]
    year = int(match.group(2))

    return date(year, month, 1), date(
        year, month, calendar.monthrange(year, month)[1]
    )


def _find_fund(db: Session, snapshot_id: str, question: str):
    funds = db.scalars(
        select(Fund).where(Fund.snapshot_id == snapshot_id)
    ).all()

    normalized_question = question.casefold()

    matches = [
        fund for fund in funds
        if fund.name.casefold() in normalized_question
    ]

    return matches[0] if len(matches) == 1 else None


def answer_finance_question(
    db: Session,
    question: str,
    snapshot_id: str,
) -> str:
    q = question.strip()
    normalized = q.casefold()

    if not q:
        return "Please enter a financial question."

    start_date, end_date = _extract_period(q)

    # Fund performance questions require a fund name and date period.
    if any(word in normalized for word in ("fund", "nav", "investment return")):
        fund = _find_fund(db, snapshot_id, q)

        if not fund:
            return (
                "I couldn't identify one fund by its full name. "
                "Please include the exact fund name."
            )

        range_match = re.search(
            r"between\s+(\d{4}-\d{2}-\d{2})\s+and\s+"
            r"(\d{4}-\d{2}-\d{2})",
            normalized,
        )

        if not range_match:
            return (
                "Please provide the date range, for example: "
                "'Calculate the return of "
                "Apex Gold Savings Fund between "
                "2023-04-01 and 2025-03-01.'"
            )

        try:
            result = calculate_fund_return(
                db,
                snapshot_id,
                fund.name,
                date.fromisoformat(range_match.group(1)),
                date.fromisoformat(range_match.group(2)),
            )
            return (
                f"{result['fund_name']} returned "
                f"{result['return_percentage']:.2f}% based on NAV change "
                f"from {result['start_nav_date']} "
                f"(NAV ₹{result['start_nav']:.2f}) to "
                f"{result['end_nav_date']} "
                f"(NAV ₹{result['end_nav']:.2f}). "
                "This excludes distributions and fees."
            )
        except ValueError as exc:
            return f"Unable to calculate fund return: {exc}"

    # Holdings / portfolio valuation questions.
    if any(word in normalized for word in ("holding", "holdings", "portfolio")):
        latest_date = db.scalar(
            select(func.max(FundNAV.date)).where(
                FundNAV.snapshot_id == snapshot_id
            )
        )

        if not latest_date:
            return f"No fund NAV data was found for {snapshot_id}."

        result = calculate_holding_returns(db, snapshot_id, latest_date)
        total_value = sum(
            item.get("current_value", 0)
            for item in result["holdings"]
        )
        total_invested = sum(
            item.get("invested_value", 0)
            for item in result["holdings"]
        )
        total_pl = total_value - total_invested

        return (
            f"As of {latest_date.isoformat()}, your {snapshot_id} dataset "
            f"contains {result['count']} holdings. Their combined "
            f"invested value is ₹{total_invested:,.2f}, current value is "
            f"₹{total_value:,.2f}, and unrealized profit/loss is "
            f"₹{total_pl:,.2f}. These estimates exclude fees "
            "and distributions."
        )

    # Spending by category.
    if "categor" in normalized or "breakdown" in normalized:
        result = spending_by_category(
            db, snapshot_id, start_date=start_date, end_date=end_date
        )
        if not result["categories"]:
            return "No matching spending records were found."

        lines = [
            f"{item['category']}: ₹{item['net_spending']:,.2f}"
            for item in result["categories"]
        ]
        period_text = (
            f" for {start_date.strftime('%B %Y')}" if start_date else ""
        )
        return (
            f"Net spending by category{period_text} in {snapshot_id}:\n"
            + "\n".join(lines)
        )

    # Spending by merchant.
    merchant = None
    for candidate in (
        "amazon", "zepto", "netflix", "spotify", "myntra",
        "indigo", "irctc", "starbucks", "bookmyshow",
        "apollo pharmacy", "tata power", "cult.fit",
    ):
        if candidate in normalized:
            merchant = candidate
            break

    if merchant:
        result = calculate_spending(
            db,
            snapshot_id,
            start_date=start_date,
            end_date=end_date,
            merchant=merchant,
        )
        return (
            f"Net spending matching '{merchant}' in {snapshot_id} was "
            f"₹{result['net_spending']:,.2f} across "
            f"{result['transaction_count']} transactions "
            f"(refunds included in the net total)."
        )

    # General spending summary.
    if any(word in normalized for word in ("spend", "spent", "spending", "expense")):
        category = next(
            (item for item in CATEGORIES if item in normalized),
            None,
        )
        result = calculate_spending(
            db,
            snapshot_id,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
        period_text = (
            f" from {start_date.isoformat()} to {end_date.isoformat()}"
            if start_date else ""
        )
        category_text = f" in '{category}'" if category else ""
        return (
            f"Net spending{category_text}{period_text} in {snapshot_id} "
            f"was ₹{result['net_spending']:,.2f}. "
            f"Gross debits: ₹{result['gross_debits']:,.2f}; "
            f"refunds: ₹{result['refunds']:,.2f}; "
            f"transactions: {result['transaction_count']}. "
            "Internal transfers were excluded."
        )

    # Show the top merchants when explicitly requested.
    if "merchant" in normalized:
        result = spending_by_merchant(db, snapshot_id, limit=10)
        lines = [
            f"{item['merchant']}: ₹{item['net_spending']:,.2f}"
            for item in result["merchants"]
        ]
        return "Top merchants by net spending:\n" + "\n".join(lines)

    return (
        "I can currently answer spending-summary, category-breakdown, "
        "merchant-spending, fund-return, and holdings questions. "
        "Try asking one of these with a date period where applicable."
    )
