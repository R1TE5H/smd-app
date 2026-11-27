from datetime import date
from decimal import Decimal

import pytest

from ledger import storage

CSV = """date,account,description,category,amount
2026-01-01,checking,Salary,salary,2000.00
2026-01-03,checking,Carrefour,groceries,-60.50
2026-01-10,savings,Interest,interest,1.25
"""


@pytest.fixture
def db(session, tmp_path):
    """The session, with the transactions of `CSV` imported."""
    path = tmp_path / "transactions.csv"
    path.write_text(CSV)
    storage.import_csv(session, path)
    return session


def test_import_csv(session, tmp_path):
    path = tmp_path / "transactions.csv"
    path.write_text(CSV)
    assert storage.import_csv(session, path) == 3
    assert len(storage.load_transactions(session)) == 3


def test_load_keeps_the_values(db):
    transactions = storage.load_transactions(db)
    assert [t.description for t in transactions] == ["Salary", "Carrefour", "Interest"]
    assert transactions[1].amount == Decimal("-60.50")
    assert transactions[2].account == "savings"


def test_add_to_an_unknown_account(db):
    with pytest.raises(ValueError, match="no account called 'cash'"):
        storage.add_transaction(
            db, "cash", Decimal("-5.00"), "food", "Coffee", date(2026, 1, 15)
        )
    assert len(storage.load_transactions(db)) == 3


def test_add_a_fraction_of_a_cent(db):
    with pytest.raises(ValueError, match="more than two decimals"):
        storage.add_transaction(
            db, "checking", Decimal("-1.005"), "food", "Gum", date(2026, 1, 15)
        )
    assert len(storage.load_transactions(db)) == 3


def test_add_then_load(db):
    added = storage.add_transaction(
        db, "checking", Decimal("-12.50"), "food", "Lunch", date(2026, 1, 15)
    )
    assert added.id is not None
    assert storage.load_transactions(db)[-1] == added
