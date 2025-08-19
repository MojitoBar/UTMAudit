"""
UTM 생성기 테스트
"""
import pytest
from src.utm.generator import UTMGenerator, UTMParams


def test_utm_params_creation():
    """UTM 파라미터 생성 테스트"""
    utm = UTMParams(
        source="google",
        medium="cpc",
        campaign="test_campaign",
        term="test_term",
        content="test_content"
    )
    
    assert utm.source == "google"
    assert utm.medium == "cpc"
    assert utm.campaign == "test_campaign"
    assert utm.term == "test_term"
    assert utm.content == "test_content"


def test_utm_generator_random():
    """랜덤 UTM 생성 테스트"""
    generator = UTMGenerator()
    utm = generator.generate_random_utm()
    
    assert isinstance(utm, UTMParams)
    assert utm.source in generator.sources
    assert utm.medium in generator.mediums
    assert utm.campaign in generator.campaigns


def test_utm_generator_test_scenarios():
    """테스트 시나리오 생성 테스트"""
    generator = UTMGenerator()
    scenarios = generator.generate_test_scenarios()
    
    assert len(scenarios) > 0
    assert all(isinstance(s, UTMParams) for s in scenarios)


def test_build_utm_url():
    """UTM URL 생성 테스트"""
    generator = UTMGenerator()
    utm = UTMParams(
        source="google",
        medium="cpc",
        campaign="test_campaign"
    )
    
    base_url = "https://example.com"
    utm_url = generator.build_utm_url(base_url, utm)
    
    assert "utm_source=google" in utm_url
    assert "utm_medium=cpc" in utm_url
    assert "utm_campaign=test_campaign" in utm_url
    assert utm_url.startswith("https://example.com")


def test_parse_utm_from_url():
    """URL에서 UTM 파라미터 추출 테스트"""
    generator = UTMGenerator()
    test_url = "https://example.com?utm_source=google&utm_medium=cpc&utm_campaign=test"
    
    utm = generator.parse_utm_from_url(test_url)
    
    assert utm is not None
    assert utm.source == "google"
    assert utm.medium == "cpc"
    assert utm.campaign == "test"


def test_parse_utm_from_url_no_utm():
    """UTM 파라미터가 없는 URL 테스트"""
    generator = UTMGenerator()
    test_url = "https://example.com"
    
    utm = generator.parse_utm_from_url(test_url)
    
    assert utm is None
