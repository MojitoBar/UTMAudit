"""
UTM 파라미터로 웹사이트 방문 후 API 패킷에서 Last Touch 수집 방식 분석 도구
"""
import asyncio
import argparse
import json
import urllib.parse
from datetime import datetime
from loguru import logger

from src.browser.playwright_client import PlaywrightClient
from src.utm.generator import UTMGenerator
from src.utils.config import settings
from src.utils.visualizer import UTMVisualizer

# 로그 레벨을 DEBUG로 설정
logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}")


class UTMWebsiteTest:
    """UTM 파라미터로 웹사이트 방문 후 API 패킷에서 Last Touch 수집 방식 분석"""
    
    def __init__(self):
        self.browser_client = PlaywrightClient()
        self.utm_generator = UTMGenerator()
        self.visualizer = UTMVisualizer()
    
    async def test_utm_website(self):
        """UTM 파라미터로 웹사이트 방문 테스트"""
        logger.info("🔍 API 패킷에서 Last Touch 수집 방식 분석 시작")
        
        try:
            async with self.browser_client as browser:
                await self._test_utm_scenarios(browser)
                
        except Exception as e:
            logger.error(f"테스트 중 오류: {e}")
    
    async def _test_utm_scenarios(self, browser):
        """UTM 시나리오 테스트"""
        logger.info("🎯 API 패킷 분석을 위한 UTM 시나리오 테스트")
        
        # 여러 UTM 시나리오 생성
        scenarios = [
            # 첫 번째 방문 (First Touch 테스트)
            {"source": "google", "medium": "cpc", "campaign": "brand_search", "description": "첫 번째 방문 - Google CPC"},
            
            # 두 번째 방문 (Last Touch 테스트) 
            {"source": "facebook", "medium": "social", "campaign": "awareness", "description": "두 번째 방문 - Facebook Social"},
            
            # 세 번째 방문 (Last Touch 업데이트)
            {"source": "naver", "medium": "cpc", "campaign": "retargeting", "description": "세 번째 방문 - Naver CPC"},
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🔍 시나리오 {i}: {scenario['description']}")
            logger.info(f"{'='*80}")
            
            # UTM 파라미터 생성
            from src.utm.generator import UTMParams
            utm_params = UTMParams(
                source=scenario["source"],
                medium=scenario["medium"], 
                campaign=scenario["campaign"]
            )
            
            # UTM URL 생성
            utm_url = self.utm_generator.build_utm_url(settings.base_url, utm_params)
            logger.info(f"🌐 방문할 URL: {utm_url}")
            
            # 페이지 방문
            if await browser.navigate_to_url(utm_url):
                # 이벤트 대기
                logger.info("⏳ 웹사이트 이벤트 대기 중... (5초)")
                await asyncio.sleep(5)
                
                # 수집된 요청 분석
                mixpanel_requests = browser.get_mixpanel_requests()
                if mixpanel_requests:
                    logger.info(f"📊 {len(mixpanel_requests)}개의 Mixpanel API 패킷 분석 중...")
                    
                    for j, request in enumerate(mixpanel_requests, 1):
                        logger.info(f"\n🔍 API 패킷 {j} 상세 분석:")
                        logger.info(f"{'─'*60}")
                        
                        # 1. 원시 요청 정보
                        logger.info("📡 원시 요청 정보:")
                        logger.info(f"   URL: {request.get('url', 'N/A')}")
                        logger.info(f"   Method: {request.get('method', 'N/A')}")
                        
                        # 2. 원시 POST 데이터 (전체 출력)
                        if 'post_data' in request and request['post_data']:
                            logger.info("\n📦 원시 POST 데이터 (전체):")
                            logger.info(f"   {request['post_data']}")
                            
                            # URL 디코딩 시도
                            try:
                                decoded_data = urllib.parse.unquote(request['post_data'])
                                logger.info(f"\n🔓 URL 디코딩된 데이터 (전체):")
                                logger.info(f"   {decoded_data}")
                                
                                # JSON 파싱 시도
                                if 'data=' in decoded_data:
                                    data_part = decoded_data.split('data=')[1]
                                    try:
                                        json_data = json.loads(data_part)
                                        logger.info(f"\n🎯 JSON 파싱된 데이터 (전체):")
                                        logger.info(f"   {json.dumps(json_data, indent=3, ensure_ascii=False)}")
                                    except json.JSONDecodeError as e:
                                        logger.warning(f"   JSON 파싱 실패: {e}")
                                        
                            except Exception as e:
                                logger.warning(f"   URL 디코딩 실패: {e}")
                        
                        # 3. 파싱된 이벤트 분석
                        if 'parsed_events' in request:
                            logger.info(f"\n🎯 파싱된 이벤트 분석 ({len(request['parsed_events'])}개):")
                            
                            for k, event in enumerate(request['parsed_events'], 1):
                                logger.info(f"\n   📋 이벤트 {k}:")
                                logger.info(f"   └─ 이벤트명: {event.get('event', 'unknown')}")
                                
                                properties = event.get('properties', {})
                                
                                # 4. Last Touch 속성 상세 분석
                                logger.info(f"\n   🔍 Last Touch 속성 분석:")
                                
                                # Last Touch 관련 모든 속성 찾기 (더 넓은 범위)
                                last_touch_keys = []
                                for key in properties.keys():
                                    key_lower = key.lower()
                                    if ('last' in key_lower and 'touch' in key_lower) or \
                                       key.endswith('[last touch]') or \
                                       key.startswith('last_touch') or \
                                       key.startswith('$last_touch'):
                                        last_touch_keys.append(key)
                                
                                if last_touch_keys:
                                    logger.info(f"   └─ Last Touch 관련 키들: {last_touch_keys}")
                                    
                                    for key in last_touch_keys:
                                        value = properties[key]
                                        logger.info(f"      • {key}: {value}")
                                else:
                                    logger.info(f"   └─ Last Touch 관련 속성 없음")
                                    
                                    # 모든 속성에서 'last' 또는 'touch'가 포함된 것 찾기
                                    all_last_touch_candidates = [k for k in properties.keys() 
                                                               if 'last' in k.lower() or 'touch' in k.lower()]
                                    if all_last_touch_candidates:
                                        logger.info(f"   └─ 'last' 또는 'touch'가 포함된 속성들: {all_last_touch_candidates}")
                                        for key in all_last_touch_candidates:
                                            value = properties[key]
                                            logger.info(f"      • {key}: {value}")
                                
                                # 5. UTM 속성 분석
                                logger.info(f"\n   📈 UTM 속성 분석:")
                                utm_keys = [k for k in properties.keys() if k.startswith('utm_')]
                                if utm_keys:
                                    logger.info(f"   └─ UTM 키들: {utm_keys}")
                                    
                                    for key in utm_keys:
                                        value = properties[key]
                                        logger.info(f"      • {key}: {value}")
                                else:
                                    logger.info(f"   └─ UTM 속성 없음")
                                
                                # 6. First Touch 속성 분석
                                logger.info(f"\n   👆 First Touch 속성 분석:")
                                first_touch_keys = []
                                for key in properties.keys():
                                    key_lower = key.lower()
                                    if ('first' in key_lower and 'touch' in key_lower) or \
                                       key.startswith('$first_touch') or \
                                       key.startswith('first_touch'):
                                        first_touch_keys.append(key)
                                
                                if first_touch_keys:
                                    logger.info(f"   └─ First Touch 키들: {first_touch_keys}")
                                    
                                    for key in first_touch_keys:
                                        value = properties[key]
                                        logger.info(f"      • {key}: {value}")
                                else:
                                    logger.info(f"   └─ First Touch 속성 없음")
                                
                                # 7. 전체 속성 요약
                                logger.info(f"\n   📊 전체 속성 요약:")
                                logger.info(f"   └─ 총 속성 수: {len(properties)}")
                                
                                # 모든 속성 출력 (디버깅용)
                                logger.info(f"\n   📋 모든 속성 (디버깅용):")
                                for key, value in properties.items():
                                    logger.info(f"      • {key}: {value}")
                                
                                # 8. 분석 결과
                                logger.info(f"\n   🎯 분석 결과:")
                                
                                # 현재 UTM 확인
                                current_utm = {
                                    'source': properties.get('utm_source', 'N/A'),
                                    'medium': properties.get('utm_medium', 'N/A'),
                                    'campaign': properties.get('utm_campaign', 'N/A')
                                }
                                
                                # Last Touch 확인
                                last_touch = {}
                                for key in properties.keys():
                                    if key.endswith('[last touch]') or 'last_touch' in key.lower():
                                        last_touch[key] = properties[key]
                                
                                # First Touch 확인
                                first_touch = {}
                                for key in properties.keys():
                                    if key.startswith('$first_touch') or key.startswith('first_touch'):
                                        first_touch[key] = properties[key]
                                
                                logger.info(f"   └─ 예상 UTM: {scenario['source']}/{scenario['medium']}/{scenario['campaign']}")
                                logger.info(f"   └─ 실제 UTM: {current_utm['source']}/{current_utm['medium']}/{current_utm['campaign']}")
                                logger.info(f"   └─ Last Touch: {last_touch if last_touch else '없음'}")
                                logger.info(f"   └─ First Touch: {first_touch if first_touch else '없음'}")
                                
                                # 매칭 여부
                                utm_match = current_utm['source'] == scenario['source']
                                logger.info(f"   └─ UTM 매칭: {'✅' if utm_match else '❌'}")
                                
                                # 시각화를 위한 결과 저장
                                test_params = {
                                    'source': scenario["source"],
                                    'medium': scenario["medium"],
                                    'campaign': scenario["campaign"],
                                    'term': None,
                                    'content': None
                                }
                                
                                self.visualizer.add_result(
                                    step=i,
                                    utm_params=test_params,
                                    current_utm=current_utm,
                                    first_touch=first_touch if first_touch else (current_utm if not last_touch else None),
                                    last_touch=last_touch,
                                    success=utm_match
                                )
                        else:
                            logger.warning("   ❌ 파싱된 이벤트가 없습니다")
                            
                            # 원시 데이터가 있다면 표시
                            if 'post_data' in request and request['post_data']:
                                logger.info("   📦 원시 데이터 분석 시도:")
                                try:
                                    # Mixpanel 데이터 파싱 시도
                                    raw_data = request['post_data']
                                    if 'data=' in raw_data:
                                        data_part = raw_data.split('data=')[1]
                                        decoded_data = urllib.parse.unquote(data_part)
                                        logger.info(f"   └─ 디코딩된 데이터: {decoded_data}")
                                        
                                        # JSON 파싱 시도
                                        try:
                                            json_data = json.loads(decoded_data)
                                            logger.info(f"   └─ JSON 파싱 성공: {json.dumps(json_data, indent=6, ensure_ascii=False)}")
                                        except json.JSONDecodeError:
                                            logger.warning("   └─ JSON 파싱 실패")
                                except Exception as e:
                                    logger.error(f"   └─ 데이터 분석 실패: {e}")
                else:
                    logger.warning("❌ Mixpanel API 패킷이 감지되지 않았습니다")
                
                # 요청 초기화
                await browser.clear_mixpanel_requests()
                
                # 시나리오 간 간격 (쿠키 저장 시간)
                logger.info(f"\n⏳ 다음 시나리오 대기 중... (3초)")
                await asyncio.sleep(3)
        
        # 시각화 리포트 생성
        logger.info(f"\n{'='*80}")
        logger.info("🎯 전체 API 패킷 분석 결과")
        logger.info(f"{'='*80}")
        self.visualizer.generate_report()


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="API 패킷에서 Last Touch 수집 방식 분석 도구")
    parser.add_argument("--url", help="테스트할 웹사이트 URL (기본값: .env의 BASE_URL)")
    
    args = parser.parse_args()
    
    # URL 설정
    if args.url:
        settings.base_url = args.url
    
    tester = UTMWebsiteTest()
    await tester.test_utm_website()


if __name__ == "__main__":
    asyncio.run(main())
