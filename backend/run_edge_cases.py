import requests
import uuid

BASE_URL = "http://localhost:8000"

def chat(session_id, message):
    response = requests.post(f"{BASE_URL}/chat", json={"session_id": session_id, "message": message})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def run_tests():
    print("--- Starting Edge Case Tests ---\n")
    
    # 1. Same product added twice
    print("Test 1: Same product added twice")
    session_1 = str(uuid.uuid4())
    chat(session_1, "Add the AeroBook 14 to my cart")
    res1 = chat(session_1, "Add another AeroBook 14")
    cart1 = res1.get('cart', {}).get('items', []) if res1 else []
    print(f"Cart 1 Items: {cart1}")
    
    # 3. Multiple accessories
    print("\nTest 3: Multiple accessories")
    session_3 = str(uuid.uuid4())
    chat(session_3, "Add the AeroBook 14")
    chat(session_3, "Add the Protective Sleeve")
    res3 = chat(session_3, "Add the Wireless Mouse")
    cart3 = res3.get('cart', {}).get('items', []) if res3 else []
    print(f"Cart 3 Items: {cart3}")

    # 4. Ambiguous product request
    print("\nTest 4: Ambiguous request")
    session_4 = str(uuid.uuid4())
    res4 = chat(session_4, "Show me something good for college under 70k.")
    if res4:
        content = res4.get('messages', [])[-1].get('content', '') if res4.get('messages') else res4.get('response', '')
        print(f"Response: {content}")
        print(f"Cart State: {res4.get('cart', {}).get('items', [])}")
    
    # 6. Session isolation
    print("\nTest 6: Session isolation")
    session_a = str(uuid.uuid4())
    session_b = str(uuid.uuid4())
    chat(session_a, "Add the AeroBook 14")
    res_b = chat(session_b, "What is in my cart?")
    cart_b = res_b.get('cart', {}).get('items', []) if res_b else []
    print(f"Session B cart (should be empty): {cart_b}")
    
run_tests()
