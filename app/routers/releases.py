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
    return crud.create_release(db=db, release=release)


@router.get("/{release_id}", response_model=schemas.ReleaseDetail)
def get_release(release_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return db_release


@router.put("/{release_id}", response_model=schemas.Release)
def update_release(release_id: int, release: schemas.ReleaseUpdate, db: Session = Depends(get_db)):
    db_release = crud.update_release(db, release_id=release_id, release=release)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return db_release


@router.delete("/{release_id}", status_code=204)
def delete_release(release_id: int, db: Session = Depends(get_db)):
    success = crud.delete_release(db, release_id=release_id)
    if not success:
        raise HTTPException(status_code=404, detail="Release not found")
    return None
