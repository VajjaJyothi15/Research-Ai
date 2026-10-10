import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship
from app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="researcher")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    projects: Mapped[List["ResearchProject"]] = orm_relationship("ResearchProject", back_populates="user", cascade="all, delete-orphan")


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user: Mapped[Optional["User"]] = orm_relationship("User", back_populates="projects")
    runs: Mapped[List["ResearchRun"]] = orm_relationship("ResearchRun", back_populates="project", cascade="all, delete-orphan")


class ResearchRun(Base):
    __tablename__ = "research_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(100), default="general")
    mode: Mapped[str] = mapped_column(String(50), default="deep")
    status: Mapped[str] = mapped_column(String(50), default="INTAKE", index=True)
    current_stage: Mapped[str] = mapped_column(String(50), default="intake")
    
    policy_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    budget_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    usage_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    reproducibility_manifest: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project: Mapped[Optional["ResearchProject"]] = orm_relationship("ResearchProject", back_populates="runs")
    plans: Mapped[List["ResearchPlan"]] = orm_relationship("ResearchPlan", back_populates="run", cascade="all, delete-orphan")
    sources: Mapped[List["Source"]] = orm_relationship("Source", back_populates="run", cascade="all, delete-orphan")
    evidence: Mapped[List["EvidenceItem"]] = orm_relationship("EvidenceItem", back_populates="run", cascade="all, delete-orphan")
    claims: Mapped[List["Claim"]] = orm_relationship("Claim", back_populates="run", cascade="all, delete-orphan")
    contradictions: Mapped[List["Contradiction"]] = orm_relationship("Contradiction", back_populates="run", cascade="all, delete-orphan")
    tool_calls: Mapped[List["ToolCallLog"]] = orm_relationship("ToolCallLog", back_populates="run", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = orm_relationship("Report", back_populates="run", cascade="all, delete-orphan")
    uploaded_files: Mapped[List["UploadedFile"]] = orm_relationship("UploadedFile", back_populates="run", cascade="all, delete-orphan")


class ResearchPlan(Base):
    __tablename__ = "research_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="PENDING_APPROVAL")  # DRAFT, PENDING_APPROVAL, APPROVED, REJECTED
    main_question: Mapped[str] = mapped_column(Text, nullable=False)
    subquestions_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    plan_data_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="plans")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="web")  # academic, official, web, dataset, user_file
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="sources")
    evidence_items: Mapped[List["EvidenceItem"]] = orm_relationship("EvidenceItem", back_populates="source", cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_text: Mapped[str] = mapped_column(Text, nullable=False)
    publication_date: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    retrieval_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    evidence_type: Mapped[str] = mapped_column(String(50), default="fact")  # fact, stat, quote, opinion, calculation
    confidence_score: Mapped[float] = mapped_column(Float, default=0.9)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")  # VERIFIED, UNVERIFIED, CONTRADICTED
    relationship: Mapped[str] = mapped_column(String(50), default="SUPPORTING")  # SUPPORTING, CONTRADICTING, NEUTRAL

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="evidence")
    source: Mapped["Source"] = orm_relationship("Source", back_populates="evidence_items")
    claim_links: Mapped[List["ClaimEvidenceLink"]] = orm_relationship("ClaimEvidenceLink", back_populates="evidence", cascade="all, delete-orphan")


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="VERIFIED")
    section_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="claims")
    evidence_links: Mapped[List["ClaimEvidenceLink"]] = orm_relationship("ClaimEvidenceLink", back_populates="claim", cascade="all, delete-orphan")


class ClaimEvidenceLink(Base):
    __tablename__ = "claim_evidence_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    evidence_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence_items.id", ondelete="CASCADE"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), default="SUPPORTING")  # SUPPORTING, CONTRADICTING

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    claim: Mapped["Claim"] = orm_relationship("Claim", back_populates="evidence_links")
    evidence: Mapped["EvidenceItem"] = orm_relationship("EvidenceItem", back_populates="claim_links")


class Contradiction(Base):
    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    claim_a: Mapped[str] = mapped_column(Text, nullable=False)
    claim_b: Mapped[str] = mapped_column(Text, nullable=False)
    source_a_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source_b_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), default="UNRESOLVED")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="contradictions")


class ToolCallLog(Base):
    __tablename__ = "tool_call_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="SUCCESS")  # SUCCESS, FAILED
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="tool_calls")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    full_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    run: Mapped["ResearchRun"] = orm_relationship("ResearchRun", back_populates="reports")
    versions: Mapped[List["ReportVersion"]] = orm_relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")


class ReportVersion(Base):
    __tablename__ = "report_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    report: Mapped["Report"] = orm_relationship("Report", back_populates="versions")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    provenance_type: Mapped[str] = mapped_column(String(50), default="user_upload")
    parsed_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    run: Mapped[Optional["ResearchRun"]] = orm_relationship("ResearchRun", back_populates="uploaded_files")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), default="system")
    payload_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CustomTool(Base):
    __tablename__ = "custom_tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    schema_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
