from openai import OpenAI
from .base import AIPlatform
import numpy as np
from pydantic import BaseModel

class Event(BaseModel): 
    name: str 
    date: str 
    description: str
    location: str = None 

class OpenAIWrapper(AIPlatform): 
  def __init__(self, api_key: str, system_prompt: str = ""): 
    self.client = OpenAI(api_key=api_key)
    self.system_prompt = system_prompt


  def chat(self, prompt : str) -> str: 
    messages = []
    if self.system_prompt: 
      messages.append({
        'role': 'system', 
        'content': self.system_prompt
      })

    messages.append({
      'role': 'user', 
      'content': prompt
    })

    response = self.client.chat.completions.parse (
      model = 'gpt-4o', 
      messages = messages, 
      response_format=Event
    )
    return response.choices[0].message.content

    # response = self.client.chat.completions.create(
    #     model="gpt-4o",
    #     messages=messages,
    #     max_tokens=200,
    #     temperature=0.3,
    #     logprobs=True,
    #     top_logprobs=5,  
    # )
    # completion = response.choices[0]
    # tokens = completion.logprobs.content.tokens
    # logprobs = completion.logprobs.content.token_logprobs

    # mean_logprob = np.mean(logprobs)
    # trust_score = round(np.exp(mean_logprob) * 100, 2)

    # return {
    #     "explanation": completion.message.content,
    #     "tokens": tokens,
    #     "logprobs": logprobs,
    #     "trust_score": trust_score
    # }




