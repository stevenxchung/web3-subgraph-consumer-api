import json
from datetime import datetime
from threading import Event
from time import sleep, time
from typing import Dict

import requests

from src.models.subgraph import SubgraphResponse, TokenHourDatas
from src.repositories.database import Database
from src.utils.constants import (
    GNO_TOKEN_ADDRESS,
    ISO_FORMAT,
    SHIB_TOKEN_ADDRESS,
    WBTC_TOKEN_ADDRESS,
)
from src.utils.consumer_helpers import (
    convert_subgraph_data,
    d_days_ago_epoch,
    generate_query,
)


class Consumer:
    def __init__(
        self,
        prefetch_complete: Event,
        poll_interval=3,
        graph_url="https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        debug=False,
    ):
        # Notify the main() function when
        self.prefetch_complete = prefetch_complete
        # Polling interval in seconds (e.g., poll every 30 seconds)
        self.poll_interval = poll_interval
        self.graph_url = graph_url
        self.debug = debug

        # Create database instance
        self.db = Database()

        token_list = [WBTC_TOKEN_ADDRESS, SHIB_TOKEN_ADDRESS, GNO_TOKEN_ADDRESS]
        # Track last queried records to determine latest timestamp positions
        last_epoch = d_days_ago_epoch()
        self.last_epochs = {token: last_epoch for token in token_list}
        self.present_epochs = {}

    def start(self):
        print("Starting the consumer...\n")
        try:
            self.prefetch_and_poll()
        except KeyboardInterrupt:
            print("Script interrupted. Terminating processes...")
            self.db.conn.close()

    def prefetch_and_poll(self):
        '''
        Prefetches 100 records every 3 seconds starting 7 days ago from current time
        for a set of tokens then switches to poll every hour when prefetching is complete
        '''
        start = time()

        while True:
            for token, epoch in self.last_epochs.items():
                self.query_and_store(token, epoch)

            # Checks latest timestamp positions
            self.is_prefetch_complete(start)

            # Set new positions based on the last fetched record timestamps in set
            self.last_epochs = self.present_epochs

            # Ensures cooldown before another request is made
            sleep(self.poll_interval)

    def is_prefetch_complete(self, start_time: float):
        '''
        Checks latest timestamp positions to determine if prefetch is complete
        '''
        if (
            self.last_epochs == self.present_epochs
            and self.poll_interval != 3600
        ):
            print("Prefetch complete! Switching to poll every hour.")

            # No need to fetch for another hour since TokenHourData is updated hourly
            self.poll_interval = 3600

            # Notify observers that prefetching is complete
            self.prefetch_complete.set()

            print(
                f"Prefetch runtime: {round(time() - start_time, 3)} seconds\n"
            )

    def query_and_store(self, token: str, epoch: int):
        '''
        Queries subgraph and saves TokenHourDatas to database
        '''
        datas: TokenHourDatas = self.query_subgraph_api(token, epoch)

        # Update each timestamp in hash table using latest timestamp
        self.present_epochs[datas[-1]["token"]["id"]] = datas[-1][
            "periodStartUnix"
        ]

        print("Saving to database...\n")
        self.db.upsert(datas)

    def query_subgraph_api(self, token_id: str, epoch: int) -> TokenHourDatas:
        '''
        Queries the subgraph via GraphQL based on the given token and epoch (Unix timestamp)
        '''
        api_res: SubgraphResponse = requests.post(
            self.graph_url,
            json={"query": generate_query(token_id, epoch, limit=100)},
        ).json()

        if "errors" in api_res:
            # Check for errors instead of HTTP status since we are using GraphQL
            for error in api_res["errors"]:
                print("GraphQL Error:", error["message"])
        else:
            converted_data = convert_subgraph_data(api_res)
            res = converted_data["data"]["tokenHourDatas"]
            self.log_if_enabled(epoch=epoch, subgraph_res=res)

            return res

    def log_if_enabled(self, epoch: str, subgraph_res: Dict):
        if self.debug:
            iso_start = datetime.fromtimestamp(epoch).strftime(ISO_FORMAT)
            iso_end = datetime.fromtimestamp(
                subgraph_res[-1]["periodStartUnix"]
            ).strftime(ISO_FORMAT)

            print(f"Query starting from: {epoch} (epoch), {iso_start} (ISO)")
            print(
                "Query success! Last fetched record: \n",
                json.dumps(subgraph_res[-1], indent=2),
                f"\nLast record timestamp: {iso_end}",
            )
