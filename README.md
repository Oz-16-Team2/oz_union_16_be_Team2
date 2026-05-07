# oz_union_16_be_Team2
오즈 코딩스쿨 16기 합동프로젝트 BE

## 커밋 템플릿

```
feat     : 기능 추가
fix      : 버그 수정
refactor : 리팩토링 (기능 변화 없음)
docs     : 문서 수정
style    : 포맷팅 (black, isort 등)
test     : 테스트 코드
chore    : 기타 설정 (ci, docker, env 등)
```

## PR 리뷰 규칙

- 본인 PR은 본인이 리뷰/머지할 수 없다
- 최소 2명 이상의 리뷰(Approve)가 필요하다
- 리뷰(Approve) 없이는 머지할 수 없다
- CI 또는 테스트가 통과해야 한다
- 브랜치 충돌이 없어야 한다

# 📌 작심몇일
> 목표 달성 및 커뮤니티 게시판 서비스

## 1. 🛠 Tech Stack
- **Framework:** Python, Django
- **Database:** PostgreSQL,redis
- **Infrastructure:** AWS EC2, AWS S3
- **Test:** `pytest`, `pytest-django`

## 2. 🚀 Core Features & Architecture

### 1) 게시판 및 목표 관리 (Board & Goals)
- **게시글(Post) & 댓글(Comment) 및 목표(Goal) 처리 로직 구현**
- **데이터 무결성 확보:** 사용자의 실수 방지 및 연관 데이터 참조 무결성(Foreign Key) 에러를 막기 위해 게시글/댓글 삭제 시 `is_deleted` 플래그를 활용한 **Soft Delete** 적용.

### 2) 다중 소셜 로그인 (Multi-Social Auth)
- **카카오(Kakao), 네이버(Naver), 구글(Google) Oauth 연동**
- 여러 소셜 계정 연동 및 일반 가입 시, 프로필 이미지 URL 노출 우선순위를 결정하는 비즈니스 로직 적용.

### 3) 미디어 파일 처리 최적화 (S3 Presigned URL)
- 애플리케이션 서버(EC2)의 대역폭 및 메모리 낭비를 방지하기 위해 서버 경유 업로드 대신 **S3 Presigned URL**을 도입. 
- 클라이언트가 S3로 이미지를 직접 업로드하는 구조를 구축하여 서버 트래픽 부하 최소화.
- 이름 중복 덮어쓰기 및 단일 경로 파일 밀집을 방지하기 위해 파일명 `UUID` 변환 및 `YYYY/MM/DD/` 디렉토리 분할 적용.

### 4) 검색 로직
- Django ORM의 `icontains`를 활용한 게시글 제목/내용 검색 기능 구현.

## 3. 🧪 Testing Strategy
- 실제 DB 오염을 방지하기 위해 격리된 환경에서 **Mock 데이터(Factory/Fixture)**를 활용한 단위 테스트 수행.
- 소셜 로그인 유저가 작성한 게시글 조회 시, 소셜 프로필 이미지 URL이 빈 값(Null) 없이 정확한 포맷으로 응답되는지 검증하는 API 테스트 파이프라인 구축.

## 4. ⚙️ Installation & Setup

이 프로젝트는 빠르고 효율적인 파이썬 환경 및 의존성 관리를 위해 [uv](https://github.com/astral-sh/uv)를 사용합니다. 사전에 `uv`가 설치되어 있어야 합니다.

```bash
# 1. 저장소 클론
git clone [https://github.com/username/repo-name.git](https://github.com/username/repo-name.git)
cd repo-name

# 2. 가상환경 생성 (uv 활용)
uv venv

# 3. 가상환경 활성화
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 4. 의존성 패키지 설치
uv pip install -r requirements.txt
# (만약 pyproject.toml 기반으로 관리 중이라면 `uv sync`를 실행하세요)

# 5. 환경 변수 설정 (예시: .env 파일 생성)
# SECRET_KEY, DB_USER, DB_PASSWORD, AWS_ACCESS_KEY, AWS_SECRET_KEY 등 셋팅

# 6. 마이그레이션 적용 및 서버 실행
python manage.py migrate
python manage.py runserver

# 7. 테스트 실행
pytest