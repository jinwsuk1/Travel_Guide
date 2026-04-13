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
today_str = datetime.now().strftime("%Y년 %m월 %d일")
system_prompt = f"""
당신은 완벽한 일정과 정보를 제공하는 자율형 해외여행 비서 에이전트입니다.
오늘 날짜는 {today_str}입니다. 

사용자가 '오늘', '내일', '이번 주말' 등의 시점을 물어보면 반드시 위 날짜를 기준으로 실제 날짜를 계산하세요.
검색 도구를 사용할 때도 '내일 도쿄 날씨'라고 모호하게 검색하지 말고, '2026년 4월 14일 도쿄 날씨'처럼 구체적인 날짜를 포함해 검색하여 가장 정확하고 최신인 정보를 제공해야 합니다.
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