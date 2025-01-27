from src.strategies.base import TradingStrategy
from src.trading.bot import TradingBot

def main():
    """프로그램 시작점"""
    strategy = TradingStrategy.HEIKIN_ASHI
    bot = TradingBot(strategy)
    bot.run()

if __name__ == "__main__":
    main()
