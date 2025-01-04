from typing import Optional, Dict
import pyupbit
from .base import Strategy

class HeikinAshiStrategy(Strategy):
    def get_heikin_ashi(self, ticker: str) -> Optional[Dict]:
        """
        하이킨 아시 지표 계산
        """
        try:
            df = pyupbit.get_ohlcv(ticker, interval=self.bot.ha_interval, count=24)
            
            ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
            ha_open = (df['open'].shift(1) + df['close'].shift(1)) / 2
            ha_open.iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2
            ha_high = df[['high', 'open', 'close']].max(axis=1)
            ha_low = df[['low', 'open', 'close']].min(axis=1)

            recent_candles = 3
            strong_trend = all(
                ha_close.iloc[-i] > ha_open.iloc[-i] 
                for i in range(1, recent_candles+1)
            ) or all(
                ha_close.iloc[-i] < ha_open.iloc[-i] 
                for i in range(1, recent_candles+1)
            )
            
            return {
                'open': ha_open.iloc[-1],
                'high': ha_high.iloc[-1],
                'low': ha_low.iloc[-1],
                'close': ha_close.iloc[-1],
                'trend': 'up' if ha_close.iloc[-1] > ha_open.iloc[-1] else 'down',
                'strong_trend': strong_trend,
                'body_size': abs(ha_close.iloc[-1] - ha_open.iloc[-1]),
                'prev_trend': 'up' if ha_close.iloc[-2] > ha_open.iloc[-2] else 'down'
            }
            
        except Exception as e:
            self.bot.logger.error(f"하이킨 아시 계산 실패 - {ticker}: {e}")
            return None

    def should_buy(self, ticker: str, current_price: float) -> bool:
        """하이킨 아시 전략 매수 시점 판단"""
        ha_data = self.get_heikin_ashi(ticker)
        if ha_data is None:
            return False
            
        return (ha_data['trend'] == 'up' and 
                ha_data['strong_trend'] and 
                ha_data['prev_trend'] == 'down')  # 상승 반전 시점 