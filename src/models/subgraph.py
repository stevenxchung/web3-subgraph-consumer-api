from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    id: str  # Included for debugging purposes but not stored
    name: str
    symbol: str
    totalSupply: str
    volumeUSD: str
    decimals: str


@dataclass
class TokenHourData:
    open: float
    close: float
    high: float
    low: float
    priceUSD: float
    token: Token
    periodStartUnix: str  # Need for ISO timestamp


@dataclass
class TokenHourDatas:
    tokenHourDatas: List[TokenHourData]


@dataclass
class SubgraphResponse:
    data: TokenHourDatas
