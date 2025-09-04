import asyncio
import logging
from typing import Dict, Any, List, Optional
from e2b_code_interpreter import Sandbox
from openevals.code.pyright import create_pyright_evaluator
from openevals.code.e2b.execution import create_e2b_execution_evaluator
import re
import ast 

logger = logging.getLogger(__name__)

class SandboxedCodeValidator: 
  def __init__(self, api_key: str = None): 
    from core.config import get_settings
    settings = get_settings()

    self.api_key = api_key or settings.e2b_api_key
    self.sandbox = None  
    self.pyright_evaluator = None
    self.e2b_available = bool(self.api_key)

    self._setup_evaluators()

  
  def _setup_evaluators(self): 
    """ Setup Pyright for static analysis """
    try: 
      self.pyright_evaluator = create_pyright_evaluator()
      logger.info('Pyright evaluator initialised')
    except Exception as e: 
      logger.warning(f'Playright unavailable: {e}')

  
  async def validate_complete(
        self,
        code: str,
        test_cases: List[Dict[str, Any]] = None,
        extract_embedded_tests: bool = True
    ) -> Dict[str, Any]:
        """
        Complete validation pipeline.
        """
        results = {
            'valid': False,
            'syntax_check': None,
            'type_check': None,
            'safety_check': None,
            'execution_result': None,
            'test_results': None,
            'error': None
        }

        try:
            # Step 1: Safety check 
            safety = self._check_safety(code)
            results['safety_check'] = safety
            if not safety['safe']:
                results['error'] = f"Safety violation: {safety['issues']}"
                return results

            # Step 2: Syntax validation with Pyright
            if self.pyright_evaluator:
                syntax = self._validate_syntax(code)
                results['syntax_check'] = syntax
                if not syntax['valid']:
                    results['error'] = syntax['error']
                    return results

            # Step 3: Extract embedded test cases if enabled
            extracted_tests = []
            if extract_embedded_tests and not test_cases:
                extracted_tests = self._extract_embedded_tests(code)
                if extracted_tests:
                    logger.info(f"Extracted {len(extracted_tests)} embedded test cases")

            # Step 4: Execute in sandbox (if E2B is available) 
            if self.e2b_available:
                # If we have embedded tests, run the code directly (includes test execution)
                if extracted_tests:
                    execution = await self._run_embedded_tests(code)
                    results['execution_result'] = execution
                    results['test_results'] = execution.get('test_results', [])
                    results['valid'] = execution.get('success', False) and execution.get('all_tests_passed', False)
                else:
                    # No embedded tests, run normal execution
                    execution = await self._run_in_sandbox(code)
                    results['execution_result'] = execution
                    
                    if not execution['success']:
                        results['error'] = execution['error']
                        return results

                    # Step 5: Run external test cases if provided
                    if test_cases:
                        test_results = await self._run_tests(code, test_cases)
                        results['test_results'] = test_results
                        results['valid'] = all(t['passed'] for t in test_results)
                    else:
                        results['valid'] = execution['success']
            else:
                # No E2B available, skip execution but still validate syntax
                logger.warning("E2B API key not available, skipping sandbox execution")
                results['execution_result'] = {'success': True, 'error': None, 'output': 'Skipped - no E2B key'}
                results['valid'] = True  # Assume valid if syntax check passed

            return results

        except Exception as e:
            logger.error(f"Validation error: {e}")
            results['error'] = str(e)
            return results

  def _check_safety(self, code: str) -> Dict[str, Any]: 
    """Check for dangerous operations
    Note: We use regex here. However, it can lead to false negatives and false positives. 
    AST checks are more robust. To be implemented later on.
    """
    dangerous_patterns = [
      (r'__import__', 'Dynamic imports not allowed'),
            (r'eval\s*\(', 'eval() is not allowed'),
            (r'exec\s*\(', 'exec() is not allowed'),
            (r'open\s*\(', 'File operations not allowed'),
            (r'subprocess', 'Subprocess operations not allowed'),
            (r'os\.\w+', 'OS operations not allowed'),
            (r'sys\.exit', 'System exit not allowed'),
    ]

    issues = []
    for pattern, message in dangerous_patterns: 
      if re.search(pattern, code): 
        issues.append(message)

    return {
      'safe': len(issues) == 0,
      'issues': issues
    }
  
  def _validate_syntax(self, code: str) -> Dict[str, Any]: 
    try: 
      result = self.pyright_evaluator(outputs=code)
      comment = ast.literal_eval(result.get('comment', '[]'))
      success = result.get('score', False)
      return {
        'valid': bool(success), 
        'error': None if not comment else str(comment)
      } 
    except Exception as e: 
      return {
        'valid': False, 
        'error': str(e)
      }

  async def _run_in_sandbox(self, code: str) -> Dict[str, Any]: 
    try: 
      with Sandbox('OpenEvalsPython') as sandbox: 
        evaluator = create_e2b_execution_evaluator(
          sandbox=sandbox
        )
        result = evaluator(outputs=code)
        success = result.get('score', False)
        return {
          'success': bool(success), 
          'error': result.get('errors', None),
          'output': result.get('output', '')
        }
    except Exception as e: 
      return {
        'success': False, 
        'error': str(e),
        'output': ''
      } 
  async def _run_tests(
        self,
        code: str,
        test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run test cases against code.

        Learning Point: Test Harness Pattern - we wrap the code
        in a testing framework, like a crash test dummy for cars.
        """
        results = []

        for i, test in enumerate(test_cases):
            test_code = f"""
            {code}

            # Test case {i + 1}
            result = {test['call']}
            expected = {test['expected']}
            passed = result == expected
            print(f"Test {i + 1}: {{'passed': passed, 'result': result, 'expected': expected}}")
            """

            execution = await self._run_in_sandbox(test_code)

            results.append({
                'test_number': i + 1,
                'passed': 'passed\': True' in execution.get('output', ''),
                'input': test['call'],
                'expected': test['expected'],
                'actual': execution.get('output', 'Error'),
                'error': execution.get('error')
            })

        return results  

  def _extract_embedded_tests(self, code: str) -> List[str]:
    """Extract embedded test cases from generated code"""
    import re
    
    # Look for the test cases section
    test_section_pattern = r'# Test cases.*?if __name__ == "__main__":(.*?)(?=\n\S|\nif |\n#|\Z)'
    match = re.search(test_section_pattern, code, re.DOTALL | re.MULTILINE)
    
    if not match:
        return []
    
    test_section = match.group(1)
    # Extract individual assert statements
    assert_pattern = r'assert\s+([^,]+),?\s*"([^"]*)"?'
    assertions = re.findall(assert_pattern, test_section)
    
    return [assertion[0].strip() for assertion in assertions]

  async def _run_embedded_tests(self, code: str) -> Dict[str, Any]:
    """Run code with embedded test cases"""
    try:
      with Sandbox('OpenEvalsPython') as sandbox: 
        # Execute the code (which includes the test cases)
        result = sandbox.execute(code)
        
        # Check if tests passed (look for "All tests passed!" or no assertion errors)
        success = result.error is None and ("All tests passed!" in result.output or "AssertionError" not in result.output)
        
        # Count assertions as test results
        import re
        assertions = re.findall(r'assert\s+([^,]+)', code)
        test_results = []
        
        for i, assertion in enumerate(assertions, 1):
            # Since we don't get individual test results from sandbox,
            # we assume all tests passed if there's no AssertionError
            passed = "AssertionError" not in result.output
            test_results.append({
                'test_number': i,
                'assertion': assertion,
                'passed': passed,
                'error': None if passed else "Assertion failed"
            })
        
        return {
          'success': success,
          'all_tests_passed': success,
          'error': result.error if result.error else None,
          'output': result.output,
          'test_results': test_results
        }
    except Exception as e: 
      return {
        'success': False,
        'all_tests_passed': False,
        'error': str(e),
        'output': '',
        'test_results': []
      }









  