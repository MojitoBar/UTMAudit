"""
Playwright 브라우저 자동화 클라이언트
"""
import asyncio
import time
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger
from ..utils.config import settings


class PlaywrightClient:
    """Playwright 브라우저 자동화 클라이언트"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    async def start(self):
        """브라우저 시작"""
        try:
            self.playwright = await async_playwright().start()
            
            # 브라우저 타입에 따라 선택
            if settings.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=settings.headless
                )
            elif settings.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(
                    headless=settings.headless
                )
            else:  # chromium (기본값)
                self.browser = await self.playwright.chromium.launch(
                    headless=settings.headless
                )
            
            # 컨텍스트 생성
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 페이지 생성
            self.page = await self.context.new_page()
            
            # 네트워크 요청 모니터링 설정
            await self._setup_network_monitoring()
            
            logger.info(f"브라우저 시작 완료: {settings.browser_type}")
            
        except Exception as e:
            logger.error(f"브라우저 시작 실패: {e}")
            raise
    
    async def close(self):
        """브라우저 종료"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("브라우저 종료 완료")
            
        except Exception as e:
            logger.error(f"브라우저 종료 실패: {e}")
    
    async def _setup_network_monitoring(self):
        """네트워크 요청 모니터링 설정"""
        if not self.page:
            return
        
        # Mixpanel API 호출 감지
        self.mixpanel_requests = []
        
        async def handle_request(request):
            if "mixpanel.com" in request.url:
                request_data = {
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data,
                    'timestamp': time.time()
                }
                
                # POST 데이터에서 이벤트명 추출
                if request.method == "POST" and request.post_data:
                    try:
                        import json
                        # URL 디코딩 후 JSON 파싱
                        import urllib.parse
                        decoded_data = urllib.parse.unquote(request.post_data)
                        
                        # 여러 이벤트가 있을 수 있으므로 라인별로 파싱
                        events = []
                        for line in decoded_data.strip().split('\n'):
                            if line:
                                try:
                                    event_data = json.loads(line)
                                    events.append(event_data)
                                except json.JSONDecodeError:
                                    continue
                        
                        request_data['parsed_events'] = events
                        
                        # 이벤트명 로깅
                        for event in events:
                            event_name = event.get('event', 'unknown')
                            logger.info(f"🎯 실제 이벤트 감지: {event_name}")
                            if 'properties' in event:
                                properties = event['properties']
                                utm_props = {k: v for k, v in properties.items() if k.startswith('utm_') and not ' [first touch]' in k and not ' [last touch]' in k}
                                initial_utm_props = {k: v for k, v in properties.items() if k.startswith('initial_utm_') or ' [first touch]' in k}
                                last_touch_props = {k: v for k, v in properties.items() if ' [last touch]' in k}
                                
                                if utm_props:
                                    logger.info(f"  📊 UTM 속성: {utm_props}")
                                if initial_utm_props:
                                    logger.info(f"  🎯 Initial UTM 속성: {initial_utm_props}")
                                if last_touch_props:
                                    logger.info(f"  👇 Last Touch 속성: {last_touch_props}")
                                if not utm_props and not initial_utm_props and not last_touch_props:
                                    logger.warning(f"  ❌ UTM 속성이 없습니다")
                                
                    except Exception as e:
                        logger.debug(f"이벤트 파싱 실패: {e}")
                
                self.mixpanel_requests.append(request_data)
                logger.debug(f"Mixpanel 요청 감지: {request.method} {request.url}")
                
                # POST 데이터가 있으면 이벤트 내용 파싱
                if request.method == "POST" and request.post_data:
                    try:
                        import json
                        import urllib.parse
                        
                        # URL 디코딩
                        decoded_data = urllib.parse.unquote(request.post_data)
                        logger.info(f"📊 POST 데이터: {decoded_data[:200]}...")  # 처음 200자만
                        logger.debug(f"📊 전체 POST 데이터: {decoded_data}")  # 전체 데이터
                        
                        # data= 파라미터에서 실제 JSON 데이터 추출
                        if 'data=' in decoded_data:
                            data_start = decoded_data.find('data=') + 5
                            json_data = decoded_data[data_start:]
                            logger.debug(f"🔍 추출된 JSON 데이터: {json_data}")
                            
                            # JSON 파싱 시도
                            try:
                                parsed_events = json.loads(json_data)
                                # 배열이 아닌 경우 배열로 변환
                                if not isinstance(parsed_events, list):
                                    parsed_events = [parsed_events]
                                
                                # 파싱된 이벤트를 요청 데이터에 저장
                                request_data['parsed_events'] = parsed_events
                                
                                # 첫 번째 이벤트 정보 출력
                                if parsed_events:
                                    first_event = parsed_events[0]
                                    if 'event' in first_event:
                                        logger.info(f"🎯 이벤트명: {first_event['event']}")
                                    if 'properties' in first_event:
                                        props = first_event['properties']
                                        utm_props = {k: v for k, v in props.items() if k.startswith('utm_') and not k.endswith('[last touch]')}
                                        if utm_props:
                                            logger.info(f"📈 현재 UTM: {utm_props}")
                                        else:
                                            logger.warning("❌ 현재 UTM 속성이 없습니다")
                                        
                                        # Last Touch 속성 확인
                                        last_touch_props = {k: v for k, v in props.items() if k.endswith('[last touch]')}
                                        if last_touch_props:
                                            logger.info(f"👇 Last Touch: {last_touch_props}")
                                        else:
                                            logger.info("👇 Last Touch: 없음 (첫 방문)")
                                        
                                        # First Touch 확인
                                        if not last_touch_props:
                                            logger.info(f"👆 First Touch: {utm_props}")
                                        else:
                                            logger.info("👆 First Touch: 이전 방문에서 설정됨")
                                        
                            except json.JSONDecodeError:
                                logger.debug("JSON 파싱 실패 (배치 데이터일 수 있음)")
                        else:
                            logger.debug("data= 파라미터를 찾을 수 없습니다")
                            
                    except Exception as e:
                        logger.debug(f"이벤트 파싱 중 오류: {e}")
        
        self.page.on("request", handle_request)
    
    async def navigate_to_url(self, url: str, wait_for_load: bool = True) -> bool:
        """URL로 이동"""
        try:
            if not self.page:
                raise Exception("페이지가 초기화되지 않았습니다")
            
            logger.info(f"URL로 이동: {url}")
            
            # 페이지 이동
            response = await self.page.goto(url, wait_until="networkidle" if wait_for_load else "domcontentloaded")
            
            if response and response.status == 200:
                logger.info(f"페이지 로드 성공: {response.status}")
                return True
            else:
                logger.warning(f"페이지 로드 실패: {response.status if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"URL 이동 실패: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """요소 대기"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except Exception as e:
            logger.warning(f"요소 대기 실패: {selector} - {e}")
            return False
    
    async def click_element(self, selector: str) -> bool:
        """요소 클릭"""
        try:
            await self.page.click(selector)
            logger.debug(f"요소 클릭: {selector}")
            return True
        except Exception as e:
            logger.error(f"요소 클릭 실패: {selector} - {e}")
            return False
    
    async def get_page_title(self) -> str:
        """페이지 제목 가져오기"""
        try:
            return await self.page.title()
        except Exception as e:
            logger.error(f"페이지 제목 가져오기 실패: {e}")
            return ""
    
    async def get_current_url(self) -> str:
        """현재 URL 가져오기"""
        try:
            return self.page.url
        except Exception as e:
            logger.error(f"현재 URL 가져오기 실패: {e}")
            return ""
    
    async def take_screenshot(self, path: str = None) -> Optional[str]:
        """스크린샷 촬영"""
        try:
            if not path:
                timestamp = int(time.time())
                path = f"screenshots/screenshot_{timestamp}.png"
            
            await self.page.screenshot(path=path)
            logger.info(f"스크린샷 저장: {path}")
            return path
            
        except Exception as e:
            logger.error(f"스크린샷 촬영 실패: {e}")
            return None
    
    def get_mixpanel_requests(self) -> list:
        """수집된 Mixpanel 요청 반환"""
        return self.mixpanel_requests.copy()
    
    async def clear_mixpanel_requests(self):
        """Mixpanel 요청 기록 초기화"""
        self.mixpanel_requests.clear()
    
    async def execute_script(self, script: str) -> Any:
        """JavaScript 코드 실행"""
        if not self.page:
            raise Exception("페이지가 초기화되지 않았습니다.")
        
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"JavaScript 실행 실패: {e}")
            raise
    
    async def wait_for_mixpanel_request(self, timeout: int = 10) -> bool:
        """Mixpanel 요청 대기"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.mixpanel_requests:
                return True
            await asyncio.sleep(0.1)
        return False
