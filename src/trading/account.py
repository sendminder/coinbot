import logging
from typing import Dict
import pyupbit
from src.utils.logger import get_logger
from src.config.trading_config import APIConfig

class TradingAccount:
    def __init__(self, api_keys: APIConfig):
        self.upbit = pyupbit.Upbit(api_keys.access_key, api_keys.secret_key)
        self.logger = get_logger(__name__)
        self.TOTAL_ASSETS = 4000000  # 총 자산 400만원
        self.MIN_INVEST_RATIO = 0.015  # 최소 투자비율 1.5%
        self.MAX_INVEST_RATIO = 0.05   # 최대 투자비율 5%

    def get_balance(self, ticker: str) -> float:
        """특정 코인/원화의 보유량 조회"""
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

    def calculate_invest_amount(self, krw_balance: float) -> float:
        """투자금액 계산"""
        min_investment = self.TOTAL_ASSETS * self.MIN_INVEST_RATIO
        max_investment = self.TOTAL_ASSETS * self.MAX_INVEST_RATIO
        return min(max(krw_balance, min_investment), max_investment)

    def get_average_buy_price(self, ticker: str) -> float:
        """특정 코인의 평균 매수가 조회"""
        try:
            balances = self.upbit.get_balances()
            for b in balances:
                if b['currency'] == ticker.replace('KRW-', ''):
                    return float(b['avg_buy_price'])
            return 0
        except Exception as e:
            self.logger.error(f"평균 매수가 조회 실패 - {ticker}: {e}")
            return 0

    def log_portfolio_status(self, coin_settings: Dict) -> None:
        """포트폴리오 상태 로깅"""
        try:
            total_value = self.get_balance("KRW")
            
            for coin, coin_config in coin_settings.items():
                ticker = coin_config.ticker
                balance = self.get_balance(coin)
                avg_price = self.get_average_buy_price(ticker)
                
                if balance > 0:
                    current_price = pyupbit.get_current_price(ticker)
                    if current_price:
                        coin_value = balance * current_price
                        profit_loss = ((current_price - avg_price) / avg_price) * 100
                        total_value += coin_value
                        
                        self.logger.info(
                            f"코인: {coin}, 보유량: {balance:.8f}, "
                            f"평균매수가: {avg_price:,.0f}, 현재가: {current_price:,.0f}, "
                            f"평가금액: {coin_value:,.0f}, 수익률: {profit_loss:.2f}%"
                        )

            self.logger.info(f"총 평가금액: {total_value:,.0f}원")
            
        except Exception as e:
            self.logger.error(f"포트폴리오 상태 로깅 실패: {e}") 