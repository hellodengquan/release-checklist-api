from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/releases/{release_id}/summary", tags=["summary"])


@router.get("/", response_model=schemas.ReleaseSummary)
def get_release_summary(release_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    summary = crud.get_release_summary(db, release_id=release_id)
    return summary


@router.get("/blockers", response_model=schemas.BlockerSummary)
def get_blocker_summary(release_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    summary = crud.get_blocker_summary(db, release_id=release_id)
    return summary
