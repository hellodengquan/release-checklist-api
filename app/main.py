from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import releases, check_items, approvals, summary

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Release Checklist API",
    description="发布检查清单 API - 管理检查项、审批状态和阻塞项汇总",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(releases.router)
app.include_router(check_items.router)
app.include_router(approvals.router)
app.include_router(summary.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
