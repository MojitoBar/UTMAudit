"""
UTM Audit Tool - 네트워크 감지 기반 UTM 추적 테스트
"""
import asyncio
import argparse
from datetime import datetime
from loguru import logger

from src.browser.playwright_client import PlaywrightClient
from src.utm.generator import UTMGenerator
from src.browser.utm_tracker import UTMNetworkTracker
from src.utils.config import settings
from src.utils.visualizer import UTMVisualizer


class UTMAuditor:
    """UTM 감사 도구 - 네트워크 감지 기반"""
    
    def __init__(self):
        self.browser_client = PlaywrightClient()
        self.utm_generator = UTMGenerator()
        self.utm_tracker = UTMNetworkTracker()
        self.visualizer = UTMVisualizer()
    
    async def run_audit(self, mode: str = "basic"):
        """UTM 추적 감사 실행"""
        logger.info("🚀 UTM 추적 감사 시작 (네트워크 감지 기반)")
        
        try:
            async with self.browser_client as browser:
                if mode == "sequential":
                    await self._run_sequential_test(browser)
                else:
                    await self._run_basic_test(browser)
                
        except Exception as e:
            logger.error(f"감사 실행 중 오류: {e}")
    
    async def _run_basic_test(self, browser):
        """기본 UTM 테스트"""
        logger.info("📊 기본 UTM 테스트 실행")
        
        # UTM 시나리오 생성
        scenarios = self.utm_generator.generate_test_scenarios()
        
        for i, utm_params in enumerate(scenarios, 1):
            logger.info(f"시나리오 {i}/{len(scenarios)}: {utm_params}")
            
            # UTM URL 생성
            utm_url = self.utm_generator.build_utm_url(settings.base_url, utm_params)
            
            # 페이지 방문
            if await browser.navigate_to_url(utm_url):
                # 이벤트 대기
                await asyncio.sleep(3)
                
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
                                    logger.warning("  ❌ 현재 UTM 속성이 없습니다")
                                
                                # Last Touch 속성 확인
                                last_touch_props = {k: v for k, v in properties.items() if k.endswith('[last touch]')}
                                if last_touch_props:
                                    logger.info(f"  👇 Last Touch: {last_touch_props}")
                                else:
                                    logger.info("  👇 Last Touch: 없음 (첫 방문)")
                                
                                # First Touch 확인 (첫 방문인 경우 현재 UTM이 First Touch)
                                if not last_touch_props:
                                    logger.info(f"  👆 First Touch: {utm_props}")
                                else:
                                    logger.info("  👆 First Touch: 이전 방문에서 설정됨")
                                
                                # 시각화를 위한 결과 저장
                                current_utm = {
                                    'source': utm_props.get('utm_source', 'N/A'),
                                    'medium': utm_props.get('utm_medium', 'N/A'),
                                    'campaign': utm_props.get('utm_campaign', 'N/A')
                                }
                                
                                first_touch = utm_props if not last_touch_props else None
                                success = bool(utm_props)  # UTM 속성이 있으면 성공으로 간주
                                
                                # UTM 파라미터를 딕셔너리로 변환
                                utm_params_dict = {
                                    'source': utm_params.source,
                                    'medium': utm_params.medium,
                                    'campaign': utm_params.campaign,
                                    'term': utm_params.term,
                                    'content': utm_params.content
                                }
                                
                                self.visualizer.add_result(
                                    step=i,
                                    utm_params=utm_params_dict,
                                    current_utm=current_utm,
                                    first_touch=first_touch,
                                    last_touch=last_touch_props,
                                    success=success
                                )
                        else:
                            logger.warning("  ❌ 파싱된 이벤트가 없습니다")
                else:
                    logger.warning("❌ Mixpanel 요청이 감지되지 않았습니다")
                
                # 요청 초기화
                await browser.clear_mixpanel_requests()
                self.utm_tracker.clear_events()
                
                # 시나리오 간 간격
                await asyncio.sleep(2)
        
        # 시각화 리포트 생성
        self.visualizer.generate_report()
    
    async def _run_sequential_test(self, browser):
        """연속 UTM 테스트 (First Touch/Last Touch 검증)"""
        logger.info("🔄 연속 UTM 테스트 실행 (First Touch/Last Touch 검증)")
        
        # 연속 시나리오 생성
        scenarios = [
            {'utm_params': self.utm_generator.generate_random_utm(), 'description': '첫 번째 방문'},
            {'utm_params': self.utm_generator.generate_random_utm(), 'description': '두 번째 방문'},
            {'utm_params': self.utm_generator.generate_random_utm(), 'description': '세 번째 방문'},
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            utm_params = scenario['utm_params']
            logger.info(f"Step {i}: {scenario['description']} - {utm_params}")
            
            # UTM URL 생성
            utm_url = self.utm_generator.build_utm_url(settings.base_url, utm_params)
            
            # 페이지 방문
            if await browser.navigate_to_url(utm_url):
                # 이벤트 대기
                await asyncio.sleep(3)
                
                # 수집된 요청 분석
                mixpanel_requests = browser.get_mixpanel_requests()
                for request in mixpanel_requests:
                    self.utm_tracker.analyze_mixpanel_request(request)
                
                # 요청 초기화
                await browser.clear_mixpanel_requests()
                
                # 시나리오 간 간격
                await asyncio.sleep(2)
        
        # 최종 분석
        analysis = self.utm_tracker.analyze_sequential_visits(scenarios)
        self.utm_tracker.print_analysis_report(analysis)
    



async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="UTM Audit Tool - 네트워크 감지 기반")
    parser.add_argument("--mode", choices=["basic", "sequential"], default="basic", 
                       help="테스트 모드: basic (기본), sequential (연속 First Touch/Last Touch 검증)")
    parser.add_argument("--discover", action="store_true", help="웹사이트의 실제 이벤트 탐지")
    
    args = parser.parse_args()
    
    if args.discover:
        # 이벤트 탐지 모드
        await discover_events()
        return
    
    auditor = UTMAuditor()
    await auditor.run_audit(mode=args.mode)


async def discover_events():
    """웹사이트의 실제 이벤트 탐지"""
    logger.info("🔍 웹사이트의 실제 이벤트 탐지 시작")
    
    from src.browser.playwright_client import PlaywrightClient
    from src.utm.generator import UTMGenerator
    
    browser_client = PlaywrightClient()
    utm_generator = UTMGenerator()
    
    try:
        async with browser_client as browser:
            # 기본 UTM으로 페이지 방문
            utm_params = utm_generator.generate_random_utm()
            utm_url = utm_generator.build_utm_url(settings.base_url, utm_params)
            
            logger.info(f"페이지 방문: {utm_url}")
            
            # 페이지 로드
            if await browser.navigate_to_url(utm_url):
                logger.info("페이지 로드 완료, 이벤트 대기 중...")
                
                # 10초간 이벤트 대기
                await asyncio.sleep(10)
                
                # 수집된 이벤트 분석
                mixpanel_requests = browser.get_mixpanel_requests()
                
                if mixpanel_requests:
                    logger.info("=== 발견된 이벤트 분석 ===")
                    
                    all_events = []
                    for request in mixpanel_requests:
                        if 'parsed_events' in request:
                            all_events.extend(request['parsed_events'])
                    
                    # 이벤트명별로 그룹화
                    event_counts = {}
                    for event in all_events:
                        event_name = event.get('event', 'unknown')
                        if event_name not in event_counts:
                            event_counts[event_name] = []
                        event_counts[event_name].append(event)
                    
                    logger.info(f"총 {len(all_events)}개 이벤트 발견")
                    
                    for event_name, events in event_counts.items():
                        logger.info(f"\n📊 이벤트: {event_name} ({len(events)}개)")
                        
                        # 첫 번째 이벤트의 속성 분석
                        if events:
                            first_event = events[0]
                            properties = first_event.get('properties', {})
                            
                            # UTM 속성
                            utm_props = {k: v for k, v in properties.items() if k.startswith('$utm_')}
                            if utm_props:
                                logger.info(f"  ✅ UTM 속성: {utm_props}")
                            else:
                                logger.warning(f"  ❌ UTM 속성 없음")
                            
                            # First Touch/Last Touch 속성
                            if '$first_touch' in properties:
                                logger.info(f"  ✅ First Touch: {properties['$first_touch']}")
                            else:
                                logger.warning(f"  ❌ First Touch 속성 없음")
                            
                            if 'last_touch' in properties:
                                logger.info(f"  ✅ Last Touch: {properties['last_touch']}")
                            else:
                                logger.warning(f"  ❌ Last Touch 속성 없음")
                            
                            # 기타 주요 속성
                            other_props = {k: v for k, v in properties.items() 
                                        if not k.startswith('$utm_') and k not in ['$first_touch', 'last_touch']}
                            if other_props:
                                logger.info(f"  📋 기타 속성: {list(other_props.keys())}")
                else:
                    logger.warning("Mixpanel 이벤트가 감지되지 않았습니다")
                    
    except Exception as e:
        logger.error(f"이벤트 탐지 중 오류: {e}")
    finally:
        await browser_client.close()


if __name__ == "__main__":
    asyncio.run(main())
