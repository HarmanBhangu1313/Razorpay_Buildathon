import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, SystemMessage

async def main():
    print("🤖 Starting Autonomous External AI Buyer...\n")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")],
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.7-flash",
        temperature=0,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(">> Fetching available tools from MCP server...")
            mcp_tools = await session.list_tools()
            
            # Map MCP tools to Langchain tool schemas
            tools_for_llm = []
            for t in mcp_tools.tools:
                tools_for_llm.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": getattr(t, "input_schema", getattr(t, "inputSchema", {}))
                    }
                })
            
            print(f">> Agent dynamically discovered {len(tools_for_llm)} tools from Merchant.\n")
            
            llm_with_tools = llm.bind_tools(tools_for_llm)
            
            system_prompt = """You are an autonomous AI purchasing agent acting on behalf of a human. 
Your human has authorized a maximum budget of ₹75,000 to purchase a suitable college laptop and wireless mouse. 
Discover the merchant's available capabilities through MCP. Search the catalog, evaluate suitable products, 
respect all merchant and buyer constraints, build the appropriate cart, obtain a final quote, and proceed to checkout. 
You may prepare the payment request, but you must never bypass merchant guardrails or independently authorize payment. 

Use the session_id 'mcp-autonomous-1' for all calls.
If you get an error, adapt and try a different strategy.
"""
            
            from langchain_core.messages import HumanMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Start your buying process.")
            ]
            
            # Start agent loop
            while True:
                response = llm_with_tools.invoke(messages)
                messages.append(response)
                
                if response.content:
                    print(f"🤖 AI Reasoning:\n{response.content}\n")
                
                if not response.tool_calls:
                    print("✅ AI finished task.")
                    break
                    
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    print(f"🔧 Calling MCP Tool: {tool_name}({tool_args})")
                    
                    try:
                        result = await session.call_tool(tool_name, tool_args)
                        result_text = result.content[0].text
                    except Exception as e:
                        result_text = f"Error: {str(e)}"
                        
                    print(f"📥 Result:\n{result_text[:500]}...\n")
                    
                    messages.append(ToolMessage(
                        content=result_text,
                        name=tool_name,
                        tool_call_id=tool_call["id"]
                    ))

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
