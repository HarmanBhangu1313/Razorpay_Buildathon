# 🛍️ AgentShop

**Razorpay Buildathon 2025 — Track 01: AI Growth & Agentic Commerce**

> **Core Thesis:** *AI can initiate commerce; AI cannot authorize payment.*

AgentShop is a fully autonomous, agent-to-agent commerce platform that proves AI buyers and AI merchants can negotiate, discover products, and build carts entirely through the **Model Context Protocol (MCP)**, while leaving the final financial authorization strictly to deterministic guardrails and human verification.

---

## 🏗️ The Architecture

AgentShop strictly decouples the AI's conversational agency from the actual movement of money. 

```text
                 EXTERNAL WORLD
                       │
                       ▼
              ┌─────────────────┐
              │  AI Buyer LLM   │ (Autonomous Agent)
              └────────┬────────┘
                       │ MCP (Model Context Protocol)
                       ▼
              ┌─────────────────┐
              │ AgentShop MCP   │ (Tool Discovery)
              │     Server      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Merchant Tools  │ (Catalog, Cart, Quote)
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ DETERMINISTIC   │ (Stock, Budget, Price)
              │  GUARDRAILS     │
              └────────┬────────┘
                       │
                 ┌─────┴─────┐
                 │           │
              BLOCK       APPROVE
                 │           │
                 ▼           ▼
              ❌ Stop    Payment Link
                              │
                              ▼
                       🧑 HUMAN CLICK
                              │
                              ▼
                        💸 PAYMENT (Razorpay)
```

## ✨ Key Differentiators

1. **MCP Agent-to-Agent Commerce:** An independent `autonomous_buyer.py` agent can dynamically connect to the merchant over standard `stdio` MCP, discover the 6 merchant capabilities, and autonomously execute a shopping objective on behalf of a human.
2. **Deterministic Guardrails:** The LLM does not control the cart or the checkout. It only requests intents. Hardcoded Python/SQL guardrails enforce:
   - **Store Transaction Limits** (Max ₹1,00,000 per order)
   - **Inventory Enforcement** (Prevents over-ordering)
   - **User Budget Constraints** (Records and enforces B2B/B2C budgets)
   - **Price Verification** (Prevents LLM price hallucination)
3. **Human-in-the-Loop Checkout:** When the AI Buyer calls the `checkout()` tool, the system explicitly returns a Razorpay Test Link. The AI is structurally incapable of silently moving money. 
4. **Immutable Audit Trails:** Every action (whether initiated via the Web UI or MCP) logs a deterministic trace of the guardrail checks, ensuring full observability into *why* an AI transaction was approved or blocked.

## 🚀 Running the Project

### 1. The Merchant Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

### 2. The Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. The Autonomous AI Buyer (MCP Client)
Watch a completely independent AI agent discover the store, reason about constraints, and build a cart.
```bash
cd backend
python autonomous_buyer.py
```

---

*Built for the Razorpay Buildathon 2025/2026. Empowering the next generation of AI-driven commerce.*
