from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ReleaseStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    BLOCKED = "blocked"
    RELEASED = "released"


class CheckItemStatus(str, enum.Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckItemCategory(str, enum.Enum):
    CODE = "code"
    TEST = "test"
    BUILD = "build"
    DEPLOY = "deploy"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ReleaseStatus), default=ReleaseStatus.DRAFT, nullable=False)
    blocker_count = Column(Integer, default=0, nullable=False)
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    check_items = relationship("CheckItem", back_populates="release", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="release", cascade="all, delete-orphan")


class CheckItem(Base):
    __tablename__ = "check_items"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(CheckItemCategory), default=CheckItemCategory.OTHER, nullable=False)
    status = Column(Enum(CheckItemStatus), default=CheckItemStatus.PENDING, nullable=False)
    is_blocking = Column(Boolean, default=False, nullable=False)
    assignee = Column(String, nullable=True)
    checked_by = Column(String, nullable=True)
    checked_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    release = relationship("Release", back_populates="check_items")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id"), nullable=False)
    approver_role = Column(String, nullable=False)
    approver_name = Column(String, nullable=True)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False)
    comment = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    release = relationship("Release", back_populates="approvals")
