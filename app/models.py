from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int]


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[str] = mapped_column(default=now)


class Scoped:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), index=True)


class Customer(Scoped, Base):
    __tablename__ = "customers"
    name: Mapped[str]
    contact: Mapped[str]
    email: Mapped[str]


class Inquiry(Scoped, Base):
    __tablename__ = "inquiries"
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    subject: Mapped[str]
    body: Mapped[str] = mapped_column(Text)
    sample_key: Mapped[str | None]
    brief: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)


class Job(Scoped, Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("workspace_id", "source_inquiry_id"),)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    source_inquiry_id: Mapped[str | None] = mapped_column(ForeignKey("inquiries.id"))
    number: Mapped[str]
    title: Mapped[str]
    site: Mapped[str]
    service: Mapped[str]
    requested_start: Mapped[date]
    requested_end: Mapped[date]
    status: Mapped[str] = mapped_column(default="draft")
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[str] = mapped_column(default=now)


class Quote(Scoped, Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("job_id", "revision"),)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    revision: Mapped[int]
    state: Mapped[str] = mapped_column(default="draft")
    total_cents: Mapped[int]
    created_at: Mapped[str] = mapped_column(default=now)


class QuoteLine(Scoped, Base):
    __tablename__ = "quote_lines"
    quote_id: Mapped[str] = mapped_column(ForeignKey("quotes.id"))
    position: Mapped[int]
    description: Mapped[str]
    quantity: Mapped[str]
    unit_price: Mapped[str]
    total_cents: Mapped[int]


class Crew(Scoped, Base):
    __tablename__ = "crews"
    name: Mapped[str]
    description: Mapped[str]


class Equipment(Scoped, Base):
    __tablename__ = "equipment"
    name: Mapped[str]
    description: Mapped[str]


class Assignment(Scoped, Base):
    __tablename__ = "assignments"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True)
    crew_id: Mapped[str] = mapped_column(ForeignKey("crews.id"))
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.id"))
    start_date: Mapped[date]
    end_date: Mapped[date]


class CommunicationDraft(Scoped, Base):
    __tablename__ = "communication_drafts"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    subject: Mapped[str]
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=now)


class ActivityEvent(Scoped, Base):
    __tablename__ = "activity_events"
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"))
    kind: Mapped[str]
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=now)


class IntegrationPreview(Scoped, Base):
    __tablename__ = "integration_previews"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    connector: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=now)
