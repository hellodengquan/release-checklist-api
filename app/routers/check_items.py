from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/releases/{release_id}/check-items", tags=["check-items"])


@router.get("/", response_model=List[schemas.CheckItem])
def list_check_items(release_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    check_items = crud.get_check_items(db, release_id=release_id, skip=skip, limit=limit)
    return check_items


@router.post("/", response_model=schemas.CheckItem, status_code=201)
def create_check_item(release_id: int, check_item: schemas.CheckItemCreate, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    return crud.create_check_item(db=db, release_id=release_id, check_item=check_item)


@router.get("/{check_item_id}", response_model=schemas.CheckItem)
def get_check_item(release_id: int, check_item_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_check_item = crud.get_check_item(db, check_item_id=check_item_id)
    if db_check_item is None or db_check_item.release_id != release_id:
        raise HTTPException(status_code=404, detail="Check item not found")
    return db_check_item


@router.put("/{check_item_id}", response_model=schemas.CheckItem)
def update_check_item(release_id: int, check_item_id: int, check_item: schemas.CheckItemUpdate, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_check_item = crud.get_check_item(db, check_item_id=check_item_id)
    if db_check_item is None or db_check_item.release_id != release_id:
        raise HTTPException(status_code=404, detail="Check item not found")
    return crud.update_check_item(db=db, check_item_id=check_item_id, check_item=check_item)


@router.delete("/{check_item_id}", status_code=204)
def delete_check_item(release_id: int, check_item_id: int, db: Session = Depends(get_db)):
    db_release = crud.get_release(db, release_id=release_id)
    if db_release is None:
        raise HTTPException(status_code=404, detail="Release not found")
    db_check_item = crud.get_check_item(db, check_item_id=check_item_id)
    if db_check_item is None or db_check_item.release_id != release_id:
        raise HTTPException(status_code=404, detail="Check item not found")
    crud.delete_check_item(db, check_item_id=check_item_id)
    return None
