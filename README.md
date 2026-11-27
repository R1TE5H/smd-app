# smd-app

Personal finance ledger: balances, spending and monthly reports, stored in a SQLite database, from the command line or a web API.

## Run it

`uv run ledger import` (loads `data/transactions.csv`)

`uv run ledger balance`

`uv run ledger spending`

`uv run ledger months`

`uv run ledger add checking -12.50 food "Lunch"`

## Web API

`uv run fastapi dev src/ledger/api.py`, then open http://127.0.0.1:8000/docs

## Tests

`uv run pytest`

`uv run ruff check`

## Roadmap

- ~~Monthly report of income and spending~~
- ~~A database instead of a CSV file~~
- ~~A web API~~
- A dashboard

## Author
Ritesh Persaud
