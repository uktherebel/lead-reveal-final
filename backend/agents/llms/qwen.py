from .base import AIPlatform
import ollama 


class Qwen(AIPlatform): 
  def __init__(self, api_key: str, system_prompt: str = ""): 
    self.system_prompt = system_prompt


  def chat(self, prompt: str) -> str: 
    messages = []
    if self.system_prompt: 
      messages.append({
        'role': 'system', 
        'content': self.system_prompt
      })
    messages.append({
      'role': 'user', 
      'content': prompt,
    })
    response = ollama.chat(
      model='qwen2.5-coder:7b', 
      messages=messages,  
      # stream=True
    )
    return response['message']['content']

  # def lead_and_reveal(self, code_solution: str) -> str:
  #     # Prepare the prompt for Qwen to generate a question
  #     prompt = f"""
  #     Decompose the following code solution into a hierarchical JSON, explaining
  #     decisions at the subgoal level to each line of code. Then, ask a guiding
  #     question based on your analysis.

  #     Code solution:{code_solution}
  #     """
  #     response = self.chat(prompt)
  #     return response

  # def evaluate_answer(self, code_solution: str, answer: str) -> str:
  #     # Prepare the prompt for Qwen to evaluate the answer
  #     prompt = f"""
  #     The user was asked a question about the following code:
  #     {code_solution}

  #     The user's answer is:
  #     {answer}

  #     Is this answer correct? Provide a brief evaluation.
  #     """
  #     response = self.chat(prompt)
  #     return response