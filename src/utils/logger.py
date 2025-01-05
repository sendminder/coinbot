import logging
from typing import Optional

def setup_logger(filename: str = 'logs/trading.log') -> None:
    """
    로깅 설정 초기화
    :param filename: 로그 파일 이름
    """
    logging.basicConfig(
        filename=filename,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    로거 인스턴스 반환
    :param name: 로거 이름
    :return: 로거 인스턴스
    """
    return logging.getLogger(name)
