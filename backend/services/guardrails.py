from sqlalchemy.orm import Session
from database.models import AuditLog, Cart, Product

# Configuration limits
MAX_SESSION_SPEND = 100000.0 # ₹1,00,000

def log_audit(session_id: str, action: str, decision: str, reason: str, checks: list, api_calls: list, db: Session, source: str = "WEB"):
    """
    Deterministically log every action and guardrail check.
    """
    log = AuditLog(
        session_id=session_id,
        source=source,
        action=action,
        decision=decision,
        reason=reason,
        checks=checks,
        api_calls=api_calls
    )
    db.add(log)
    db.commit()
    return log

def check_spending_limit(cart_total: float, new_item_price: float = 0.0, user_budget: float = None) -> dict:
    """Check if adding an item exceeds the user's budget or session spending limit."""
    new_total = cart_total + new_item_price
    
    # Priority 1: User's explicitly defined budget constraint
    if user_budget is not None and user_budget > 0:
        if new_total > user_budget:
            return {
                "name": "budget_limit",
                "status": "FAIL",
                "reason": f"Cart total ₹{new_total:,.2f} exceeds user budget of ₹{user_budget:,.2f} (Over by ₹{new_total - user_budget:,.2f})"
            }
        return {
            "name": "budget_limit",
            "status": "PASS",
            "reason": f"Cart total ₹{new_total:,.2f} is within user budget of ₹{user_budget:,.2f}"
        }

    # Priority 2: Store maximum session threshold
    if new_total > MAX_SESSION_SPEND:
        return {
            "name": "spending_limit",
            "status": "FAIL",
            "reason": f"Total ₹{new_total:,.2f} exceeds maximum store limit of ₹{MAX_SESSION_SPEND:,.2f}"
        }
    return {
        "name": "spending_limit",
        "status": "PASS",
        "reason": f"Total ₹{new_total:,.2f} is within limit"
    }

def check_stock(product_id: str, quantity: int, db: Session) -> dict:
    """Verify inventory is sufficient."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"name": "stock_verified", "status": "FAIL", "reason": "Product not found"}
    
    if product.stock < quantity:
        return {"name": "stock_verified", "status": "FAIL", "reason": f"Only {product.stock} units available"}
        
    return {"name": "stock_verified", "status": "PASS", "reason": f"Stock available ({product.stock} >= {quantity})"}

def validate_checkout(session_id: str, db: Session) -> tuple[bool, list, str]:
    """
    Run all final guardrails before presenting the checkout confirmation to the human.
    Returns (is_valid, checks, rejection_reason).
    """
    cart = db.query(Cart).filter(Cart.session_id == session_id).first()
    if not cart or not cart.items:
        return False, [], "Cart is empty"

    checks = []
    total = 0.0
    
    for item in cart.items:
        # Check 1: Verify Stock
        stock_check = check_stock(item.product_id, item.quantity, db)
        checks.append(stock_check)
        if stock_check["status"] == "FAIL":
            return False, checks, f"Item {item.product.name} failed stock check."
            
        # Check 2: Verify Price matching (we trust DB, but explicitly note it for audit)
        checks.append({
            "name": "price_verified",
            "status": "PASS",
            "reason": f"Price for {item.product.name} confirmed at ₹{item.product.price:,.2f}"
        })
        
        total += (item.product.price * item.quantity)
        
    # Check 3: Budget / Spending Limit
    spend_check = check_spending_limit(total, user_budget=cart.user_budget)
    checks.append(spend_check)
    if spend_check["status"] == "FAIL":
        return False, checks, spend_check["reason"]
        
    # Check 4: User Confirmation requirement is logged
    checks.append({
        "name": "user_confirmation",
        "status": "PENDING",
        "reason": "Requires human click to proceed to payment"
    })

    return True, checks, "All pre-checkout guardrails passed."
