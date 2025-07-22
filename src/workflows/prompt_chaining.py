from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List
import os, json
from dotenv import load_dotenv
import ollama
load_dotenv()



class AnalyseRequest(BaseModel): 
  """First LLM call: Analyse the user request"""

  description: str = Field(description="What is the user asking me to do code?")

  confidence_score: float = Field(description="Confidence score between 0 and 1")


class SubGoal(BaseModel): 
  """Second LLM call: Decomposing the programming problem into multiple sub-goals"""

  sub_goal: str = Field(description="A human-readable subgoal")
  line_span: str = Field(description="1-based indices of lines responsible")
  rationale: str = Field(description="Why was this goal generated and how is it relevant to the question?")


class SocraticQuestion(BaseModel): 
   """Second LLM call: Authoring one Socratic question for each sub-goal"""
   question: str 
   choice = List[str]
   correct_index: int = Field(ge=0)
   next_line_code: str = Field(description="Single line of code to reveal")


class Evaluation(BaseModel): 
  evaluation: str 
  hint: str 
  revealed_line: str 

# -----------------------------------------------------------
# Step 2: Define the functions -----------------------------------------------------------

def generate_subgoal(user_input: str) -> SubGoal:
  prompt =  f"""
You are a pedagogy-oriented coding tutor.

Analyse the user input and produce ONE JSON object with the shape:
{SubGoal.model_schema_json(indent=2)}

CONSTRAINTS:
- Output ONLY valid JSON, no markdown fences, no extra keys.
- Fill in "step_number", "description", and "rationale".
"""
  response = ollama.chat(
    model='qwen2.5-coder:7b', 
    messages = [
      {
        'role': 'system',
        'content': prompt,
        }, 
      {
        'role': 'user', 
        'content': user_input
      }
    ]
  )
  try: 
    raw_json = json.loads(response['message']['content'])
    return SubGoal(**raw_json)
  except (json.JSONDecodeError, ValidationError) as e: 
    raise RuntimeError(f"Could not parse LLM output: {e}")


def generate_socratic_question(subgoal: SubGoal) -> SocraticQuestion: 
  prompt =  f"""
      You are an expert coding tutor who uses Socratic questioning.

      TASK
      ----
      Given ONE sub-goal from a larger programming problem, you must
      author exactly ONE multiple-choice question (four options).  
      The question should check whether the learner knows what needs
      to be done **before** the corresponding line of code is revealed.

      FORMAT
      ------
      Respond ONLY with valid JSON that satisfies this schema:

      {SocraticQuestion.model_json_schema(indent=2)}

      RULES
      -----
      * Do NOT add markdown fences around the JSON.
      * Make sure there are exactly four options.
      * The explanation MUST reference the *concept* behind the right answer
        (e.g. “We need a while-loop here because …”).  
      * Keep the question short and action-oriented (“What should run next?”).

      SUB-GOAL
      ---------
      {str(subgoal.model_dump())}
      """
  response = ollama.chat(
    model='qwen2.5-coder:7b', 
    messages = [
      {
        'role': 'system',
        'content': prompt,
        }, 
      {
        'role': 'user', 
        'content': str(subgoal.model_dump()),
      }
    ]
  )

  try: 
    raw_json = json.loads(response['message']['content'])
    return SocraticQuestion(**raw_json)
  except (json.JSONDecodeError, ValidationError) as e: 
    raise RuntimeError(f"Could not parse LLM output: {e}")
  

# def 
  