from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser 
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from dotenv import load_dotenv
from typing import List, Dict
from src.prompts.decomposition_prompt import decomposition_prompt

load_dotenv()

class Decomposer: 
  def __init__(self): 
      self.llm = ChatOpenAI(
      model='gpt-4o', 
      temperature = 0.4,
   )

  def _get_format_instructions(self): 
      # Define the structure more explicitly for a list
      steps_schema = ResponseSchema(
          name='steps',
          description='''A JSON array where each item is an object with these exact keys:
          - "step_number" (integer): The number of the step, increment by 1
          - "explanation" (string): What does this step entail? What's the justification for having this step?
          - "concept" (string): What are the concepts involved for this particular step?
          - "cognitive_load" (integer): [1-5, where 1=easy, 5=complex]
          
          Example format:
          {
            "steps": [
              {
                "code": str,
                "step_number": 1,
                "explanation": "...",
                "concept": "...", 
                "cognitive_load": 3
              },
              {
                "code": str,
                "step_number": 2,
                "explanation": "...",
                "concept": "...", 
                "cognitive_load": 1

              }
            ]
          }''',
          type='array'
      )
          
      response_schemas = [steps_schema]
      output_parser = StructuredOutputParser.from_response_schemas(response_schemas=response_schemas)
      format_instructions = output_parser.get_format_instructions()
      return format_instructions, output_parser

  def generate_steps(self, code: str) -> List[Dict]: 
   format_instructions, output_parser = self._get_format_instructions()
   
   chain = decomposition_prompt | self.llm | StrOutputParser()
   response = chain.invoke({
      'code': code, 
      'format_instructions': format_instructions,
      })
   formatted_response = output_parser.parse(response) 
   return formatted_response

if __name__ == "__main__": 
  pass 