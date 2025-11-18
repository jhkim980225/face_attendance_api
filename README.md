# Face Attendance API

[![FastAPI](https://img.shields.io/badge/FastAPI-1.0+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?logo=opencv)](https://opencv.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com)

얼굴 인식 기반 실시간 출퇴근 관리 시스템입니다. 서버 카메라 스트리밍(MODE_A)과 이미지 업로드(MODE_B) 두 가지 방식을 지원합니다.

## ✨ 주요 기능

- **얼굴 인식**: OpenCV + HOG 기반 고정밀 얼굴 감지 및 인식
- **MJPEG 스트리밍**: 실시간 카메라 피드 (20 FPS)
- **듀얼 모드**: 서버 카메라(JSON) / 이미지 업로드(Multipart)
- **타원 가이드**: 정확한 포지션 가이드로 오인식 방지
- **출퇴근 관리**: IN/OUT 자동 기록, 신뢰도(distance) 추적
- **자동 ID 생성**: EMP001, EMP002... 자동 증가

## 📁 프로젝트 구조

```
face_attendance_api/
├── app/
│   ├── main.py                    # FastAPI 진입점
│   ├── api/v1/                    # API 라우트
│   │   ├── routes_health.py       # 헬스체크
│   │   ├── routes_stream.py       # MJPEG 스트리밍
│   │   ├── routes_capture.py      # 프레임 캡처
│   │   ├── routes_identify.py     # 얼굴 인식
│   │   ├── routes_enroll.py       # 사용자 등록
│   │   └── routes_attendance.py   # 출퇴근 로그
│   ├── core/                      # 핵심 설정
│   │   ├── config.py              # 환경 설정
│   │   ├── cors.py                # CORS 설정
│   │   └── logging.py             # 로깅 설정
│   ├── db/                        # 데이터베이스
│   │   ├── base.py                # DB 세션
│   │   └── models.py              # SQLAlchemy 모델
│   ├── services/                  # 비즈니스 로직
│   │   ├── camera_worker.py       # 카메라 백그라운드 워커
│   │   ├── face_service.py        # 얼굴 처리
│   │   ├── inference.py           # 인식 추론
│   │   └── attendance_service.py  # 출퇴근 기록
│   ├── schemas/                   # Pydantic 스키마
│   ├── utils/                     # 유틸리티
│   └── static/
│       ├── images/                # 썸네일 저장
│       └── encodings/             # 임베딩 .npy 파일
├── logs/                          # 로그 파일
├── .env                           # 환경 변수
├── requirements.txt
├── migrate_schema.py
├── reset_users.py
└── README.md
```

## 🔧 주요 함수 레퍼런스

### face_service.py - 얼굴 처리 핵심 함수

#### `detect_single_face(bgr_image: np.ndarray)`
- **기능**: 이미지에서 얼굴 감지
- **방식**: DeepFace SSD → Haar Cascade (fallback)
- **반환**: `(bbox, face_image)` 튜플 또는 None
- **특징**: 
  - 이미지 품질 사전 체크 (밝기, 대비)
  - 여러 얼굴 감지 시 가장 큰 얼굴 선택
  - 얼굴 영역이 너무 어두우면 거부

#### `embed(face_bgr: np.ndarray)`
- **기능**: 얼굴 이미지를 벡터로 변환 (임베딩 생성)
- **방식**: DeepFace Facenet (128D) → HOG 기반 fallback (512D)
- **반환**: numpy 배열 (임베딩 벡터) 또는 None
- **특징**:
  - Facenet 모델 사용 시 LFW 99.65% 정확도
  - Fallback: 히스토그램 평활화 + HOG 특징 추출 + L2 정규화

#### `l2_distance(embedding1, embedding2)`
- **기능**: 두 임베딩 간 유클리드 거리 계산
- **반환**: float (거리 값, 낮을수록 유사)
- **용도**: 얼굴 유사도 측정

#### `save_embedding(employee_id, embedding)`
- **기능**: 임베딩 벡터를 .npy 파일로 저장
- **저장 위치**: `app/static/encodings/{employee_id}_{timestamp}.npy`
- **반환**: 파일 경로 또는 None

#### `load_embedding(filepath)`
- **기능**: .npy 파일에서 임베딩 로드
- **반환**: numpy 배열 또는 None

#### `save_thumbnail(bgr_image, employee_id)`
- **기능**: 썸네일 이미지 저장 (300x300)
- **저장 위치**: `app/static/images/{employee_id}_thumb_{timestamp}.jpg`
- **반환**: 파일 경로 또는 None

---

### inference.py - 인식 및 등록 로직

#### `identify_from_camera(db: Session)`
- **기능**: MODE_A - 서버 카메라에서 실시간 얼굴 인식
- **프로세스**:
  1. 카메라 워커에서 최신 프레임 가져오기
  2. `identify_from_image()` 호출
- **반환**: `IdentifyResult` 객체

#### `identify_from_upload(db: Session, file_bytes: bytes)`
- **기능**: MODE_B - 업로드된 이미지에서 얼굴 인식
- **프로세스**:
  1. 이미지 디코딩 및 크기 검증
  2. `identify_from_image()` 호출
- **반환**: `IdentifyResult` 객체

#### `identify_from_image(db: Session, image: np.ndarray)`
- **기능**: 이미지에서 얼굴 인식 (공통 로직)
- **프로세스**:
  1. 얼굴 감지
  2. 타원 가이드 영역 검증 (현재 비활성화)
  3. 임베딩 생성
  4. DB의 모든 사용자와 거리 비교
  5. 최소 거리가 TOLERANCE 이하면 인증 성공
- **반환**: `IdentifyResult` (success, employee_id, name, distance, message)

#### `find_best_match(db: Session, embedding: np.ndarray)`
- **기능**: DB의 모든 등록 임베딩과 비교하여 가장 유사한 사용자 찾기
- **프로세스**:
  1. DB에서 임베딩 파일 경로가 있는 모든 사용자 조회
  2. 각 임베딩 파일 로드
  3. L2 거리 계산
  4. 최소 거리 사용자 반환
- **반환**: `(employee_id, name, distance)` 튜플 또는 None

#### `generate_employee_id(db: Session)`
- **기능**: 자동 직원 ID 생성 (EMP001, EMP002, ...)
- **로직**: DB에서 마지막 EMP 번호 조회 후 +1
- **반환**: 새 employee_id (str)

#### `enroll_user_with_image(db: Session, name: str, file_bytes: bytes)`
- **기능**: 이미지와 함께 신규 사용자 등록
- **프로세스**:
  1. employee_id 자동 생성
  2. 이미지 디코딩 및 검증
  3. 썸네일 저장
  4. 얼굴 감지
  5. 임베딩 생성 및 저장
  6. DB에 사용자 레코드 생성
- **반환**: `EnrollResult` (success, employee_id, message)

---

### camera_worker.py - 카메라 관리

#### `CameraWorker` 클래스
백그라운드 스레드에서 카메라를 지속적으로 캡처하는 워커

#### `start()`
- **기능**: 카메라 초기화 및 캡처 스레드 시작
- **설정**: 640x480 해상도, 설정된 FPS
- **반환**: bool (성공 여부)

#### `stop()`
- **기능**: 카메라 캡처 중지 및 리소스 해제
- **동작**: 스레드 종료, 카메라 릴리즈

#### `is_alive()`
- **기능**: 카메라 워커 정상 동작 확인
- **반환**: bool

#### `get_latest_frame()`
- **기능**: 최신 캡처된 프레임 반환
- **동작**: thread-safe lock으로 프레임 복사
- **반환**: numpy 배열 (BGR 이미지) 또는 None

#### `_capture_loop()`
- **기능**: 백그라운드에서 실행되는 캡처 루프
- **동작**: 
  - 목표 FPS에 맞춰 지속적으로 프레임 캡처
  - `latest_frame`에 최신 프레임 업데이트
  - 에러 발생 시 자동 재시도

---

### attendance_service.py - 출퇴근 기록 관리

#### `check_already_checked_in_today(db: Session, employee_id: str)`
- **기능**: 오늘 이미 출근했는지 확인
- **조회**: 오늘 날짜의 IN 타입 기록
- **반환**: bool

#### `check_already_checked_out_today(db: Session, employee_id: str)`
- **기능**: 오늘 이미 퇴근했는지 확인
- **조회**: 오늘 날짜의 OUT 타입 기록
- **반환**: bool

#### `record_success(db, employee_id, type, device_id, distance, image_ref, ts_client)`
- **기능**: 성공한 출퇴근 기록 저장
- **파라미터**:
  - `employee_id`: 직원 ID
  - `type`: 'IN' 또는 'OUT'
  - `distance`: 얼굴 인식 거리 (신뢰도)
  - `device_id`: 디바이스 식별자 (선택)
  - `image_ref`: 이미지 파일 경로 (선택)
  - `ts_client`: 클라이언트 타임스탬프 (선택)
- **반환**: bool

#### `record_unknown(db, type, device_id, distance, image_ref, ts_client)`
- **기능**: 미등록 얼굴 시도 기록 (감사 추적용)
- **저장**: employee_id='UNKNOWN'으로 저장
- **반환**: bool

#### `record_fail(db, reason, type, device_id, ts_client)`
- **기능**: 실패한 인증 시도 기록
- **저장**: employee_id='FAILED_{reason}'으로 저장
- **사유**: no_face, multi_face, bad_quality 등
- **반환**: bool

#### `get_recent_attendance(db: Session, employee_id: str, limit: int)`
- **기능**: 특정 직원의 최근 출퇴근 기록 조회
- **정렬**: 최신순 (ts_server DESC)
- **반환**: Attendance 객체 리스트

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Python 3.9+
- MySQL 8.0+
- (선택) 웹캠 (MODE_A 사용 시)

### 2. 설치

```bash
# 가상환경 생성
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 설정

`.env` 파일 생성:

```env
# MySQL 설정
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=attendance_db
MYSQL_POOL_SIZE=5
MYSQL_MAX_OVERFLOW=10

# 얼굴 인식 설정
TOLERANCE=0.45

# 저장 경로
IMAGE_DIR=app/static/images
ENCODING_DIR=app/static/encodings

# 카메라 설정 (MODE_A)
STREAM_FPS=20
CAMERA_DEVICE_INDEX=0
```

### 4. 데이터베이스 생성

```sql
CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

테이블은 앱 시작 시 자동 생성됩니다.

### 5. 서버 실행

```bash
# 개발 모드
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# 운영 모드
uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4
```

- API 서버: http://localhost:5000
- API 문서: http://localhost:5000/docs

## 📡 API 엔드포인트

### 1. 헬스 체크
```
GET /health
```

### 2. MJPEG 스트리밍 (MODE_A)
```
GET /stream.mjpeg
```
실시간 비디오 스트림 (타원 가이드, 얼굴 감지 박스 포함)

### 3. 얼굴 인식 (출퇴근)

**MODE_A (서버 카메라)**
```bash
POST /identify
Content-Type: application/json

{
  "type": "IN",
  "device_id": "KIOSK_01",
  "ts_client": "2025-01-01T09:00:00Z"
}
```

**MODE_B (이미지 업로드)**
```bash
POST /identify
Content-Type: multipart/form-data

image: [파일]
type: "IN"
device_id: "KIOSK_01"
ts_client: "2025-01-01T09:00:00Z"
```

**성공 응답**
```json
{
  "success": true,
  "employee_id": "EMP001",
  "name": "홍길동",
  "distance": 0.35,
  "decided_threshold": 0.45,
  "message": "인증 성공"
}
```

**실패 응답**
```json
{
  "success": false,
  "message": "얼굴을 인식할 수 없습니다",
  "reason": "unknown",
  "min_distance": 0.52
}
```

**실패 사유 코드:**
- `no_face`: 얼굴 미감지
- `multi_face`: 여러 얼굴 감지
- `out_of_area`: 타원 영역 밖
- `bad_quality`: 이미지 품질 불량
- `unknown`: 미등록 얼굴
- `camera_unavailable`: 카메라 사용 불가
- `internal_error`: 서버 오류

### 4. 사용자 등록

```bash
POST /enroll
Content-Type: multipart/form-data

image: [파일]
name: "홍길동"
```

**응답**
```json
{
  "success": true,
  "employee_id": "EMP003",
  "message": "등록 완료"
}
```

### 5. 출퇴근 기록 조회

```
GET /attendance?employee_id=EMP001&limit=10
```

## 🗄️ 데이터베이스 스키마

### users 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT | Primary Key |
| employee_id | VARCHAR(50) | 직원 ID (UNIQUE) |
| name | VARCHAR(100) | 이름 |
| profile_image | VARCHAR(255) | 임베딩 파일 경로 (.npy) |
| created_at | DATETIME | 생성일시 |

### attendance 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INT | Primary Key |
| employee_id | VARCHAR(50) | 직원 ID (FK) |
| type | VARCHAR(10) | 'IN' 또는 'OUT' |
| device_id | VARCHAR(50) | 디바이스 ID |
| distance | FLOAT | 인식 거리 (낮을수록 유사) |
| ts_server | DATETIME | 서버 타임스탬프 |
| ts_client | DATETIME | 클라이언트 타임스탬프 |
| image_ref | VARCHAR(255) | 이미지 참조 |

## ⚙️ 주요 설정

### TOLERANCE (얼굴 인식 임계값)

| 값 | 설명 | 추천 상황 |
|----|------|-----------|
| 0.25-0.30 | 매우 엄격 | 보안 중요 환경 |
| 0.30-0.40 | 엄격 (권장) | 일반 출퇴근 관리 |
| 0.40-0.50 | 관대 | 편의성 우선 |
| 0.50+ | 매우 관대 | 비권장 (오인식 위험) |

- 값을 낮추면: 본인 인식 실패 ↑, 타인 오인식 ↓
- 값을 높이면: 본인 인식 실패 ↓, 타인 오인식 ↑

### 카메라 설정
- `CAMERA_DEVICE_INDEX`: 카메라 장치 인덱스 (기본 0)
- `STREAM_FPS`: 스트리밍 프레임 레이트 (기본 20)

## 🛠 운영 환경 권장사항

### 1. CORS 설정
`app/core/cors.py`에서 운영 도메인 화이트리스트 추가:
```python
PROD_CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com"
]
```

### 2. HTTPS 사용
Nginx를 리버스 프록시로 사용:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 5000
```

### 3. 로그 관리
로그 파일은 `logs/` 디렉토리에 자동 저장:
- `logs/app.log`: 일반 로그 (7일 보관)
- `logs/error.log`: 오류 로그 (30일 보관)

### 4. 보안
- `.env` 파일을 git에 커밋하지 마세요
- API Key 또는 JWT 인증 추가 권장
- 얼굴 임베딩 파일 암호화 고려
- 정기적인 데이터베이스 백업

## 🐛 문제 해결

### 카메라가 인식되지 않음
```bash
# 다른 카메라 인덱스 시도
CAMERA_DEVICE_INDEX=1

# 카메라 없이도 MODE_B는 정상 작동합니다
```

### MySQL 연결 오류
```bash
# MySQL 서비스 확인
sudo systemctl status mysql  # Linux
# Windows: services.msc에서 MySQL 확인

# 접속 정보 확인
mysql -u root -p -e "SELECT 1"
```

### 인식률이 낮음 (본인이 인식 안 됨)
```env
# TOLERANCE 완화
TOLERANCE=0.45  # 0.35 → 0.45

# 재등록 시 유의사항:
# - 정면 얼굴
# - 밝은 조명
# - 타원 가이드 안에 얼굴 위치
```

### 오인식 발생 (다른 사람 인식됨)
```env
# TOLERANCE 강화
TOLERANCE=0.30  # 0.40 → 0.30
```

### face_recognition 설치 실패 (Windows)
1. Visual Studio Build Tools 설치
2. CMake 설치: `choco install cmake`
3. dlib 수동 설치: `pip install dlib`
4. 설치 실패 시, 시스템은 대체 임베딩 방식으로 자동 전환

## 🔧 유틸리티 스크립트

### 사용자 데이터 초기화
```bash
python reset_users.py
```
모든 사용자 삭제 (출퇴근 기록은 유지)

### 임베딩 경로 수정
```bash
python fix_embedding_path.py
```
`profile_image` 컬럼을 임베딩 파일 경로로 업데이트

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues에 등록해주세요.

---

**Made with ❤️ for modern attendance management**

*Last Updated: 2025-11-18*
