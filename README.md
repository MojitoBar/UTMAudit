# UTM Audit Tool

Mixpanel UTM 파라미터의 First Touch vs Last Touch 분석 도구

## 🚀 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# Mixpanel API 설정 (필수)
MIXPANEL_SERVICE_ACCOUNT=your_service_account_here
MIXPANEL_SERVICE_PASSWORD=your_service_password_here
MIXPANEL_PROJECT_ID=your_project_id_here

# 웹사이트 설정
BASE_URL=https://your-website.com

# 브라우저 설정
HEADLESS=true
BROWSER_TYPE=chromium

# 감사 설정
TEST_TIMEOUT=30
MAX_RETRIES=3

# 로깅 설정
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Mixpanel API 정보 확인
1. Mixpanel 프로젝트 설정 → Service Accounts
2. Service Account 생성 또는 기존 계정 사용
3. Username과 Password를 `.env` 파일에 입력
4. Project ID 확인 (프로젝트 설정에서 확인 가능)

## 🎯 사용 방법

### Streamlit 앱 실행
```bash
streamlit run streamlit_app.py
```

### 사용법
1. User ID 입력 (분석할 사용자의 distinct_id)
2. "UTM 테스트 시작" 버튼 클릭
3. First Touch vs Last Touch 분석 결과 확인

## 📊 기능

- **사용자 프로퍼티 조회**: Mixpanel API를 통한 직접 조회
- **First Touch 분석**: `initial_utm_*` 속성 추적
- **Last Touch 분석**: `utm_*` 속성 추적
- **UTM 시나리오 테스트**: 순차적 UTM 방문 시뮬레이션
- **시각적 결과**: First Touch vs Last Touch 변화 분석

## 🔧 문제 해결

### "invalid literal for int()" 오류
- `.env` 파일의 `MIXPANEL_PROJECT_ID`가 숫자로 설정되었는지 확인
- 예: `MIXPANEL_PROJECT_ID=123456` (문자열이 아닌 숫자)

### "사용자 프로퍼티를 찾을 수 없습니다" 오류
- User ID가 올바른 distinct_id인지 확인
- Mixpanel 프로젝트에 해당 사용자가 존재하는지 확인

## 📁 프로젝트 구조

```
UTMAudit/
├── src/
│   ├── browser/          # 브라우저 자동화
│   ├── mixpanel/         # Mixpanel API 클라이언트
│   ├── utm/             # UTM 생성기
│   └── utils/           # 유틸리티
├── tests/               # 테스트
├── streamlit_app.py     # 메인 앱
└── requirements.txt     # 의존성
```
