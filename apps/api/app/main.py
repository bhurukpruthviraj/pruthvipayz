from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.routes.recovery import router as recovery_router
from apps.api.app.routes.catalog import router as catalog_router
from apps.api.app.routes.buyer import router as buyer_router
from apps.api.app.routes.policy import router as policy_router
from apps.api.app.routes.commerce import router as commerce_router
from apps.api.app.routes.payment import router as payment_router
from apps.api.app.routes.payment_failure import router as payment_failure_router
from apps.api.app.routes.agent import router as agent_router
from apps.api.app.routes.merchant import router as merchant_router
from apps.api.app.routes.audit import router as audit_router
from apps.api.app.routes.negotiation import router as negotiation_router
from apps.api.app.routes.recommendations import router as recommendations_router
app = FastAPI(
    title="PruthviPayz API",
    description="Agentic Commerce Gateway for AI Buyers",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "pruthvipayz-api",
    }


app.include_router(catalog_router)
app.include_router(buyer_router)
app.include_router(policy_router)
app.include_router(commerce_router)
app.include_router(payment_router)
app.include_router(recovery_router)
app.include_router(payment_failure_router)
app.include_router(agent_router)
app.include_router(merchant_router)
app.include_router(audit_router)
app.include_router(negotiation_router)
app.include_router(recommendations_router)