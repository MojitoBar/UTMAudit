"""
UTM 파라미터 생성 모듈
"""
import random
from typing import Dict, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs, urlunparse
from pydantic import BaseModel
from loguru import logger


class UTMParams(BaseModel):
    """UTM 파라미터 모델"""
    source: str
    medium: str
    campaign: str
    term: Optional[str] = None
    content: Optional[str] = None


class UTMGenerator:
    """UTM 파라미터 생성기"""
    
    def __init__(self):
        # 일반적인 UTM 소스들
        self.sources = [
            "google", "facebook", "instagram", "twitter", "linkedin", 
            "youtube", "tiktok", "email", "direct", "organic", "referral",
            "naver", "kakao", "daum", "cafe24", "blog"
        ]
        
        # 일반적인 UTM 미디움들
        self.mediums = [
            "cpc", "social", "email", "banner", "affiliate", "referral",
            "organic", "paid", "display", "video", "native"
        ]
        
        # 일반적인 UTM 캠페인들
        self.campaigns = [
            "summer_sale", "black_friday", "christmas", "new_year",
            "product_launch", "brand_awareness", "lead_generation",
            "retargeting", "seasonal", "promotional"
        ]
        
        # UTM 텀들 (검색 키워드)
        self.terms = [
            "마케팅", "디지털마케팅", "온라인마케팅", "브랜딩", "SEO",
            "광고", "소셜미디어", "이메일마케팅", "콘텐츠마케팅"
        ]
        
        # UTM 콘텐츠들
        self.contents = [
            "banner_top", "banner_sidebar", "email_header", "social_post",
            "video_ad", "text_ad", "image_ad", "carousel_ad"
        ]
    
    def generate_random_utm(self) -> UTMParams:
        """랜덤 UTM 파라미터 생성"""
        return UTMParams(
            source=random.choice(self.sources),
            medium=random.choice(self.mediums),
            campaign=random.choice(self.campaigns),
            term=random.choice(self.terms) if random.random() > 0.5 else None,
            content=random.choice(self.contents) if random.random() > 0.5 else None
        )
    
    def generate_test_scenarios(self) -> List[UTMParams]:
        """테스트용 UTM 시나리오 생성"""
        scenarios = []
        
        # First Touch 시나리오
        scenarios.extend([
            UTMParams(source="google", medium="cpc", campaign="brand_search"),
            UTMParams(source="facebook", medium="social", campaign="awareness"),
        ])
        
        # Last Touch 시나리오
        scenarios.extend([
            UTMParams(source="google", medium="cpc", campaign="retargeting"),
            UTMParams(source="facebook", medium="social", campaign="conversion"),
        ])
        
        return scenarios
    
    def build_utm_url(self, base_url: str, utm_params: UTMParams) -> str:
        """UTM 파라미터가 포함된 URL 생성"""
        parsed_url = urlparse(base_url)
        query_params = parse_qs(parsed_url.query)
        
        # UTM 파라미터 추가
        utm_dict = utm_params.dict(exclude_none=True)
        for key, value in utm_dict.items():
            query_params[f"utm_{key}"] = [value]
        
        # URL 재구성
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        logger.debug(f"생성된 UTM URL: {new_url}")
        return new_url
    
    def parse_utm_from_url(self, url: str) -> Optional[UTMParams]:
        """URL에서 UTM 파라미터 추출"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            utm_data = {}
            for key, values in query_params.items():
                if key.startswith("utm_"):
                    param_name = key[4:]  # "utm_" 제거
                    utm_data[param_name] = values[0] if values else None
            
            if utm_data:
                return UTMParams(**utm_data)
            return None
            
        except Exception as e:
            logger.error(f"URL에서 UTM 파라미터 추출 실패: {e}")
            return None
