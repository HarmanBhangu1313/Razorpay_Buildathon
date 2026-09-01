import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from database.db import SessionLocal
from services.catalog import search_products as db_search, get_product as db_get_product, add_to_cart as db_add_to_cart, get_cart_summary as db_get_cart
from services.razorpay_client import create_payment_link

# Tool Input Schemas
class SearchInput(BaseModel):
    query: str = Field(description="Search query to find products (e.g., 'laptop', 'headphones')")

class ProductDetailsInput(BaseModel):
    product_id: str = Field(description="The exact SKU/ID of the product")

class AddToCartInput(BaseModel):
    session_id: str = Field(description="The user's session ID")
    product_id: str = Field(description="The exact SKU/ID of the product to add")
    quantity: int = Field(description="Quantity to add", default=1)

class SetBudgetInput(BaseModel):
    session_id: str = Field(description="The user's session ID")
    budget: float = Field(description="The user's maximum budget constraint in INR (e.g. 50000)")

class CartSummaryInput(BaseModel):
    session_id: str = Field(description="The user's session ID")

class GetQuoteInput(BaseModel):
    session_id: str = Field(description="The user's session ID")

@tool("set_budget", args_schema=SetBudgetInput)
def set_budget(session_id: str, budget: float) -> str:
    """Record the user's explicit maximum budget constraint for the current session."""
    from services.catalog import set_user_budget as db_set_budget
    db = SessionLocal()
    try:
        res = db_set_budget(session_id, budget, db)
        return json.dumps(res)
    finally:
        db.close()

# Tool Functions
@tool("search_products", args_schema=SearchInput)
def search_products(query: str) -> str:
    """Search the catalog for products based on a query."""
    db = SessionLocal()
    try:
        results = db_search(query, db)
        if not results:
            return "No products found matching your query."
        return json.dumps(results, indent=2)
    finally:
        db.close()

@tool("get_product_details", args_schema=ProductDetailsInput)
def get_product_details(product_id: str) -> str:
    """Get detailed information about a specific product, including stock, price, and related products."""
    db = SessionLocal()
    try:
        product = db_get_product(product_id, db)
        if not product:
            return f"Product with ID {product_id} not found."
        return json.dumps(product, indent=2)
    finally:
        db.close()

@tool("add_to_cart", args_schema=AddToCartInput)
def add_to_cart(session_id: str, product_id: str, quantity: int = 1) -> str:
    """Add a product to the user's cart."""
    db = SessionLocal()
    try:
        result = db_add_to_cart(session_id, product_id, quantity, db)
        return json.dumps(result)
    finally:
        db.close()

@tool("get_cart", args_schema=CartSummaryInput)
def get_cart(session_id: str) -> str:
    """Get the current contents and total of the user's cart."""
    db = SessionLocal()
    try:
        result = db_get_cart(session_id, db)
        return json.dumps(result, indent=2)
    finally:
        db.close()

from services.guardrails import validate_checkout, log_audit

@tool("get_quote", args_schema=GetQuoteInput)
def get_quote(session_id: str) -> str:
    """
    Get a final quote for the cart. 
    Use this right before confirming with the user to show them the total.
    """
    db = SessionLocal()
    try:
        cart = db_get_cart(session_id, db)
        if not cart['items']:
            return "Cart is empty."
        
        is_valid, checks, reason = validate_checkout(session_id, db)
        
        quote = {
            "cart_id": cart['cart_id'],
            "subtotal": cart['total'],
            "tax": 0.0,
            "shipping": 0.0,
            "final_total": cart['total'],
            "items": cart['items'],
            "guardrails": checks,
            "can_checkout": is_valid,
            "rejection_reason": reason if not is_valid else ""
        }
        
        # Log this quote generation action
        log_audit(
            session_id=session_id,
            action="get_quote",
            decision="APPROVED" if is_valid else "REJECTED",
            reason="Quote generated" if is_valid else f"Quote generated but failed guardrails: {reason}",
            checks=checks,
            api_calls=[],
            db=db
        )
        
        return json.dumps(quote, indent=2)
    finally:
        db.close()

# Note: Checkout is NOT a tool the agent can call directly.
# Checkout requires human confirmation, so the agent will return a structured
# response indicating it's ready for checkout, and the backend handles the payment link.
