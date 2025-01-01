import os
import time
import pyupbit
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# 업비트 접근 키
access_key = os.getenv('UPBIT_ACCESS_KEY')
secret_key = os.getenv('UPBIT_SECRET_KEY')

# 업비트 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def get_target_price(ticker):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * 0.5
    return target_price

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
    
    while True:
        try:
            now = time.localtime()
            current_price = get_current_price(ticker)
            
            # 매수 로직 개선
            if 9 <= now.tm_hour < 20:  # 거래시간 확대
                target_price = get_target_price(ticker)
                krw = get_balance("KRW")
                
                if target_price < current_price and krw > 5000:
                    upbit.buy_market_order(ticker, krw * 0.9995)
                    print(f"매수 주문: {ticker} - 가격: {current_price}")
            
            # 매도 로직 개선
            else:
                btc = get_balance("BTC")
                if btc > 0.00008:
                    # 수익률 계산 추가
                    avg_buy_price = upbit.get_avg_buy_price(ticker)
                    profit_rate = (current_price - avg_buy_price) / avg_buy_price * 100
                    
                    # 수익률에 따른 매도 조건
                    if profit_rate >= 3 or profit_rate <= -2:
                        upbit.sell_market_order(ticker, btc)
                        print(f"매도 주문: {ticker} - 수익률: {profit_rate:.2f}%")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"에러 발생: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main() 