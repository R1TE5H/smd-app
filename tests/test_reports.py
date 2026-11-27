from datetime import date
from decimal import Decimal

import pytest

from ledger import reports
from ledger.models import Transaction


def make(day: str, account: str, category: str, amount: str) -> Transaction:
    return Transaction(
        date=date.fromisoformat(day),
        account=account,
        description=category,
        category=category,
        amount=Decimal(amount),
    )


@pytest.fixture
def transactions() -> list[Transaction]:
    return [
        make("2026-01-01", "checking", "salary", "2000.00"),
        make("2026-01-03", "checking", "groceries", "-60.50"),
        make("2026-01-10", "checking", "transfer", "-300.00"),
        make("2026-01-10", "savings", "transfer", "300.00"),
        make("2026-02-02", "checking", "groceries", "-40.25"),
        make("2026-02-05", "checking", "housing", "-900.00"),
    ]


def test_balances(transactions):
    assert reports.balances(transactions) == {
        "checking": Decimal("699.25"),
        "savings": Decimal("300.01"),
    }


def test_balances_of_no_transactions():
    assert reports.balances([]) == {}


def test_a_transfer_is_not_spending(transactions):
    assert "transfer" not in reports.spending_by_category(transactions)


def test_spending_by_category(transactions):
    spending = reports.spending_by_category(transactions)
    assert spending == {
        "housing": Decimal("900.00"),
        "groceries": Decimal("100.75"),
    }
    assert list(spending) == ["housing", "groceries"]


def test_net_by_month(transactions):
    assert reports.net_by_month(transactions) == {
        "2026-01": Decimal("1939.50"),
        "2026-02": Decimal("-940.25"),
    }
