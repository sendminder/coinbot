import os
import time
import pyupbit
from dotenv import load_dotenv
import logging
import numpy

# .env 파일에서 환경변수 로드
load_dotenv()

# 업비트 접근 키
access_key = os.getenv('UPBIT_ACCESS_KEY')
secret_key = os.getenv('UPBIT_SECRET_KEY')

# 업비트 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def get_target_price(ticker):
    """변동성 돌파 전략으로 매수 목표가 조회
    - K값을 변동성에 따라 동적으로 조정
    - 이동평균선을 활용하여 추세 반영
    - 거래량 가중치 적용
    """
    # 최근 20개의 4시간봉 데이터 조회
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=20)
    
    # 변동성 계산 (ATR 활용)
    df['TR'] = numpy.maximum(
        df['high'] - df['low'],
        numpy.abs(df['high'] - df['close'].shift(1)),
        numpy.abs(df['low'] - df['close'].shift(1))
    )
    atr = df['TR'].mean()
    
    # 거래량 가중치 계산
    volume_ma = df['volume'].mean()
    volume_weight = df.iloc[-1]['volume'] / volume_ma
    
    # K값을 변동성에 따라 동적 조정 (0.3~0.7 범위)
    k = max(0.3, min(0.7, (atr / df.iloc[-1]['close']) * 5))
    
    # 20기간 이동평균선
    ma20 = df['close'].mean()
    
    # 기준가격 설정
    last_close = df.iloc[-1]['close']
    price_range = df.iloc[-1]['high'] - df.iloc[-1]['low']
    
    # 추세와 거래량을 반영한 목표가격 계산
    target_price = last_close + (price_range * k * volume_weight)
    
    # 이동평균선 위에 있을 때만 매수 신호
    if last_close > ma20:
        return target_price
    else:
        return float('inf')  # 매수 신호 없음

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
    return 0

def main():
    """메인 함수"""
    print("자동매매 시작")
    ticker = "KRW-BTC"
    
    # 거래 기록을 위한 로그 파일 설정
    logging.basicConfig(filename='trading.log', level=logging.INFO)
    
    while True:
        try:
            now = time.localtime()
            current_price = get_current_price(ticker)
            
            # 매수 로직 - 24시간 운영으로 변경
            target_price = get_target_price(ticker)
            krw = get_balance("KRW")
            
            # 투자금액 제한 설정 (전체 자산의 5%로 축소)
            max_investment = krw * 0.05  # 더 잦은 매매를 고려해 비중 축소
            
            if target_price < current_price and krw > 5000:
                invest_amount = min(krw * 0.9995, max_investment)
                upbit.buy_market_order(ticker, invest_amount)
                logging.info(f"매수: {ticker} - 가격: {current_price}, 투자금액: {invest_amount}")
            
            # 매도 로직 개선
            else:
                btc = get_balance("BTC")
                if btc > 0.00008:
                    avg_buy_price = upbit.get_avg_buy_price(ticker)
                    profit_rate = (current_price - avg_buy_price) / avg_buy_price * 100
                    
                    # 손절/익절 조건 개선
                    if profit_rate >= 5:  # 5% 이상 수익 시 익절
                        sell_amount = btc * 0.5  # 보유량의 50%만 매도
                        upbit.sell_market_order(ticker, sell_amount)
                        logging.info(f"익절 매도: {ticker} - 수익률: {profit_rate:.2f}%")
                    elif profit_rate <= -3:  # 3% 이상 손실 시 부분 손절
                        sell_amount = btc * 0.5  # 보유량의 50%만 매도
                        upbit.sell_market_order(ticker, sell_amount)
                        logging.info(f"부분 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%")
                    elif profit_rate <= -5:  # 5% 이상 손실 시 전량 손절
                        upbit.sell_market_order(ticker, btc)
                        logging.info(f"전량 손절 매도: {ticker} - 수익률: {profit_rate:.2f}%")
            
            time.sleep(600)  # 10분마다 체크 (너무 자주 체크할 필요 없음)
            
        except Exception as e:
            logging.error(f"에러 발생: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main() 
