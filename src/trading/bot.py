import os
import time
import pyupbit
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Optional, List

from src.strategies.base import Strategy, TradingStrategy
from src.strategies.volatility import VolatilityStrategy
from src.strategies.heikin_ashi import HeikinAshiStrategy
from src.strategies.combined import CombinedStrategy
from src.utils.logger import setup_logger, get_logger

class TradingBot:
    def __init__(self, strategy_type: TradingStrategy = TradingStrategy.COMBINED):
        """
        트레이딩 봇 초기화
        :param strategy_type: 사용할 전략 유형 (기본값: 복합 전략)
        """
        load_dotenv()  # 환경 변수 로드
        setup_logger()  # 로깅 설정
        self.logger = get_logger(__name__)
        self._initialize_upbit()    # 업비트 API 초기화
        self.coin_settings = self._get_coin_settings()  # 코인별 설정 로드
        
        # 전략 설정
        self.strategy_type = strategy_type
        self.strategy = self._get_strategy(strategy_type)
        
        # 시간 프레임 설정
        self.ha_interval = "minute60"    # 하이킨 아시용 1시간봉
        self.trade_interval = "minute240"  # 거래용 4시간봉

        # 투자 설정
        self.TOTAL_ASSETS = 4000000  # 총 자산 400만원
        self.MIN_INVEST_RATIO = 0.015  # 최소 투자비율 1.5%
        self.MAX_INVEST_RATIO = 0.05   # 최대 투자비율 5%

    def _initialize_upbit(self) -> None:
        """업비트 API 초기화"""
        try:
            access_key = os.getenv('UPBIT_ACCESS_KEY')
            secret_key = os.getenv('UPBIT_SECRET_KEY')
            self.upbit = pyupbit.Upbit(access_key, secret_key)
        except Exception as e:
            self.logger.error(f"업비트 초기화 실패: {e}")
            raise

    def _get_coin_settings(self) -> Dict:
        """
        코인별 거래 설정 정의
        """
        return {
            "BTC": {
                "ticker": "KRW-BTC",
                "min_unit": 0.00008,
                "take_profit": 1.5,     # 비트코인은 변동성이 작아 보수적 설정
                "profit_sell": 0.6,
                "stop_loss": -2.0,
                "partial_stop": -1.2,
                "partial_sell": 0.4
            },
            "ETH": {
                "ticker": "KRW-ETH",
                "min_unit": 0.001,
                "take_profit": 2.0,     # ETH는 중간 정도의 변동성
                "profit_sell": 0.5,
                "stop_loss": -2.5,
                "partial_stop": -1.5,
                "partial_sell": 0.4
            },
            "ETC": {
                "ticker": "KRW-ETC",
                "min_unit": 0.01,
                "take_profit": 2.5,     # ETC는 변동성이 가장 큼
                "profit_sell": 0.5,
                "stop_loss": -3.0,
                "partial_stop": -2.0,
                "partial_sell": 0.4
            }
        }

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

    def get_current_price(self, ticker: str) -> Optional[float]:
        """현재가 조회"""
        try:
            return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]
        except Exception as e:
            self.logger.error(f"현재가 조회 실패 - {ticker}: {e}")
            return None

    def get_balance(self, ticker: str) -> float:
        """
        특정 코인/원화의 보유량 조회
        """
        try:
            balances = self.upbit.get_balances()
            for b in balances:
                if b['currency'] == ticker:
                    if b['balance'] is not None:
                        return float(b['balance'])
            return 0
        except Exception as e:
            self.logger.error(f"잔고 조회 실패 - {ticker}: {e}")
            return 0

    @staticmethod
    def is_trade_time() -> bool:
        """
        거래 시점 체크 (4시간 봉 시작 시점)
        """
        now = datetime.now()
        trade_hours = [0, 4, 8, 12, 16, 20]
        return now.hour in trade_hours and now.minute < 5

    def execute_buy(self, ticker: str, current_price: float) -> None:
        """매수 로직 실행"""
        try:
            if not self.strategy.should_buy(ticker, current_price):
                return
                
            krw = self.get_balance("KRW")
            
            min_investment = self.TOTAL_ASSETS * self.MIN_INVEST_RATIO
            max_investment = self.TOTAL_ASSETS * self.MAX_INVEST_RATIO
            
            invest_amount = min(max(krw * 0.05, min_investment), max_investment)
            
            if krw > invest_amount:
                invest_amount = invest_amount * 0.9995
                self.upbit.buy_market_order(ticker, invest_amount)
                self.logger.info(f"매수 성공: {ticker} - 가격: {current_price:,}원, 투자금액: {invest_amount:,}원 (총자산의 {(invest_amount/self.TOTAL_ASSETS)*100:.1f}%), 전략: {self.strategy_type.value}")
                
        except Exception as e:
            self.logger.error(f"매수 실패 - {ticker}: {e}")

    def execute_sell(self, coin: str, settings: Dict, current_price: float) -> None:
        """
        매도 로직 실행
        """
        try:
            coin_balance = self.get_balance(coin)
            if coin_balance <= settings["min_unit"]:
                return

            ticker = settings["ticker"]
            avg_buy_price = self.upbit.get_avg_buy_price(ticker)
            profit_rate = (current_price - avg_buy_price) / avg_buy_price * 100

            if profit_rate >= settings["take_profit"]:
                self._handle_profit_sell(ticker, coin_balance, settings, profit_rate)
            elif profit_rate <= settings["stop_loss"]:
                self._handle_full_stop_loss(ticker, coin_balance, profit_rate)
            elif profit_rate <= settings["partial_stop"]:
                self._handle_partial_stop_loss(ticker, coin_balance, settings, profit_rate)

        except Exception as e:
            self.logger.error(f"매도 실패 - {coin}: {e}")

    def _handle_profit_sell(self, ticker: str, balance: float, settings: Dict, profit_rate: float) -> None:
        """익절 처리"""
        sell_amount = balance * settings["profit_sell"]
        self.upbit.sell_market_order(ticker, sell_amount)
        self.logger.info(f"익절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {sell_amount}")

    def _handle_full_stop_loss(self, ticker: str, balance: float, profit_rate: float) -> None:
        """전량 손절 처리"""
        self.upbit.sell_market_order(ticker, balance)
        self.logger.info(f"전량 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {balance}")

    def _handle_partial_stop_loss(self, ticker: str, balance: float, settings: Dict, profit_rate: float) -> None:
        """부분 손절 처리"""
        sell_amount = balance * settings["partial_sell"]
        self.upbit.sell_market_order(ticker, sell_amount)
        self.logger.info(f"부분 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {sell_amount}")

    def log_portfolio_status(self) -> None:
        """
        포트폴리오 상태 로깅
        """
        total_value = 0
        for coin, settings in self.coin_settings.items():
            balance = self.get_balance(coin)
            if balance > 0:
                ticker = settings["ticker"]
                current = self.get_current_price(ticker)
                avg_price = self.upbit.get_avg_buy_price(ticker)
                profit = (current - avg_price) / avg_price * 100
                value = current * balance
                total_value += value
                
                self.logger.info(
                    f"보유현황 - {coin}: {balance:.8f}, "
                    f"평균매수가: {avg_price:,}원, "
                    f"현재가: {current:,}원, "
                    f"평가금액: {value:,}원, "
                    f"수익률: {profit:.2f}%"
                )
        
        krw_balance = self.get_balance("KRW")
        total_value += krw_balance
        self.logger.info(f"총 보유자산: {total_value:,}원 (현금: {krw_balance:,}원)")

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
        """
        메인 실행 함수
        """
        self.logger.info(f"자동매매 프로그램 시작 - 전략: {self.strategy_type.value}")
        print(f"자동매매 시작 - 전략: {self.strategy_type.value}")

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

                if daily_trade_count >= 20:
                    self.logger.info("일일 거래 한도 도달")
                    time.sleep(60)
                    continue

                if self.is_trade_time():
                    for coin, settings in self.coin_settings.items():
                        ticker = settings["ticker"]
                        current_price = self.get_current_price(ticker)
                        
                        if current_price is None:
                            continue

                        self.execute_buy(ticker, current_price)
                        self.execute_sell(coin, settings, current_price)
                        time.sleep(1)

                    self.log_portfolio_status()
                    daily_trade_count += 1

                time.sleep(60)

            except Exception as e:
                self.logger.error(f"전체 실행 중 에러 발생: {e}")
                time.sleep(60) 