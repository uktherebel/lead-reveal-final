from src.state.schemas import LearningState


def should_continue_after_generation(state: LearningState) -> str:
    """
    Decide next step after code generation.
    """
    if state.get('error'):
        return 'handle_error'
    elif state.get('validated_code'):
        return 'decompose'
    elif state.get('code_solution'):
        return 'validate'
    else:
        return 'retry_generation'

def should_continue_after_decomposition(state: LearningState) -> str:
    """Decide whether to start questioning or finalize"""
    if state.get('error'):
        return 'handle_error'
    elif state.get('total_steps', 0) > 0:
        return 'start_questioning'
    else:
        return 'finalize'