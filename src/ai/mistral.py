import os 
from mistralai import MistralClient
from .base import AIPlatform

class Mistral(AIPlatform): 
  def __init__(self, api_key : str, system_prompt: str = ""): 
    self.client = MistralClient(api_key=api_key)
    self.system_prompt = system_prompt 


  def chat(self, prompt: str) -> str: 
    messages = []
    if self.system_prompt:
      messages.append({
        'role': 'system', 
        'content': self.system_prompt
      })
    messages.append(
      {
        'role': 'user', 
        'content': prompt
      }
    )
    response = self.client.chat(model="mistral-tiny", messages=messages)
    return response.choices[0].message.content