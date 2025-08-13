from typing import Dict, Any, List
import logging
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.workers.base_worker import BaseWorker
from langchain_core.prompts import ChatPromptTemplate

# Temporarily disable sandboxed validation due to dependency issues
try:
    from validation.sandboxed_validator import SandboxedCodeValidator
    SANDBOXING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Sandboxed validation unavailable: {e}")
    SandboxedCodeValidator = None
    SANDBOXING_AVAILABLE = False

logger = logging.getLogger(__name__)

class ValidatedSolutionWorker(BaseWorker):
    """
    Worker that generates code and validates it in sandbox.
    """

    def _setup(self):
        """Initialize validator and prompts"""
        self.validator = None  # Lazy initialization
        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert programming instructor.
            Generate clear, educational code that:
            1. Solves the problem correctly
            2. Includes comprehensive comments
            3. Handles edge cases
            4. Uses descriptive variable names
            5. Follows best practices"""),
            ("human", "Task: {task}\nDifficulty: {difficulty}\nGenerate a complete solution:")
        ])

    def _ensure_validator(self):
        if self.validator is None and self.settings.enable_sandboxing and SANDBOXING_AVAILABLE:
            self.validator = SandboxedCodeValidator()

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and validate code solution.
        Process:
        1. Generate code with LLM
        2. Validate in sandbox
        3. Retry with feedback if validation fails
        """
        task = input_data.get('task_description')
        difficulty = input_data.get('difficulty_level', 'intermediate')
        max_attempts = input_data.get('max_attempts', 3)

        for attempt in range(max_attempts):
            try:
                # Generate code
                logger.info(f"Generating code, attempt {attempt + 1}/{max_attempts}")
                code = await self._generate_code(task, difficulty)

                # Validate if sandboxing is enabled and available
                if self.settings.enable_sandboxing and SANDBOXING_AVAILABLE:
                    self._ensure_validator()

                    # Create test cases based on task
                    test_cases = self._generate_test_cases(task)

                    # Validate code
                    validation = await self.validator.validate_complete(code, test_cases)

                    if validation['valid']:
                        return {
                            'success': True,
                            'code': code,
                            'validation': validation,
                            'attempts': attempt + 1
                        }
                    else:
                        # Use validation feedback for next attempt
                        task = f"{task}\n\nPrevious attempt failed: {validation['error']}\nPlease fix."
                else:
                    # No validation, return generated code
                    return {
                        'success': True,
                        'code': code,
                        'validation': None,
                        'attempts': attempt + 1
                    }

            except Exception as e:
                logger.error(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    return await self.handle_error(e, input_data)

        return {
            'success': False,
            'error': 'Max attempts reached without valid solution',
            'attempts': max_attempts
        }

    async def _generate_code(self, task: str, difficulty: str) -> str:
        """Generate code using LLM"""
        chain = self.generation_prompt | self.llm
        response = await chain.ainvoke({
            'task': task,
            'difficulty': difficulty
        })
        return response.content

    def _generate_test_cases(self, task: str) -> List[Dict[str, Any]]:
        """
        Generate test cases based on task description.

        Learning Point: Heuristic approach - we use patterns
        in the task description to generate relevant tests.
        """
        test_cases = []

        # Example heuristics for common programming tasks
        task_lower = task.lower()

        if 'reverse' in task_lower and 'string' in task_lower:
            test_cases = [
                {'call': 'reverse_string("hello")', 'expected': '"olleh"'},
                {'call': 'reverse_string("")', 'expected': '""'},
                {'call': 'reverse_string("a")', 'expected': '"a"'}
            ]
        elif 'fibonacci' in task_lower:
            test_cases = [
                {'call': 'fibonacci(0)', 'expected': '0'},
                {'call': 'fibonacci(1)', 'expected': '1'},
                {'call': 'fibonacci(5)', 'expected': '5'}
            ]
        elif 'sort' in task_lower:
            test_cases = [
                {'call': 'sort_list([3,1,2])', 'expected': '[1,2,3]'},
                {'call': 'sort_list([])', 'expected': '[]'},
                {'call': 'sort_list([1])', 'expected': '[1]'}
            ]
        else:
            # Generic test case
            logger.warning(f"No specific test cases for task: {task}")
            test_cases = [
                {'call': 'solution()', 'expected': 'None'}
            ]

        return test_cases
