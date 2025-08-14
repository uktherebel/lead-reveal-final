from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser 
from src.prompts.educational_prompts import EDUCATIONAL_CODE_PROMPT
from dotenv import load_dotenv
load_dotenv()

class Coder: 
  def __init__(self): 
      self.llm = ChatOllama(
      model='qwen2.5-coder:7b', 
      temperature = 0.2,
      base_url='http://localhost:11434',
      top_p=0.95,
   )

  def generate_code(self, task: str): 
    prompt = EDUCATIONAL_CODE_PROMPT
    chain = prompt | self.llm | StrOutputParser()
    return chain.invoke({'task': task}) 


