from langchain.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

def create_code_chain(): 
  llm = ChatOllama(
    model='qwen2.5-coder:7b',
    base_url='http://localhost:11434'
  )

  template = """
    Write python code to: {task}\n\nCode:
  """
  prompt_template = ChatPromptTemplate.from_template(template)
  return (llm, prompt_template)


# uvicorn src.main:app --reload