"""
ReviveAI backend entrypoint.

Run locally:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.database import Base, engine
from app.api.routes import health, orders, payments, recovery, agent, dashboard, webhooks, demo, policy, stream
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

app = FastAPI(
    title="ReviveAI API",
    description="AI-native agentic revenue recovery platform for Razorpay merchants (TEST MODE).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("ReviveAI backend started (env=%s)", settings.ENV)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # We must commit after each ALTER TYPE if using a transaction block, 
            # or execute them separately if they might already exist.
            # However, ADD VALUE IF NOT EXISTS cannot be executed inside a transaction block in older Postgres.
            # In Postgres 12+ it's fine, but let's do them one by one.
            try:
                conn.execute(text("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'FRAUD_LOCK'"))
                conn.commit()
            except Exception: pass
            
            try:
                conn.execute(text("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'DYNAMIC_OFFER'"))
                conn.commit()
            except Exception: pass
            
            try:
                conn.execute(text("ALTER TYPE actiontype ADD VALUE IF NOT EXISTS 'RESTRICTED_LINK'"))
                conn.commit()
            except Exception: pass
            
            # Add missing is_blocked column to customers table for the FRAUD_LOCK feature
            try:
                conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE"))
                conn.commit()
            except Exception: pass
            
    except Exception as e:
        logger.error("Could not alter database schema: %s", e)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Something went wrong"}},
    )


app.include_router(health.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(recovery.router)
app.include_router(agent.router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)
app.include_router(demo.router)
app.include_router(policy.router)
app.include_router(stream.router)
