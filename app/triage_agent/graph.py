import logging

from langgraph.graph import StateGraph, START, END
from app.triage_agent.state import TriageState
from app.triage_agent.nodes import categorize_hospitals_node, parse_user_input_node, fetch_wait_times_node
logger = logging.getLogger("app.triage_agent.graph")
# 1. Build the graph
builder = StateGraph(TriageState)

# 2. Add the nodes
builder.add_node("parse_input", parse_user_input_node)
builder.add_node("fetch_data", fetch_wait_times_node)
builder.add_node("off_topic_response", 
                 lambda state: {"recommendations": "I'm here to help with medical triage. Could you please provide details about your symptoms and location?"})
builder.add_node("categorize", categorize_hospitals_node)

#determines whether or not to route to the off_topic response or 
# the fetch data node based on the is_relevant variable set in the parse_user_input_node
async def route_after_parse(state: TriageState):
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