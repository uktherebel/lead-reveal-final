from fastapi import FastAPI, Depends
from typing import Annotated

app = FastAPI()

class Logger: 
  def log(self, message: str): 
    print(f"Logging message: {message}")

def get_logger(): 
  return Logger()

logger_dependency = Annotated[Logger, Depends(get_logger)]

app.get('/log/{message}')
def log_message(message: str, logger: logger_dependency): 
  # logger = Logger()
  logger.log(message)
  return message; 


# imagine many different use the logger class...doing what we did above means instantiating a new logger instance every time...


class EmailService: 
  def send_email(self, recipient: str, message: str):
    print(f"Sending email to {recipient}: {message}")

def get_email_service(): 
  return EmailService()

email_service_dependency = Annotated[EmailService, Depends(get_email_service)]

def send_email(recipient: str, message: str, email_service: email_service_dependency): 
  email_service.send_email(recipient, message)


