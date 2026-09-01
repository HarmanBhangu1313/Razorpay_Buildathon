import uuid
from sqlalchemy.orm import Session
from database.models import Product, Cart, CartItem
from database.db import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def search_products(query: str, db: Session) -> list:
    """Simple semantic-like search using LIKE on name and description."""
    q = f"%{query}%"
    results = db.query(Product).filter(
        (Product.name.ilike(q)) | (Product.description.ilike(q)) | (Product.category.ilike(q))
    ).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "description": p.description,
            "category": p.category,
            "features": p.features
        }
        for p in results
    ]

def get_product(product_id: str, db: Session) -> dict:
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        return None
    return {
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "description": p.description,
        "category": p.category,
        "stock": p.stock,
        "features": p.features,
        "related_products": p.related_products
    }

def get_or_create_cart(session_id: str, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.session_id == session_id).first()
    if not cart:
        cart = Cart(id=str(uuid.uuid4()), session_id=session_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def set_user_budget(session_id: str, budget: float, db: Session, source: str = "WEB") -> dict:
    cart = get_or_create_cart(session_id, db)
    cart.user_budget = budget
    db.commit()
    from services.guardrails import log_audit
    log_audit(
        session_id=session_id,
        action="set_budget",
        decision="APPROVED",
        reason=f"User budget constraint recorded as ₹{budget:,.2f}",
        checks=[],
        api_calls=[],
        db=db,
        source=source
    )
    return {"success": True, "message": f"User budget constraint recorded as ₹{budget:,.2f}"}

from services.guardrails import log_audit, check_stock, check_spending_limit

def add_to_cart(session_id: str, product_id: str, quantity: int, db: Session, source: str = "WEB"):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"success": False, "error": "Product not found"}
        
    cart = get_or_create_cart(session_id, db)
    
    # Run Guardrails
    stock_check = check_stock(product_id, quantity, db)
    
    cart_summary = get_cart_summary(session_id, db)
    spend_check = check_spending_limit(cart_summary["total"], product.price * quantity)
    
    checks = [stock_check, spend_check]
    
    if stock_check["status"] == "FAIL" or spend_check["status"] == "FAIL":
        reason = stock_check["reason"] if stock_check["status"] == "FAIL" else spend_check["reason"]
        
        # Log the rejection
        log_audit(
            session_id=session_id,
            action="add_to_cart",
            decision="REJECTED",
            reason=reason,
            checks=checks,
            api_calls=[],
            db=db,
            source=source
        )
        return {"success": False, "error": reason, "checks": checks}

    # If passed, add to cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id, 
        CartItem.product_id == product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        db.add(new_item)
        
    db.commit()
    
    # Log the approval
    log_audit(
        session_id=session_id,
        action="add_to_cart",
        decision="APPROVED",
        reason=f"Added {quantity} x {product.name} to cart.",
        checks=checks,
        api_calls=[],
        db=db,
        source=source
    )
    
    return {"success": True, "message": f"Added {quantity} of {product.name} to cart."}

def get_cart_summary(session_id: str, db: Session) -> dict:
    cart = db.query(Cart).filter(Cart.session_id == session_id).first()
    if not cart:
        return {"items": [], "total": 0.0}
        
    items = []
    total = 0.0
    for item in cart.items:
        product = item.product
        item_total = product.price * item.quantity
        total += item_total
        items.append({
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": item.quantity,
            "item_total": item_total
        })
        
    return {
        "cart_id": cart.id,
        "items": items,
        "total": total,
        "user_budget": cart.user_budget
    }

def checkout(session_id: str, db: Session, customer_details: dict = None, source: str = "WEB"):
    cart_summary = get_cart_summary(session_id, db)
    
    # Idempotency check
    from database.models import Order
    existing_order = db.query(Order).filter(
        Order.cart_id == cart_summary.get("cart_id"), 
        Order.status == "PAYMENT_PENDING"
    ).first()
    
    if existing_order:
        return {
            "success": True,
            "order_id": existing_order.id,
            "payment_link": existing_order.razorpay_payment_link,
            "message": "Duplicate checkout attempt. Returning existing payment link."
        }

    # 1. Re-run guardrails (never trust client)
    from services.guardrails import validate_checkout
    is_valid, checks, reason = validate_checkout(session_id, db)
    if not is_valid:
        log_audit(
            session_id=session_id,
            action="checkout",
            decision="REJECTED",
            reason=reason,
            checks=checks,
            api_calls=[],
            db=db,
            source=source
        )
        return {"success": False, "error": reason}
        
    total_inr = cart_summary["total"]
    
    # 2. Call Razorpay
    from services.razorpay_client import create_payment_link
    import uuid
    
    order_id = str(uuid.uuid4())
    desc = f"Order {order_id[:8]}"
    
    rp_result = create_payment_link(
        amount_inr=total_inr,
        reference_id=order_id,
        description=desc,
        customer_details=customer_details
    )
    
    api_calls = [{
        "endpoint": "create_payment_link",
        "amount_inr": total_inr,
        "amount_paise": int(total_inr * 100),
        "result": rp_result
    }]
    
    if not rp_result["success"]:
        log_audit(
            session_id=session_id,
            action="checkout",
            decision="REJECTED",
            reason=f"Razorpay API failed: {rp_result['error']}",
            checks=checks,
            api_calls=api_calls,
            db=db,
            source=source
        )
        return {"success": False, "error": "Payment gateway error"}
        
    # 3. Create Order in DB
    order = Order(
        id=order_id,
        session_id=session_id,
        cart_id=cart_summary["cart_id"],
        amount=total_inr,
        status="PAYMENT_PENDING",
        razorpay_payment_link_id=rp_result["payment_link_id"],
        razorpay_payment_link=rp_result["payment_link_url"]
    )
    db.add(order)
    
    # Check off the 'user_confirmation' guardrail as passed since they clicked it
    for c in checks:
        if c["name"] == "user_confirmation":
            c["status"] = "PASS"
            
    db.commit()
    
    log_audit(
        session_id=session_id,
        action="checkout",
        decision="APPROVED",
        reason="Order created and payment link generated.",
        checks=checks,
        api_calls=api_calls,
        db=db,
        source=source
    )
    
    return {
        "success": True,
        "order_id": order_id,
        "payment_link": rp_result["payment_link_url"]
    }
