from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser 
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from dotenv import load_dotenv

load_dotenv()

def _llm_for_decomposition(): 
   llm = ChatOpenAI(
      model='gpt-4o', 
      temperature = 0.4,
   )
   return llm 

def _llm(): 
    llm = ChatOllama(
    model='qwen2.5-coder:7b',
    base_url='http://localhost:11434', 
    temperature=0.2,
    num_ctx=4096,
    top_p=0.95,

  )
    return llm 

def _get_format_instructions(): 
    # Define the structure more explicitly for a list
    steps_schema = ResponseSchema(
        name='steps',
        description='''A JSON array where each item is an object with these exact keys:
        - "step_number" (integer): The number of the step, increment by 1
        - "explanation" (string): What does this step entail? What's the justification for having this step?
        - "concept" (string): What are the concepts involved for this particular step?
        
        Example format:
        {
          "steps": [
            {
              "step_number": 1,
              "explanation": "...",
              "concept": "..."
            },
            {
              "step_number": 2,
              "explanation": "...",
              "concept": "..."
            }
          ]
        }''',
        type='array'
    )
        
    response_schemas = [steps_schema]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas=response_schemas)
    format_instructions = output_parser.get_format_instructions()
    return format_instructions, output_parser

def create_code_chain(task: str): 
  llm = _llm()
  prompt = PromptTemplate(
        input_variables=["task"],
        template="""You are an expert Python programmer and teacher.

                  Generate clean, educational Python code for the following task:
                  {task}

                  Requirements:
                  1. Include a proper function definition
                  2. Add descriptive docstring
                  3. Include helpful comments
                  4. Handle edge cases
                  5. Follow Python best practices

                  Code:
                  """
    )
  chain = prompt | llm | StrOutputParser()
  return chain.invoke({'task': task}) 

def decomposition_chain(code: str): 
   llm = _llm_for_decomposition()
   format_instructions, output_parser = _get_format_instructions()
   decomposition_prompt = ChatPromptTemplate.from_template(
      """ 
        For the following code / programming problem: 
          - Decompose the code into meaningful, atomic steps that promote critical thinking and active learning.
        Code: {code}

        For each step, store the information in this format: 
        {format_instructions}
      """
   )
   chain = decomposition_prompt | llm | StrOutputParser()
   response = chain.invoke({
      'code': code, 
      'format_instructions': format_instructions,
      })
   formatted_response = output_parser.parse(response) 
   return formatted_response

