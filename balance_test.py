import os
import pyupbit
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# 업비트 접근 키
access_key = os.getenv('UPBIT_ACCESS_KEY')
secret_key = os.getenv('UPBIT_SECRET_KEY')

# 업비트 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def print_balances():
    """전체 보유 자산 출력"""
    print("=== 나의 보유 자산 ===")
    balances = upbit.get_balances()

    for b in balances:
        currency = b['currency']          # 화폐 종류
        balance = float(b['balance'])     # 보유 수량
        avg_buy_price = float(b['avg_buy_price'])  # 매수 평균가

        if currency == 'KRW':
            print(f"원화: {balance:,.0f}원")
        else:
            current_price = pyupbit.get_current_price(f"KRW-{currency}")
            if current_price is not None:
                evaluation = balance * current_price
                profit_loss = evaluation - (avg_buy_price * balance)
                print(f"{currency}: {balance:.8f} 개")
                print(f"평가금액: {evaluation:,.0f}원")
                print(f"손익: {profit_loss:,.0f}원")
                print("------------------------")

if __name__ == "__main__":
    print_balances()
