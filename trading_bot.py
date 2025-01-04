"""
암호화폐 자동매매 봇
- 변동성 돌파 전략
- 하이킨 아시 전략
- 복합 전략(두 전략 조합)
을 선택적으로 사용할 수 있는 트레이딩 봇

작성자: [작성자명]
최종수정: [날짜]
"""

import os
import time
import pyupbit
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
from abc import ABC, abstractmethod

# 거래 전략 유형 정의
class TradingStrategy(Enum):
    VOLATILITY = "volatility"    # 변동성 돌파 전략
    HEIKIN_ASHI = "heikin_ashi"  # 하이킨 아시 전략
    COMBINED = "combined"        # 두 전략 조합

# 전략 추상 클래스 - 모든 전략은 이 클래스를 상속받아야 함
class Strategy(ABC):
    @abstractmethod
    def should_buy(self, ticker: str, current_price: float, target_price: float) -> bool:
        """
        매수 시점 판단
        :param ticker: 코인 티커
        :param current_price: 현재가
        :param target_price: 목표가
        :return: 매수 여부 (True/False)
        """
        pass

# 변동성 돌파 전략 구현
class VolatilityStrategy(Strategy):
    def should_buy(self, ticker: str, current_price: float, target_price: float) -> bool:
        """
        변동성 돌파 전략 매수 시점 판단
        - 현재가가 목표가를 상향 돌파하면 매수
        """
        return current_price > target_price

# 하이킨 아시 전략 구현
class HeikinAshiStrategy(Strategy):
    def __init__(self, bot):
        self.bot = bot

    def should_buy(self, ticker: str, current_price: float, target_price: float) -> bool:
        """
        하이킨 아시 전략 매수 시점 판단
        - 상승 추세
        - 강한 추세 확인
        - 캔들 실체 존재
        - 이전 봉도 상승 추세
        모든 조건이 충족되어야 매수
        """
        ha_data = self.bot.get_heikin_ashi(ticker)
        if not ha_data:
            return False
            
        conditions = [
            ha_data['trend'] == 'up',      # 현재 상승 추세
            ha_data['strong_trend'],       # 강한 추세 확인
            ha_data['body_size'] > 0,      # 캔들 실체 존재
            ha_data['prev_trend'] == 'up'  # 이전 봉도 상승 추세
        ]
        
        return all(conditions)

# 복합 전략 구현 (변동성 돌파 + 하이킨 아시)
class CombinedStrategy(Strategy):
    def __init__(self, bot):
        self.volatility = VolatilityStrategy()
        self.heikin_ashi = HeikinAshiStrategy(bot)

    def should_buy(self, ticker: str, current_price: float, target_price: float) -> bool:
        """
        복합 전략 매수 시점 판단
        - 변동성 돌파 조건과 하이킨 아시 조건이 모두 충족되어야 매수
        """
        return (self.volatility.should_buy(ticker, current_price, target_price) and 
                self.heikin_ashi.should_buy(ticker, current_price, target_price))

# 메인 트레이딩 봇 클래스
class TradingBot:
    def __init__(self, strategy_type: TradingStrategy = TradingStrategy.COMBINED):
        """
        트레이딩 봇 초기화
        :param strategy_type: 사용할 전략 유형 (기본값: 복합 전략)
        """
        load_dotenv()  # 환경 변수 로드
        self._initialize_logging()  # 로깅 설정
        self._initialize_upbit()    # 업비트 API 초기화
        self.coin_settings = self._get_coin_settings()  # 코인별 설정 로드
        
        # 전략 설정
        self.strategy_type = strategy_type
        self.strategy = self._get_strategy(strategy_type)
        
        # 시간 프레임 설정
        self.ha_interval = "minute60"    # 하이킨 아시용 1시간봉
        self.trade_interval = "minute240"  # 거래용 4시간봉

    def _initialize_logging(self) -> None:
        """로깅 설정 초기화"""
        logging.basicConfig(
            filename='trading.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _initialize_upbit(self) -> None:
        """업비트 API 초기화"""
        try:
            access_key = os.getenv('UPBIT_ACCESS_KEY')
            secret_key = os.getenv('UPBIT_SECRET_KEY')
            self.upbit = pyupbit.Upbit(access_key, secret_key)
        except Exception as e:
            logging.error(f"업비트 초기화 실패: {e}")
            raise

    def _get_coin_settings(self) -> Dict:
        """
        코인별 거래 설정 정의
        - min_unit: 최소 거래 단위
        - take_profit: 익절 기준 (%)
        - profit_sell: 익절 시 매도 비율
        - stop_loss: 전체 손절 기준 (%)
        - partial_stop: 부분 손절 기준 (%)
        - partial_sell: 부분 손절 시 매도 비율
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
        :param strategy_type: 전략 유형
        :return: 해당 전략 객체
        """
        if strategy_type == TradingStrategy.VOLATILITY:
            return VolatilityStrategy()
        elif strategy_type == TradingStrategy.HEIKIN_ASHI:
            return HeikinAshiStrategy(self)
        else:
            return CombinedStrategy(self)

    def get_target_price(self, ticker: str) -> Optional[float]:
        """
        변동성 돌파 전략의 목표가 계산
        :param ticker: 코인 티커
        :return: 목표가 또는 None (실패시)
        """
        try:
            df = pyupbit.get_ohlcv(ticker, interval=self.trade_interval, count=2)
            target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * 0.5
            return target_price
        except Exception as e:
            logging.error(f"목표가 계산 실패 - {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> Optional[float]:
        """현재가 조회"""
        try:
            return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]
        except Exception as e:
            logging.error(f"현재가 조회 실패 - {ticker}: {e}")
            return None

    def get_balance(self, ticker: str) -> float:
        """
        특정 코인/원화의 보유량 조회
        :param ticker: 코인 티커 또는 'KRW'
        :return: 보유량 (실패시 0)
        """
        try:
            balances = self.upbit.get_balances()
            for b in balances:
                if b['currency'] == ticker:
                    if b['balance'] is not None:
                        return float(b['balance'])
            return 0
        except Exception as e:
            logging.error(f"잔고 조회 실패 - {ticker}: {e}")
            return 0

    def get_heikin_ashi(self, ticker: str) -> Optional[dict]:
        """
        하이킨 아시 지표 계산
        :param ticker: 코인 티커
        :return: 하이킨 아시 데이터 딕셔너리 또는 None (실패시)
        
        하이킨 아시 계산식:
        - HA_Close = (Open + High + Low + Close) / 4
        - HA_Open = (이전 HA_Open + 이전 HA_Close) / 2
        - HA_High = max(High, HA_Open, HA_Close)
        - HA_Low = min(Low, HA_Open, HA_Close)
        """
        try:
            df = pyupbit.get_ohlcv(ticker, interval=self.ha_interval, count=24)
            
            ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
            ha_open = (df['open'].shift(1) + df['close'].shift(1)) / 2
            ha_open.iloc[0] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2
            ha_high = df[['high', 'open', 'close']].max(axis=1)
            ha_low = df[['low', 'open', 'close']].min(axis=1)

            # 3개 연속 봉으로 강한 추세 판단
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
            logging.error(f"하이킨 아시 계산 실패 - {ticker}: {e}")
            return None

    @staticmethod
    def is_trade_time() -> bool:
        """
        거래 시점 체크 (4시간 봉 시작 시점)
        - 0시, 4시, 8시, 12시, 16시, 20시
        - 각 시간대 시작 후 5분 이내
        """
        now = datetime.now()
        trade_hours = [0, 4, 8, 12, 16, 20]
        return now.hour in trade_hours and now.minute < 5

    def execute_buy(self, ticker: str, current_price: float) -> None:
        """
        매수 로직 실행
        - 전략 조건 충족 시 매수
        - 각 코인당 총 자산의 5% 이내로 매수
        """
        try:
            target_price = self.get_target_price(ticker)
            if target_price is None:
                return

            if not self.strategy.should_buy(ticker, current_price, target_price):
                return
                
            krw = self.get_balance("KRW")
            max_investment = krw * 0.05  # 각 코인당 최대 5% 투자
            
            if krw > 5000:  # 최소 주문금액
                invest_amount = min(krw * 0.9995, max_investment)  # 수수료 고려
                self.upbit.buy_market_order(ticker, invest_amount)
                logging.info(f"매수 성공: {ticker} - 가격: {current_price:,}원, 투자금액: {invest_amount:,}원, 전략: {self.strategy_type.value}")
                
        except Exception as e:
            logging.error(f"매수 실패 - {ticker}: {e}")

    def execute_sell(self, coin: str, settings: Dict, current_price: float) -> None:
        """
        매도 로직 실행
        - 익절: take_profit 이상 수익 시
        - 전량 손절: stop_loss 이하 손실 시
        - 부분 손절: partial_stop 이하 손실 시
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
            logging.error(f"매도 실패 - {coin}: {e}")

    def _handle_profit_sell(self, ticker: str, balance: float, settings: Dict, profit_rate: float) -> None:
        """익절 처리"""
        sell_amount = balance * settings["profit_sell"]
        self.upbit.sell_market_order(ticker, sell_amount)
        logging.info(f"익절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {sell_amount}")

    def _handle_full_stop_loss(self, ticker: str, balance: float, profit_rate: float) -> None:
        """전량 손절 처리"""
        self.upbit.sell_market_order(ticker, balance)
        logging.info(f"전량 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {balance}")

    def _handle_partial_stop_loss(self, ticker: str, balance: float, settings: Dict, profit_rate: float) -> None:
        """부분 손절 처리"""
        sell_amount = balance * settings["partial_sell"]
        self.upbit.sell_market_order(ticker, sell_amount)
        logging.info(f"부분 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%, 매도량: {sell_amount}")

    def log_portfolio_status(self) -> None:
        """
        포트폴리오 상태 로깅
        - 각 코인별 보유현황
        - 현재 평가금액
        - 수익률
        - 총 보유자산
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
                
                logging.info(
                    f"보유현황 - {coin}: {balance:.8f}, "
                    f"평균매수가: {avg_price:,}원, "
                    f"현재가: {current:,}원, "
                    f"평가금액: {value:,}원, "
                    f"수익률: {profit:.2f}%"
                )
        
        krw_balance = self.get_balance("KRW")
        total_value += krw_balance
        logging.info(f"총 보유자산: {total_value:,}원 (현금: {krw_balance:,}원)")

    def check_system_status(self) -> bool:
        """
        시스템 상태 점검
        - API 키 유효성
        - 잔고 상태
        - 서버 연결 상태
        """
        try:
            balance = self.upbit.get_balance("KRW")
            if balance is None:
                logging.error("API 키 인증 실패")
                return False

            if balance < 5000:
                logging.warning(f"잔고 부족: {balance}원")
                return False

            server_time = pyupbit.get_current_price("KRW-BTC")
            if server_time is None:
                logging.error("서버 연결 실패")
                return False

            return True

        except Exception as e:
            logging.error(f"시스템 체크 중 에러 발생: {e}")
            return False

    def run(self) -> None:
        """
        메인 실행 함수
        - 시스템 상태 체크
        - 일일 거래 횟수 제한
        - 정해진 시간에 매매 실행
        - 포트폴리오 상태 모니터링
        """
        logging.info(f"자동매매 프로그램 시작 - 전략: {self.strategy_type.value}")
        print(f"자동매매 시작 - 전략: {self.strategy_type.value}")

        if not self.check_system_status():
            logging.error("시스템 상태 체크 실패. 프로그램을 종료합니다.")
            return

        daily_trade_count = 0
        last_trade_date = datetime.now().date()

        while True:
            try:
                current_date = datetime.now().date()
                
                # 일일 거래 횟수 초기화
                if current_date != last_trade_date:
                    daily_trade_count = 0
                    last_trade_date = current_date

                # 일일 거래 한도 체크 (20회)
                if daily_trade_count >= 20:
                    logging.info("일일 거래 한도 도달")
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
                logging.error(f"전체 실행 중 에러 발생: {e}")
                time.sleep(60)

def main():
    """프로그램 시작점"""
    # 사용할 전략 선택
    strategy = TradingStrategy.COMBINED  # 또는 VOLATILITY 또는 HEIKIN_ASHI
    bot = TradingBot(strategy)
    bot.run()

if __name__ == "__main__":
    main() 
