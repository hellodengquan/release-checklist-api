from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app import models, schemas
from app.models import CheckItemStatus, ApprovalStatus, ReleaseStatus


def get_release(db: Session, release_id: int) -> Optional[models.Release]:
    return db.query(models.Release).filter(models.Release.id == release_id).first()


def get_release_by_version(db: Session, version: str) -> Optional[models.Release]:
    return db.query(models.Release).filter(models.Release.version == version).first()


def get_releases(db: Session, skip: int = 0, limit: int = 100) -> List[models.Release]:
    return db.query(models.Release).order_by(models.Release.created_at.desc()).offset(skip).limit(limit).all()


def create_release(db: Session, release: schemas.ReleaseCreate) -> models.Release:
    db_release = models.Release(**release.model_dump())
    db.add(db_release)
    db.commit()
    db.refresh(db_release)
    return db_release


def update_release(db: Session, release_id: int, release: schemas.ReleaseUpdate) -> Optional[models.Release]:
    db_release = get_release(db, release_id)
    if not db_release:
        return None
    update_data = release.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_release, key, value)
    db.commit()
    db.refresh(db_release)
    return db_release


def delete_release(db: Session, release_id: int) -> bool:
    db_release = get_release(db, release_id)
    if not db_release:
        return False
    db.delete(db_release)
    db.commit()
    return True


def get_check_items(db: Session, release_id: int, skip: int = 0, limit: int = 100) -> List[models.CheckItem]:
    return (
        db.query(models.CheckItem)
        .filter(models.CheckItem.release_id == release_id)
        .order_by(models.CheckItem.sort_order, models.CheckItem.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_check_item(db: Session, check_item_id: int) -> Optional[models.CheckItem]:
    return db.query(models.CheckItem).filter(models.CheckItem.id == check_item_id).first()


def create_check_item(db: Session, release_id: int, check_item: schemas.CheckItemCreate) -> models.CheckItem:
    db_check_item = models.CheckItem(**check_item.model_dump(), release_id=release_id)
    db.add(db_check_item)
    db.commit()
    db.refresh(db_check_item)
    _update_release_status(db, release_id)
    return db_check_item


def update_check_item(db: Session, check_item_id: int, check_item: schemas.CheckItemUpdate) -> Optional[models.CheckItem]:
    db_check_item = get_check_item(db, check_item_id)
    if not db_check_item:
        return None
    update_data = check_item.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] != db_check_item.status:
        update_data["checked_at"] = datetime.utcnow()
    for key, value in update_data.items():
        setattr(db_check_item, key, value)
    db.commit()
    db.refresh(db_check_item)
    _update_release_status(db, db_check_item.release_id)
    return db_check_item


def delete_check_item(db: Session, check_item_id: int) -> bool:
    db_check_item = get_check_item(db, check_item_id)
    if not db_check_item:
        return False
    release_id = db_check_item.release_id
    db.delete(db_check_item)
    db.commit()
    _update_release_status(db, release_id)
    return True


def get_approvals(db: Session, release_id: int, skip: int = 0, limit: int = 100) -> List[models.Approval]:
    return (
        db.query(models.Approval)
        .filter(models.Approval.release_id == release_id)
        .order_by(models.Approval.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_approval(db: Session, approval_id: int) -> Optional[models.Approval]:
    return db.query(models.Approval).filter(models.Approval.id == approval_id).first()


def create_approval(db: Session, release_id: int, approval: schemas.ApprovalCreate) -> models.Approval:
    db_approval = models.Approval(**approval.model_dump(), release_id=release_id)
    if db_approval.status == ApprovalStatus.APPROVED:
        db_approval.approved_at = datetime.utcnow()
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    _update_release_status(db, release_id)
    return db_approval


def update_approval(db: Session, approval_id: int, approval: schemas.ApprovalUpdate) -> Optional[models.Approval]:
    db_approval = get_approval(db, approval_id)
    if not db_approval:
        return None
    update_data = approval.model_dump(exclude_unset=True)
    if "status" in update_data:
        if update_data["status"] == ApprovalStatus.APPROVED:
            update_data["approved_at"] = datetime.utcnow()
        else:
            update_data["approved_at"] = None
    for key, value in update_data.items():
        setattr(db_approval, key, value)
    db.commit()
    db.refresh(db_approval)
    _update_release_status(db, db_approval.release_id)
    return db_approval


def delete_approval(db: Session, approval_id: int) -> bool:
    db_approval = get_approval(db, approval_id)
    if not db_approval:
        return False
    release_id = db_approval.release_id
    db.delete(db_approval)
    db.commit()
    _update_release_status(db, release_id)
    return True


def get_blocker_summary(db: Session, release_id: int) -> Optional[schemas.BlockerSummary]:
    db_release = get_release(db, release_id)
    if not db_release:
        return None

    blocking_items = (
        db.query(models.CheckItem)
        .filter(
            models.CheckItem.release_id == release_id,
            models.CheckItem.is_blocking == True,
            models.CheckItem.status != CheckItemStatus.PASSED,
            models.CheckItem.status != CheckItemStatus.SKIPPED,
        )
        .order_by(models.CheckItem.sort_order, models.CheckItem.id)
        .all()
    )

    pending_approvals = (
        db.query(models.Approval)
        .filter(
            models.Approval.release_id == release_id,
            models.Approval.status == ApprovalStatus.PENDING,
        )
        .all()
    )

    can_release = len(blocking_items) == 0 and len(pending_approvals) == 0

    return schemas.BlockerSummary(
        release_id=db_release.id,
        release_version=db_release.version,
        release_name=db_release.name,
        total_blockers=len(blocking_items),
        blocking_check_items=blocking_items,
        pending_approvals=pending_approvals,
        can_release=can_release,
    )


def get_release_summary(db: Session, release_id: int) -> Optional[schemas.ReleaseSummary]:
    db_release = get_release(db, release_id)
    if not db_release:
        return None

    check_items = db.query(models.CheckItem).filter(models.CheckItem.release_id == release_id).all()
    approvals = db.query(models.Approval).filter(models.Approval.release_id == release_id).all()

    total = len(check_items)
    passed = sum(1 for c in check_items if c.status == CheckItemStatus.PASSED)
    failed = sum(1 for c in check_items if c.status == CheckItemStatus.FAILED)
    pending = sum(1 for c in check_items if c.status == CheckItemStatus.PENDING)
    skipped = sum(1 for c in check_items if c.status == CheckItemStatus.SKIPPED)
    blocking = sum(
        1 for c in check_items
        if c.is_blocking and c.status not in (CheckItemStatus.PASSED, CheckItemStatus.SKIPPED)
    )

    total_app = len(approvals)
    approved = sum(1 for a in approvals if a.status == ApprovalStatus.APPROVED)
    pending_app = sum(1 for a in approvals if a.status == ApprovalStatus.PENDING)
    rejected = sum(1 for a in approvals if a.status == ApprovalStatus.REJECTED)

    can_release = blocking == 0 and pending_app == 0 and rejected == 0

    return schemas.ReleaseSummary(
        release_id=db_release.id,
        release_version=db_release.version,
        release_name=db_release.name,
        status=db_release.status,
        total_check_items=total,
        passed_check_items=passed,
        failed_check_items=failed,
        pending_check_items=pending,
        skipped_check_items=skipped,
        blocking_items_count=blocking,
        total_approvals=total_app,
        approved_approvals=approved,
        pending_approvals=pending_app,
        rejected_approvals=rejected,
        can_release=can_release,
    )


def _update_release_status(db: Session, release_id: int) -> None:
    summary = get_release_summary(db, release_id)
    if not summary:
        return

    db_release = get_release(db, release_id)
    if not db_release:
        return

    if db_release.status == ReleaseStatus.RELEASED:
        return

    if summary.blocking_items_count > 0 or summary.rejected_approvals > 0:
        new_status = ReleaseStatus.BLOCKED
    elif summary.pending_check_items == 0 and summary.pending_approvals == 0 and summary.total_check_items > 0:
        new_status = ReleaseStatus.READY
    elif summary.total_check_items == 0 and summary.total_approvals == 0:
        new_status = ReleaseStatus.DRAFT
    else:
        new_status = ReleaseStatus.IN_PROGRESS

    if db_release.status != new_status:
        db_release.status = new_status
        db.commit()
