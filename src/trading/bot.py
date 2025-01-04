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
from src.config.trading_config import TradingConfig, Environment

class TradingBot:
    def __init__(self, 
                 strategy_type: TradingStrategy = TradingStrategy.COMBINED,
                 env: Environment = Environment.PRODUCTION):
        """트레이딩 봇 초기화"""
        setup_logger()
        self.logger = get_logger(__name__)
        
        self.config = TradingConfig(env)
        if not self.config.is_valid():
            raise ValueError("설정이 올바르지 않습니다.")
            
        self.upbit = self._initialize_upbit()
        self.account = TradingAccount(self.upbit)
        self.market = Market()
        self.order_manager = OrderManager(self.upbit, self.account, self.market)
        
        self.strategy_type = strategy_type
        self.strategy = self._get_strategy(strategy_type)

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

    def _get_strategy(self, strategy_type: TradingStrategy) -> Strategy:
        """
        전략 객체 생성
        """
        if strategy_type == TradingStrategy.VOLATILITY:
            return VolatilityStrategy(self)
        elif strategy_type == TradingStrategy.HEIKIN_ASHI:
            return HeikinAshiStrategy(self)
        else:
            return CombinedStrategy(self)

    def check_system_status(self) -> bool:
        """
        시스템 상태 점검
        """
        try:
            balance = self.upbit.get_balance("KRW")
            if balance is None:
                self.logger.error("API 키 인증 실패")
                return False

            if balance < 5000:
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
                    time.sleep(self.config.trade_settings.trade_interval)
                    continue

                if self.market.is_trade_time():
                    self._execute_trading_cycle()
                    daily_trade_count += 1

                time.sleep(self.config.trade_settings.trade_interval)

            except Exception as e:
                self.logger.error(f"전체 실행 중 에러 발생: {e}")
                time.sleep(self.config.trade_settings.trade_interval)

    def _execute_trading_cycle(self):
        """거래 사이클 실행"""
        for coin, settings in self.config.coin_settings.items():
            ticker = settings["ticker"]
            current_price = self.market.get_current_price(ticker)
            
            if current_price is None:
                continue

            self.order_manager.execute_buy(ticker, current_price, self.strategy)
            self.order_manager.execute_sell(coin, settings, current_price)
            time.sleep(1)

        self.account.log_portfolio_status(self.config.coin_settings) 