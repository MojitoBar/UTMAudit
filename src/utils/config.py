"""
설정 관리 모듈
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Mixpanel 설정
    mixpanel_service_account: str = Field("your_service_account_here", env="MIXPANEL_SERVICE_ACCOUNT")
    mixpanel_service_password: str = Field("your_service_password_here", env="MIXPANEL_SERVICE_PASSWORD")
    mixpanel_project_id: int = Field(0, env="MIXPANEL_PROJECT_ID")
    
    # 웹사이트 설정
    base_url: str = Field("https://example.com", env="BASE_URL")
    
    # 브라우저 설정
    headless: bool = Field(True, env="HEADLESS")
    browser_type: str = Field("chromium", env="BROWSER_TYPE")
    
    # 감사 설정
    test_timeout: int = Field(30, env="TEST_TIMEOUT")
    max_retries: int = Field(3, env="MAX_RETRIES")
    
    # 로깅 설정
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()
