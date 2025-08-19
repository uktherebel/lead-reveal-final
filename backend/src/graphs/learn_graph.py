from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from src.graphs.learn_nodes import choose_next_question, hint_node

class LearnState(TypedDict):
    pass

g = StateGraph(LearnState)
g.add_node("choose", choose_next_question)
g.add_node("hint", hint_node)
g.set_entry_point("choose")
g.add_edge("choose", END)
learn_app = g.compile()
