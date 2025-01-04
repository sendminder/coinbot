import logging
from typing import Optional
import pyupbit
from datetime import datetime

class Market:
    def __init__(self):
        self.ha_interval = "minute60"    # 하이킨 아시용 1시간봉
        self.trade_interval = "minute240"  # 거래용 4시간봉

    def get_current_price(self, ticker: str) -> Optional[float]:
        """현재가 조회"""
        try:
            return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]
        except Exception as e:
            logging.error(f"현재가 조회 실패 - {ticker}: {e}")
            return None

    @staticmethod
    def is_trade_time() -> bool:
        """거래 시점 체크"""
        now = datetime.now()
        trade_hours = [0, 4, 8, 12, 16, 20]
        return now.hour in trade_hours and now.minute < 5 