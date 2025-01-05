from .base import Strategy
from .volatility import VolatilityStrategy
from .heikin_ashi import HeikinAshiStrategy

class CombinedStrategy(Strategy):
    def __init__(self, bot):
        super().__init__(bot)
        self.volatility = VolatilityStrategy(bot)
        self.heikin_ashi = HeikinAshiStrategy(bot)

    def should_buy(self, ticker: str, current_price: float) -> bool:
        """복합 전략 매수 시점 판단"""
        return (self.volatility.should_buy(ticker, current_price) or
                self.heikin_ashi.should_buy(ticker, current_price))
