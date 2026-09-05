# PruthviPayz

PruthviPayz is an AI-native commerce platform that allows AI agents to discover products, make purchase decisions, negotiate within merchant-defined limits, recommend bundles, and complete payments through Razorpay.


## What Problem Does It Solve?

AI agents can understand what users want and recommend products, but giving an AI agent the ability to spend money creates an important problem:

How do we let AI buy things without giving it unlimited authority?

Traditional e-commerce assumes a human is always making the final purchase decision. AI-driven commerce changes this — an agent may need to select a product, negotiate a price, choose an add-on, and initiate a payment.

PruthviPayz provides a controlled layer between the AI agent and the payment system.

It ensures that:

- AI purchases stay within the buyer's budget.
- The LLM never directly controls the money.
- Product selections come from a machine-readable merchant catalogue.
- AI negotiation is bounded by merchant-defined discount limits.
- Bundle recommendations respect the buyer's spending authority.
- Payment actions are executed through Razorpay Test Mode.
- Failed payments can trigger a controlled retry.
- Every important decision and money action is recorded in an audit trail.



## How It Works

AI Buyer
   ↓
Product Discovery
   ↓
AI Product Decision
   ↓
Policy & Catalogue Validation
   ↓
Negotiation / Bundle Recommendation
   ↓
Authorization
   ↓
Razorpay Payment
   ↓
Transaction + Audit Trail

HOW TO RUN IT:

1. git clone <https://github.com/bhurukpruthviraj/pruthvipayz.git>

activate backend:
1.cd apps/api
2.python3 -m venv .venv
3.source .venv/bin/activate
4.uvicorn apps.api.app.main:app --reload --port 8000

in another terminal start frontend:

cd apps/web
npm install
npm run dev -- --host 0.0.0.0

create .env and add :
RAZORPAY_KEY_ID=your_razorpay_test_key_id
RAZORPAY_KEY_SECRET=your_razorpay_test_key_secret
GEMINI_API_KEY=your_gemini_api_key