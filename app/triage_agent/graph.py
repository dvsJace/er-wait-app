from langgraph.graph import StateGraph, START, END
from app.triage_agent.state import TriageState
from app.triage_agent.nodes import categorize_hospitals, parse_user_input_node, fetch_wait_times

# 1. Build the graph
builder = StateGraph(TriageState)

# 2. Add the nodes
builder.add_node("parse_input", parse_user_input_node)
builder.add_node("fetch_data", fetch_wait_times)
builder.add_node("off_topic_response", 
                 lambda state: {"recommendations": "I'm here to help with medical triage. Could you please provide details about your symptoms and location?"})
builder.add_node("categorize", categorize_hospitals)

# 3. Define the flow
def route_after_parse(state):
    # This function decides where to go next
    if state.get("is_relevant"):
        return "fetch_data"
    else:
        return "off_topic_response"
    

builder.add_edge(START, "parse_input")
builder.add_conditional_edges("parse_input", route_after_parse) 
builder.add_edge("fetch_data", "categorize")
builder.add_edge("categorize", END)

# 4. Compile
graph = builder.compile()