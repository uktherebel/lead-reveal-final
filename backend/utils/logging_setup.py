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

