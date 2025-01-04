import logging
from typing import Dict
from src.utils.logger import get_logger

class OrderManager:
    def __init__(self, upbit, account, market):
        self.upbit = upbit
        self.account = account
        self.market = market
        self.logger = get_logger(__name__)

    def execute_buy(self, ticker: str, current_price: float, strategy) -> None:
        """매수 로직 실행"""
        try:
            if not strategy.should_buy(ticker, current_price):
                return
                
            krw = self.account.get_balance("KRW")
            invest_amount = self.account.calculate_invest_amount(krw)
            
            if krw > invest_amount:
                invest_amount = invest_amount * 0.9995  # 수수료 고려
                self.upbit.buy_market_order(ticker, invest_amount)
                self.logger.info(
                    f"매수 성공: {ticker} - 가격: {current_price:,}원, "
                    f"투자금액: {invest_amount:,}원 "
                    f"(총자산의 {(invest_amount/self.account.TOTAL_ASSETS)*100:.1f}%)"
                )
                
        except Exception as e:
            self.logger.error(f"매수 실패 - {ticker}: {e}")

    def execute_sell(self, coin: str, settings: Dict, current_price: float) -> None:
        """매도 로직 실행"""
        try:
            balance = self.account.get_balance(coin)
            if balance <= settings["min_unit"]:
                return

            avg_price = self.account.get_average_buy_price(settings["ticker"])
            if avg_price == 0:
                return

            profit_rate = ((current_price - avg_price) / avg_price) * 100
            profit_krw = (current_price - avg_price) * balance  # 현재 수익/손실 금액 계산

            # 익절 (수익률과 최소 수익금액 모두 만족해야 함)
            if profit_rate >= settings["take_profit"] and profit_krw >= self.config.trade_settings.min_profit_krw:
                sell_amount = balance * settings["profit_sell"]
                if sell_amount >= settings["min_unit"]:
                    self.upbit.sell_market_order(settings["ticker"], sell_amount)
                    self.logger.info(f"익절 매도: {settings['ticker']} - 수익률: {profit_rate:.2f}%, 수익금액: {profit_krw:,.0f}원")
                return

            # 손절 (손실률과 최소 손실금액 모두 만족해야 함)
            if profit_rate <= settings["stop_loss"] and abs(profit_krw) >= self.config.trade_settings.min_loss_krw:
                self.upbit.sell_market_order(settings["ticker"], balance)
                self.logger.info(f"손절 매도: {settings['ticker']} - 수익률: {profit_rate:.2f}%, 손실금액: {profit_krw:,.0f}원")
                return

            # 부분 손절 (손실률과 최소 손실금액 모두 만족해야 함)
            if profit_rate <= settings["partial_stop"] and abs(profit_krw) >= self.config.trade_settings.min_loss_krw:
                sell_amount = balance * settings["partial_sell"]
                if sell_amount >= settings["min_unit"]:
                    self.upbit.sell_market_order(settings["ticker"], sell_amount)
                    self.logger.info(f"부분 손절: {settings['ticker']} - 수익률: {profit_rate:.2f}%, 손실금액: {profit_krw:,.0f}원")
                return

        except Exception as e:
            self.logger.error(f"매도 실패 - {settings['ticker']}: {e}") 