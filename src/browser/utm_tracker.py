"""
네트워크 감지만으로 UTM 추적 분석
"""
import json
import urllib.parse
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger


class UTMNetworkTracker:
    """네트워크 요청만으로 UTM 추적 분석"""
    
    def __init__(self):
        self.utm_events = []
        self.session_data = {}
    
    def analyze_mixpanel_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mixpanel 요청 분석"""
        try:
            if request_data['method'] != 'POST' or not request_data.get('post_data'):
                return {}
            
            # URL 디코딩
            decoded_data = urllib.parse.unquote(request_data['post_data'])
            
            # JSON 파싱
            try:
                event_data = json.loads(decoded_data)
            except json.JSONDecodeError:
                # 배치 데이터일 수 있음 - 라인별로 파싱
                events = []
                for line in decoded_data.strip().split('\n'):
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                if events:
                    event_data = events[0]  # 첫 번째 이벤트 사용
                else:
                    return {}
            
            # 이벤트 분석
            analysis = {
                'timestamp': request_data['timestamp'],
                'event_name': event_data.get('event', 'unknown'),
                'properties': event_data.get('properties', {}),
                'utm_attribution': self._extract_utm_attribution(event_data.get('properties', {}))
            }
            
            # UTM 이벤트 저장
            self.utm_events.append(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Mixpanel 요청 분석 중 오류: {e}")
            return {}
    
    def _extract_utm_attribution(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """UTM 속성 추출"""
        utm_attribution = {
            'utm_source': properties.get('$utm_source'),
            'utm_medium': properties.get('$utm_medium'),
            'utm_campaign': properties.get('$utm_campaign'),
            'utm_term': properties.get('$utm_term'),
            'utm_content': properties.get('$utm_content'),
            'first_touch': properties.get('$first_touch'),
            'last_touch': properties.get('last_touch'),  # 직접 구현한 경우
            'distinct_id': properties.get('$distinct_id'),
            'device_id': properties.get('$device_id')
        }
        
        return utm_attribution
    
    def analyze_sequential_visits(self, utm_scenarios: List[Dict]) -> Dict[str, Any]:
        """연속 방문 분석"""
        if len(self.utm_events) < len(utm_scenarios):
            return {
                'success': False,
                'error': f"예상 이벤트 수: {len(utm_scenarios)}, 실제 이벤트 수: {len(self.utm_events)}"
            }
        
        analysis = {
            'total_scenarios': len(utm_scenarios),
            'total_events': len(self.utm_events),
            'scenario_results': [],
            'first_touch_consistency': True,
            'last_touch_changes': True,
            'errors': []
        }
        
        first_touch_values = []
        last_touch_values = []
        
        for i, (scenario, event) in enumerate(zip(utm_scenarios, self.utm_events)):
            utm_params = scenario['utm_params']
            attribution = event['utm_attribution']
            
            # 예상 UTM과 실제 UTM 비교
            utm_match = (
                attribution['utm_source'] == utm_params.source and
                attribution['utm_medium'] == utm_params.medium and
                attribution['utm_campaign'] == utm_params.campaign
            )
            
            # First Touch/Last Touch 분석
            first_touch = attribution['first_touch']
            last_touch = attribution['last_touch']
            
            if first_touch:
                first_touch_values.append(first_touch)
            if last_touch:
                last_touch_values.append(last_touch)
            
            scenario_result = {
                'step': i + 1,
                'utm_params': utm_params,
                'actual_utm': {
                    'source': attribution['utm_source'],
                    'medium': attribution['utm_medium'],
                    'campaign': attribution['utm_campaign']
                },
                'utm_match': utm_match,
                'first_touch': first_touch,
                'last_touch': last_touch,
                'event_name': event['event_name'],
                'success': utm_match and first_touch and last_touch
            }
            
            analysis['scenario_results'].append(scenario_result)
            
            if not utm_match:
                analysis['errors'].append(f"Step {i+1}: UTM 파라미터 불일치")
            if not first_touch:
                analysis['errors'].append(f"Step {i+1}: First Touch 속성 누락")
            if not last_touch:
                analysis['errors'].append(f"Step {i+1}: Last Touch 속성 누락")
        
        # First Touch 일관성 확인
        if len(set(first_touch_values)) > 1:
            analysis['first_touch_consistency'] = False
            analysis['errors'].append("First Touch가 일관되지 않음")
        
        # Last Touch 변경 확인
        if len(set(last_touch_values)) <= 1:
            analysis['last_touch_changes'] = False
            analysis['errors'].append("Last Touch가 변경되지 않음")
        
        analysis['success'] = len(analysis['errors']) == 0
        analysis['success_rate'] = sum(1 for r in analysis['scenario_results'] if r['success']) / len(analysis['scenario_results']) * 100
        
        return analysis
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """분석 결과 출력"""
        logger.info("=== UTM 네트워크 추적 분석 결과 ===")
        logger.info(f"총 시나리오: {analysis['total_scenarios']}")
        logger.info(f"총 이벤트: {analysis['total_events']}")
        logger.info(f"성공률: {analysis['success_rate']:.1f}%")
        
        if analysis['success']:
            logger.info("✅ 모든 UTM 추적이 정상 작동")
        else:
            logger.warning("❌ UTM 추적에 문제가 있음")
            for error in analysis['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("\n=== 시나리오별 상세 결과 ===")
        for result in analysis['scenario_results']:
            status = "✅" if result['success'] else "❌"
            logger.info(f"{status} Step {result['step']}: {result['event_name']}")
            logger.info(f"  UTM: {result['actual_utm']['source']}_{result['actual_utm']['medium']}_{result['actual_utm']['campaign']}")
            logger.info(f"  First Touch: {result['first_touch']}")
            logger.info(f"  Last Touch: {result['last_touch']}")
        
        # First Touch/Last Touch 속성 분석
        logger.info("\n=== 속성 분석 ===")
        logger.info(f"First Touch 일관성: {'✅' if analysis['first_touch_consistency'] else '❌'}")
        logger.info(f"Last Touch 변경: {'✅' if analysis['last_touch_changes'] else '❌'}")
    
    def clear_events(self):
        """이벤트 데이터 초기화"""
        self.utm_events.clear()
