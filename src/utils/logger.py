"""
로깅 설정 모듈
"""
import sys
from loguru import logger
from .config import settings


def setup_logger():
    """로거 설정"""
    # 기존 핸들러 제거
    logger.remove()
    
    # 콘솔 출력 설정
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 파일 출력 설정 (디버그 모드에서만)
    if settings.debug:
        logger.add(
            "logs/utm_audit.log",
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    return logger


# 로거 초기화
setup_logger()
