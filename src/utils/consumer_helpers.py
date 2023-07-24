from datetime import datetime, timedelta

from models.subgraph import SubgraphResponse


def generate_query(token_id: str, epoch: int, limit=100):
    """
    Uniswap V3 Subgraph (https://thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3)
    Sample Query
    {
        tokenHourDatas(
        orderBy: periodStartUnix
        first: 5
        orderDirection: asc
        where: {token: "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599", periodStartUnix_gte: 1689534000}
        ) {
        open
        close
        high
        low
        priceUSD
        token {
            name
            symbol
            totalSupply
            volumeUSD
            decimals
            id
        }
        periodStartUnix
        }
    }
    """
    query = f"""
            {{
                tokenHourDatas(
                    orderBy: periodStartUnix
                    first: {limit}
                    orderDirection: asc
                    where: {{
                            token: "{str(token_id).lower()}",
                            periodStartUnix_gte: {epoch}
                        }}
                    )
                {{
                    open
                    close
                    high
                    low
                    priceUSD
                    token {{
                        name
                        symbol
                        totalSupply
                        volumeUSD
                        decimals
                        id
                    }}
                    periodStartUnix
                }}
            }}
        """
    return query


def convert_subgraph_data(subgraph_res: SubgraphResponse) -> SubgraphResponse:
    token_hour_datas = subgraph_res["data"]["tokenHourDatas"]
    # Mainly want to convert these fields to floats
    fields = ["open", "close", "high", "low", "priceUSD"]
    for token_data in token_hour_datas:
        for field in fields:
            token_data[field] = round(float(token_data[field]), 2)

    return subgraph_res


def d_days_ago_epoch(days=7) -> int:
    # Default is one week ago from today
    d_days_ago = int((datetime.now() - timedelta(days=days)).timestamp())
    # Round down to nearest hour since TokenHourData goes by hours
    return (d_days_ago // 3600) * 3600
