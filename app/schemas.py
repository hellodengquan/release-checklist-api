from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models import (
    ReleaseStatus,
    CheckItemStatus,
    CheckItemCategory,
    ApprovalStatus,
)


class ReleaseBase(BaseModel):
    version: str
    name: str
    description: Optional[str] = None
    status: ReleaseStatus = ReleaseStatus.DRAFT
    release_date: Optional[datetime] = None


class ReleaseCreate(ReleaseBase):
    pass


class ReleaseUpdate(BaseModel):
    version: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReleaseStatus] = None
    release_date: Optional[datetime] = None


class Release(ReleaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReleaseDetail(Release):
    check_items: List["CheckItem"] = []
    approvals: List["Approval"] = []


class CheckItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: CheckItemCategory = CheckItemCategory.OTHER
    status: CheckItemStatus = CheckItemStatus.PENDING
    is_blocking: bool = False
    assignee: Optional[str] = None
    notes: Optional[str] = None
    sort_order: int = 0


class CheckItemCreate(CheckItemBase):
    pass


class CheckItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[CheckItemCategory] = None
    status: Optional[CheckItemStatus] = None
    is_blocking: Optional[bool] = None
    assignee: Optional[str] = None
    checked_by: Optional[str] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None


class CheckItem(CheckItemBase):
    id: int
    release_id: int
    checked_by: Optional[str] = None
    checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApprovalBase(BaseModel):
    approver_role: str
    approver_name: Optional[str] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalUpdate(BaseModel):
    approver_role: Optional[str] = None
    approver_name: Optional[str] = None
    status: Optional[ApprovalStatus] = None
    comment: Optional[str] = None


class Approval(ApprovalBase):
    id: int
    release_id: int
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BlockerSummary(BaseModel):
    release_id: int
    release_version: str
    release_name: str
    total_blockers: int
    blocking_check_items: List[CheckItem]
    pending_approvals: List[Approval]
    can_release: bool


class ReleaseSummary(BaseModel):
    release_id: int
    release_version: str
    release_name: str
    status: ReleaseStatus
    total_check_items: int
    passed_check_items: int
    failed_check_items: int
    pending_check_items: int
    skipped_check_items: int
    blocking_items_count: int
    total_approvals: int
    approved_approvals: int
    pending_approvals: int
    rejected_approvals: int
    can_release: bool


ReleaseDetail.model_rebuild()
