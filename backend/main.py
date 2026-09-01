from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.models import Base
from database.db import engine, SessionLocal
from services.catalog import get_cart_summary

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentShop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel
from agents.graph import app_graph
from langchain_core.messages import HumanMessage
from database.db import SessionLocal
from database.models import AuditLog, Order
from services.catalog import checkout, get_cart_summary

class ChatRequest(BaseModel):
    session_id: str
    message: str

from fastapi.responses import StreamingResponse
import json

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    state = {"messages": [HumanMessage(content=req.message)], "session_id": req.session_id}
    config = {"configurable": {"thread_id": req.session_id}}
    final_state = app_graph.invoke(state, config)
    last_msg = final_state["messages"][-1]
    
    content_raw = last_msg.content
    if isinstance(content_raw, list):
        content_str = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content_raw])
    else:
        content_str = str(content_raw)
        
    is_ready_for_checkout = "READY_FOR_CHECKOUT" in content_str
    
    # Clean the message
    content = content_str.replace("READY_FOR_CHECKOUT", "").strip()
    
    db = SessionLocal()
    try:
        cart = get_cart_summary(req.session_id, db)
        
        # If ready for checkout, run validate to get guardrails
        guardrails = []
        if is_ready_for_checkout:
            from services.guardrails import validate_checkout
            _, checks, _ = validate_checkout(req.session_id, db)
            guardrails = checks

        return {
            "response": content,
            "ready_for_checkout": is_ready_for_checkout,
            "cart": cart,
            "guardrails": guardrails
        }
    finally:
        db.close()

class CheckoutRequest(BaseModel):
    session_id: str
    email: str = None
    
@app.post("/checkout")
def checkout_endpoint(req: CheckoutRequest):
    db = SessionLocal()
    try:
        result = checkout(req.session_id, db, {"email": req.email} if req.email else None)
        return result
    finally:
        db.close()

@app.get("/audit")
def get_audit_logs():
    db = SessionLocal()
    try:
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50).all()
        return [
            {
                "id": log.id,
                "session_id": log.session_id,
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "decision": log.decision,
                "reason": log.reason,
                "checks": log.checks,
                "api_calls": log.api_calls
            } for log in logs
        ]
    finally:
        db.close()
