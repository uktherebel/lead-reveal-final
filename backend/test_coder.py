#!/usr/bin/env python3

import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add backend to path
backend_path = os.path.abspath(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.workers.coder import CodeWorker

def test_coder():
    task = """
    Write a function that finds the length of the longest valid parentheses substring.
    Given a string containing just '(' and ')' characters.
    
    Example: "(()" should return 2 (for "()")
    """
    
    worker = CodeWorker()
    result = worker.process_sync({
        "task_description": task,
        "difficulty_level": "intermediate",
        "max_attempts": 1
    })
    
    print("=== RESULT ===")
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Generated code:\n{result.get('code')}")
    else:
        print(f"Error: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    test_coder()