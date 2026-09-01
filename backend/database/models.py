from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(String, primary_key=True) # SKU e.g., AERO-14
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False) # INR
    stock = Column(Integer, default=0)
    features = Column(JSON) # List of features for AI reasoning
    related_products = Column(JSON) # List of SKUs for upsell

class Cart(Base):
    __tablename__ = 'carts'
    
    id = Column(String, primary_key=True) # UUID
    session_id = Column(String, nullable=False, index=True)
    user_budget = Column(Float, nullable=True) # User-defined maximum budget constraint
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String, ForeignKey('carts.id'))
    product_id = Column(String, ForeignKey('products.id'))
    quantity = Column(Integer, default=1)
    
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(String, primary_key=True) # UUID
    session_id = Column(String, nullable=False)
    cart_id = Column(String, ForeignKey('carts.id'))
    amount = Column(Float, nullable=False) # INR
    status = Column(String, default="CREATED") # CREATED, CONFIRMED, PAYMENT_PENDING, PAID, FAILED
    razorpay_order_id = Column(String)
    razorpay_payment_link_id = Column(String)
    razorpay_payment_link = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    source = Column(String, default="WEB")
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, nullable=False)
    decision = Column(String, nullable=False) # APPROVED, REJECTED, INFO
    reason = Column(Text, nullable=False)
    checks = Column(JSON) # e.g., [{"name": "price_verified", "status": "PASS"}]
    api_calls = Column(JSON) # Record of external calls if any
