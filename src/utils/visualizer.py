"""
UTM 추적 결과 시각화 모듈
"""
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger


class UTMVisualizer:
    """UTM 추적 결과 시각화"""
    
    def __init__(self):
        self.results = []
    
    def add_result(self, step: int, utm_params: Dict, current_utm: Dict, 
                   first_touch: Dict, last_touch: Dict, success: bool):
        """결과 추가"""
        self.results.append({
            'step': step,
            'utm_params': utm_params,
            'current_utm': current_utm,
            'first_touch': first_touch,
            'last_touch': last_touch,
            'success': success,
            'timestamp': datetime.now()
        })
    
    def print_summary(self):
        """요약 결과 출력"""
        logger.info("\n" + "="*80)
        logger.info("🎯 UTM 추적 감사 결과 요약")
        logger.info("="*80)
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"📊 총 테스트: {total_tests}개")
        logger.info(f"✅ 성공: {successful_tests}개")
        logger.info(f"❌ 실패: {total_tests - successful_tests}개")
        logger.info(f"📈 성공률: {success_rate:.1f}%")
        
        if success_rate == 100:
            logger.info("🎉 모든 UTM 추적이 정상 작동합니다!")
        elif success_rate >= 80:
            logger.info("👍 대부분의 UTM 추적이 정상 작동합니다.")
        else:
            logger.warning("⚠️ UTM 추적에 문제가 있습니다.")
    
    def print_detailed_results(self):
        """상세 결과 출력"""
        logger.info("\n" + "="*80)
        logger.info("📋 상세 테스트 결과")
        logger.info("="*80)
        
        for result in self.results:
            step = result['step']
            utm_params = result['utm_params']
            current_utm = result['current_utm']
            first_touch = result['first_touch']
            last_touch = result['last_touch']
            success = result['success']
            
            status = "✅" if success else "❌"
            
            logger.info(f"\n{status} Step {step}: UTM 테스트")
            logger.info(f"   🎯 테스트 UTM: {utm_params.get('source', 'N/A')}/{utm_params.get('medium', 'N/A')}/{utm_params.get('campaign', 'N/A')}")
            logger.info(f"   📈 실제 UTM: {current_utm.get('source', 'N/A')}/{current_utm.get('medium', 'N/A')}/{current_utm.get('campaign', 'N/A')}")
            
            if first_touch:
                logger.info(f"   👆 First Touch: {first_touch}")
            else:
                logger.info(f"   👆 First Touch: 없음")
            
            if last_touch:
                logger.info(f"   👇 Last Touch: {last_touch}")
            else:
                logger.info(f"   👇 Last Touch: 없음 (첫 방문)")
    
    def print_flow_diagram(self):
        """플로우 다이어그램 출력"""
        logger.info("\n" + "="*80)
        logger.info("🔄 UTM 추적 플로우 다이어그램")
        logger.info("="*80)
        
        for i, result in enumerate(self.results):
            step = result['step']
            current_utm = result['current_utm']
            first_touch = result['first_touch']
            last_touch = result['last_touch']
            
            # 현재 UTM 문자열 생성
            current_str = f"{current_utm.get('source', 'N/A')}/{current_utm.get('medium', 'N/A')}/{current_utm.get('campaign', 'N/A')}"
            
            # First Touch 문자열 생성
            if first_touch:
                if isinstance(first_touch, dict):
                    ft_str = f"{first_touch.get('utm_source', 'N/A')}/{first_touch.get('utm_medium', 'N/A')}/{first_touch.get('utm_campaign', 'N/A')}"
                else:
                    ft_str = str(first_touch)
            else:
                ft_str = "없음"
            
            # Last Touch 문자열 생성
            if last_touch:
                if isinstance(last_touch, dict):
                    lt_str = f"{last_touch.get('utm_source [last touch]', 'N/A')}/{last_touch.get('utm_medium [last touch]', 'N/A')}/{last_touch.get('utm_campaign [last touch]', 'N/A')}"
                else:
                    lt_str = str(last_touch)
            else:
                lt_str = "없음 (첫 방문)"
            
            logger.info(f"\nStep {step}:")
            logger.info(f"   📍 현재 UTM: {current_str}")
            logger.info(f"   👆 First Touch: {ft_str}")
            logger.info(f"   👇 Last Touch: {lt_str}")
            
            if i < len(self.results) - 1:
                logger.info("   ⬇️")
    
    def print_recommendations(self):
        """권장사항 출력"""
        logger.info("\n" + "="*80)
        logger.info("💡 권장사항")
        logger.info("="*80)
        
        # First Touch 일관성 확인
        first_touches = []
        for result in self.results:
            if result['first_touch']:
                first_touches.append(result['first_touch'])
        
        if len(set(str(ft) for ft in first_touches)) == 1:
            logger.info("✅ First Touch가 일관되게 유지되고 있습니다.")
        else:
            logger.warning("⚠️ First Touch가 일관되지 않습니다. 설정을 확인해주세요.")
        
        # Last Touch 변경 확인
        last_touches = []
        for result in self.results:
            if result['last_touch']:
                last_touches.append(result['last_touch'])
        
        if len(set(str(lt) for lt in last_touches)) > 1:
            logger.info("✅ Last Touch가 올바르게 변경되고 있습니다.")
        else:
            logger.warning("⚠️ Last Touch가 변경되지 않습니다. 설정을 확인해주세요.")
        
        # 전반적인 권장사항
        logger.info("\n📋 일반적인 권장사항:")
        logger.info("   • UTM 파라미터는 일관된 명명 규칙을 사용하세요")
        logger.info("   • First Touch는 사용자의 첫 방문을 정확히 추적해야 합니다")
        logger.info("   • Last Touch는 최근 방문을 정확히 반영해야 합니다")
        logger.info("   • 정기적으로 UTM 추적을 감사하여 정확성을 확인하세요")
    
    def generate_report(self):
        """전체 리포트 생성"""
        self.print_summary()
        self.print_detailed_results()
        self.print_flow_diagram()
        self.print_recommendations()
        
        logger.info("\n" + "="*80)
        logger.info("🏁 UTM 추적 감사 완료")
        logger.info("="*80)
