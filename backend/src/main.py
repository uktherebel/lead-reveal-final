from typing import Annotated
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    status,
    WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse 
import os, json
from ai.openai import OpenAIWrapper
from ai.qwen import Qwen
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from typing import List, Annotated
import numpy as np 
# import ollama
# from .pydantic.base import ChatRequest, ChatResponse
# from .pydantic.lead_and_reveal import PlanItem, PlanResponse, LeadAndRevealRequest, LeadAndRevealResponse
from datetime import datetime
from Langchain.llm_config import create_code_chain
import logging
load_dotenv()

# --- App Initialization ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

logger = logging.getLogger(__name__)

# --- AI Configuration ---
def load_system_prompt(): 
   try: 
      with open('src/prompts/teacher.md', 'r') as f: 
         return f.read()

   except FileNotFoundError: 
      return None 
   
system_prompt = load_system_prompt()
openai_api_key = os.getenv("OPENAI_API_KEY")
qwen_api_key = os.getenv('QWEN_API_KEY')

if not qwen_api_key: 
   raise ValueError('QWEN_API_KEY environment variable not set.')

ai_platform = Qwen(
   api_key=qwen_api_key, 
   # system_prompt=system_prompt
)

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"Client connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            logger.info(f"Received: {request}")
            
            if request.get("command") == "generate":
                try:
                    # Generate code using your chain
                    llm, prompt_template = create_code_chain(request["task"])
                    result = llm.invoke(
                        prompt_template.invoke(
                            {
                                'task': request["task"]
                            }
                        )
                    )
                    code = result.content
                    
                    response = {
                        "status": "success",
                        "code": code,
                        "requestId": request.get("requestId")
                    }
                except Exception as e:
                    logger.error(f"Generation error: {e}")
                    response = {
                        "status": "error",
                        "error": str(e),
                        "requestId": request.get("requestId")
                    }
                
                await websocket.send_text(json.dumps(response))
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")

@app.post('/generate')
async def generate_code(task: str): 
    llm, prompt_template = create_code_chain()
    result = llm.invoke(
        prompt_template.invoke(
            {
                'task': task
            }
        )
    )
    return {'code': result.content}

# @app.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest):
#     result = ai_platform.chat(request.prompt)
#     return ChatResponse(
#       explanation = result
#     )

# @app.post("/lead-and-reveal", response_model=LeadAndRevealResponse)
# async def lead_and_reveal(request: LeadAndRevealRequest):
#     if request.answer:
#         # 2. If answer is provided, evaluate it
#         evaluation = ai_platform.evaluate_answer(request.code_solution, request.answer)
#         return LeadAndRevealResponse(question="", evaluation=evaluation)
#     else:
#         # 1. If no answer, generate a question
#         question = ai_platform.lead_and_reveal(request.code_solution)
#         return LeadAndRevealResponse(question=question)

# ai_platform1 = OpenAIWrapper(api_key=openai_api_key)

# @app.post('/event_identifier')
# async def get_event_details(request: ChatRequest):
#     result = ai_platform1.chat(request.prompt)
#     return result

