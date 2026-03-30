from langgraph.graph import StateGraph, START, END
from app.triage_agent.state import TriageState
from build.lib.app.triage_agent.nodes import parse_user_input_node, fetch_wait_times

# 1. Build the graph
builder = StateGraph(TriageState)

# 2. Add the nodes
builder.add_node("parse_input", parse_user_input_node)
builder.add_node("fetch_data", fetch_wait_times)
# builder.add_node("categorize", categorize_node) # We will add this next

# 3. Define the flow
builder.add_edge(START, "parse_input")
builder.add_edge("parse_input", "fetch_data")
builder.add_edge("fetch_data", END) # Temporarily routing to END until Categorize is built

# 4. Compile
graph = builder.compile()