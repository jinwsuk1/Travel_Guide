# 1. 가상환경 생성
python -m venv venv

# 2. 가상환경 활성화 (Windows 기준)
.\venv\Scripts\activate

# 3. 라이브러리 목록 설치
pip install -r requirements.txt

# 4. 실행
uvicorn main:app --reload