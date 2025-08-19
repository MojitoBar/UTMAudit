"""
Mixpanel API 클라이언트
"""
import requests
import base64
import json
from typing import Dict, List, Any, Optional
from src.utils.config import settings


class MixpanelAPIClient:
    """Mixpanel API 클라이언트"""
    
    def __init__(self):
        self.project_id = settings.mixpanel_project_id
        self.service_account = settings.mixpanel_service_account
        self.service_password = settings.mixpanel_service_password
        self.base_url = "https://mixpanel.com/api"
        
        print(f"🔧 Mixpanel API 클라이언트 초기화")
        print(f"📊 Project ID: {self.project_id}")
        print(f"👤 Service Account: {self.service_account}")
        print(f"🔑 Service Password: {'*' * len(self.service_password) if self.service_password else 'None'}")
        
        # 인증 헤더 생성
        credentials = f"{self.service_account}:{self.service_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
        
        print(f"🔐 인증 헤더 생성 완료")
    
    def get_user_profile(self, distinct_id: str, output_properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """사용자 프로필 조회"""
        url = f"{self.base_url}/query/engage"
        
        # 기본 UTM 속성들
        default_properties = [
            "initial_utm_source",
            "initial_utm_medium", 
            "initial_utm_campaign",
            "initial_utm_term",
            "initial_utm_content",
            "initial_utm_id",
            "initial_utm_source_platform",
            "initial_utm_campaign_id",
            "initial_utm_creative_format",
            "initial_utm_marketing_tactic",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "utm_id",
            "utm_source_platform",
            "utm_campaign_id",
            "utm_creative_format",
            "utm_marketing_tactic"
        ]
        
        if output_properties:
            properties = output_properties
        else:
            properties = default_properties
        
        # 방법 1: distinct_id 사용
        data = {
            'project_id': self.project_id,
            'distinct_id': distinct_id,
            'output_properties': json.dumps(properties)  # JSON 문자열로 변환
        }
        
        try:
            print(f"🔍 Mixpanel API 요청 시작: {distinct_id}")
            print(f"📡 요청 URL: {url}")
            print(f"📦 요청 데이터: {data}")
            
            # curl과 동일한 방식으로 form data 전송
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📦 응답 데이터: {json.dumps(result, indent=2)}")
            
            # 디버깅 정보 추가
            debug_info = {
                'request_data': data,
                'response_status': response.status_code,
                'response_headers': dict(response.headers),
                'response_body': result
            }
            
            if result.get('results'):
                user_profile = result['results'][0]
                print(f"🔍 원본 사용자 프로필: {json.dumps(user_profile, indent=2)}")
                
                # Mixpanel API 응답에서 가능한 필드명들 확인
                distinct_id = user_profile.get('distinct_id') or user_profile.get('$distinct_id')
                properties = user_profile.get('properties') or user_profile.get('$properties', {})
                
                print(f"✅ 사용자 프로필 찾음: {distinct_id}")
                print(f"📋 프로필 속성: {json.dumps(properties, indent=2)}")
                return {
                    'success': True,
                    'user_profile': user_profile,
                    'properties': properties,
                    'distinct_id': distinct_id,
                    'debug_info': debug_info
                }
            else:
                print(f"❌ 사용자 프로필을 찾을 수 없음. distinct_ids 방법 시도...")
                # 방법 2: distinct_ids 배열 사용
                data_alt = {
                    'project_id': self.project_id,
                    'distinct_ids': json.dumps([distinct_id]),  # JSON 문자열로 변환
                    'output_properties': json.dumps(properties)  # JSON 문자열로 변환
                }
                
                try:
                    print(f"📡 distinct_ids 요청 데이터: {data_alt}")
                    response_alt = requests.post(url, headers=self.headers, data=data_alt)
                    response_alt.raise_for_status()
                    result_alt = response_alt.json()
                    
                    print(f"📊 distinct_ids 응답 상태: {response_alt.status_code}")
                    print(f"📦 distinct_ids 응답 데이터: {json.dumps(result_alt, indent=2)}")
                    
                    debug_info_alt = {
                        'request_data': data_alt,
                        'response_status': response_alt.status_code,
                        'response_headers': dict(response_alt.headers),
                        'response_body': result_alt
                    }
                    
                    if result_alt.get('results'):
                        user_profile_alt = result_alt['results'][0]
                        # Mixpanel API 응답에서 가능한 필드명들 확인
                        distinct_id_alt = user_profile_alt.get('distinct_id') or user_profile_alt.get('$distinct_id')
                        properties_alt = user_profile_alt.get('properties') or user_profile_alt.get('$properties', {})
                        
                        print(f"✅ distinct_ids로 사용자 프로필 찾음: {distinct_id_alt}")
                        return {
                            'success': True,
                            'user_profile': user_profile_alt,
                            'properties': properties_alt,
                            'distinct_id': distinct_id_alt,
                            'debug_info': debug_info_alt,
                            'method': 'distinct_ids'
                        }
                    else:
                        print(f"❌ distinct_ids 방법도 실패")
                        return {
                            'success': False,
                            'error': '사용자 프로필을 찾을 수 없습니다. (distinct_id와 distinct_ids 모두 시도)',
                            'distinct_id': distinct_id,
                            'debug_info': {
                                'method1': debug_info,
                                'method2': debug_info_alt
                            }
                        }
                        
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'사용자 프로필을 찾을 수 없습니다. (대체 방법 실패: {str(e)})',
                        'distinct_id': distinct_id,
                        'debug_info': debug_info
                    }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {str(e)}")
            return {
                'success': False,
                'error': f'API 요청 실패: {str(e)}',
                'distinct_id': distinct_id
            }
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {str(e)}")
            return {
                'success': False,
                'error': f'JSON 파싱 실패: {str(e)}',
                'distinct_id': distinct_id
            }
    
    def query_users(self, where: str, output_properties: Optional[List[str]] = None, page_size: int = 100) -> Dict[str, Any]:
        """사용자 쿼리 (페이지네이션 지원)"""
        url = f"{self.base_url}/query/engage"
        
        # 기본 UTM 속성들
        default_properties = [
            "initial_utm_source",
            "initial_utm_medium", 
            "initial_utm_campaign",
            "initial_utm_term",
            "initial_utm_content",
            "initial_utm_id",
            "initial_utm_source_platform",
            "initial_utm_campaign_id",
            "initial_utm_creative_format",
            "initial_utm_marketing_tactic",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "utm_id",
            "utm_source_platform",
            "utm_campaign_id",
            "utm_creative_format",
            "utm_marketing_tactic"
        ]
        
        if output_properties:
            properties = output_properties
        else:
            properties = default_properties
        
        data = {
            'project_id': self.project_id,
            'where': where,
            'output_properties': json.dumps(properties),  # JSON 문자열로 변환
            'page_size': page_size
        }
        
        try:
            # curl과 동일한 방식으로 form data 전송
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'results': result.get('results', []),
                'page': result.get('page', 0),
                'page_size': result.get('page_size', page_size),
                'session_id': result.get('session_id'),
                'total_count': len(result.get('results', []))
            }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'API 요청 실패: {str(e)}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'JSON 파싱 실패: {str(e)}'
            }
    
    def get_all_users_with_utm(self, page_size: int = 100) -> Dict[str, Any]:
        """UTM 속성이 있는 모든 사용자 조회"""
        # UTM 속성이 있는 사용자 필터링
        where_expression = 'defined(initial_utm_source) or defined(utm_source)'
        return self.query_users(where_expression, page_size=page_size)
    
    def get_user_profile_all_properties(self, distinct_id: str) -> Dict[str, Any]:
        """사용자 프로필 조회 (모든 속성)"""
        url = f"{self.base_url}/query/engage"
        
        # 모든 속성을 조회하기 위해 output_properties를 지정하지 않음
        data = {
            'project_id': self.project_id,
            'distinct_ids': json.dumps([distinct_id])  # JSON 문자열로 변환
        }
        
        try:
            print(f"🔍 모든 속성 조회 시작: {distinct_id}")
            print(f"📡 요청 URL: {url}")
            print(f"📦 요청 데이터: {data}")
            
            # curl과 동일한 방식으로 form data 전송
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"📊 응답 상태: {response.status_code}")
            print(f"📦 응답 데이터: {json.dumps(result, indent=2)}")
            
            if result.get('results'):
                user_profile = result['results'][0]
                # Mixpanel API 응답에서 가능한 필드명들 확인
                distinct_id = user_profile.get('distinct_id') or user_profile.get('$distinct_id')
                properties = user_profile.get('properties') or user_profile.get('$properties', {})
                
                print(f"✅ 모든 속성 조회 성공. 속성 수: {len(properties)}")
                print(f"📋 모든 속성: {json.dumps(properties, indent=2)}")
                
                return {
                    'success': True,
                    'user_profile': user_profile,
                    'properties': properties,
                    'distinct_id': distinct_id,
                    'debug_info': {
                        'request_data': data,
                        'response_status': response.status_code,
                        'response_body': result
                    }
                }
            else:
                print(f"❌ 모든 속성 조회 실패")
                return {
                    'success': False,
                    'error': '사용자 프로필을 찾을 수 없습니다.',
                    'distinct_id': distinct_id
                }
                
        except Exception as e:
            print(f"❌ 모든 속성 조회 중 오류: {str(e)}")
            return {
                'success': False,
                'error': f'모든 속성 조회 중 오류: {str(e)}',
                'distinct_id': distinct_id
            }
