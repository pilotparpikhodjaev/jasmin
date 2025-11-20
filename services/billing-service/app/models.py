import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("admin", "reseller", "client", name="account_type"), nullable=False, default="client"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "suspended", name="account_status"), nullable=False, default="active"
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True
    )
    profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    balance: Mapped["AccountBalance"] = relationship(back_populates="account", uselist=False, cascade="all")
    templates: Mapped[List["Template"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    credentials: Mapped[Optional["AccountCredential"]] = relationship(uselist=False)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255))
    allowed_ips: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(64)))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[Account] = relationship(back_populates="api_keys")


class AccountBalance(Base):
    __tablename__ = "account_balances"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), primary_key=True
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    account: Mapped[Account] = relationship(back_populates="balance")


class BalanceLedger(Base):
    __tablename__ = "balance_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    direction: Mapped[str] = mapped_column(
        Enum("debit", "credit", name="ledger_direction"), nullable=False, default="debit"
    )
    reason: Mapped[Optional[str]] = mapped_column(Text)
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[Account] = relationship()

    __table_args__ = (Index("idx_balance_ledger_account_created_at", "account_id", created_at.desc()),)


class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    mcc: Mapped[Optional[str]] = mapped_column(String(3))
    mnc: Mapped[Optional[str]] = mapped_column(String(3))
    connector_id: Mapped[Optional[str]] = mapped_column(String(64))
    price_per_submit: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "mcc",
            "mnc",
            "connector_id",
            name="uq_tariff_account_prefix_connector",
        ),
    )


class SmsCdr(Base):
    __tablename__ = "sms_cdr"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    connector_id: Mapped[Optional[str]] = mapped_column(String(64))
    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("operators.id"))
    msisdn: Mapped[str] = mapped_column(String(32), nullable=False)
    sender: Mapped[Optional[str]] = mapped_column(String(32))
    message_text: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="submitted")
    parts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[Optional[Numeric]] = mapped_column(Numeric(18, 6))
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    country: Mapped[Optional[str]] = mapped_column(String(2))
    dispatch_id: Mapped[Optional[str]] = mapped_column(String(255))
    user_sms_id: Mapped[Optional[str]] = mapped_column(String(255))
    submit_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[Optional[str]] = mapped_column(String(32))
    dlr_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_sms_cdr_account_created_at", "account_id", created_at.desc()),
        Index("idx_sms_cdr_message_id", "message_id", unique=True),
        Index("idx_sms_cdr_dispatch", "dispatch_id"),
        Index("idx_sms_cdr_user_sms_id", "user_sms_id"),
    )


class TemplateStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    status: Mapped[TemplateStatus] = mapped_column(Enum(TemplateStatus), default=TemplateStatus.pending)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text)
    last_submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    account: Mapped[Account] = relationship(back_populates="templates")


# ============================================================================
# ENTERPRISE MODELS
# ============================================================================


class Operator(Base):
    __tablename__ = "operators"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str]
    code: Mapped[Optional[str]]
    country: Mapped[Optional[str]]
    mcc: Mapped[Optional[str]]
    mnc: Mapped[Optional[str]]
    price_per_sms: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 6))
    currency: Mapped[Optional[str]]
    priority: Mapped[Optional[int]]
    weight: Mapped[Optional[int]]
    status: Mapped[Optional[str]]
    health_check_enabled: Mapped[Optional[bool]]
    health_check_interval: Mapped[Optional[int]]
    smpp_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    jasmin_connector_id: Mapped[Optional[str]]
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[Optional[datetime]]
    updated_at: Mapped[Optional[datetime]]

    health_metrics: Mapped[List["OperatorHealthMetric"]] = relationship(
        back_populates="operator", cascade="all, delete-orphan"
    )


class OperatorHealthMetric(Base):
    __tablename__ = "operator_health_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("operators.id"), nullable=False)
    is_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    connection_uptime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    submit_sm_count: Mapped[int] = mapped_column(Integer, default=0)
    submit_sm_resp_count: Mapped[int] = mapped_column(Integer, default=0)
    delivery_count: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    submit_success_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)
    delivery_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.0)
    avg_submit_latency_ms: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    p95_submit_latency_ms: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    p99_submit_latency_ms: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.0)
    health_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.0)
    health_status: Mapped[str] = mapped_column(
        Enum("healthy", "degraded", "unhealthy", "unknown", name="health_status_type"),
        nullable=False,
        default="unknown",
    )
    recent_errors: Mapped[list] = mapped_column(JSONB, default=list)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    operator: Mapped[Operator] = relationship(back_populates="health_metrics")

    __table_args__ = (Index("idx_operator_health_operator_measured", "operator_id", measured_at.desc()),)


class Nickname(Base):
    __tablename__ = "nicknames"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    nickname: Mapped[str] = mapped_column(String(11), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "approved", "rejected", name="nickname_status"), nullable=False, default="pending"
    )
    category: Mapped[Optional[str]] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("account_id", "nickname", name="uq_nickname_account"),
        Index("idx_nicknames_account", "account_id"),
        Index("idx_nicknames_status", "status"),
    )


class AccountCredential(Base):
    __tablename__ = "account_credentials"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (Index("idx_account_credentials_email", "email"),)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("charge", "refund", "topup", "adjustment", "commission", name="transaction_type"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    reference_type: Mapped[Optional[str]] = mapped_column(String(64))
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_transactions_account_created", "account_id", created_at.desc()),
        Index("idx_transactions_reference", "reference_type", "reference_id"),
    )


class Dispatch(Base):
    __tablename__ = "dispatches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    total_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    submitted_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("processing", "completed", "failed", "cancelled", name="dispatch_status"),
        nullable=False,
        default="processing",
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_dispatches_account", "account_id", created_at.desc()),
        Index("idx_dispatches_dispatch_id", "dispatch_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    changes: Mapped[Optional[dict]] = mapped_column(JSONB)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_audit_logs_account", "account_id", created_at.desc()),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )

