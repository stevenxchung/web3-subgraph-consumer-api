# Consumer + API Design

This document highlights some high-level design choices and implementation details for the Consumer + API design. We will try not to get too granular unless context is necessary as all of the core classes and methods in the repository already include comments and are named according to their functionality.

## Layout

The project layout is similar to most backend projects (e.g., Java Spring) to keep code as modular as possible but without going overboard with too many redundant classes, methods, interfaces, etc. since there are not multiple external services, data sources, etc. that we need to worry about.

- /src
  - /api - includes the API users can access
  - /models - includes classes based on the subgraph response
  - /repositories - includes methods to query a SQL database
  - /services - includes an API service layer to help convert query response into desired format and the subgraph consumer which are not directly accessible by the user
  - /utils - includes constants and helper functions
- app.py - the main entry point with both the consumer and API server
- /tests
  - /e2e - includes e2e tests for core components (e.g., API server)

## The Main Pieces

The high-level functionality of the application could be seen in `src/app.py` file where we run the consumer on its own thread and listen for when the **prefetching process** is completed before starting the API server. Let's break down the steps:

1. **Getting data**:
   - We look back 7 days from the current time for the consumer prefetching process and pull data directly from the subgraph for a given set of tokens
   - During the prefetching process, the consumer will pull 100 records at a time every 3 seconds and check the last record timestamp to see if we have caught up to current time
   - Once we have caught up to the current time, the consumer will notify `main()` in `src/app.py` with `prefetch_complete.set()` to start the API server and switch to poll hourly since `TokenHourData` is provided hourly from the subgraph
2. **Ingesting data**:
   - We store information in two SQL tables: `token_hour_data` and `token` which includes fields corresponding to `TokenHourData` and `Token` from the subgraph respectively
   - Postgres was selected for querying flexibility (key for our use case), transactional consistency, and where the performance compared to a NoSQL database like DynamoDB is negligible for the current payload and use case we have
   - On the database layer, the SQL query ensures that we check for conflicts on existing records during insertion so we may proceed with an update
3. **Serving data**:
   - Python Flask was selected as the framework for the API server since it is relatively simple and comes with the bare minimum modules which matches our requirements for a single endpoint
   - We use an API service layer to convert the SQL query response into a 3D array, decouple responsibilities, and avoid exposing a user-facing API directly to the database layer
   - When querying with SQL, the database layer first uses a CTE (virtual table) of timestamps based on the smallest and largest timestamp for a particular token. Then, it joins the CTE with the existing `token_hour_data` table and fills in missing data with `0` for `open, close, high, low, and priceUSD` fields before returning

### Serving Data

## Q&A

**Q: What went well?**

- Had a lot of fun figuring out how to query the Uniswap V3 Subgraph. It was interesting to see how much information is open for querying
- Also had fun piecing together a bunch of things from messing around with the consumer logic and database queries, to adding the API server and ensuring that the API server is triggered correctly
- The given requirements were well documented so there was not a whole lot of trouble regarding implementation

**Q: What could have gone better?**

The documentation on Uniswap is fair for basic querying but there seemed to be limitations when trying to request multiple tokens in one query for instance, the query below:

```typescript
{
  tokenHourDatas(
    first: 2
    orderBy: periodStartUnix
    orderDirection: asc
    where: {token: "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", or: {token: "0x6b175474e89094c44da98b954eedeac495271d0f"}}
  ) {
    periodStartUnix
    token {
      id
    }
  }
}
```

Which returns this error:

```json
{
  "errors": [
    {
      "locations": [
        {
          "column": 0,
          "line": 0
        }
      ],
      "message": "Invalid value provided for argument `where`: Object({\"or\": Object({\"token\": String(\"0x6b175474e89094c44da98b954eedeac495271d0f\")}), \"token\": String(\"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984\")})"
    }
  ]
}
```

There were hundreds of fields one could query from and some fields were less documented than others, e.g., timestamp was named `periodStartUnix` and some fields had vague abbreviations such as `_gt, _gte, _lt, _lte` which was not immediately clear in the beginning.

**Q: Is there anything specific you'd like to come back and improve if you had time? Why?**

- For simplicity, the current implementation does not make use of concurrency and threading during reads/writes on the database as the dataset is relatively small and takes only a few seconds to fetch and store a couple hundred records over 7 days but if the payload were to increase then it would be a desired performance enhancement to add particularly when fetching or storing data for hundreds of tokens at the same time over a longer period of time (e.g., 1 year)
- Similarly, when fetching via `get_chart_data()`, we may utilize a pandas DataFrame for more efficient transforms on bulk tabular data in the API service layer once we observe larger payloads or where more intensive transforms are necessary
- Currently `get_chart_data()` returns `TokenHourData` fields sorted in ascending order. There is no querying based on a specific date range or pagination support as of writing but this would be another enhancement which would enable more flexibility in querying especially when there are many more records
- Adding some unit tests for each component to ensure functionality
- Adding e2e tests for the consumer (currently only includes the API server)

Other open questions include:

- How many records to display from `get_chart_data()` by default?
- Should `get_chart_data()` response be sorted by ascending or descending by default?
- How do we want to handle when `token_symbol` or `time_unit_in_hours` is not provided to the API? The app returns `HTTP 400 Bad Request` as of writing
- What is the preferred response when the user passes in a token that is not being tracked, e.g., ETH? The app returns `[]` as of writing
- Although requirements mention to store `name, symbol, totalSupply, volumeUSD, and decimals`, we do not have an API defined for fetching this data. What additional features would utilize this data?
