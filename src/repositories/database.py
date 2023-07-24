import os
from datetime import datetime
from typing import List

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import DictCursor

from src.models.subgraph import TokenHourDatas


class Database:
    def __init__(self):
        load_dotenv()
        self.conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST"),
            database=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
        )
        # Set w/ DictCursor to format outputs as dict
        self.cur = self.conn.cursor(cursor_factory=DictCursor)

    def query(self, token_symbol: str, step=1) -> List[DictCursor]:
        '''
        Returns rows of select fields and values from TokenHourData
        Note: default step is 1 hour to prevent step size error
        '''
        try:
            self.cur.execute(
                f"""
                WITH min_max_ts AS (
                    SELECT
                        MIN(DATE_TRUNC('hour', iso_timestamp)) AS min_timestamp,
                        MAX(DATE_TRUNC('hour', iso_timestamp)) AS max_timestamp
                    FROM
                        token_hour_data
                    WHERE
                        token_symbol = '{token_symbol}'
                ),
                ts_series AS (
                    SELECT
                        generate_series(min_timestamp, max_timestamp, INTERVAL '{step} hours') AS ts
                    FROM
                        min_max_ts
                )
                SELECT
                    ts AS iso_timestamp,
                    COALESCE(open, 0) AS open,
                    COALESCE(close, 0) AS close,
                    COALESCE(high, 0) AS high,
                    COALESCE(low, 0) AS low,
                    COALESCE(price_usd, 0) AS price_usd
                FROM
                    ts_series
                LEFT JOIN
                    token_hour_data ON DATE_TRUNC('hour', iso_timestamp) = ts AND token_symbol = '{token_symbol}'
                ORDER BY
                    ts;
                """
            )
            res = self.cur.fetchall()
            # Close cursor and connection after fetch completes
            self.cur.close()
            self.conn.close()
            return res

        except Exception as e:
            print(f"Database read error! {e}")

    def upsert(self, token_hour_datas: TokenHourDatas):
        '''
        Converts specific fields from TokenHourDatas and Token and upserts into a persistent SQL database
        '''
        batch_data = []
        for thd in token_hour_datas:
            iso_timestamp = datetime.fromtimestamp(
                thd["periodStartUnix"]
            ).isoformat()
            token = thd["token"]
            token_symbol = token["symbol"]

            open_value = thd["open"]
            close_value = thd["close"]
            high_value = thd["high"]
            low_value = thd["low"]
            price_usd_value = thd["priceUSD"]

            batch_data.append(
                (
                    iso_timestamp,
                    token_symbol,
                    open_value,
                    close_value,
                    high_value,
                    low_value,
                    price_usd_value,
                )
            )

        # For latest token, we only need to upsert once
        token = token_hour_datas[-1]["token"]
        token_as_row = [
            token["name"],
            token["symbol"],
            token["totalSupply"],
            token["volumeUSD"],
            token["decimals"],
        ]

        try:
            # Upsert the data in batches into the token_hour_data table
            self.cur.executemany(
                """
                INSERT INTO token_hour_data (iso_timestamp, token_symbol, open, close, high, low, price_usd)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (iso_timestamp, token_symbol) DO UPDATE
                SET
                    open = EXCLUDED.open,
                    close = EXCLUDED.close,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    price_usd = EXCLUDED.price_usd;
                """,
                batch_data,
            )

            # Upsert row into the token table
            self.cur.execute(
                """
                INSERT INTO token (name, symbol, total_supply, volume_usd, decimals)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE
                SET
                    name = EXCLUDED.name,
                    total_supply = EXCLUDED.total_supply,
                    volume_usd = EXCLUDED.volume_usd,
                    decimals = EXCLUDED.decimals;
                """,
                token_as_row,
            )

            # Commit and close the cursor (automatically handled by psycopg2)
            self.conn.commit()

        except Exception as e:
            print(f"Database write error! {e}")
