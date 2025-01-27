import time
import pyupbit
from datetime import datetime

from src.strategies.base import Strategy, TradingStrategy
from src.strategies.volatility import VolatilityStrategy
from src.strategies.heikin_ashi import HeikinAshiStrategy
from src.strategies.combined import CombinedStrategy
from src.utils.logger import setup_logger, get_logger
from src.trading.account import TradingAccount
from src.trading.market import Market
from src.trading.order import OrderManager
from src.config.trading_config import TradingConfig

class TradingBot:
    def __init__(self, strategy_type: TradingStrategy):
        """트레이딩 봇 초기화"""
        setup_logger()
        self.logger = get_logger(__name__)

        self.strategy_type = strategy_type
        self.config = TradingConfig()
        self.market = Market()
        self.account = TradingAccount(self.config.api_keys)
        self.upbit = self.account.upbit
        self.order_manager = OrderManager(self.config, self.account, self.market)
        self.strategy = self._create_strategy()

    def _initialize_upbit(self) -> pyupbit.Upbit:
        """업비트 API 초기화"""
        try:
            return pyupbit.Upbit(
                self.config.api_keys.access_key,
                self.config.api_keys.secret_key
            )
        except Exception as e:
            self.logger.error(f"업비트 초기화 실패: {e}")
            raise

    def _create_strategy(self) -> Strategy:
        """전략 타입에 따른 전략 객체 생성"""
        if self.strategy_type == TradingStrategy.VOLATILITY:
            from src.strategies.volatility import VolatilityStrategy
            return VolatilityStrategy(self)
        elif self.strategy_type == TradingStrategy.HEIKIN_ASHI:
            from src.strategies.heikin_ashi import HeikinAshiStrategy
            return HeikinAshiStrategy(self)
        elif self.strategy_type == TradingStrategy.COMBINED:
            from src.strategies.combined import CombinedStrategy
            return CombinedStrategy(self)
        else:
            raise ValueError(f"지원하지 않는 전략 타입입니다: {self.strategy_type}")

    def check_system_status(self) -> bool:
        """시스템 상태 점검"""
        try:
            balance = self.account.get_balance("KRW")
            if balance is None:
                self.logger.error("API 키 인증 실패")
                return False

            if balance < self.config.trade_settings.min_krw_balance:
                self.logger.warning(f"잔고 부족: {balance}원")
                return False

            server_time = pyupbit.get_current_price("KRW-BTC")
            if server_time is None:
                self.logger.error("서버 연결 실패")
                return False

            return True

        except Exception as e:
            self.logger.error(f"시스템 체크 중 에러 발생: {e}")
            return False

    def run(self) -> None:
        """메인 실행 함수"""
        self.logger.info(f"자동매매 프로그램 시작 - 전략: {self.strategy_type.value}")

        if not self.check_system_status():
            self.logger.error("시스템 상태 체크 실패. 프로그램을 종료합니다.")
            return

        daily_trade_count = 0
        last_trade_date = datetime.now().date()

        while True:
            try:
                current_date = datetime.now().date()
                if current_date != last_trade_date:
                    daily_trade_count = 0
                    last_trade_date = current_date

                if daily_trade_count >= self.config.trade_settings.max_daily_trades:
                    self.logger.info("일일 거래 한도 도달")
                    time.sleep(1000)
                    continue

                if self.market.is_trade_time():
                    trades_executed = self._execute_trading_cycle()
                    if trades_executed:
                        daily_trade_count += 1

                time.sleep(self.config.trade_settings.trade_interval)

            except Exception as e:
                self.logger.error(f"전체 실행 중 에러 발생: {e}")
                time.sleep(self.config.trade_settings.trade_interval)

    def _execute_trading_cycle(self) -> bool:
        """거래 사이클 실행"""
        trades_executed = False
        for coin, coin_config in self.config.coin_settings.items():
            ticker = coin_config.ticker
            current_price = pyupbit.get_current_price(ticker)

            if current_price is None:
                continue

            if self.order_manager.execute_buy(ticker, current_price, self.strategy):
                trades_executed = True
            if self.order_manager.execute_sell(coin, coin_config, current_price):
                trades_executed = True
            time.sleep(1)

        return trades_executed
