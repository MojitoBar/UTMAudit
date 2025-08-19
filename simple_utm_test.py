"""
간단한 UTM Last Touch API 패킷 확인 도구
"""
import asyncio
import json
import urllib.parse
from loguru import logger

from src.browser.playwright_client import PlaywrightClient
from src.utm.generator import UTMGenerator
from src.utils.config import settings


class SimpleUTMTest:
    """간단한 UTM Last Touch 확인"""
    
    def __init__(self):
        self.browser_client = PlaywrightClient()
        self.utm_generator = UTMGenerator()
    
    async def test_last_touch(self):
        """Last Touch 확인 테스트"""
        logger.info("🔍 Last Touch API 패킷 확인 시작")
        
        try:
            async with self.browser_client as browser:
                await self._test_two_visits(browser)
                
        except Exception as e:
            logger.error(f"테스트 중 오류: {e}")
    
    async def _test_two_visits(self, browser):
        """두 번 방문해서 Last Touch 확인"""
        
        # 첫 번째 방문
        logger.info("\n" + "="*60)
        logger.info("🌐 첫 번째 방문: google/cpc/brand_search")
        logger.info("="*60)
        
        from src.utm.generator import UTMParams
        utm1 = UTMParams(source="google", medium="cpc", campaign="brand_search")
        url1 = self.utm_generator.build_utm_url(settings.base_url, utm1)
        
        logger.info(f"방문 URL: {url1}")
        
        if await browser.navigate_to_url(url1):
            await asyncio.sleep(5)
            
            requests1 = browser.get_mixpanel_requests()
            if requests1:
                logger.info(f"📊 첫 번째 방문 - {len(requests1)}개 요청")
                for i, req in enumerate(requests1, 1):
                    logger.info(f"\n🔍 요청 {i}:")
                    if 'post_data' in req and req['post_data']:
                        logger.info(f"POST 데이터: {req['post_data']}")
                        
                        # 디코딩 및 JSON 파싱
                        try:
                            decoded = urllib.parse.unquote(req['post_data'])
                            if 'data=' in decoded:
                                data_part = decoded.split('data=')[1]
                                json_data = json.loads(data_part)
                                
                                logger.info("📋 파싱된 이벤트:")
                                for event in json_data:
                                    props = event.get('properties', {})
                                    logger.info(f"  이벤트: {event.get('event')}")
                                    
                                    # Last Touch 확인
                                    last_touch_props = {k: v for k, v in props.items() 
                                                      if 'last' in k.lower() and 'touch' in k.lower()}
                                    if last_touch_props:
                                        logger.info(f"  ✅ Last Touch 발견: {last_touch_props}")
                                    else:
                                        logger.info(f"  ❌ Last Touch 없음")
                                    
                                    # UTM 확인
                                    utm_props = {k: v for k, v in props.items() if k.startswith('utm_')}
                                    logger.info(f"  📈 UTM: {utm_props}")
                                    
                        except Exception as e:
                            logger.error(f"파싱 오류: {e}")
            
            await browser.clear_mixpanel_requests()
            await asyncio.sleep(3)
        
        # 두 번째 방문
        logger.info("\n" + "="*60)
        logger.info("🌐 두 번째 방문: facebook/social/awareness")
        logger.info("="*60)
        
        utm2 = UTMParams(source="facebook", medium="social", campaign="awareness")
        url2 = self.utm_generator.build_utm_url(settings.base_url, utm2)
        
        logger.info(f"방문 URL: {url2}")
        
        if await browser.navigate_to_url(url2):
            await asyncio.sleep(5)
            
            requests2 = browser.get_mixpanel_requests()
            if requests2:
                logger.info(f"📊 두 번째 방문 - {len(requests2)}개 요청")
                for i, req in enumerate(requests2, 1):
                    logger.info(f"\n🔍 요청 {i}:")
                    if 'post_data' in req and req['post_data']:
                        logger.info(f"POST 데이터: {req['post_data']}")
                        
                        # 디코딩 및 JSON 파싱
                        try:
                            decoded = urllib.parse.unquote(req['post_data'])
                            if 'data=' in decoded:
                                data_part = decoded.split('data=')[1]
                                json_data = json.loads(data_part)
                                
                                logger.info("📋 파싱된 이벤트:")
                                for event in json_data:
                                    props = event.get('properties', {})
                                    logger.info(f"  이벤트: {event.get('event')}")
                                    
                                    # Last Touch 확인
                                    last_touch_props = {k: v for k, v in props.items() 
                                                      if 'last' in k.lower() and 'touch' in k.lower()}
                                    if last_touch_props:
                                        logger.info(f"  ✅ Last Touch 발견: {last_touch_props}")
                                    else:
                                        logger.info(f"  ❌ Last Touch 없음")
                                    
                                    # UTM 확인
                                    utm_props = {k: v for k, v in props.items() if k.startswith('utm_')}
                                    logger.info(f"  📈 UTM: {utm_props}")
                                    
                                    # 모든 속성 출력 (Last Touch 찾기용)
                                    logger.info("  📋 모든 속성:")
                                    for key, value in props.items():
                                        logger.info(f"    • {key}: {value}")
                                    
                        except Exception as e:
                            logger.error(f"파싱 오류: {e}")
            
            await browser.clear_mixpanel_requests()


async def main():
    """메인 함수"""
    tester = SimpleUTMTest()
    await tester.test_last_touch()


if __name__ == "__main__":
    asyncio.run(main())
