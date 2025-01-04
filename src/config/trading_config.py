from dataclasses import dataclass
from typing import Dict, Optional
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class CoinConfig:
    ticker: str
    min_unit: float
    take_profit: float
    profit_sell: float
    stop_loss: float
    partial_stop: float
    partial_sell: float

@dataclass
class APIConfig:
    access_key: str
    secret_key: str

@dataclass
class TradeSettings:
    max_daily_trades: int
    trade_interval: int
    min_krw_balance: int
    min_profit_krw: int
    min_loss_krw: int

class TradingConfig:
    def __init__(self):
        self._load_environment()
        self.api_keys = self._load_api_keys()
        self._load_yaml_config()
        
    def _load_environment(self) -> None:
        """환경 변수 로드"""
        load_dotenv()

    def _load_api_keys(self) -> APIConfig:
        """API 키 설정 로드"""
        return APIConfig(
            access_key=os.getenv('UPBIT_ACCESS_KEY', ''),
            secret_key=os.getenv('UPBIT_SECRET_KEY', '')
        )

    def _load_yaml_config(self) -> None:
        """YAML 설정 파일 로드"""
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # 거래 설정 로드
        self.trade_settings = TradeSettings(**config['trade_settings'])
        
        # 코인 설정 로드
        self.coin_settings = {}
        for coin, settings in config['coins'].items():
            self.coin_settings[coin] = CoinConfig(**settings)

    def get_coin_config(self, coin: str) -> Optional[CoinConfig]:
        """특정 코인의 설정 반환"""
        return self.coin_settings.get(coin)

    def get_ticker_list(self) -> list[str]:
        """모든 거래 대상 티커 리스트 반환"""
        return [config.ticker for config in self.coin_settings.values()]

    def is_valid(self) -> bool:
        """설정 유효성 검사"""
        if not self.api_keys.access_key or not self.api_keys.secret_key:
            return False
        if not self.coin_settings:
            return False
        return True 