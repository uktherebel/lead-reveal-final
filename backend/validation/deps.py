from typing import Dict, List, Any, Set
import ast 
import sys 

def _collect_imports_ast(code: str) -> Set[str]: 
  try: 
    tree = ast.parse(code)
  except SyntaxError: 
    return set()
  
  packages: Set[str] = set()

  class ImportVisitor(ast.NodeVisitor): 
    def visit_Import(self, node: ast.Import): 
      for alias in node.names: 
        packages.add(alias.name.split('.')[0])
      self.generic_visit(node)


    def visit_ImportForm(self, node: ast.ImportFrom): 
      if node.module: 
        packages.add(node.module.split('.')[0]) 
      self.generic_visit(node)

  ImportVisitor().visit(tree)
  return packages

def _is_system_import(package: str) -> bool: 
  """ Checks whether a single import is a part of the system imports """
  standard_modules = getattr(sys, 'stdlib_module_names', None)
  if standard_modules: 
    return package in standard_modules
  
  standard_modules_fallback = {
    "sys", "os", "math", "random", "re", "json", "time", "datetime",
    "pathlib", "collections", "itertools", "functools", "typing",
    "statistics", "subprocess", "asyncio", "heapq", "logging", "importlib",
    "dataclasses", "argparse", "unittest", "threading", "multiprocessing",
    "http", "urllib", "email", "decimal", "fractions", "hashlib",
    "hmac", "gzip", "bz2", "lzma", "sqlite3", "enum", "inspect",
  }
  return package in standard_modules_fallback or package in dir(sys.modules['builtins'])
  


if  __name__ == "__main__": 
  code = """ 
import os
import sys
import math
import json
import time
import random
import string
import re
import uuid
import base64
import hashlib
import logging
import threading
import asyncio
import concurrent.futures
import statistics
import functools
import itertools
import tempfile
import shutil
import pathlib
import datetime
import collections
import inspect
import socket
import http.client
import urllib.request
import urllib.parse
import zipfile
import tarfile
import mimetypes
import csv
import sqlite3
import subprocess
import platform
import ctypes
import signal
import typing
import pprint

# Third-party imports (these would require pip install)
try:
    import requests
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import bs4
    from bs4 import BeautifulSoup
    import yaml
    import pytz
    import dateutil
    from PIL import Image
    import flask
    from flask import Flask, jsonify
    import fastapi
    from fastapi import FastAPI
    import sqlalchemy
    import sklearn
    import tensorflow as tf
    import torch
    import plotly.express as px
except ImportError:
    print("Some third-party packages are not installed. Install them with pip if needed.")

# Random functional chaos
def random_string(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def compute_hash(data: str):
    return hashlib.sha256(data.encode()).hexdigest()

def async_print_numbers():
    async def inner():
        for i in range(5):
            await asyncio.sleep(0.5)
            print(f"Number: {i}")
    return asyncio.run(inner())

def random_dataframe():
    df = pd.DataFrame({
        'id': [uuid.uuid4() for _ in range(5)],
        'value': np.random.rand(5),
        'timestamp': pd.date_range(start="2025-01-01", periods=5, freq="D")
    })
    print(df)
    return df

def scrape_example():
    url = "https://example.com"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    print("Title:", soup.title.string if soup.title else "No title")
"""

imports = _collect_imports_ast(code)
print(imports)

system_imports = set(filter(_is_system_import, imports))

third_party = imports - system_imports
print(third_party)