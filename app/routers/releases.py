from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/releases", tags=["releases"])


@router.get("/", response_model=List[schemas.Release])
def list_releases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    releases = crud.get_releases(db, skip=skip, limit=limit)
    return releases


@router.post("/", response_model=schemas.Release, status_code=201)
def create_release(release: schemas.ReleaseCreate, db: Session = Depends(get_db)):
    db_release = crud.get_release_by_version(db, version=release.version)
    if db_release:
        raise HTTPException(status_code=400, detail="Release with this version already exists")
    db_release = crud.create_release(db=db, release=release)
    return crud.get_release_schema(db, release_id=db_release.id)


@router.get("/{release_id}", response_model=schemas.ReleaseDetail)
def get_release(release_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    detail = schemas.ReleaseDetail(
        id=db_release.id,
        version=db_release.version,
        name=db_release.name,
        description=db_release.description,
        status=db_release.status,
        release_date=db_release.release_date,
        blocker_count=db_release.blocker_count,
        created_at=db_release.created_at,
        updated_at=db_release.updated_at,
        check_items=db_release.check_items,
        approvals=db_release.approvals,
    )
    return detail


@router.put("/{release_id}", response_model=schemas.Release)
def update_release(release_id: int, release: schemas.ReleaseUpdate, db: Session = Depends(get_db)):
    db_release = crud.update_release(db, release_id=release_id, release=release)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return crud.get_release_schema(db, release_id=release_id)


@router.delete("/{release_id}", status_code=204)
def delete_release(release_id: int, db: Session = Depends(get_db)):
    success = crud.delete_release(db, release_id=release_id)
    if not success:
        raise HTTPException(status_code=404, detail="Release not found")
    return None


@router.get("/{release_id}/blockers", response_model=schemas.ReleaseBlockers)
def get_release_blockers(release_id: int, db: Session = Depends(get_db)):
    blockers = crud.get_release_blockers(db, release_id=release_id)
    if blockers is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return blockers


@router.get("/{release_id}/recount-blockers", response_model=schemas.Release)
def recount_blockers(release_id: int, db: Session = Depends(get_db)):
    result = crud.recount_blockers(db, release_id=release_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return crud.get_release_schema(db, release_id=release_id)
