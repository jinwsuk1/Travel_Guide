from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from datetime import datetime # 💡 [추가] 파이썬의 날짜/시간 라이브러리

# LangChain & LangGraph 관련 모듈
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import create_react_agent

load_dotenv()

app = FastAPI(title="Travel Agent API")

search_tool = DuckDuckGoSearchRun()
tools = [search_tool]

# 두뇌(LLM) 세팅
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

# 💡 [추가] 오늘 날짜를 구해서 시스템 메시지로 작성
# 💡 [수정] 모호한 질문과 구체적인 질문을 나누어 대응하는 시스템 프롬프트
today_str = datetime.now().strftime("%Y년 %m월 %d일")
system_prompt = f"""
당신은 완벽한 일정과 정보를 제공하는 최고급 자율형 해외여행 비서 에이전트입니다.
오늘 날짜는 {today_str}입니다. 

사용자의 질문 수준(Detail Level)을 스스로 판단하여 아래 가이드라인에 따라 맞춤형으로 응답하세요.

[대응 가이드라인]
1. 넓고 모호한 질문 (Level 1)
   - 예시: "일본 여행 추천해줘", "어디로 여행 갈까?"
   - 행동: 당장 구체적인 일정을 짜지 마세요. 
   - 응답: 현재 계절(오늘 날짜 기준)에 가장 인기 있는 지역 2~3곳의 매력을 가볍게 소개하고, 대략적인 추천 여행 일수(예: 3박 4일)를 제안합니다.
   - 필수 요소: 반드시 답변 마지막에 "원하시는 예산이나 선호하는 여행 스타일(맛집, 쇼핑, 자연경관 등), 혹은 누구와 가시는지 알려주시면 딱 맞는 상세 일정을 짜드릴게요!"라고 역질문(Follow-up)하여 정보를 더 끌어내세요.

2. 구체적인 질문 (Level 2)
   - 예시: "다음 달 3일 정도, 100만 원 예산으로 일본 감성 느낄 수 있는 곳 추천하고 동선 짜줘."
   - 행동: 역질문 없이 즉시 검색 도구(Search Tool)를 가동합니다.
   - 응답: 사용자가 제시한 예산, 기간, 취향에 완벽히 들어맞는 특정 도시를 선정하고, 일자별(1일 차, 2일 차 등) 방문 장소와 동선을 매우 상세하게 작성합니다.
   - 필수 요소: 검색을 통해 식당이나 관광지의 최신 정보를 반영하고, "원하시면 특정 식당을 바로 예약해 드릴 수도 있습니다."라고 예약 도구(Reservation Tool) 사용을 유도하세요.
"""

# 💡 [수정] 에이전트를 만들 때 state_modifier에 시스템 프롬프트를 주입
travel_agent = create_react_agent(llm, tools, prompt=system_prompt)

# --- 아래 ChatRequest와 @app.post("/chat") 코드는 기존(텍스트만 뽑아내는 버전)과 동일하게 유지 ---
class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    inputs = {"messages": [("user", request.query)]}
    
    response_messages = []
    async for event in travel_agent.astream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        
        clean_text = ""
        if isinstance(message.content, list):
            for part in message.content:
                if isinstance(part, dict) and "text" in part:
                    clean_text += part["text"]
        else:
            clean_text = message.content

        response_messages.append({
            "role": message.type,
            "content": clean_text
        })
        message.pretty_print()

    return {"reply": response_messages[-1]["content"], "internal_steps": response_messages}