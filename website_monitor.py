"""
웹사이트 자체 Mixpanel 호출 감지 도구
"""
import asyncio
import argparse
from datetime import datetime
from loguru import logger

from src.browser.playwright_client import PlaywrightClient
from src.utils.config import settings
from src.utils.visualizer import UTMVisualizer


class WebsiteMonitor:
    """웹사이트 자체 Mixpanel 호출 감지"""
    
    def __init__(self):
        self.browser_client = PlaywrightClient()
        self.visualizer = UTMVisualizer()
    
    async def monitor_website(self):
        """웹사이트 자체 Mixpanel 호출 감지"""
        logger.info("🔍 웹사이트 자체 Mixpanel 호출 감지 시작")
        
        try:
            async with self.browser_client as browser:
                await self._monitor_website_events(browser)
                
        except Exception as e:
            logger.error(f"모니터링 중 오류: {e}")
    
    async def _monitor_website_events(self, browser):
        """웹사이트 이벤트 모니터링"""
        logger.info("📊 웹사이트 자체 Mixpanel 호출 감지")
        
        # 웹사이트 방문 (UTM 파라미터 없이)
        logger.info(f"웹사이트 방문: {settings.base_url}")
        
        # 페이지 방문
        if await browser.navigate_to_url(settings.base_url):
            # 이벤트 대기
            logger.info("⏳ 웹사이트 이벤트 대기 중... (10초)")
            await asyncio.sleep(10)
            
            # 수집된 요청 분석
            mixpanel_requests = browser.get_mixpanel_requests()
            if mixpanel_requests:
                logger.info(f"📊 {len(mixpanel_requests)}개의 Mixpanel 요청 분석 중...")
                
                for i, request in enumerate(mixpanel_requests, 1):
                    logger.info(f"🔍 요청 {i} 분석:")
                    
                    # 요청 데이터에서 이벤트 정보 추출
                    if 'parsed_events' in request:
                        for event in request['parsed_events']:
                            event_name = event.get('event', 'unknown')
                            properties = event.get('properties', {})
                            
                            logger.info(f"  🎯 이벤트: {event_name}")
                            
                            # UTM 속성 확인
                            utm_props = {k: v for k, v in properties.items() if k.startswith('utm_') and not k.endswith('[last touch]')}
                            if utm_props:
                                logger.info(f"  📈 현재 UTM: {utm_props}")
                            else:
                                logger.info("  📈 현재 UTM: 없음 (직접 방문)")
                            
                            # Last Touch 속성 확인
                            last_touch_props = {k: v for k, v in properties.items() if k.endswith('[last touch]')}
                            if last_touch_props:
                                logger.info(f"  👇 Last Touch: {last_touch_props}")
                            else:
                                logger.info("  👇 Last Touch: 없음 (첫 방문)")
                            
                            # First Touch 확인
                            first_touch_props = {k: v for k, v in properties.items() if k.startswith('$first_touch') or k.startswith('first_touch')}
                            if first_touch_props:
                                logger.info(f"  👆 First Touch: {first_touch_props}")
                            elif not last_touch_props:
                                logger.info("  👆 First Touch: 없음 (첫 방문)")
                            else:
                                logger.info("  👆 First Touch: 이전 방문에서 설정됨")
                            
                            # 기타 주요 속성들
                            other_props = {k: v for k, v in properties.items() 
                                         if not k.startswith('utm_') and not k.endswith('[last touch]') 
                                         and not k.startswith('$first_touch') and not k.startswith('first_touch')
                                         and k not in ['$os', '$browser', '$current_url', '$browser_version', 
                                                      '$screen_height', '$screen_width', 'mp_lib', '$lib_version',
                                                      '$insert_id', 'time', 'mp_loader', 'distinct_id', '$device_id',
                                                      '$initial_referrer', '$initial_referring_domain', 'page_name',
                                                      'business_type', 'content_title', 'current_page_title', 'token',
                                                      'mp_sent_by_lib_version']}
                            
                            if other_props:
                                logger.info(f"  📋 기타 속성: {other_props}")
                            
                            # 시각화를 위한 결과 저장
                            current_utm = {
                                'source': utm_props.get('utm_source', 'N/A'),
                                'medium': utm_props.get('utm_medium', 'N/A'),
                                'campaign': utm_props.get('utm_campaign', 'N/A')
                            }
                            
                            # 테스트 파라미터 (웹사이트 자체 호출이므로 실제 UTM과 비교 불가)
                            test_params = {
                                'source': '웹사이트 자체',
                                'medium': '직접 방문',
                                'campaign': '테스트',
                                'term': None,
                                'content': None
                            }
                            
                            success = True  # 웹사이트가 이벤트를 전송했으면 성공
                            
                            self.visualizer.add_result(
                                step=i,
                                utm_params=test_params,
                                current_utm=current_utm,
                                first_touch=first_touch_props if first_touch_props else None,
                                last_touch=last_touch_props,
                                success=success
                            )
                    else:
                        logger.warning("  ❌ 파싱된 이벤트가 없습니다")
            else:
                logger.warning("❌ Mixpanel 요청이 감지되지 않았습니다")
            
            # 요청 초기화
            await browser.clear_mixpanel_requests()
        
        # 시각화 리포트 생성
        self.visualizer.generate_report()


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="웹사이트 자체 Mixpanel 호출 감지 도구")
    parser.add_argument("--url", help="감지할 웹사이트 URL (기본값: .env의 BASE_URL)")
    
    args = parser.parse_args()
    
    # URL 설정
    if args.url:
        settings.base_url = args.url
    
    monitor = WebsiteMonitor()
    await monitor.monitor_website()


if __name__ == "__main__":
    asyncio.run(main())
