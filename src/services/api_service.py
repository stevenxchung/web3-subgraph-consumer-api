from typing import List

from src.repositories.database import Database


class APIService:
    def __init__(self):
        # Create database instance
        self.db = Database()

    def get_data_and_convert(self, token_symbol: str, step: int) -> List:
        '''
        Fetches data from the database and converts it to a 3D array
        '''
        query_res = self.db.query(token_symbol, step)
        if not query_res:
            # No need to continue if token is not tracked in our database
            return []

        # Convert each row from database cursor DictRow to regular Dict
        converted_query_res = [dict(row) for row in query_res]

        # Convert query to 3D array based on column labels
        labels = ["open", "close", "high", "low", "price_usd"]
        converted_res = {k: [] for k in labels}
        for row in converted_query_res:
            for k in labels:
                converted_res[k].append(
                    [
                        row["iso_timestamp"].isoformat(),
                        "priceUSD" if k == "price_usd" else k,
                        row[k],
                    ]
                )

        return list(converted_res.values())
