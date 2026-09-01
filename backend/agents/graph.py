from typing import Annotated, Literal, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from agents.tools import search_products, get_product_details, add_to_cart, get_cart, get_quote, set_budget

# Define the State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str

import os
import itertools
import time
import re
from dotenv import load_dotenv

load_dotenv()

# Define Tools
tools = [search_products, get_product_details, add_to_cart, get_cart, get_quote, set_budget]

# Load API Key Pool
raw_keys = os.environ.get("GEMINI_API_KEYS", os.environ.get("GEMINI_API_KEY", ""))
api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
if not api_keys:
    api_keys = [os.environ.get("GEMINI_API_KEY", "")]

print(f"Loaded {len(api_keys)} Gemini API Keys into rotation pool.")

MODELS = ["gemini-3.7-flash", "gemini-2.5-flash", "gemini-3.5-flash", "gemini-flash-latest"]

def get_llm(api_key: str, model_name: str):
    llm = ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=0, 
        api_key=api_key,
        google_api_key=api_key,
        max_retries=1
    )
    return llm.bind_tools(tools)

# System Prompt
SYSTEM_PROMPT = """You are AgentShop, an AI shopping assistant.
Your goal is to help users find products, recommend complementary items (upsell), and build their cart.

Rules:
1. Whenever the user specifies a budget or maximum price (e.g. "under 50,000", "within 50k", "budget is 70k"), you MUST IMMEDIATELY call `set_budget(budget=...)` to record this constraint into the database.
2. ALWAYS use the `search_products` tool to find items. Do NOT hallucinate products or prices.
3. If a user asks for a recommendation, explain WHY you recommend it based on features and budget.
4. Once they add an item, check its `related_products` via `get_product_details` and suggest ONE complementary item (upsell).
5. When the user says they are ready to buy or checkout, use `get_quote` to summarize the cart, and then explicitly state:
"READY_FOR_CHECKOUT" in your response so the system can trigger the human confirmation gate.
6. NEVER ask for payment details directly.

Pass the `session_id` to tools that require it. It is provided in the state.
"""

def chatbot(state: AgentState):
    messages = state["messages"]
    session_id = state["session_id"]
    
    # Ensure system prompt is present
    from langchain_core.messages import SystemMessage
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [sys_msg] + messages

    reminded_messages = messages + [SystemMessage(content=f"Your current session_id is {session_id}")]
    
    # Automatic Multi-Key & Multi-Model Resilience Loop
    last_error = None
    for model in MODELS:
        for key in api_keys:
            try:
                llm_with_tools = get_llm(key, model)
                response = llm_with_tools.invoke(reminded_messages)
                return {"messages": [response]}
            except Exception as e:
                err_str = str(e)
                print(f"[{model}] Key {key[:10]}... hit error: {err_str[:120]}")
                last_error = e
                
                # If rate-limited and a retry delay is given, we can quickly pause or move to next key
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(0.5)
                    continue
                elif "404" in err_str:
                    # Model not supported, break out to next model
                    break
                    
    # If all keys and models failed, sleep 2 seconds and do one final attempt on the first key
    print("All immediate key attempts failed. Waiting 2.5s for rate limit window to clear...")
    time.sleep(2.5)
    try:
        llm_with_tools = get_llm(api_keys[0], "gemini-2.5-flash")
        response = llm_with_tools.invoke(reminded_messages)
        return {"messages": [response]}
    except Exception as e:
        raise last_error or e

def route_tools(state: AgentState) -> Literal["tools", "__end__"]:
    """Determine whether to use tools or end."""
    last_message = state["messages"][-1]
    # If the LLM makes a tool call, route to the "tools" node
    if getattr(last_message, "tool_calls", None):
        return "tools"
    # Otherwise, we stop (end of turn)
    return "__end__"

class ToolNode:
    """A node that executes the tools requested by the LLM."""
    def __init__(self, tools: list):
        self.tools_by_name = {t.name: t for t in tools}

    def __call__(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        outputs = []
        for tool_call in last_message.tool_calls:
            tool = self.tools_by_name[tool_call["name"]]
            # Execute tool
            try:
                result = tool.invoke(tool_call["args"])
            except Exception as e:
                result = f"Error: {str(e)}"
            
            outputs.append(
                ToolMessage(
                    content=str(result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

from langgraph.checkpoint.memory import MemorySaver

# Build the Graph
graph_builder = StateGraph(AgentState)

graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", route_tools)
graph_builder.add_edge("tools", "chatbot")

memory = MemorySaver()
app_graph = graph_builder.compile(checkpointer=memory)
