from enum import Enum
from abc import ABC, abstractmethod
from typing import Optional

class TradingStrategy(Enum):
    VOLATILITY = "volatility"
    HEIKIN_ASHI = "heikin_ashi"
    COMBINED = "combined"

class Strategy(ABC):
    def __init__(self, bot):
        self.bot = bot

    @abstractmethod
    def should_buy(self, ticker: str, current_price: float) -> bool:
        """
        매수 시점 판단
        :param ticker: 코인 티커
        :param current_price: 현재가
        :return: 매수 여부 (True/False)
        """
        pass

    def get_target_price(self, ticker: str) -> Optional[float]:
        """기본 목표가 계산 메서드 - 필요시 오버라이드"""
        return None
