# 얼굴 인식 출퇴근 관리 시스템# Face Attendance API

각 사용자는 1번만 등록 (중복 등록 X)

재등록이 필요하면:

reset_users.py 실행 → 전체 초기화
또는 특정 사용자만 DB에서 삭제
등록 시 좋은 조건:

정면 얼굴
밝은 조명
타원 가이드 안에 얼굴 위치



[![FastAPI](https://img.shields.io/badge/FastAPI-1.0+-009688?logo=fastapi)](https://fastapi.tiangolo.com)FastAPI 기반 얼굴 인식 출퇴근 관리 시스템 백엔드

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://www.python.org)

[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?logo=opencv)](https://opencv.org)## 📋 개요

[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com)

이 프로젝트는 얼굴 인식을 통한 출퇴근 관리 시스템의 백엔드 API입니다. 서버 카메라를 사용한 실시간 스트리밍(MODE_A)과 이미지 업로드(MODE_B) 두 가지 방식을 모두 지원합니다.

실시간 얼굴 인식 기반 출퇴근 관리 시스템입니다. 서버 카메라를 통한 MJPEG 스트리밍과 이미지 업로드 방식을 모두 지원합니다.

### 주요 기능

## 📋 목차

- ✅ **얼굴 인식**: face_recognition 라이브러리를 사용한 고정밀 얼굴 인식

- [주요 기능](#주요-기능)- 📹 **MJPEG 스트리밍**: 서버 카메라의 실시간 비디오 스트림 제공

- [기술 스택](#기술-스택)- 🎯 **듀얼 모드 지원**: 

- [시스템 아키텍처](#시스템-아키텍처)  - MODE_A: 서버 카메라 사용 (JSON 요청)

- [설치 및 실행](#설치-및-실행)  - MODE_B: 이미지 업로드 (Multipart 요청)

- [API 명세](#api-명세)- 💾 **데이터베이스**: MySQL 기반 사용자 및 출퇴근 기록 관리

- [프로젝트 구조](#프로젝트-구조)- 🔐 **임베딩 저장**: 얼굴 임베딩 벡터를 .npy 파일로 저장

- [환경 변수](#환경-변수)- 📊 **출퇴근 로그**: 상세한 출퇴근 기록 및 실패 사유 추적

- [데이터베이스](#데이터베이스)

- [개발 가이드](#개발-가이드)---

- [트러블슈팅](#트러블슈팅)

## 📁 프로젝트 구조

## 🎯 주요 기능

```

### 얼굴 인식 시스템face_attendance_api/

- **실시간 얼굴 감지**: OpenCV Haar Cascade 기반 고속 감지├─ app/

- **타원 가이드 영역**: 정확한 포지션 가이드 제공 (오인식 방지)│  ├─ main.py                    # FastAPI 애플리케이션 진입점

- **HOG 특징 기반 임베딩**: 조명 변화에 강한 얼굴 특징 추출│  ├─ api/

- **L2 Distance 매칭**: 빠르고 정확한 유사도 측정│  │  └─ v1/

- **자동 품질 검증**: 얼굴 크기, 위치 자동 체크│  │     ├─ routes_health.py     # 헬스체크 엔드포인트

│  │     ├─ routes_stream.py     # MJPEG 스트리밍

### 듀얼 운영 모드│  │     ├─ routes_identify.py   # 얼굴 인식

#### MODE_A (서버 카메라)│  │     ├─ routes_enroll.py     # 사용자 등록

- MJPEG 스트리밍 제공│  │     └─ routes_attendance.py # 출퇴근 로그 (선택)

- 실시간 얼굴 감지 박스 오버레이│  ├─ core/

  - 🟢 초록색: 인식 준비 완료│  │  ├─ config.py               # 환경 설정

  - 🟡 노란색: 거리 조정 필요│  │  ├─ cors.py                 # CORS 설정

  - 🟠 주황색: 여러 얼굴 감지│  │  └─ logging.py              # 로깅 설정

- 동적 가이드 메시지 표시│  ├─ db/

│  │  ├─ base.py                 # DB 연결 및 세션

#### MODE_B (이미지 업로드)│  │  └─ models.py               # SQLAlchemy 모델

- Multipart 파일 업로드 지원│  ├─ services/

- Base64 인코딩 이미지 지원│  │  ├─ camera_worker.py        # 카메라 백그라운드 워커

- 모바일/웹 클라이언트 친화적│  │  ├─ face_service.py         # 얼굴 검출/임베딩

│  │  ├─ inference.py            # 고수준 추론 로직

### 출퇴근 관리│  │  └─ attendance_service.py   # 출퇴근 기록

- 출근(IN) / 퇴근(OUT) 자동 기록│  ├─ schemas/

- 인증 거리(distance) 저장으로 신뢰도 추적│  │  └─ dto.py                  # Pydantic 스키마

- 미등록 사용자 시도 기록│  ├─ utils/

- 타임스탬프 이중 기록 (서버/클라이언트)│  │  ├─ env.py                  # 환경변수 유틸

│  │  ├─ image_io.py             # 이미지 처리

### 사용자 관리│  │  └─ paths.py                # 경로 관리

- 자동 직원 ID 생성 (EMP001, EMP002, ...)│  └─ static/

- 얼굴 임베딩 자동 저장 (.npy 파일)│     ├─ images/                 # 썸네일 저장

- 타원 영역 검증으로 품질 보장│     └─ encodings/              # 임베딩 .npy 파일

├─ .env                          # 환경 변수

## 🛠 기술 스택├─ requirements.txt              # 의존성

└─ README.md

### Backend Framework```

- **FastAPI 1.0+** - 현대적인 고성능 비동기 웹 프레임워크

  - 자동 API 문서 생성 (Swagger/ReDoc)---

  - Type hints 기반 자동 검증

  - 비동기 I/O 지원## 🚀 설치 및 실행

- **Uvicorn** - ASGI 서버 (운영 환경 Worker 모드 지원)

- **Pydantic** - 데이터 검증 및 설정 관리### 1. 사전 요구사항



### Computer Vision & ML- Python 3.8 이상

- **OpenCV 4.8+** - 이미지 처리 및 얼굴 감지- MySQL 8.0 이상

  - Haar Cascade Classifier (빠른 실시간 감지)- (선택) 웹캠 (MODE_A 사용 시)

  - HOG (Histogram of Oriented Gradients) 특징 추출

- **NumPy** - 고성능 수치 연산 및 배열 처리### 2. 의존성 설치

- **face_recognition** (선택) - dlib 기반 고정밀 인식 (설치 실패 시 fallback)

```powershell

### Database & ORMpip install -r requirements.txt

- **MySQL 8.0+** - 관계형 데이터베이스```

  - InnoDB 엔진 (트랜잭션 지원)

  - 유니코드 완전 지원 (utf8mb4)**주요 의존성:**

- **SQLAlchemy 2.0** - Python SQL 툴킷 및 ORM- fastapi

  - Connection Pool 관리- uvicorn[standard]

  - Migration-free 개발 (자동 테이블 생성)- SQLAlchemy

- **PyMySQL** - Pure Python MySQL 클라이언트- pymysql

- opencv-python

### Infrastructure- numpy

- **Loguru** - 구조화된 로깅 시스템- face_recognition (설치 실패 시 대체 임베딩 방식 사용)

  - 자동 로그 로테이션- loguru

  - 색상 코드 지원 (개발 환경)- python-dotenv

  - Exception traceback 자동 캡처

- **python-dotenv** - 환경 변수 관리### 3. 환경 설정

- **aiofiles** - 비동기 파일 I/O

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 설정하세요:

## 🏗 시스템 아키텍처

```env

```# MySQL 설정

┌─────────────────────────────────────────────────────────────────┐MYSQL_HOST=127.0.0.1

│                        Client Layer                              │MYSQL_PORT=3306

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │MYSQL_USER=root

│  │   Web UI     │  │  Mobile App  │  │  Kiosk       │          │MYSQL_PASSWORD=zzjhkim12!

│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │MYSQL_DB=attendance_db

│         │                  │                  │                   │MYSQL_POOL_SIZE=5

│         └──────────────────┴──────────────────┘                   │MYSQL_MAX_OVERFLOW=10

│                            │                                      │

│                     HTTPS / REST API                              │# 얼굴 인식 설정

│                            │                                      │TOLERANCE=0.45

└────────────────────────────┼─────────────────────────────────────┘

                             │# 저장 경로

┌────────────────────────────┼─────────────────────────────────────┐IMAGE_DIR=app/static/images

│                        API Layer                                 │ENCODING_DIR=app/static/encodings

│                     FastAPI + Uvicorn                            │

│  ┌──────────────────────────────────────────────────────────┐   │# 카메라 설정 (MODE_A)

│  │  Routes (Endpoints)                                      │   │STREAM_FPS=20

│  │  ├─ /health           : Health check                     │   │CAMERA_DEVICE_INDEX=0

│  │  ├─ /stream.mjpeg     : MJPEG video stream              │   │```

│  │  ├─ /capture          : Snapshot capture                │   │

│  │  ├─ /identify         : Face recognition                │   │### 4. 데이터베이스 생성

│  │  ├─ /enroll           : User registration               │   │

│  │  └─ /attendance       : Log retrieval                   │   │MySQL에 접속하여 데이터베이스를 생성하세요:

│  └──────────────────────────────────────────────────────────┘   │

│                            │                                      │```sql

└────────────────────────────┼─────────────────────────────────────┘CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

                             │```

┌────────────────────────────┼─────────────────────────────────────┐

│                      Service Layer                               │테이블은 앱 시작 시 자동으로 생성됩니다.

│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │

│  │ Camera Worker   │  │  Face Service   │  │   Inference    │  │### 5. 서버 실행

│  │ (Background)    │  │  - Detection    │  │   Service      │  │

│  │ - Frame capture │  │  - Embedding    │  │  - Matching    │  │**개발 모드:**

│  │ - 20 FPS stream │  │  - HOG features │  │  - Validation  │  │

│  └─────────────────┘  └─────────────────┘  └────────────────┘  │```powershell

│                            │                                      │uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

└────────────────────────────┼─────────────────────────────────────┘```

                             │

┌────────────────────────────┼─────────────────────────────────────┐**운영 모드:**

│                     Persistence Layer                            │

│  ┌─────────────────────────────────┐  ┌─────────────────────┐   │```powershell

│  │        MySQL Database           │  │   File System       │   │uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4

│  │  ├─ users                       │  │  ├─ encodings/*.npy │   │```

│  │  ├─ attendance                  │  │  └─ images/*.jpg    │   │

│  │  └─ (indices, constraints)      │  │                     │   │서버가 시작되면 다음 주소로 접속할 수 있습니다:

│  └─────────────────────────────────┘  └─────────────────────┘   │- API 서버: http://localhost:5000

└─────────────────────────────────────────────────────────────────┘- API 문서: http://localhost:5000/docs

```- ReDoc: http://localhost:5000/redoc



### 데이터 흐름---



#### 얼굴 인식 플로우## 📡 API 엔드포인트

```

Camera/Upload → Face Detection → Ellipse Validation → Feature Extraction### 1. 헬스 체크

                                                              ↓

Attendance Log ← Distance Check ← Database Match ← Embedding Compare**`GET /health`**

```

서버 상태 및 데이터베이스 연결 확인

## 💻 시스템 요구사항

**응답 예시:**

### 필수 요구사항```json

| 항목 | 요구사항 |{

|------|----------|  "status": "ok",

| OS | Windows 10+, Linux (Ubuntu 20.04+), macOS 11+ |  "timestamp": "2025-01-01T12:00:00Z"

| Python | 3.9 이상 |}

| MySQL | 8.0 이상 |```

| 메모리 | 최소 4GB (권장 8GB+) |

| 디스크 | 10GB 이상 여유 공간 |---



### 선택 요구사항### 2. MJPEG 스트리밍

| 항목 | 용도 |

|------|------|**`GET /stream.mjpeg`**

| 웹캠 | MODE_A (서버 카메라) 사용 시 |

| GPU | 대량 동시 요청 처리 시 성능 향상 |서버 카메라의 실시간 비디오 스트림 (MODE_A)



## 🚀 설치 및 실행**응답:**

- Content-Type: `multipart/x-mixed-replace; boundary=frame`

### 빠른 시작 (Quick Start)- 카메라가 없으면 503 오류 반환



```bash**사용 예:**

# 1. 저장소 클론```html

git clone <repository-url><img src="http://localhost:5000/stream.mjpeg" />

cd face_attendance_api```



# 2. 가상환경 생성 및 활성화---

python -m venv venv

# Windows### 3. 얼굴 인식

venv\Scripts\activate

# Linux/Mac**`POST /identify`**

source venv/bin/activate

얼굴을 인식하고 출퇴근을 기록합니다.

# 3. 의존성 설치

pip install -r requirements.txt#### MODE_A (JSON - 서버 카메라 사용)



# 4. 환경 변수 설정**요청:**

cp .env.example .env```json

# .env 파일을 편집하여 MySQL 접속 정보 입력{

  "type": "IN",

# 5. MySQL 데이터베이스 생성  "device_id": "DEVICE_01",

mysql -u root -p -e "CREATE DATABASE attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"  "ts_client": "2025-01-01T09:00:00Z"

}

# 6. 서버 실행```

uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

```#### MODE_B (Multipart - 이미지 업로드)



### 상세 설치 가이드**요청 (Form Data):**

- `image`: 이미지 파일 (필수)

#### 1. Python 가상환경 설정- `type`: "IN" 또는 "OUT" (필수)

- `device_id`: 디바이스 ID (선택)

**Windows (PowerShell):**- `ts_client`: 클라이언트 타임스탬프 (선택)

```powershell

python -m venv venv**성공 응답:**

.\venv\Scripts\Activate.ps1```json

```{

  "success": true,

**Linux/macOS:**  "employee_id": "EMP001",

```bash  "name": "홍길동",

python3 -m venv venv  "user": "홍길동",

source venv/bin/activate  "distance": 0.35,

```  "decided_threshold": 0.45,

  "message": "인증 성공"

#### 2. 의존성 패키지 설치}

```

```bash

pip install --upgrade pip**실패 응답:**

pip install -r requirements.txt```json

```{

  "success": false,

**주요 패키지:**  "message": "얼굴을 인식할 수 없습니다",

```  "reason": "unknown",

fastapi>=1.0.0  "min_distance": 0.52

uvicorn[standard]>=0.24.0}

SQLAlchemy>=2.0.0```

pymysql>=1.1.0

opencv-python>=4.8.0**실패 사유 코드:**

numpy>=1.24.0- `no_face`: 얼굴이 감지되지 않음

loguru>=0.7.0- `multi_face`: 여러 얼굴이 감지됨

python-dotenv>=1.0.0- `bad_quality`: 이미지 품질 불량

pydantic>=2.0.0- `camera_unavailable`: 카메라 사용 불가 (MODE_A)

pydantic-settings>=2.0.0- `unknown`: 등록되지 않은 얼굴

```- `internal_error`: 서버 내부 오류



#### 3. MySQL 설정---



**데이터베이스 생성:**### 4. 사용자 등록

```sql

CREATE DATABASE IF NOT EXISTS attendance_db **`POST /enroll`**

CHARACTER SET utf8mb4 

COLLATE utf8mb4_unicode_ci;새 사용자를 등록하거나 기존 사용자에게 얼굴 임베딩을 추가합니다.



-- 사용자 권한 설정 (선택)**요청 (Form Data):**

CREATE USER 'attendance_user'@'localhost' IDENTIFIED BY 'secure_password';- `employee_id`: 직원 ID (필수)

GRANT ALL PRIVILEGES ON attendance_db.* TO 'attendance_user'@'localhost';- `image`: 얼굴 이미지 파일 (필수, 1명의 얼굴만)

FLUSH PRIVILEGES;- `name`: 직원 이름 (신규 등록 시 필수)

```- `device_id`: 디바이스 ID (선택)



#### 4. 환경 변수 구성**성공 응답:**

```json

`.env` 파일 생성:{

  "success": true,

```env  "employee_id": "EMP001",

# MySQL Database Configuration  "message": "등록 완료"

MYSQL_HOST=127.0.0.1}

MYSQL_PORT=3306```

MYSQL_USER=root

MYSQL_PASSWORD=your_secure_password**실패 응답:**

MYSQL_DB=attendance_db```json

MYSQL_POOL_SIZE=5{

MYSQL_MAX_OVERFLOW=10  "success": false,

  "message": "얼굴을 감지할 수 없습니다. 정면 사진을 사용해주세요",

# Face Recognition Settings  "reason": "no_face"

TOLERANCE=0.35}

```

# Storage Paths

IMAGE_DIR=app/static/images---

ENCODING_DIR=app/static/encodings

### 5. 출퇴근 기록 (선택)

# Camera Settings (MODE_A)

STREAM_FPS=20**`POST /attendance`**

CAMERA_DEVICE_INDEX=0

```얼굴 인식 없이 직접 출퇴근을 기록합니다.



#### 5. 디렉토리 구조 확인**요청:**

```json

애플리케이션이 자동으로 생성하지만, 수동으로 확인:{

```bash  "employee_id": "EMP001",

mkdir -p app/static/images app/static/encodings logs  "type": "OUT",

```  "device_id": "DEVICE_01",

  "distance": 0.35,

#### 6. 서버 실행  "image_ref": "path/to/image.jpg",

  "ts_client": "2025-01-01T18:00:00Z"

**개발 환경 (Hot Reload):**}

```bash```

uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

```**응답:**

```json

**프로덕션 환경 (Multi-worker):**{

```bash  "success": true,

uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4  "message": "출퇴근 기록이 저장되었습니다"

```}

```

**프로덕션 환경 (Gunicorn + Uvicorn):**

```bash---

gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

```## 🗄️ 데이터베이스 스키마



### 서비스 등록 (Linux Systemd)### users 테이블

| 컬럼 | 타입 | 설명 |

`/etc/systemd/system/face-attendance.service`:|------|------|------|

```ini| id | INT | Primary Key |

[Unit]| employee_id | VARCHAR(50) | 직원 ID (UNIQUE) |

Description=Face Attendance API| name | VARCHAR(100) | 이름 |

After=network.target mysql.service| created_at | DATETIME | 생성일시 |



[Service]### user_embeddings 테이블

Type=notify| 컬럼 | 타입 | 설명 |

User=www-data|------|------|------|

WorkingDirectory=/opt/face_attendance_api| id | INT | Primary Key |

Environment="PATH=/opt/face_attendance_api/venv/bin"| employee_id | VARCHAR(50) | 직원 ID (FK) |

ExecStart=/opt/face_attendance_api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4| vector_path | VARCHAR(255) | 임베딩 .npy 파일 경로 |

Restart=always| quality_score | FLOAT | 품질 점수 (선택) |

| created_at | DATETIME | 생성일시 |

[Install]

WantedBy=multi-user.target### attendance 테이블

```| 컬럼 | 타입 | 설명 |

|------|------|------|

```bash| id | INT | Primary Key |

sudo systemctl daemon-reload| employee_id | VARCHAR(50) | 직원 ID (FK) |

sudo systemctl enable face-attendance| type | VARCHAR(10) | 'IN' 또는 'OUT' |

sudo systemctl start face-attendance| device_id | VARCHAR(50) | 디바이스 ID (선택) |

```| distance | FLOAT | 인식 거리 (선택) |

| ts_server | DATETIME | 서버 타임스탬프 |

### Docker 배포 (선택)| ts_client | DATETIME | 클라이언트 타임스탬프 (선택) |

| image_ref | VARCHAR(255) | 이미지 참조 (선택) |

`Dockerfile`:

```dockerfile---

FROM python:3.11-slim

## ⚙️ 주요 설정

WORKDIR /app

### 얼굴 인식 임계값

# Install system dependencies

RUN apt-get update && apt-get install -y \`.env` 파일의 `TOLERANCE` 값을 조정하여 인식 민감도를 설정할 수 있습니다:

    gcc \

    g++ \- **0.4 이하**: 엄격 (False positive 감소, False negative 증가)

    libgl1-mesa-glx \- **0.45**: 권장 (균형)

    libglib2.0-0 \- **0.5 이상**: 관대 (False negative 감소, False positive 증가)

    && rm -rf /var/lib/apt/lists/*

### 카메라 설정

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt- `CAMERA_DEVICE_INDEX`: 카메라 장치 인덱스 (기본 0)

- `STREAM_FPS`: 스트리밍 프레임 레이트 (기본 20)

COPY . .

---

EXPOSE 5000

## 🔒 운영 환경 권장 사항

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]

```### 1. CORS 설정



`docker-compose.yml`:`app/core/cors.py`에서 운영 도메인을 화이트리스트에 추가하세요:

```yaml

version: '3.8'```python

PROD_CORS_ORIGINS = [

services:    "https://yourdomain.com",

  api:    "https://app.yourdomain.com"

    build: .]

    ports:```

      - "5000:5000"

    environment:### 2. HTTPS 사용

      - MYSQL_HOST=db

      - MYSQL_USER=root운영 환경에서는 HTTPS를 필수로 사용하세요:

      - MYSQL_PASSWORD=rootpassword

      - MYSQL_DB=attendance_db```bash

    depends_on:# Nginx를 리버스 프록시로 사용 권장

      - dbuvicorn app.main:app --host 127.0.0.1 --port 5000

    volumes:```

      - ./app/static:/app/app/static

      - ./logs:/app/logs### 3. API Key 인증



  db:디바이스별 API Key 인증을 추가하는 것을 권장합니다.

    image: mysql:8.0

    environment:### 4. 업로드 제한

      - MYSQL_ROOT_PASSWORD=rootpassword

      - MYSQL_DATABASE=attendance_db`main.py`에서 파일 크기 제한을 설정하세요:

    volumes:

      - mysql_data:/var/lib/mysql```python

app.add_middleware(

volumes:    RequestSizeLimitMiddleware,

  mysql_data:    max_upload_size=10 * 1024 * 1024  # 10MB

```)

```

```bash

docker-compose up -d### 5. 로그 관리

```

로그 파일은 자동으로 `logs/` 디렉토리에 저장됩니다:

## 📚 API 명세- `logs/app.log`: 일반 로그 (7일 보관)

- `logs/error.log`: 오류 로그 (30일 보관)

### Base URL

```### 6. 타임존 설정

http://localhost:5000

```서버 타임존을 UTC로 유지하고, 프론트엔드에서 로컬 시간으로 변환하세요.



### 인증---

현재 버전은 인증이 없습니다. 프로덕션 환경에서는 API Key 또는 JWT 인증 추가를 권장합니다.

## 🐛 문제 해결

---

### face_recognition 설치 실패

### 1. Health Check

Windows에서 `face_recognition` 설치가 실패하는 경우:

시스템 상태 및 데이터베이스 연결을 확인합니다.

1. Visual Studio Build Tools 설치

**Endpoint:**2. CMake 설치

```3. dlib 수동 설치: `pip install dlib`

GET /health4. 그래도 실패 시, 시스템은 대체 임베딩 방식으로 동작합니다 (정확도 감소)

```

### 카메라가 인식되지 않음

**응답:**

```json- `CAMERA_DEVICE_INDEX`를 0, 1, 2 등으로 변경해보세요

{- 다른 애플리케이션에서 카메라를 사용 중인지 확인하세요

  "status": "healthy",- 카메라 없이도 MODE_B (업로드)는 정상 작동합니다

  "database": "connected",

  "timestamp": "2025-11-10T12:00:00.000Z"### MySQL 연결 오류

}

```- MySQL 서버가 실행 중인지 확인하세요

- `.env`의 접속 정보를 확인하세요

**상태 코드:**- 방화벽 설정을 확인하세요

- `200 OK`: 정상

- `503 Service Unavailable`: DB 연결 실패---



---## 📝 라이선스



### 2. MJPEG 스트리밍이 프로젝트는 MIT 라이선스 하에 배포됩니다.



서버 카메라의 실시간 비디오 스트림을 제공합니다 (MODE_A).---



**Endpoint:**## 🙋‍♂️ 지원

```

GET /stream.mjpeg문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.

```

**행복한 코딩 되세요! 🎉**

**응답 헤더:**
```
Content-Type: multipart/x-mixed-replace; boundary=frame
```

**특징:**
- 20 FPS 스트리밍
- 타원 가이드 오버레이
- 얼굴 감지 박스 및 메시지 표시
- 무한 스트림 (클라이언트 연결 종료 시까지)

**상태 코드:**
- `200 OK`: 스트리밍 시작
- `503 Service Unavailable`: 카메라 사용 불가

**HTML 사용 예:**
```html
<img src="http://localhost:5000/stream.mjpeg" alt="Live Stream" />
```

---

### 3. 카메라 프레임 캡처

현재 카메라 프레임의 스냅샷을 반환합니다.

**Endpoint:**
```
GET /capture?preview=1
```

**Query Parameters:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| preview | int | ❌ | 0 또는 1 (기본값: 0) |

**응답:**
- `Content-Type: image/jpeg`
- JPEG 이미지 바이너리

**상태 코드:**
- `200 OK`: 이미지 반환
- `503 Service Unavailable`: 카메라 사용 불가

---

### 4. 얼굴 인식 (출퇴근)

얼굴을 인식하고 출퇴근을 기록합니다.

#### MODE_A (서버 카메라)

**Endpoint:**
```
POST /identify
Content-Type: application/json
```

**요청 본문:**
```json
{
  "type": "IN",
  "device_id": "KIOSK_01",
  "ts_client": "2025-11-10T09:00:00Z"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| type | string | ✅ | "IN" (출근) 또는 "OUT" (퇴근) |
| device_id | string | ❌ | 디바이스 식별자 |
| ts_client | datetime | ❌ | 클라이언트 타임스탬프 (ISO 8601) |

#### MODE_B (이미지 업로드)

**Endpoint:**
```
POST /identify
Content-Type: multipart/form-data
```

**Form Data:**
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| image | file | ✅ | 얼굴 이미지 파일 (JPEG/PNG) |
| type | string | ✅ | "IN" 또는 "OUT" |
| device_id | string | ❌ | 디바이스 식별자 |
| ts_client | datetime | ❌ | 클라이언트 타임스탬프 |

**성공 응답 (200 OK):**
```json
{
  "success": true,
  "employee_id": "EMP001",
  "name": "김철수",
  "distance": 0.21,
  "decided_threshold": 0.35,
  "message": "인증 성공"
}
```

**실패 응답 (200 OK):**
```json
{
  "success": false,
  "message": "가이드 영역 안에서 인증해주세요",
  "reason": "out_of_area",
  "distance": null
}
```

**오류 사유 코드:**
| 코드 | 설명 |
|------|------|
| `no_face` | 얼굴이 감지되지 않음 |
| `out_of_area` | 타원 가이드 영역 밖 |
| `bad_quality` | 이미지 품질 불량 |
| `unknown` | 등록되지 않은 얼굴 |
| `camera_unavailable` | 카메라 사용 불가 (MODE_A) |
| `internal_error` | 서버 내부 오류 |

---

### 5. 사용자 등록

새 사용자를 등록합니다.

**Endpoint:**
```
POST /enroll
Content-Type: multipart/form-data
```

**Form Data:**
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | ✅ | 사용자 이름 |
| image | file | ✅ | 얼굴 이미지 (1명만) |

**대체 엔드포인트 (Base64):**
```
POST /enroll/json
Content-Type: application/json

{
  "name": "김철수",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**성공 응답 (200 OK):**
```json
{
  "success": true,
  "employee_id": "EMP003",
  "message": "등록 완료"
}
```

**실패 응답 (200 OK):**
```json
{
  "success": false,
  "message": "얼굴을 감지할 수 없습니다. 정면 얼굴이 보이도록 촬영해주세요.",
  "reason": "no_face"
}
```

**자동 생성 규칙:**
- 직원 ID: `EMP001`, `EMP002`, ... (자동 증가)
- 임베딩 파일: `app/static/encodings/EMP001.npy`

---

### 6. 출퇴근 기록 조회

출퇴근 기록을 조회합니다.

**Endpoint:**
```
GET /attendance?employee_id=EMP001&limit=10
```

**Query Parameters:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| employee_id | string | ❌ | 특정 직원 필터링 |
| limit | int | ❌ | 최대 레코드 수 (기본: 100) |

**응답 (200 OK):**
```json
{
  "records": [
    {
      "id": 1,
      "employee_id": "EMP001",
      "type": "IN",
      "distance": 0.21,
      "ts_server": "2025-11-10T09:00:00Z",
      "ts_client": "2025-11-10T09:00:00Z",
      "device_id": "KIOSK_01",
      "image_ref": "app/static/images/..."
    }
  ],
  "count": 1
}
```

---

## 📁 프로젝트 구조

```
face_attendance_api/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 애플리케이션 진입점
│   │
│   ├── api/                       # API 라우트
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── routes_health.py        # Health check 엔드포인트
│   │       ├── routes_stream.py        # MJPEG 스트리밍
│   │       ├── routes_capture.py       # 프레임 캡처
│   │       ├── routes_identify.py      # 얼굴 인식 (출퇴근)
│   │       ├── routes_enroll.py        # 사용자 등록
│   │       └── routes_attendance.py    # 출퇴근 기록 조회
│   │
│   ├── core/                      # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.py              # 환경 설정 (Pydantic Settings)
│   │   ├── cors.py                # CORS 설정
│   │   └── logging.py             # Loguru 로깅 설정
│   │
│   ├── db/                        # 데이터베이스
│   │   ├── __init__.py
│   │   ├── base.py                # DB 세션 관리 및 초기화
│   │   └── models.py              # SQLAlchemy 모델 (User, Attendance)
│   │
│   ├── schemas/                   # Pydantic 스키마
│   │   ├── __init__.py
│   │   └── dto.py                 # DTO (Request/Response 모델)
│   │
│   ├── services/                  # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── camera_worker.py       # 카메라 백그라운드 워커
│   │   ├── face_service.py        # 얼굴 감지 및 임베딩
│   │   ├── inference.py           # 얼굴 인식 추론 로직
│   │   └── attendance_service.py  # 출퇴근 기록 서비스
│   │
│   ├── utils/                     # 유틸리티
│   │   ├── __init__.py
│   │   ├── env.py                 # 환경 변수 헬퍼
│   │   ├── image_io.py            # 이미지 I/O 처리
│   │   └── paths.py               # 파일 경로 관리
│   │
│   └── static/                    # 정적 파일
│       ├── images/                # 썸네일 이미지 저장소
│       └── encodings/             # 얼굴 임베딩 파일 (.npy)
│
├── logs/                          # 로그 파일 (자동 생성)
│   ├── app_2025-11-10.log
│   └── ...
│
├── .env                           # 환경 변수 (git 제외)
├── .gitignore
├── requirements.txt               # Python 의존성
├── README.md                      # 프로젝트 문서
│
├── migrate_schema.py              # 스키마 마이그레이션 스크립트
├── reset_users.py                 # 사용자 데이터 초기화 스크립트
└── fix_embedding_path.py          # 임베딩 경로 수정 스크립트
```

### 주요 모듈 설명

#### `app/main.py`
- FastAPI 애플리케이션 인스턴스 생성
- 라우터 등록
- 미들웨어 설정 (CORS)
- Lifespan 이벤트 (startup/shutdown)
- 카메라 워커 초기화

#### `app/services/camera_worker.py`
- 백그라운드 스레드에서 카메라 프레임 캡처
- 20 FPS로 최신 프레임 유지
- Thread-safe lock으로 동시 접근 제어

#### `app/services/face_service.py`
- `detect_single_face()`: 얼굴 감지 (Haar Cascade)
- `embed()`: 얼굴 특징 추출 (HOG)
- `load_embedding()`: .npy 파일 로드
- `save_embedding()`: 임베딩 저장
- `l2_distance()`: 유사도 계산

#### `app/services/inference.py`
- `identify_from_camera()`: MODE_A 인식
- `identify_from_upload()`: MODE_B 인식
- `identify_from_image()`: 공통 인식 로직
- `find_best_match()`: DB 매칭
- `enroll_user_with_image()`: 사용자 등록

## ⚙️ 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 값 |
|--------|------|---------|
| `MYSQL_HOST` | MySQL 서버 호스트 | `127.0.0.1` |
| `MYSQL_PORT` | MySQL 서버 포트 | `3306` |
| `MYSQL_USER` | MySQL 사용자명 | `root` |
| `MYSQL_PASSWORD` | MySQL 비밀번호 | `secure_password` |
| `MYSQL_DB` | 데이터베이스 이름 | `attendance_db` |

### 선택 환경 변수

| 변수명 | 설명 | 기본값 | 범위 |
|--------|------|--------|------|
| `MYSQL_POOL_SIZE` | 커넥션 풀 기본 크기 | `5` | 1-20 |
| `MYSQL_MAX_OVERFLOW` | 커넥션 풀 최대 오버플로우 | `10` | 0-50 |
| `TOLERANCE` | 얼굴 인식 임계값 | `0.35` | 0.2-0.6 |
| `IMAGE_DIR` | 이미지 저장 디렉토리 | `app/static/images` | - |
| `ENCODING_DIR` | 임베딩 저장 디렉토리 | `app/static/encodings` | - |
| `STREAM_FPS` | 스트리밍 FPS | `20` | 10-30 |
| `CAMERA_DEVICE_INDEX` | 카메라 장치 인덱스 | `0` | 0-10 |

### TOLERANCE 값 가이드

얼굴 인식의 민감도를 조정합니다. **낮을수록 더 엄격**합니다.

| 값 | 설명 | 추천 상황 |
|----|------|-----------|
| `0.25-0.30` | 매우 엄격 | 보안이 중요한 환경 (출입 통제) |
| `0.30-0.35` | 엄격 | 일반적인 출퇴근 관리 (권장) |
| `0.35-0.40` | 보통 | 편의성 우선 환경 |
| `0.40-0.50` | 관대 | 테스트 환경 |
| `0.50+` | 매우 관대 | 비권장 (오인식 위험) |

**조정 시 주의사항:**
- 값을 낮추면: 본인 인식 실패 증가 ↑, 타인 오인식 감소 ↓
- 값을 높이면: 본인 인식 실패 감소 ↓, 타인 오인식 증가 ↑

## 🗄️ 데이터베이스

### 스키마 다이어그램

```
┌──────────────────────────────┐
│          users               │
├──────────────────────────────┤
│ id (PK)           INT         │
│ employee_id       VARCHAR(50) │ UNIQUE
│ name              VARCHAR(100)│
│ profile_image     VARCHAR(255)│ ← 임베딩 파일 경로 (.npy)
│ created_at        DATETIME    │
└──────────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌──────────────────────────────┐
│        attendance            │
├──────────────────────────────┤
│ id (PK)           INT         │
│ employee_id       VARCHAR(50) │ ← INDEX
│ type              VARCHAR(10) │ 'IN' | 'OUT'
│ device_id         VARCHAR(50) │
│ distance          FLOAT       │ ← 인식 거리
│ ts_server         DATETIME    │ ← INDEX
│ ts_client         DATETIME    │
│ image_ref         VARCHAR(255)│
└──────────────────────────────┘
```

### 테이블 상세

#### `users` 테이블

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    profile_image VARCHAR(255) COMMENT '얼굴 임베딩 파일 경로 (.npy)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_employee_id (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**컬럼 설명:**
- `id`: Primary Key (자동 증가)
- `employee_id`: 직원 고유 ID (EMP001, EMP002, ...)
- `name`: 직원 이름
- `profile_image`: **얼굴 임베딩 .npy 파일 경로** (이름과 달리 임베딩 저장)
- `created_at`: 등록 일시

**주의사항:**
- `profile_image`는 실제로는 임베딩 파일 경로를 저장합니다
- 사진 여러 장을 찍지 않으므로 1:1 관계

#### `attendance` 테이블

```sql
CREATE TABLE attendance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id VARCHAR(50),
    type VARCHAR(10) NOT NULL,
    device_id VARCHAR(50),
    distance FLOAT COMMENT '얼굴 인식 L2 거리 (낮을수록 유사)',
    ts_server DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ts_client DATETIME,
    image_ref VARCHAR(255) COMMENT '인증 시 캡처된 이미지 경로',
    
    INDEX idx_attendance_employee_id (employee_id),
    INDEX idx_attendance_ts_server (ts_server)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**컬럼 설명:**
- `id`: Primary Key
- `employee_id`: 직원 ID (NULL 가능 - 미등록 사용자 시도)
- `type`: 출근('IN') 또는 퇴근('OUT')
- `device_id`: 인증 디바이스 식별자
- `distance`: L2 거리 (0에 가까울수록 유사)
- `ts_server`: 서버 타임스탬프 (신뢰 가능)
- `ts_client`: 클라이언트 타임스탬프 (참고용)
- `image_ref`: 인증 시 사용된 이미지 경로

**인덱스 전략:**
- `idx_attendance_employee_id`: 특정 직원 기록 조회 최적화
- `idx_attendance_ts_server`: 시간 범위 쿼리 최적화

### 데이터베이스 초기화

애플리케이션 시작 시 자동으로 테이블이 생성됩니다:

```python
# app/db/base.py
Base.metadata.create_all(bind=engine)
```

수동 초기화:
```bash
python -c "from app.db.base import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 백업 및 복원

**백업:**
```bash
mysqldump -u root -p attendance_db > backup_$(date +%Y%m%d).sql
```

**복원:**
```bash
mysql -u root -p attendance_db < backup_20251110.sql
```

## 🔧 개발 가이드

### 로컬 개발 환경 설정

```bash
# 가상환경 활성화
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 개발 의존성 설치 (선택)
pip install pytest pytest-asyncio httpx black flake8

# Pre-commit hook 설정 (선택)
pip install pre-commit
pre-commit install
```

### 코드 스타일

**Black (자동 포매팅):**
```bash
black app/ --line-length 120
```

**Flake8 (린터):**
```bash
flake8 app/ --max-line-length=120 --ignore=E203,W503
```

### 로깅

애플리케이션은 Loguru를 사용합니다:

```python
from app.core.logging import app_logger

app_logger.info("정보 메시지")
app_logger.warning("경고 메시지")
app_logger.error("에러 발생", exc_info=True)
app_logger.debug("디버그 정보")
```

**로그 파일:**
- `logs/app_{날짜}.log`: 일별 로테이션
- 자동 압축 및 7일 보관
- 콘솔 출력 (개발 환경)

### 환경별 설정

**개발 환경 (.env.dev):**
```env
MYSQL_HOST=localhost
TOLERANCE=0.40
```

**프로덕션 환경 (.env.prod):**
```env
MYSQL_HOST=db.production.com
TOLERANCE=0.35
```

환경 전환:
```bash
cp .env.dev .env  # 개발
cp .env.prod .env  # 프로덕션
```

### API 테스트

**cURL:**
```bash
# Health check
curl http://localhost:5000/health

# 얼굴 인식 (JSON)
curl -X POST http://localhost:5000/identify \
  -H "Content-Type: application/json" \
  -d '{"type":"IN"}'

# 사용자 등록
curl -X POST http://localhost:5000/enroll \
  -F "name=홍길동" \
  -F "image=@face.jpg"
```

**Python (httpx):**
```python
import httpx

# 얼굴 인식
response = httpx.post(
    "http://localhost:5000/identify",
    json={"type": "IN"}
)
print(response.json())

# 사용자 등록
with open("face.jpg", "rb") as f:
    response = httpx.post(
        "http://localhost:5000/enroll",
        files={"image": f},
        data={"name": "홍길동"}
    )
print(response.json())
```

### 얼굴 인식 파라미터 튜닝

#### 1. 얼굴 감지 민감도

`app/services/face_service.py`:
```python
def detect_single_face(bgr_image: np.ndarray):
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.05,     # 낮을수록 더 세밀 (1.01-1.3)
        minNeighbors=3,        # 낮을수록 더 많이 감지 (1-10)
        minSize=(20, 20)       # 최소 얼굴 크기 (픽셀)
    )
```

#### 2. 타원 가이드 영역

`app/api/v1/routes_stream.py` 및 `app/services/inference.py`:
```python
ellipse_width = int(w * 0.35)   # 화면 너비의 35%
ellipse_height = int(h * 0.55)  # 화면 높이의 55%
```

더 크게: `0.40`, `0.65` (편의성 우선)  
더 작게: `0.30`, `0.50` (정확도 우선)

#### 3. HOG 파라미터

`app/services/face_service.py`:
```python
hog = cv2.HOGDescriptor(
    (128, 128),      # win_size
    (16, 16),        # block_size
    (8, 8),          # block_stride
    (8, 8),          # cell_size
    9                # nbins (방향 구간 수)
)
```

### 유틸리티 스크립트

#### 사용자 데이터 초기화

```bash
python reset_users.py
```

재등록을 위해 모든 사용자 삭제 (attendance 기록은 유지).

#### 임베딩 경로 수정

```bash
python fix_embedding_path.py
```

`profile_image` 컬럼을 임베딩 파일 경로로 업데이트.

#### 스키마 마이그레이션 (사용 안 함)

```bash
python migrate_schema.py
```

현재는 `user_embeddings` 테이블을 제거한 상태.

### 성능 최적화

#### 1. 커넥션 풀 최적화

`.env`:
```env
MYSQL_POOL_SIZE=10        # 동시 요청 수에 맞춰 조정
MYSQL_MAX_OVERFLOW=20
```

#### 2. 임베딩 캐싱

현재는 DB 조회 시마다 파일을 읽지만, Redis 캐싱 추가 고려:
```python
# 의사 코드
cached_embedding = redis.get(f"emb:{employee_id}")
if not cached_embedding:
    cached_embedding = face_service.load_embedding(path)
    redis.setex(f"emb:{employee_id}", 3600, cached_embedding)
```

#### 3. 비동기 I/O

파일 저장을 비동기로:
```python
import aiofiles

async def save_embedding_async(employee_id, embedding):
    filepath = get_encoding_path(employee_id)
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(embedding.tobytes())
```

## 🐛 트러블슈팅

### 카메라 관련

#### 문제: `Failed to open camera device 0`

**원인:**
- 카메라가 다른 애플리케이션에서 사용 중
- 잘못된 `CAMERA_DEVICE_INDEX`
- 카메라 권한 없음

**해결:**
```bash
# 1. 다른 카메라 인덱스 시도
CAMERA_DEVICE_INDEX=1  # .env 수정

# 2. 카메라 사용 중인 프로세스 확인 (Linux)
sudo lsof /dev/video0

# 3. 카메라 권한 확인 (Linux)
sudo usermod -a -G video $USER
```

### 데이터베이스 관련

#### 문제: `Can't connect to MySQL server`

**해결:**
```bash
# 1. MySQL 서비스 상태 확인
sudo systemctl status mysql    # Linux
# Windows: services.msc에서 MySQL 확인

# 2. 방화벽 확인
sudo ufw allow 3306/tcp

# 3. MySQL 바인드 주소 확인
# /etc/mysql/mysql.conf.d/mysqld.cnf
bind-address = 0.0.0.0  # 외부 접속 허용
```

#### 문제: `Access denied for user`

**해결:**
```sql
-- MySQL 사용자 확인
SELECT user, host FROM mysql.user;

-- 권한 부여
GRANT ALL PRIVILEGES ON attendance_db.* TO 'root'@'%' IDENTIFIED BY 'password';
FLUSH PRIVILEGES;
```

### 얼굴 인식 관련

#### 문제: 인식률이 낮음 (본인이 인식 안 됨)

**원인:**
- `TOLERANCE` 값이 너무 낮음
- 등록 시 품질이 낮은 사진 사용
- 조명 차이 (등록 vs 인증)

**해결:**
```env
# 1. TOLERANCE 완화
TOLERANCE=0.40  # 0.35 → 0.40

# 2. 재등록 (고품질 사진)
# - 정면 얼굴
# - 밝은 조명
# - 고해상도

# 3. 로그 확인
tail -f logs/app_*.log | grep distance
```

#### 문제: 오인식 발생 (다른 사람 인식됨)

**원인:**
- `TOLERANCE` 값이 너무 높음
- 등록된 사용자 간 유사도가 높음

**해결:**
```env
# 1. TOLERANCE 강화
TOLERANCE=0.30  # 0.35 → 0.30

# 2. 유사도 분석
SELECT employee_id, distance 
FROM attendance 
WHERE type='IN' 
ORDER BY distance DESC 
LIMIT 50;

# 3. 임베딩 재생성
rm app/static/encodings/*.npy
# 모든 사용자 재등록
```

#### 문제: "가이드 영역 안에서 인증해주세요" 계속 발생

**원인:**
- 타원 영역이 너무 작음
- 얼굴이 화면 밖에 위치

**해결:**
```python
# app/api/v1/routes_stream.py, app/services/inference.py
ellipse_width = int(w * 0.45)   # 0.35 → 0.45
ellipse_height = int(h * 0.65)  # 0.55 → 0.65
```

### 성능 관련

#### 문제: 느린 응답 속도

**진단:**
```bash
# 로그 확인
grep "took" logs/app_*.log

# DB 커넥션 풀 상태 확인
SELECT * FROM information_schema.processlist WHERE db='attendance_db';
```

**해결:**
```env
# 1. 커넥션 풀 증가
MYSQL_POOL_SIZE=20
MYSQL_MAX_OVERFLOW=40

# 2. Worker 증가 (프로덕션)
uvicorn app.main:app --workers 4

# 3. 인덱스 확인
SHOW INDEX FROM attendance;
```

### 파일 시스템 관련

#### 문제: 임베딩 파일을 찾을 수 없음

**원인:**
- 상대 경로 vs 절대 경로 혼용
- 디렉토리 권한 없음

**해결:**
```bash
# 1. 디렉토리 존재 확인
ls -la app/static/encodings/

# 2. 권한 확인 및 수정
chmod 755 app/static/encodings/
chown -R www-data:www-data app/static/

# 3. 경로 일관성 확인
python -c "from app.utils.paths import get_encoding_path; print(get_encoding_path('EMP001'))"
```

### 기타

#### 문제: `face_recognition` 설치 실패 (Windows)

**해결:**

1. **Visual Studio Build Tools 설치**
   - https://visualstudio.microsoft.com/downloads/
   - "Desktop development with C++" 선택

2. **CMake 설치**
   ```powershell
   choco install cmake
   ```

3. **dlib 수동 설치**
   ```powershell
   pip install cmake
   pip install dlib
   pip install face_recognition
   ```

4. **설치 포기 시**
   - 시스템은 fallback 임베딩 방식으로 자동 전환
   - HOG 기반으로도 충분한 성능 제공

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

### 기여 가이드라인

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 코드 리뷰 기준
- Black 포매팅 준수
- Type hints 사용
- Docstring 작성 (Google Style)
- 테스트 코드 포함

## 📞 지원 및 문의

- **이슈 트래커**: [GitHub Issues]
- **문서**: 본 README.md 및 `/docs` 참조
- **이메일**: contact@example.com

## 🔐 보안 권고사항

프로덕션 환경에서는 다음 사항을 반드시 고려하세요:

1. **환경 변수 보호**
   - `.env` 파일을 git에 커밋하지 마세요
   - 프로덕션에서는 환경 변수를 시스템 레벨에서 설정

2. **HTTPS 사용**
   - Nginx/Apache를 리버스 프록시로 사용
   - Let's Encrypt로 무료 SSL 인증서 발급

3. **API 인증**
   - API Key 또는 JWT 인증 추가
   - Rate Limiting 적용

4. **데이터 보호**
   - 얼굴 임베딩 파일 암호화
   - 개인정보 보호 규정 (GDPR, PIPA) 준수
   - 정기적인 백업

5. **접근 제어**
   - MySQL 사용자 권한 최소화
   - 방화벽 설정

---

**Made with ❤️ for modern attendance management**

*Last Updated: 2025-11-10*
