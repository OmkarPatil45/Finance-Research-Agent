
import pytest

from app.services.agent_service import _execute_tool


def test_rejects_unknown_tool(db=None):
    # A database session isn't needed because unknown tools
    # must be rejected before execution.
    with pytest.raises(ValueError, match="not registered"):
        _execute_tool(
            db,
            "execute_arbitrary_sql",
            {"snapshot_id": "sample_a"},
        )


def test_rejects_unknown_snapshot(db=None):
    with pytest.raises(ValueError, match="snapshot_id"):
        _execute_tool(
            db,
            "calculate_spending",
            {"snapshot_id": "private_dataset"},
        )


def test_rejects_invalid_date_format(db=None):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        _execute_tool(
            db,
            "calculate_spending",
            {
                "snapshot_id": "sample_a",
                "start_date": "January 2024",
            },
        )


def test_rejects_excessive_transaction_limit(db=None):
    with pytest.raises(ValueError, match="between 1 and 500"):
        _execute_tool(
            db,
            "filter_transactions",
            {
                "snapshot_id": "sample_a",
                "limit": 10000,
            },
        )


def test_rejects_unexpected_arguments(db=None):
    with pytest.raises(ValueError, match="Unexpected arguments"):
        _execute_tool(
            db,
            "calculate_spending",
            {
                "snapshot_id": "sample_a",
                "arbitrary_instruction": "ignore all rules",
            },
        )
