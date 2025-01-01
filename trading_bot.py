import os
import time
import pyupbit
from dotenv import load_dotenv
import logging

# .env 파일에서 환경변수 로드
load_dotenv()

# 업비트 접근 키
access_key = os.getenv('UPBIT_ACCESS_KEY')
secret_key = os.getenv('UPBIT_SECRET_KEY')

# 업비트 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def get_target_price(ticker):
    """3시간 기준 변동성 돌파 전략"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)  # 4시간봉 사용 (240분)
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
                    elif profit_rate <= -3:  # 3% 이상 손실 시 손절
                        upbit.sell_market_order(ticker, btc)
                        logging.info(f"손절 매도: {ticker} - 수익률: {profit_rate:.2f}%")
            
            time.sleep(180)  # 3분마다 체크 (너무 자주 체크할 필요 없음)
            
        except Exception as e:
            logging.error(f"에러 발생: {e}")
            time.sleep(180)

if __name__ == "__main__":
    main() 