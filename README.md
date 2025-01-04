# Upbit Auto Trading Bot

업비트 자동매매 봇입니다. 변동성 돌파 전략과 하이킨 아시 전략을 결합한 알고리즘 트레이딩 시스템입니다.

## 주요 기능
- 멀티 코인 동시 트레이딩 지원
- 실시간 시장 모니터링 및 자동 주문 실행
- 다양한 트레이딩 전략 구현
  - 변동성 돌파 전략 (Volatility Breakout)
  - 하이킨 아시 지표 기반 전략 (Heikin-Ashi)
  - 복합 전략 (Combined Strategy)
- YAML 기반의 유연한 설정 시스템
- 상세한 로깅 및 성과 분석 기능
- 리스크 관리 시스템 내장

## 시스템 요구사항
- Python 3.9+
- pip 패키지 관리자
- Upbit API 액세스 키 ([발급 가이드](https://upbit.com/service_center/open_api_guide))

## 설치 가이드

### 1. 저장소 클론
```bash
git clone https://github.com/sendminder/coinbot.git
cd coinbot
``` 

### 2. 환경 설정
```bash
# 설치 스크립트 실행
chmod +x setup.sh
./setup.sh

# 또는 수동으로 의존성 설치
pip install -r requirements.txt
```

### 3. 설정 파일 구성

1. `.env` 파일 생성
```plaintext
UPBIT_ACCESS_KEY=your_access_key_here
UPBIT_SECRET_KEY=your_secret_key_here
```

2. `src/config/config.yaml` 설정
```yaml
trade_settings:
  max_daily_trades: 20          # 일일 최대 거래 횟수
  trade_interval: 60            # 거래 주기 (초)
  min_krw_balance: 5000        # 최소 보유 원화
  min_profit_krw: 50000        # 최소 수익 목표액
  min_loss_krw: 50000          # 최대 손실 허용액

coins:
  BTC:
    ticker: KRW-BTC
    min_unit: 0.00008          # 최소 거래 단위
    take_profit: 1.5           # 익절 비율 (%)
    stop_loss: -1.0            # 손절 비율 (%)
```

## 실행 방법

### 기본 실행
```bash
python src/main.py
```

### 백그라운드 실행 (Linux/Mac)
```bash
nohup python src/main.py > trading.log 2>&1 &
```

## 모니터링 및 로그 확인
- 거래 로그: `logs/trading.log`

## 안전 수칙
- 실제 투자 전 반드시 테스트넷이나 소액으로 충분한 테스트를 진행하세요.
- API 키는 절대 외부에 노출되지 않도록 주의하세요.
- 거래소의 API 사용량 제한을 확인하고 준수하세요.
- 정기적으로 로그를 확인하여 비정상적인 거래가 없는지 모니터링하세요.

## 면책 조항
이 프로그램은 투자의 결과를 보장하지 않습니다. 모든 투자 결정과 그에 따른 결과는 사용자의 책임입니다.

## 기여하기
버그 리포트, 기능 제안, PR은 언제나 환영합니다.

## 라이선스
MIT License