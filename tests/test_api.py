from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from ledger import api, storage
from ledger.db import Account


@pytest.fixture
def client(session):
    """A client of the API that uses the test database, with two accounts."""
    session.add_all([Account(name="checking"), Account(name="savings")])
    session.commit()
    storage.add_transaction(
        session, "checking", Decimal("2000.00"), "salary", "Salary", date(2026, 1, 1)
    )
    storage.add_transaction(
        session, "checking", Decimal("-39.90"), "health", "Gym", date(2026, 1, 10)
    )
    storage.add_transaction(
        session, "savings", Decimal("1.25"), "interest", "Interest", date(2026, 1, 31)
    )
    api.app.dependency_overrides[api.get_session] = lambda: session
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def lunch(**changes) -> dict:
    body = {
        "date": "2026-02-01",
        "account": "checking",
        "description": "Lunch",
        "category": "food",
        "amount": "-12.50",
    }
    return body | changes


def test_list_accounts(client):
    response = client.get("/api/accounts")
    assert response.status_code == 200
    assert response.json() == [
        {"name": "checking", "balance": "1960.10"},
        {"name": "savings", "balance": "1.25"},
    ]


def test_get_a_transaction(client):
    response = client.get("/api/transactions/2")
    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "date": "2026-01-10",
        "account": "checking",
        "description": "Gym",
        "category": "health",
        "amount": "-39.90",
    }


def test_get_a_missing_transaction(client):
    response = client.get("/api/transactions/99")
    assert response.status_code == 404
    assert "99" in response.json()["detail"]


def test_filter_transactions(client):
    response = client.get(
        "/api/transactions", params={"account": "checking", "category": "health"}
    )
    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [2]


def test_create_a_transaction(client):
    response = client.post("/api/transactions", json=lunch())
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == 4
    assert client.get("/api/transactions/4").json() == created
    assert client.get("/api/accounts").json()[0]["balance"] == "1947.60"


def test_create_in_an_unknown_account(client):
    response = client.post("/api/transactions", json=lunch(account="cash"))
    assert response.status_code == 400
    assert response.json() == {"detail": "there is no account called 'cash'"}


def test_create_with_a_bad_date(client):
    response = client.post("/api/transactions", json=lunch(date="2026-02-30"))
    assert response.status_code == 422


def test_delete_a_transaction(client):
    response = client.delete("/api/transactions/2")
    assert response.status_code == 204
    assert client.get("/api/transactions/2").status_code == 404
    assert client.delete("/api/transactions/2").status_code == 404
