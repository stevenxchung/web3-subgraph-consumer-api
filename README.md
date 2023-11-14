# web3-subgraph-consumer-api

Consumer and API server for open [Web3 subgraphs](https://medium.com/iearn/subgraphs-explained-yearning-for-data-4e90d18e33e). For more information regarding implementation and design considerations, see [consumer-api-design.md](https://github.com/stevenxchung/web3-subgraph-consumer-api/blob/master/consumer-api-design.md). Enthusiasts may visit the official docs to learn more about [The Graph indexing protocol](https://thegraph.com/docs/en/about/).

## Setup

1. Ensure Python 3.10 is installed
2. Create a virtual environment: `python -m venv .venv`
3. Activate virtual environment:
   - Windows: `.venv/Scripts/activate`
   - Mac: `. .venv/bin/activate`
4. Run `pip install -r requirements.txt`

### Database Configuration

1. Following the `.env.example`, create an `.env` file with your database configuration
2. You will need to create a new `token_hour_data` and `token` table as shown below

```SQL
CREATE TABLE
    token_hour_data (
        PRIMARY KEY (iso_timestamp, token_symbol),
        iso_timestamp TIMESTAMP NOT NULL,
        token_symbol VARCHAR(255) NOT NULL,
        open FLOAT NOT NULL,
        close FLOAT NOT NULL,
        high FLOAT NOT NULL,
        low FLOAT NOT NULL,
        price_usd FLOAT NOT NULL
    );

CREATE TABLE
    token (
        PRIMARY KEY (symbol),
        name VARCHAR(255) NOT NULL,
        symbol VARCHAR(255) NOT NULL,
        total_supply VARCHAR(255) NOT NULL,
        volume_usd VARCHAR(255) NOT NULL,
        decimals VARCHAR(255) NOT NULL
    );
```

## Local Run

The `run.sh` script activates the environment and runs the app. Note that you may need to update the paths depending on your operating system. Alternatively, you may run the app by following the steps below:

1. Activate virtual environment:
   - Windows: `.venv/Scripts/activate`
   - Mac: `. .venv/bin/activate`
2. Run `python src/app.py`

### Querying The API

For querying the API manually I recommend using Postman:

- Create a new HTTP GET under a new collection
- Base URL is `{{your_base_url}}/chart-data`
- Query params are `token_symbol` (case-insensitive) and `time_unit_in_hours`

### Querying The API Externally

Oftentimes, if you aren't running Postman locally, you may have trouble reaching localhost. One recommendation is to setup [ngrok](https://ngrok.com/) which allows you to access your localhost from the internet.

## Debugging

If using VSCode, when debugging be sure to set breakpoints in any file but start the debugger on `src/app.py`. Otherwise, a `ModuleNotFoundError` will be thrown.

## Linting

Use `flake8 src/` in the root project directory to run against all `src/` files.

## Automated Testing

To run automated acceptance tests:

1. Ensure that your database and tables are setup according to above
2. If the database has not been populated yet run `sh run.sh` (skip if already populated)
3. Run `sh run_test.sh` to trigger e2e tests
