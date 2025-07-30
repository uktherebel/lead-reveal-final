import logging, os, json, traceback
from datetime import datetime
from functools import wraps
from typing import Optional 

class ColouredFormatter(logging.Formatter):
  colours = {
    'grey': '\x1b[38;21m', 
    'yellow': "\x1b[33;21m", 
    'red': "\x1b[31;21m", 
    'bold_red': '\x1b[31;1m', 
    'green': '\x1b[32;21m',
    'reset': "\x1b[0m",
  }

  reset = colours['reset']

  FORMATS = {
    logging.DEBUG: colours['grey'],
    logging.INFO:colours['green'],
    logging.WARNING: colours['yellow'], 
    logging.ERROR: colours['red'], 
    logging.CRITICAL: colours['bold_red'],
  }

  for key, value in FORMATS.items(): 
    FORMATS[key] = value + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + reset

  def format(self, record): 
    log_format = self.FORMATS.get(record.levelno)
    formatter = logging.Formatter(log_format)
    return formatter.format(record)

def setup_logging(log_level: str = 'INFO') -> logging.Logger: 
  os.makedirs('logs', exist_ok=True)

  logger = logging.getLogger('cognitive learning')
  logger.setLevel(getattr(logging, log_level.upper()))

  logger.handlers = []

  file_handler = logging.FileHandler(
    f'logs/app_{datetime.now():%Y%m%d_%H%M%S}.log', 
  )
  file_handler.setLevel(logging.DEBUG)
  file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
  file_handler.setFormatter(file_formatter)

  console_handler = logging.StreamHandler()
  console_handler.setLevel(logging.INFO)
  console_handler.setFormatter(ColouredFormatter())

  logger.addHandler(file_handler)
  logger.addHandler(console_handler)

  return logger 

logger = setup_logging()

