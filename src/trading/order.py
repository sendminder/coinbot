import logging
from typing import Dict
import pyupbit
from src.config.trading_config import CoinConfig
from src.utils.logger import get_logger

class OrderManager:
    def __init__(self, config, account, market):
        self.config = config
        self.account = account
        self.market = market
        self.upbit = account.upbit
        self.logger = get_logger(__name__)

    def execute_buy(self, ticker: str, current_price: float, strategy) -> None:
        """매수 로직 실행"""
        try:
            if not strategy.should_buy(ticker, current_price):
                self.logger.info(f"매수 안함 - {ticker}: 매수 조건 불만족")
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
            else:
                self.logger.info(f"매수 안함 - {ticker}: 잔액 부족")
                
        except Exception as e:
            self.logger.error(f"매수 실패 - {ticker}: {e}")

    def execute_sell(self, coin: str, coin_config: CoinConfig, current_price: float) -> None:
        """매도 로직 실행"""
        try:
            self.logger.info(f"매도 검토 시작 - {coin_config.ticker}")
            balance = self.account.get_balance(coin)
            if balance <= coin_config.min_unit:
                self.logger.info(f"매도 검토 제외 - {coin_config.ticker}: 최소 거래량({coin_config.min_unit}) 미만")
                return

            avg_price = self.account.get_average_buy_price(coin_config.ticker)
            if avg_price == 0:
                self.logger.info(f"매도 검토 제외 - {coin_config.ticker}: 평균 매수가 없음")
                return

            profit_rate = ((current_price - avg_price) / avg_price) * 100
            profit_krw = (current_price - avg_price) * balance
            
            self.logger.info(
                f"매도 검토 중 - {coin_config.ticker}: "
                f"현재가 {current_price:,}원, 평균매수가 {avg_price:,}원, "
                f"수익률 {profit_rate:.2f}%, 수익금액 {profit_krw:,.0f}원"
            )

            # 익절
            if profit_rate >= coin_config.take_profit:
                if profit_krw >= self.config.trade_settings.min_profit_krw:
                    sell_amount = balance * coin_config.profit_sell
                    if sell_amount >= coin_config.min_unit:
                        self.upbit.sell_market_order(coin_config.ticker, sell_amount)
                        self.logger.info(f"익절 매도: {coin_config.ticker} - 수익률: {profit_rate:.2f}%, 수익금액: {profit_krw:,.0f}원")
                    else:
                        self.logger.info(f"익절 보류 - {coin_config.ticker}: 매도량({sell_amount})이 최소 거래량({coin_config.min_unit}) 미만")
                else:
                    self.logger.info(f"익절 보류 - {coin_config.ticker}: 최소 수익금액({self.config.trade_settings.min_profit_krw:,}원) 미만")
                return

            # 손절
            if profit_rate <= coin_config.stop_loss and abs(profit_krw) >= self.config.trade_settings.min_loss_krw:
                self.upbit.sell_market_order(coin_config.ticker, balance)
                self.logger.info(f"손절 매도: {coin_config.ticker} - 수익률: {profit_rate:.2f}%, 손실금액: {profit_krw:,.0f}원")
                return

            # 부분 손절
            if profit_rate <= coin_config.partial_stop and abs(profit_krw) >= self.config.trade_settings.min_loss_krw:
                sell_amount = balance * coin_config.partial_sell
                if sell_amount >= coin_config.min_unit:
                    self.upbit.sell_market_order(coin_config.ticker, sell_amount)
                    self.logger.info(f"부분 손절: {coin_config.ticker} - 수익률: {profit_rate:.2f}%, 손실금액: {profit_krw:,.0f}원")
                return

        except Exception as e:
            self.logger.error(f"매도 실패 - {coin_config.ticker}: {e}") 