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

PRUTHVIPAYZ — RUN INSTRUCTIONS
===============================

PREREQUISITES
-------------
- Python 3.10+ (Python 3.12 recommended)
- Node.js + npm
- Git
- Razorpay Test Mode credentials
- Gemini API key


1. CLONE THE REPOSITORY
-----------------------
git clone https://github.com/bhurukpruthviraj/pruthvipayz.git
cd pruthvipayz


2. BACKEND SETUP
----------------

Linux / macOS / GitHub Codespaces:

python3 -m venv apps/api/.venv
source apps/api/.venv/bin/activate
pip install -r apps/api/requirements.txt

Create:
apps/api/.env

Add:

RAZORPAY_KEY_ID=your_razorpay_test_key_id
RAZORPAY_KEY_SECRET=your_razorpay_test_key_secret
GEMINI_API_KEY=your_gemini_api_key

Start the backend:

uvicorn apps.api.app.main:app --reload --port 8000

Keep this terminal running.


Windows PowerShell:

python -m venv apps\api\.venv
apps\api\.venv\Scripts\python.exe -m pip install -r apps\api\requirements.txt

If PowerShell blocks Activate.ps1, do NOT change the execution policy.
Run the backend directly:

apps\api\.venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --port 8000

Create apps/api/.env with the same three variables above.


3. FRONTEND SETUP
-----------------
Open a SECOND terminal.

cd apps/web
npm install
npm run dev -- --host 0.0.0.0

Open the URL shown by Vite (normally port 5173).


4. DEMO FLOW
------------
1. Open AI Buyer.
2. Enter a natural-language product request.
3. Enter the buyer's maximum budget.
4. Evaluate the purchase.
5. Review AI product selection and policy checks.
6. Try an over-budget request to demonstrate negotiation.
7. Show merchant-defined negotiation limits.
8. Show bundle/add-on recommendations.
9. Create a Razorpay Test Mode order.
10. Complete a Test Mode payment.
11. Open Audit Trail and show the complete decision/payment history.

For payment-failure testing, use Razorpay Test Mode.
The application limits recovery to one controlled retry.


5. PRODUCTION BUILD CHECK
-------------------------
cd apps/web
npm install
npm run build

A successful build creates:
apps/web/dist/


6. IMPORTANT SECURITY NOTES
---------------------------
- Never commit apps/api/.env.
- Never commit real Razorpay secrets or Gemini API keys.
- .env.example is safe to commit.
- Use Razorpay Test Mode for the demo.


7. PROJECT ARCHITECTURE
-----------------------
AI Buyer
   |
   v
FastAPI Backend
   |
   +--> AI Product Decision
   |
   +--> Policy + Catalogue Validation
   |
   +--> Negotiation
   |
   +--> Bundle Recommendation
   |
   v
Razorpay Test Mode
   |
   v
Transactions + Audit Trail


