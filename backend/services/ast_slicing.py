import ast
from typing import List, Dict, Any, Optional


def _get_end_lineno(node: ast.AST) -> Optional[int]:
    return getattr(node, "end_lineno", getattr(node, "lineno", None))


def _slice_source(lines: List[str], start: int, end: int) -> str:
    start = max(1, start)
    end = max(start, end)
    return "".join(lines[start - 1 : end])


def _concept_for(node: ast.AST) -> str:
    if isinstance(node, (ast.For, ast.While)):
        return "iteration"
    if isinstance(node, ast.If):
        return "conditional branching"
    if isinstance(node, ast.Try):
        return "error handling"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return "initialization"
    if isinstance(node, ast.Return):
        return "result construction"
    if isinstance(node, ast.FunctionDef):
        return "function definition"
    return "computation"


def _is_docstring_expr(node: ast.AST) -> bool:
    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str)


def _is_main_guard(node: ast.AST) -> bool:
    # if __name__ == "__main__": ...
    if not isinstance(node, ast.If):
        return False
    try:
        left = node.test.left  # type: ignore[attr-defined]
        right = node.test.comparators[0]  # type: ignore[attr-defined]
        return (
            isinstance(node.test, ast.Compare)
            and isinstance(left, ast.Name)
            and left.id == "__name__"
            and isinstance(right, ast.Constant)
            and str(right.value) == "__main__"
        )
    except Exception:
        return False


def _is_io_call(call: ast.Call) -> bool:
    # Very small filter for IO/printing etc.
    def _name(n: ast.AST) -> str:
        if isinstance(n, ast.Name):
            return n.id
        if isinstance(n, ast.Attribute):
            return f"{_name(n.value)}.{n.attr}"
        return ""

    name = _name(call.func)
    return name in {"print", "input", "open"} or name.startswith("logging") or name.endswith(".write")


def _intrinsic_load(node: ast.AST, depth: int = 0) -> int:
    score = 1
    if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
        score += 1
    # Nesting depth heuristic
    score += min(2, max(0, depth - 1))
    # Condition complexity
    cond = None
    if isinstance(node, (ast.If, ast.While)):
        cond = node.test
    if isinstance(cond, (ast.BoolOp, ast.Compare)):
        score += 1
    # Multiple targets or ops
    if isinstance(node, (ast.Assign, ast.AugAssign)):
        score += 1 if isinstance(node, ast.Assign) and len(node.targets) > 1 else 0
    return max(1, min(5, score))


def _collect_units_from_body(body: List[ast.stmt]) -> List[ast.AST]:
    units: List[ast.AST] = []
    i = 0
    # Skip docstring if present
    if i < len(body) and _is_docstring_expr(body[i]):
        i += 1
    # Merge leading simple assignments as initialization block
    init_start = None
    init_end = None
    while i < len(body) and isinstance(body[i], (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        node = body[i]
        init_start = init_start or getattr(node, "lineno", None)
        init_end = _get_end_lineno(node)
        i += 1
    if init_start is not None and init_end is not None:
        # Create a synthetic Assign node covering the block
        synth = ast.Assign(lineno=init_start, col_offset=0, targets=[], value=ast.Name(id="_", ctx=ast.Load()))
        setattr(synth, "end_lineno", init_end)
        units.append(synth)

    # Remaining statements as individual units (skip pure IO expr calls)
    for node in body[i:]:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and _is_io_call(node.value):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        units.append(node)
    return units


def build_steps_from_code(source: str, language: str = "python") -> List[Dict[str, Any]]:
    """AST-based slicer for Python code only.
    For non-Python languages, returns empty list (will fallback to LLM-only).
    
    Returns: list of dicts with step_number, code_snippet, concept, intrinsic_load
    """
    if language.lower() != "python":
        # Only Python is supported by AST approach
        return []
    
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    lines = source.splitlines(keepends=True)

    # Walk functions; if none, use module body
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    modules: List[ast.stmt] = [] if functions else tree.body

    steps: List[Dict[str, Any]] = []
    step_no = 1

    if functions:
        for fn in functions:
            # 1) Function signature as a step (single line)
            sig_line = fn.lineno
            sig_snippet = _slice_source(lines, sig_line, sig_line)
            steps.append(
                {
                    "step_number": step_no,
                    "code_snippet": sig_snippet,
                    "explanation": "",
                    "concept": "function definition",
                    "intrinsic_load": 2,
                    "reveal": False,
                }
            )
            step_no += 1

            # 2) Function body units (skip docstring handled in collector)
            for node in _collect_units_from_body(fn.body):
                start = getattr(node, "lineno", None)
                end = _get_end_lineno(node)
                if start is None or end is None:
                    continue
                snippet = _slice_source(lines, start, end).rstrip() + "\n"
                concept = _concept_for(node)
                load = _intrinsic_load(node)
                steps.append(
                    {
                        "step_number": step_no,
                        "code_snippet": snippet,
                        "explanation": "",
                        "concept": concept,
                        "intrinsic_load": load,
                        "reveal": False,
                    }
                )
                step_no += 1
    else:
        for node in _collect_units_from_body(modules):
            if _is_main_guard(node):
                continue
            start = getattr(node, "lineno", None)
            end = _get_end_lineno(node)
            if start is None or end is None:
                continue
            snippet = _slice_source(lines, start, end).rstrip() + "\n"
            concept = _concept_for(node)
            load = _intrinsic_load(node)
            steps.append(
                {
                    "step_number": step_no,
                    "code_snippet": snippet,
                    "explanation": "",
                    "concept": concept,
                    "intrinsic_load": load,
                    "reveal": False,
                }
            )
            step_no += 1

    return steps