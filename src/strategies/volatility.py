from typing import Optional
import pyupbit
from .base import Strategy

class VolatilityStrategy(Strategy):
    def __init__(self, bot):
        super().__init__(bot)
        self.trade_interval = "minute240"  # 거래용 4시간봉

    def get_target_price(self, ticker: str) -> Optional[float]:
        """
        변동성 돌파 전략의 목표가 계산
        """
        try:
            df = pyupbit.get_ohlcv(ticker, interval=self.trade_interval, count=2)
            target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * 0.5
            return target_price
        except Exception as e:
            self.bot.logger.error(f"목표가 계산 실패 - {ticker}: {e}")
            return None

    def should_buy(self, ticker: str, current_price: float) -> bool:
        """
        변동성 돌파 전략 매수 시점 판단
        - 현재가가 목표가를 상향 돌파하면 매수
        """
        target_price = self.get_target_price(ticker)
        if target_price is None:
            return False
        
        if current_price > target_price:
            self.bot.logger.info(f"변동성 돌파 매수 - {ticker}: 현재가 {current_price:,}원, 목표가 {target_price:,}원")
            return True
        
        return False 