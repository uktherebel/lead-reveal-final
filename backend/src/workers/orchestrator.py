import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json

from backend.src.workers.coder import CodeWorker
from decomposer import Decomposer
from question_writer import QuestionWriter  
from state.schemas import LearningState, LearningPhase
from core.config import get_settings

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LearningStep(BaseModel): 
  step_id: str 
  title: str 
  code_snippet: str 
  explanation: str 
  question: str
  answer_options: List[str]
  correct_answer: int 
  hint: Optional[str] = None 
  difficulty: int = Field(ge=1, le=5, default=3)

@dataclass 
class OrchestrationState: 
  pass