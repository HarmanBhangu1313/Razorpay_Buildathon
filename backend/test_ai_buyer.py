import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys
import os

async def main():
    print("🤖 Simulating External AI Buyer connecting via MCP...\n")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            print(">> Fetching available tools from MCP server...")
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"Available tools: {tool_names}\n")
            
            # 2. Search Products
            print(">> Agent intent: 'Find me a laptop'")
            print(">> Calling tool: search_products(query='laptop')...")
            search_result = await session.call_tool("search_products", {"query": "laptop"})
            print(f"Result:\n{search_result.content[0].text}\n")
            
            # 3. Add to Cart
            session_id = "test-ai-buyer-session-1"
            print(f">> Calling tool: add_to_cart(session_id='{session_id}', product_id='AERO-14')...")
            cart_result = await session.call_tool("add_to_cart", {"session_id": session_id, "product_id": "AERO-14", "quantity": 1})
            print(f"Result:\n{cart_result.content[0].text}\n")
            
            # 4. Get Quote
            print(f">> Calling tool: get_quote(session_id='{session_id}')...")
            quote_result = await session.call_tool("get_quote", {"session_id": session_id})
            print(f"Result:\n{quote_result.content[0].text}\n")
            
            # 5. Checkout (User confirmed)
            print(">> Simulating AI Buyer confirming quote and proceeding to checkout...")
            checkout_result = await session.call_tool("checkout", {"session_id": session_id, "email": "ai.buyer@example.com"})
            print(f"Result:\n{checkout_result.content[0].text}\n")
            
            print("🎉 AI Buyer successfully navigated the store via MCP!")

if __name__ == "__main__":
    asyncio.run(main())
