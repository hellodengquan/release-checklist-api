from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/releases/{release_id}/approvals", tags=["approvals"])


@router.get("/", response_model=List[schemas.Approval])
def list_approvals(release_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    approvals = crud.get_approvals(db, release_id=release_id, skip=skip, limit=limit)
    return approvals


@router.post("/", response_model=schemas.Approval, status_code=201)
def create_approval(release_id: int, approval: schemas.ApprovalCreate, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return crud.create_approval(db=db, release_id=release_id, approval=approval)


@router.get("/{approval_id}", response_model=schemas.Approval)
def get_approval(release_id: int, approval_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_approval = crud.get_approval(db, approval_id=approval_id)
    if db_approval is None or db_approval.release_id != release_id:
        raise HTTPException(status_code=404, detail="Approval not found")
    return db_approval


@router.put("/{approval_id}", response_model=schemas.Approval)
def update_approval(release_id: int, approval_id: int, approval: schemas.ApprovalUpdate, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_approval = crud.get_approval(db, approval_id=approval_id)
    if db_approval is None or db_approval.release_id != release_id:
        raise HTTPException(status_code=404, detail="Approval not found")
    return crud.update_approval(db=db, approval_id=approval_id, approval=approval)


@router.delete("/{approval_id}", status_code=204)
def delete_approval(release_id: int, approval_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_approval = crud.get_approval(db, approval_id=approval_id)
    if db_approval is None or db_approval.release_id != release_id:
        raise HTTPException(status_code=404, detail="Approval not found")
    crud.delete_approval(db, approval_id=approval_id)
    return None
