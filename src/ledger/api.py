"""The web API: reads the requests, calls storage and reports, returns JSON."""

import datetime
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ledger import db, reports, storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.create_tables()
    yield


app = FastAPI(title="ledger", lifespan=lifespan)


def get_session() -> Iterator[Session]:
    """One session per request, closed after the response."""
    with db.get_session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


class NewTransaction(BaseModel):
    date: datetime.date
    account: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    amount: Decimal


class TransactionOut(NewTransaction):
    id: int


class AccountOut(BaseModel):
    name: str
    balance: Decimal


@app.get("/api/accounts")
def list_accounts(session: SessionDep) -> list[AccountOut]:
    totals = reports.balances(storage.load_transactions(session))
    return [AccountOut(name=name, balance=total) for name, total in totals.items()]


@app.get("/api/transactions")
def list_transactions(
    session: SessionDep, account: str | None = None, category: str | None = None
) -> list[TransactionOut]:
    transactions = storage.load_transactions(
        session, account=account, category=category
    )
    return [
        TransactionOut.model_validate(t, from_attributes=True) for t in transactions
    ]


@app.get("/api/transactions/{transaction_id}")
def get_transaction(session: SessionDep, transaction_id: int) -> TransactionOut:
    transaction = storage.get_transaction(session, transaction_id)
    if transaction is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"there is no transaction {transaction_id}"
        )
    return TransactionOut.model_validate(transaction, from_attributes=True)


@app.post("/api/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(session: SessionDep, new: NewTransaction) -> TransactionOut:
    try:
        transaction = storage.add_transaction(
            session,
            new.account,
            new.amount,
            new.category,
            new.description,
            new.date,
        )
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from None
    return TransactionOut.model_validate(transaction, from_attributes=True)


@app.delete(
    "/api/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_transaction(session: SessionDep, transaction_id: int) -> None:
    if not storage.delete_transaction(session, transaction_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"there is no transaction {transaction_id}"
        )


@app.get("/api/reports/spending")
def spending(session: SessionDep) -> dict[str, Decimal]:
    return reports.spending_by_category(storage.load_transactions(session))


@app.get("/api/reports/months")
def months(session: SessionDep) -> dict[str, Decimal]:
    return reports.net_by_month(storage.load_transactions(session))
