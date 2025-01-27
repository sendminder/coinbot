from src.config.trading_config import CoinConfig
from src.utils.logger import get_logger
from datetime import datetime

class OrderManager:
    def __init__(self, config, account, market):
        self.config = config
        self.account = account
        self.market = market
        self.upbit = account.upbit
        self.logger = get_logger(__name__)
        self.last_buy_time = {}  # 코인별 마지막 구매 시점 저장

    def execute_buy(self, ticker: str, current_price: float, strategy) -> None:
        """매수 로직 실행"""
        try:
            # 최근 1시간 이내 구매 여부 확인
            current_time = datetime.now()
            if ticker in self.last_buy_time:
                time_diff = (current_time - self.last_buy_time[ticker]).total_seconds() / 3600  # 시간 단위로 변환
                if time_diff < 1:  # 1시간 이내라면
                    self.logger.info(f"매수 제외 - {ticker}: 최근 1시간 이내 매수 이력 있음")
                    return

            if not strategy.should_buy(ticker, current_price):
                return

            krw = self.account.get_balance("KRW")
            invest_amount = self.account.calculate_invest_amount(krw)

            if krw > invest_amount:
                invest_amount = invest_amount * 0.9995  # 수수료 고려
                self.upbit.buy_market_order(ticker, invest_amount)
                self.last_buy_time[ticker] = current_time  # 구매 시점 기록
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

            # 익절
            if profit_rate >= coin_config.take_profit:
                if profit_krw >= self.config.trade_settings.min_profit_krw:
                    sell_amount = balance * coin_config.profit_sell
                    if sell_amount >= coin_config.min_unit:
                        self.upbit.sell_market_order(coin_config.ticker, sell_amount)
                        self.logger.info(f"익절 매도: {coin_config.ticker} - 수익률: {profit_rate:.2f}%, 수익금액: {profit_krw:,.0f}원")
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
