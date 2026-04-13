import os
import json
import urllib.request
from dotenv import load_dotenv

# .env 파일에서 API 키 불러오기
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("API 키를 찾을 수 없습니다. .env 파일을 확인해주세요.")
else:
    # 구글 서버에 직접 모델 목록 요청
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("\n=== 내 API 키로 쓸 수 있는 모델 목록 ===")
            for m in data.get('models', []):
                # 글자 생성(대화)이 가능한 모델만 필터링해서 출력
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(m['name'].replace('models/', ''))
            print("=======================================\n")
    except Exception as e:
        print("서버에 연결하는 중 에러가 발생했습니다:", e)