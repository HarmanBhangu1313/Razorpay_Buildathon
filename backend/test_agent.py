import uuid
from langchain_core.messages import HumanMessage
from agents.graph import app_graph
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Welcome to AgentShop! (Type 'quit' to exit)")
    session_id = str(uuid.uuid4())
    print(f"[Session ID: {session_id}]\n")
    
    state = {"messages": [], "session_id": session_id}
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
            
        state["messages"].append(HumanMessage(content=user_input))
        
        # Run the graph
        for event in app_graph.stream(state):
            for value in event.values():
                if "messages" in value:
                    last_msg = value["messages"][-1]
                    # If it's an AI message without tool calls, print it
                    if last_msg.type == "ai" and not getattr(last_msg, "tool_calls", None):
                        print(f"\nAgentShop: {last_msg.content}\n")
                        
                        if "READY_FOR_CHECKOUT" in last_msg.content:
                            print("\n--- HUMAN CONFIRMATION GATE ---")
                            print("The agent is ready for checkout. In the actual app, this is where the Guardrails UI appears.")
                            print("-------------------------------\n")
                    
                    # Update our state's messages
                    if last_msg not in state["messages"]:
                        state["messages"].append(last_msg)

if __name__ == "__main__":
    main()
