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
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from typing import List, Annotated
import numpy as np 
import json, logging 
from src.graphs.simple_graph import create_simple_graph
from src.state.schemas import create_initial_state
import logging
from contextlib import asynccontextmanager
load_dotenv()

logger = logging.getLogger(__name__)

active_graphs = {}

@asynccontextmanager 
async def lifespan(app: FastAPI): 
    logger.info("Starting application...")

    yield 

    logger.info('Shutting down...')
    active_graphs.clear()

app = FastAPI(title='Cognitive Learning System', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# # --- AI Configuration ---
# def load_system_prompt(): 
#    try: 
#       with open('src/prompts/teacher.md', 'r') as f: 
#          return f.read()

#    except FileNotFoundError: 
#       return None 
   
# system_prompt = load_system_prompt()
openai_api_key = os.getenv("OPENAI_API_KEY")
qwen_api_key = os.getenv('QWEN_API_KEY')

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"Client connected")
    session_id = None
    
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            logger.info(f"Received: {request}")
            
            if request.get("command") == "generate":
                try:
                    # Create new learning session
                    task = request.get('task', '')
                    technique = request.get('technique', 'lead-and-reveal')
                    request_id = request.get('requestId')

                    # create init state 
                    initial_state = create_initial_state(task, technique)
                    session_id = initial_state['session_id']

                    # create and store graph 
                    graph = create_simple_graph()
                    active_graphs[session_id] = graph

                    # running the graph 
                    try: 
                        final_state = await graph.ainvoke(initial_state)

                        # send results to user 
                        if final_state.get('code_solution'): 
                            response = {
                                "status": "success",
                                "code": final_state['code_solution'],
                                "steps": final_state.get('steps', []),
                                "messages": final_state.get('messages', []),
                                "requestId": request_id
                            }
                        else: 
                            response = {
                                "status": "error",
                                "error": final_state.get('error', 'Failed to generate code'),
                                "requestId": request_id
                            }

                    except Exception as e: 
                        logger.error(f'Graph execution error: {e}')
                        response = {
                            "status": "error",
                            "error": str(e),
                            "requestId": request_id
                        }
                             
                    finally: 
                        if session_id in active_graphs: 
                            del active_graphs[session_id]
                         
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
        if session_id and session_id in active_graphs: 
            del active_graphs[session_id]

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

