"""
Streamlit UTM 분석 웹 앱 - First Touch vs Last Touch 분석
"""
import streamlit as st
import asyncio
import json
import pandas as pd
from datetime import datetime
import time
from typing import Dict, List, Any, Optional

from src.browser.playwright_client import PlaywrightClient
from src.utm.generator import UTMGenerator, UTMParams
from src.utils.config import settings, Settings
from src.mixpanel.api_client import MixpanelAPIClient


class UTMUserAnalyzer:
    """사용자별 UTM 분석기"""
    
    def __init__(self, mixpanel_settings: Optional[Dict[str, Any]] = None):
        self.browser_client = PlaywrightClient()
        self.utm_generator = UTMGenerator()
        self.mixpanel_client = MixpanelAPIClient(custom_settings=mixpanel_settings)
    
    def get_user_properties(self, user_id: str, property_query_mode: str = "기본 UTM 속성", custom_properties: List[str] = None) -> Dict[str, Any]:
        """사용자의 현재 프로퍼티 조회 (Mixpanel API 사용)"""
        try:
            print(f"🔍 사용자 프로퍼티 조회 시작: {user_id}")
            print(f"🔍 조회 모드: {property_query_mode}")
            
            # 조회 모드에 따라 API 호출
            if property_query_mode == "모든 속성":
                print(f"🔍 모든 속성 조회 모드")
                api_result = self.mixpanel_client.get_user_profile_all_properties(user_id)
            elif property_query_mode == "사용자 지정 속성" and custom_properties:
                print(f"🔍 사용자 지정 속성 조회 모드: {custom_properties}")
                api_result = self.mixpanel_client.get_user_profile(user_id, output_properties=custom_properties)
            else:
                print(f"🔍 기본 UTM 속성 조회 모드")
                api_result = self.mixpanel_client.get_user_profile(user_id)
            
            if api_result['success']:
                properties = api_result['properties']
                distinct_id = api_result['distinct_id']
                print(f"✅ API 조회 성공. 속성 수: {len(properties)}")
                print(f"👤 Distinct ID: {distinct_id}")
                print(f"📋 전체 속성: {properties}")
                
                # Initial UTM 속성 추출
                initial_utm = {}
                for key, value in properties.items():
                    if key.startswith('initial_utm_'):
                        initial_utm[key] = value
                
                print(f"🎯 Initial UTM 속성: {initial_utm}")
                
                # Current UTM 속성 추출
                current_utm = {}
                for key, value in properties.items():
                    if key.startswith('utm_') and not key.startswith('initial_utm_'):
                        current_utm[key] = value
                
                print(f"📊 Current UTM 속성: {current_utm}")
                
                user_properties = {
                    'user_id': user_id,
                    'distinct_id': distinct_id,
                    'initial_utm': initial_utm,
                    'current_utm': current_utm,
                    'all_properties': properties,
                    'source': 'mixpanel_api'
                }
                
                return {
                    'success': True,
                    'user_properties': user_properties,
                    'debug_info': {
                        'source': 'mixpanel_api',
                        'total_properties': len(properties),
                        'initial_utm_count': len(initial_utm),
                        'current_utm_count': len(current_utm),
                        'api_debug': api_result.get('debug_info', {})
                    }
                }
            else:
                print(f"❌ API 조회 실패: {api_result['error']}")
                return {
                    'success': False,
                    'error': api_result['error'],
                    'debug_info': {
                        'source': 'mixpanel_api',
                        'distinct_id': user_id,
                        'api_debug': api_result.get('debug_info', {})
                    }
                }
                    
        except Exception as e:
            print(f"❌ 사용자 프로퍼티 조회 중 오류: {str(e)}")
            return {
                'success': False,
                'error': f'사용자 프로퍼티 조회 중 오류: {str(e)}',
                'debug_info': {
                    'source': 'mixpanel_api',
                    'error_type': type(e).__name__
                }
            }
    
    async def test_utm_scenario(self, user_id: str, base_url: str, utm_params: Dict[str, str], user_properties: Dict[str, Any], property_query_mode: str = "기본 UTM 속성", custom_properties: List[str] = None) -> Dict[str, Any]:
        """UTM 시나리오 테스트 (접속 전후 비교)"""
        try:
            import webbrowser
            
            # UTM URL 생성
            utm_obj = UTMParams(**utm_params)
            utm_url = self.utm_generator.build_utm_url(base_url, utm_obj)
            
            print(f"🔗 사용자 방문 URL: {utm_url}")
            
            # 실제 브라우저에서 URL 열기
            try:
                webbrowser.open(utm_url)
                print(f"✅ 브라우저에서 URL을 열었습니다: {utm_url}")
            except Exception as e:
                print(f"⚠️ 브라우저 열기 실패: {e}")
                return {
                    'success': False,
                    'error': f'브라우저 열기 실패: {str(e)}'
                }
            
            # 사용자에게 안내 메시지
            print(f"📋 사용자 안내:")
            print(f"   1. 브라우저에서 열린 페이지를 확인하세요")
            print(f"   2. 로그인되어 있다면 로그인된 상태로 방문됩니다")
            print(f"   3. 페이지를 몇 분간 둘러보신 후 아래 '테스트 완료' 버튼을 클릭하세요")
            
            # 대기 시간 (사용자가 직접 방문하는 시간)
            print(f"⏳ 사용자 직접 방문 대기 중... (3분)")
            await asyncio.sleep(180)  # 3분 대기
            
            # 접속 후 사용자 프로퍼티 재조회
            after_user_result = self.get_user_properties(user_id, property_query_mode, custom_properties)
            after_properties = {}
            
            if after_user_result['success']:
                after_properties = after_user_result['user_properties'].get('all_properties', {})
                print(f"✅ 접속 후 프로퍼티 조회 성공: {len(after_properties)}개 속성")
            else:
                print(f"❌ 접속 후 프로퍼티 조회 실패: {after_user_result['error']}")
            
            return {
                'success': True,
                'utm_url': utm_url,
                'before_properties': user_properties.get('all_properties', {}),
                'after_properties': after_properties,
                'mixpanel_available': True  # 실제 브라우저 방문이므로 True로 설정
            }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'UTM 테스트 중 오류: {str(e)}'
            }





def display_user_properties(user_properties: Dict[str, Any]):
    """사용자 프로퍼티 표시"""
    st.subheader(f"👤 사용자 프로퍼티: {user_properties['user_id']}")
    
    # 소스 정보 표시
    if 'source' in user_properties:
        st.info(f"**데이터 소스**: {user_properties['source']}")
    
    if 'distinct_id' in user_properties:
        st.info(f"**Distinct ID**: {user_properties['distinct_id']}")
    
    # UTM 키워드가 포함된 모든 속성 추출 및 정렬
    all_properties = user_properties.get('all_properties', {})
    utm_properties = {}
    
    for key, value in all_properties.items():
        if 'utm' in key.lower():
            utm_properties[key] = value
    
    # 오름차순 정렬
    sorted_utm_properties = dict(sorted(utm_properties.items()))
    
    st.markdown("**🎯 UTM 관련 속성 (오름차순)**")
    if sorted_utm_properties:
        for key, value in sorted_utm_properties.items():
            st.write(f"**{key}**: {value}")
    else:
        st.info("UTM 관련 속성이 없습니다.")
    
    # 전체 속성 (접을 수 있게)
    with st.expander("📋 전체 속성 보기"):
        properties_df = pd.DataFrame([
            {'속성명': key, '값': str(value)} 
            for key, value in all_properties.items()
        ])
        if not properties_df.empty:
            st.dataframe(properties_df, use_container_width=True)
        else:
            st.info("속성이 없습니다.")


def display_utm_test_results(before_properties: Dict[str, Any], after_properties: Dict[str, Any], utm_params: Dict[str, str], scenario_name: str):
    """UTM 테스트 결과 표시 (접속 전후 비교)"""
    st.subheader(f"📊 UTM 테스트 결과: {scenario_name}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔍 접속 전 UTM 속성**")
        if before_properties:
            for key, value in sorted(before_properties.items()):
                st.write(f"**{key}**: {value}")
        else:
            st.info("접속 전 UTM 속성이 없습니다.")
    
    with col2:
        st.markdown("**🎯 접속 후 UTM 속성**")
        if after_properties:
            for key, value in sorted(after_properties.items()):
                st.write(f"**{key}**: {value}")
        else:
            st.info("접속 후 UTM 속성이 없습니다.")
    
    # 변화 분석
    st.markdown("**🔄 변화 분석**")
    
    # 공통 키 찾기
    all_keys = set(before_properties.keys()) | set(after_properties.keys())
    
    if all_keys:
        changes = []
        for key in sorted(all_keys):
            before_value = before_properties.get(key, "없음")
            after_value = after_properties.get(key, "없음")
            
            if before_value != after_value:
                changes.append({
                    '속성': key,
                    '변경 전': before_value,
                    '변경 후': after_value,
                    '변화': '✅ 변경됨' if after_value != "없음" else '❌ 삭제됨'
                })
            else:
                changes.append({
                    '속성': key,
                    '변경 전': before_value,
                    '변경 후': after_value,
                    '변화': '➡️ 유지'
                })
        
        if changes:
            changes_df = pd.DataFrame(changes)
            st.dataframe(changes_df, use_container_width=True)
        else:
            st.info("변화가 없습니다.")
    else:
        st.info("비교할 속성이 없습니다.")


def run_utm_analysis(user_id: str, base_url: str, scenarios: List[Dict], property_query_mode: str = "기본 UTM 속성", custom_properties: List[str] = None, mixpanel_settings: Optional[Dict[str, Any]] = None):
    """UTM 분석 실행"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        analyzer = UTMUserAnalyzer(mixpanel_settings=mixpanel_settings)
        all_results = []
        
        # 진행 상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. 사용자 프로퍼티 조회
        st.markdown("### 1️⃣ 사용자 프로퍼티 조회")
        with st.spinner("사용자 프로퍼티를 조회하는 중..."):
            progress_bar.progress(10)
            status_text.text("사용자 프로퍼티 조회 중...")
            
            user_result = analyzer.get_user_properties(user_id, property_query_mode, custom_properties)
            
            if user_result['success']:
                st.success("✅ 사용자 프로퍼티 조회 완료")
                display_user_properties(user_result['user_properties'])
                user_properties = user_result['user_properties']
                
                # 디버깅 정보 표시
                if 'debug_info' in user_result:
                    with st.expander("🔍 디버깅 정보"):
                        debug_info = user_result['debug_info']
                        st.write(f"**데이터 소스**: {debug_info.get('source', 'mixpanel_api')}")
                        
                        # API 응답 정보 표시
                        if 'request_data' in debug_info:
                            st.write("**📡 API 요청 데이터:**")
                            st.json(debug_info['request_data'])
                        
                        if 'response_status' in debug_info:
                            st.write(f"**📊 응답 상태**: {debug_info['response_status']}")
                        
                        if 'response_body' in debug_info:
                            st.write("**📦 API 응답 데이터:**")
                            st.json(debug_info['response_body'])
                        
                        if 'method' in user_result:
                            st.write(f"**🔧 사용된 방법**: {user_result['method']}")
                        
                        # API 디버깅 정보
                        if 'api_debug' in debug_info:
                            api_debug = debug_info['api_debug']
                            if 'request_data' in api_debug:
                                st.write("**📡 API 요청 데이터:**")
                                st.json(api_debug['request_data'])
                            
                            if 'response_status' in api_debug:
                                st.write(f"**📊 응답 상태**: {api_debug['response_status']}")
                            
                            if 'response_body' in api_debug:
                                st.write("**📦 API 응답 데이터:**")
                                st.json(api_debug['response_body'])
                        
                        if 'total_properties' in debug_info:
                            st.write(f"**총 속성 수**: {debug_info['total_properties']}")
                            st.write(f"**Initial UTM 속성 수**: {debug_info['initial_utm_count']}")
                            st.write(f"**Current UTM 속성 수**: {debug_info['current_utm_count']}")
                        if 'distinct_id' in debug_info:
                            st.write(f"**조회한 Distinct ID**: {debug_info['distinct_id']}")
                        if 'error_type' in debug_info:
                            st.write(f"**오류 타입**: {debug_info['error_type']}")
            else:
                st.error(f"❌ 사용자 프로퍼티 조회 실패: {user_result['error']}")
                
                # 디버깅 정보 표시
                if 'debug_info' in user_result:
                    with st.expander("🔍 디버깅 정보"):
                        debug_info = user_result['debug_info']
                        st.write(f"**데이터 소스**: {debug_info.get('source', 'mixpanel_api')}")
                        
                        # API 디버깅 정보
                        if 'api_debug' in debug_info:
                            api_debug = debug_info['api_debug']
                            if 'request_data' in api_debug:
                                st.write("**📡 API 요청 데이터:**")
                                st.json(api_debug['request_data'])
                            
                            if 'response_status' in api_debug:
                                st.write(f"**📊 응답 상태**: {api_debug['response_status']}")
                            
                            if 'response_body' in api_debug:
                                st.write("**📦 API 응답 데이터:**")
                                st.json(api_debug['response_body'])
                        
                        if 'distinct_id' in debug_info:
                            st.write(f"**조회한 Distinct ID**: {debug_info['distinct_id']}")
                        if 'error_type' in debug_info:
                            st.write(f"**오류 타입**: {debug_info['error_type']}")
                
                # 계속 진행할지 확인
                if st.button("⚠️ 계속 진행 (사용자 프로퍼티 없이)"):
                    user_properties = {
                        'user_id': user_id,
                        'event_name': 'unknown',
                        'initial_utm': {},
                        'current_utm': {},
                        'all_properties': {}
                    }
                else:
                    return
        
        # 2. UTM 시나리오 테스트
        st.markdown("### 2️⃣ UTM 시나리오 테스트")
        
        async def run_scenarios():
            async with PlaywrightClient() as browser:
                for i, scenario in enumerate(scenarios):
                    st.markdown(f"#### {scenario['name']}")
                    
                    with st.spinner(f"시나리오 {i+1} 실행 중..."):
                        progress = 20 + (i + 1) * (70 / len(scenarios))
                        progress_bar.progress(int(progress))
                        status_text.text(f"시나리오 {i+1}: {scenario['name']}")
                        
                        # UTM 파라미터 설정
                        utm_scenario_params = {
                            'source': scenario['source'],
                            'medium': scenario['medium'],
                            'campaign': scenario['campaign'],
                            'term': None,
                            'content': None
                        }
                        
                        # UTM 테스트 실행
                        # 사용자에게 직접 방문 안내
                        st.info(f"""
                        📋 **사용자 직접 방문 안내**
                        
                        1. 브라우저에서 UTM URL이 열립니다
                        2. 로그인되어 있다면 로그인된 상태로 방문됩니다  
                        3. 페이지를 몇 분간 둘러보신 후 결과를 확인하세요
                        4. 3분 후 자동으로 접속 후 프로퍼티를 조회합니다
                        """)
                        
                        test_result = await analyzer.test_utm_scenario(
                            user_id, base_url, utm_scenario_params, user_properties, property_query_mode, custom_properties
                        )
                        
                        if test_result['success']:
                            st.success(f"✅ {scenario['name']} 완료")
                            all_results.append({
                                'scenario': scenario,
                                'result': test_result
                            })
                            
                            # 결과 표시
                            if test_result['success']:
                                display_utm_test_results(
                                    test_result['before_properties'], 
                                    test_result['after_properties'], 
                                    utm_scenario_params, 
                                    scenario['name']
                                )
                        else:
                            st.error(f"❌ {scenario['name']} 실패: {test_result['error']}")
                    
                    # 요청 초기화 (다음 시나리오를 위해)
                    await browser.clear_mixpanel_requests()
                    
                    # 시나리오 간 대기 (쿠키 저장 시간)
                    if i < len(scenarios) - 1:
                        st.info("⏳ 다음 시나리오 대기 중... (쿠키 저장)")
                        # 시나리오가 하나만 있으므로 대기 불필요
                        pass
        
        # 비동기 함수 실행
        loop.run_until_complete(run_scenarios())
        
        progress_bar.progress(100)
        status_text.text("UTM 분석 완료!")
        
        # 3. 전체 결과 요약
        st.markdown("### 3️⃣ 전체 결과 요약")
        
        if all_results:
            summary_data = []
            for res in all_results:
                scenario = res['scenario']
                result = res['result']
                
                if result['success']:
                    before_properties = result['before_properties']
                    after_properties = result['after_properties']
                    
                    # 속성 변화 분석
                    all_keys = set(before_properties.keys()) | set(after_properties.keys())
                    changed_properties = []
                    
                    for key in sorted(all_keys):
                        before_value = before_properties.get(key, "없음")
                        after_value = after_properties.get(key, "없음")
                        
                        if before_value != after_value:
                            changed_properties.append(f"{key}: {before_value} → {after_value}")
                    
                    summary_data.append({
                        '시나리오': scenario['name'],
                        '예상 UTM': f"{scenario['source']}/{scenario['medium']}/{scenario['campaign']}",
                        '접속 전 속성 수': len(before_properties),
                        '접속 후 속성 수': len(after_properties),
                        '변경된 속성': ', '.join(changed_properties) if changed_properties else '변화 없음'
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
                

                
    except Exception as e:
        st.error(f"❌ UTM 분석 중 오류: {str(e)}")
    finally:
        loop.close()


def main():
    """Streamlit 메인 앱"""
    st.set_page_config(
        page_title="UTM First/Last Touch 분석기",
        page_icon="",
        layout="wide"
    )
    
    st.title("UTM First Touch vs Last Touch 분석기")
    st.markdown("사용자별 UTM 파라미터의 First Touch와 Last Touch 변화를 분석합니다.")
    
    # Mixpanel API 설정
    st.sidebar.markdown("### 🔑 Mixpanel API 설정")
    
    # 현재 설정값 가져오기
    current_settings = Settings()
    
    # API 설정 입력
    mixpanel_service_account = st.sidebar.text_input(
        "Service Account",
        value=current_settings.mixpanel_service_account if current_settings.mixpanel_service_account != "your_service_account_here" else "",
        help="Mixpanel Service Account 이름"
    )
    
    mixpanel_service_password = st.sidebar.text_input(
        "Service Password",
        value=current_settings.mixpanel_service_password if current_settings.mixpanel_service_password != "your_service_password_here" else "",
        type="password",
        help="Mixpanel Service Account 비밀번호"
    )
    
    mixpanel_project_id = st.sidebar.number_input(
        "Project ID",
        value=current_settings.mixpanel_project_id if current_settings.mixpanel_project_id != 0 else 0,
        min_value=0,
        help="Mixpanel 프로젝트 ID (숫자)"
    )
    
    # 설정 유효성 검사
    if not mixpanel_service_account or not mixpanel_service_password or mixpanel_project_id == 0:
        st.sidebar.error("⚠️ Mixpanel API 설정을 완료해주세요!")
        st.sidebar.markdown("""
        **필수 설정:**
        - Service Account: Mixpanel 서비스 계정명
        - Service Password: 서비스 계정 비밀번호  
        - Project ID: Mixpanel 프로젝트 ID
        """)
        return
    
    # 설정을 전역 변수로 저장
    st.session_state.mixpanel_settings = {
        'service_account': mixpanel_service_account,
        'service_password': mixpanel_service_password,
        'project_id': mixpanel_project_id
    }
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 설정")
    
    # URL 입력
    base_url = st.sidebar.text_input(
        "웹 사이트 URL",
        value="https://marketfitlab.webflow.io/",
        help="분석할 웹사이트 URL을 입력하세요"
    )
    
    # User ID 입력
    user_id = st.sidebar.text_input(
        "👤 User ID",
        value="jude",
        help="분석할 사용자의 ID를 입력하세요"
    )
    
    # UTM 파라미터 입력
    st.sidebar.markdown("### 🎯 UTM 파라미터")
    utm_source = st.sidebar.text_input(
        "UTM Source",
        value="google",
        help="utm_source 파라미터 값"
    )
    utm_medium = st.sidebar.text_input(
        "UTM Medium", 
        value="cpc",
        help="utm_medium 파라미터 값"
    )
    utm_campaign = st.sidebar.text_input(
        "UTM Campaign",
        value="brand_search", 
        help="utm_campaign 파라미터 값"
    )
    utm_term = st.sidebar.text_input(
        "UTM Term (선택사항)",
        value="",
        help="utm_term 파라미터 값 (선택사항)"
    )
    utm_content = st.sidebar.text_input(
        "UTM Content (선택사항)",
        value="",
        help="utm_content 파라미터 값 (선택사항)"
    )
    
    # 사용자 지정 속성 입력
    custom_properties_input = st.sidebar.text_area(
        "📝 조회할 속성 목록",
        value="",
        help="조회할 속성명을 한 줄에 하나씩 입력하세요 (빈 값이면 기본 UTM 속성 조회)",
        height=100
    )
    custom_properties = [prop.strip() for prop in custom_properties_input.split('\n') if prop.strip()]
    
    # 속성 조회 모드 결정
    if custom_properties:
        property_query_mode = "사용자 지정 속성"
        st.sidebar.success(f"✅ {len(custom_properties)}개 사용자 지정 속성")
    else:
        property_query_mode = "기본 UTM 속성"
        custom_properties = None
        st.sidebar.info("ℹ️ 기본 UTM 속성 조회 모드")
    
    # UTM 테스트 버튼
    if st.sidebar.button("🚀 UTM 테스트 시작 (3분 소요)", type="primary"):
        if not base_url:
            st.error("URL을 입력해주세요.")
            return
        
        if not user_id:
            st.error("User ID를 입력해주세요.")
            return
            
        # UTM 필수 파라미터 검사
        if not utm_source:
            st.error("UTM Source를 입력해주세요.")
            return
        if not utm_medium:
            st.error("UTM Medium을 입력해주세요.")
            return
        if not utm_campaign:
            st.error("UTM Campaign을 입력해주세요.")
            return
        
        # 사용자 지정 속성 모드에서 속성이 입력되지 않은 경우
        if property_query_mode == "사용자 지정 속성" and not custom_properties:
            st.error("사용자 지정 속성을 입력해주세요.")
            return
        
        # 사용자 입력 UTM 파라미터로 시나리오 생성
        utm_params = {
            'source': utm_source,
            'medium': utm_medium, 
            'campaign': utm_campaign
        }
        
        # 선택사항 파라미터 추가
        if utm_term:
            utm_params['term'] = utm_term
        if utm_content:
            utm_params['content'] = utm_content
            
        scenarios = [{
            'name': f'UTM 테스트 ({utm_source}/{utm_medium}/{utm_campaign})',
            'source': utm_source,
            'medium': utm_medium,
            'campaign': utm_campaign,
            'description': f'{utm_source} {utm_medium}로 {utm_campaign} 캠페인 방문'
        }]
        
        # term과 content가 있으면 추가
        if utm_term:
            scenarios[0]['term'] = utm_term
        if utm_content:
            scenarios[0]['content'] = utm_content
        
        # 분석 실행
        run_utm_analysis(user_id, base_url, scenarios, property_query_mode, custom_properties, st.session_state.mixpanel_settings)
    
    # 도움말
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 도움말")
    st.sidebar.markdown("""
    **🔑 Mixpanel API 설정:**
    - **Service Account**: Mixpanel 서비스 계정명
    - **Service Password**: 서비스 계정 비밀번호
    - **Project ID**: Mixpanel 프로젝트 ID (숫자)
    
    **🎯 UTM 테스트 방법:**
    
    **1. 기본 설정:**
    - Mixpanel API 설정 완료
    - 웹사이트 URL과 User ID 입력
    - UTM 파라미터 설정 (Source, Medium, Campaign 필수)
    
    **2. 속성 조회:**
    - 빈 값: 기본 UTM 속성만 조회
    - 입력 시: 지정한 속성만 조회
    
    **3. 테스트 과정:**
    - 접속 전 사용자 속성 조회
    - 브라우저에서 UTM URL 자동 열기
    - 3분 대기 후 접속 후 속성 조회
    - 접속 전후 속성 변화 분석
    
    **📋 UTM 파라미터 설명:**
    - **Source**: 트래픽 출처 (google, facebook, email 등)
    - **Medium**: 마케팅 매체 (cpc, banner, social 등)
    - **Campaign**: 캠페인명 (brand_search, summer_sale 등)
    - **Term**: 키워드 (선택사항)
    - **Content**: 광고 내용 (선택사항)
    
    **🔍 결과 확인:**
    - 접속 전후 UTM 속성 비교
    - 새로운 UTM 속성 추가 여부 확인
    - 속성 값 변경 사항 분석
    """)


if __name__ == "__main__":
    main()