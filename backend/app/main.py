import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.health import router as health_router
from app.api.cases import router as cases_router
from app.api.entities import router as entities_router
from app.api.graph import router as graph_router
from app.api.transactions import router as transactions_router
from app.api.campaigns import router as campaigns_router
from app.api.investigations import router as investigations_router
from app.api.search import router as search_router
from app.api.stats import router as stats_router
from app.services.graph_service import graph_service

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberscope")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CYBERSCOPE database tables...")
    Base.metadata.create_all(bind=engine)

    # Initial graph synchronization
    try:
        db = SessionLocal()
        graph_service.sync_from_db(db)
        db.close()
        logger.info("Fraud Graph synchronized successfully.")
    except Exception as e:
        logger.warning(f"Initial graph sync skipped or deferred: {e}")

    yield
    logger.info("CYBERSCOPE backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Explainable Cyber-Fraud Intelligence & Investigation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the investigation query.",
            "path": request.url.path
        }
    )


# Register API Routers
app.include_router(health_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(entities_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(investigations_router, prefix="/api")
app.include_router(search_router, prefix="/api")


@app.get("/")
def root():
    return {
        "platform": "CYBERSCOPE",
        "description": "Explainable Cyber-Fraud Intelligence & Investigation Platform",
        "docs_url": "/docs",
        "health_url": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
