from typing import List, Dict, Any

try:
    from tree_sitter_languages import get_parser
except Exception as e:  # pragma: no cover
    get_parser = None  # type: ignore


def build_steps_from_code(source: str, language: str = "python") -> List[Dict[str, Any]]:
    """Tree-sitter powered slicer (simple). Falls back to empty if parser missing.

    Currently tuned for Python grammar node names.
    """
    if get_parser is None:
        return []

    parser = get_parser(language)
    tree = parser.parse(bytes(source, "utf-8"))
    root = tree.root_node
    lines = source.splitlines(keepends=True)

    def slice_node(n):
        start = n.start_point[0]
        end = n.end_point[0]
        return "".join(lines[start : end + 1])

    steps: List[Dict[str, Any]] = []

    # Simple selectors for python
    CONTROL = {
        "if_statement": "conditional branching",
        "for_statement": "iteration",
        "while_statement": "iteration",
        "try_statement": "error handling",
        "return_statement": "result construction",
        "assignment": "initialization",
        "augmented_assignment": "initialization",
        "function_definition": "function definition",
    }

    # Traverse top-level functions; otherwise module body
    top_funcs = [c for c in root.children if c.type == "function_definition"]
    nodes = top_funcs if top_funcs else [c for c in root.children if c.type != "import_statement"]

    step_no = 1
    for node in nodes:
        if node.type == "function_definition":
            # def line
            snippet = slice_node(node)
            steps.append(
                {
                    "step_number": step_no,
                    "code_snippet": snippet.splitlines(True)[0],
                    "explanation": "",
                    "concept": CONTROL["function_definition"],
                    "intrinsic_load": 2,
                    "reveal": False,
                }
            )
            step_no += 1
            # body children
            body = [c for c in node.children if c.start_point[0] > node.start_point[0]]
            for c in body:
                concept = CONTROL.get(c.type)
                if not concept:
                    continue
                steps.append(
                    {
                        "step_number": step_no,
                        "code_snippet": slice_node(c),
                        "explanation": "",
                        "concept": concept,
                        "intrinsic_load": 3 if concept != "initialization" else 2,
                        "reveal": False,
                    }
                )
                step_no += 1
        else:
            concept = CONTROL.get(node.type)
            if not concept:
                continue
            steps.append(
                {
                    "step_number": step_no,
                    "code_snippet": slice_node(node),
                    "explanation": "",
                    "concept": concept,
                    "intrinsic_load": 3 if concept != "initialization" else 2,
                    "reveal": False,
                }
            )
            step_no += 1

    return steps
