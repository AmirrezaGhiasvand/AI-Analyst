"""
Agent graph assembly.

Wires the Planner and Analyst nodes together:

    START -> planner --route="direct"--> END
                     --route="analyze"--> analyst -> END

The Planner's `route` field (set on the shared state) drives which path
executes next via a conditional edge — LangGraph's native mechanism for
branching. This is the actual "orchestration" piece: everything upstream
(state, nodes) exists to make this graph possible.
"""

from langgraph.graph import END, StateGraph

from app.agents.analyst import analyze
from app.agents.planner import plan
from app.agents.state import AgentState


def _route_after_planner(state: AgentState) -> str:
    """Reads the Planner's decision and picks the next node."""
    return "analyst" if state["route"] == "analyze" else "__end__"


def build_agent_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner", plan)
    builder.add_node("analyst", analyze)

    builder.set_entry_point("planner")
    builder.add_conditional_edges(
        "planner",
        _route_after_planner,
        {"analyst": "analyst", "__end__": END},
    )
    builder.add_edge("analyst", END)

    return builder.compile()


# Compiled once at import time — building the graph is cheap and the
# structure never changes at runtime, so there's no need to rebuild it
# on every request.
agent_graph = build_agent_graph()
