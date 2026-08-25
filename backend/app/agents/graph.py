from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.planner import plan
from app.agents.analyst import analyze
from app.agents.visualizer import visualize


def _route_after_planner(state: AgentState) -> str:
    """Only 'analyze' needs the Analyst/Visualizer pipeline — both
    'direct' and 'report' are already fully answered by the Planner."""
    return "analyst" if state["route"] == "analyze" else "__end__"


def build_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("planner", plan)
    builder.add_node("analyst", analyze)
    builder.add_node("visualizer", visualize)
    builder.set_entry_point("planner")
    builder.add_conditional_edges("planner", _route_after_planner, {"analyst": "analyst", "__end__": END})
    builder.add_edge("analyst", "visualizer")
    builder.add_edge("visualizer", END)
    return builder.compile()


agent_graph = build_agent_graph()