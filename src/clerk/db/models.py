"""SQLAlchemy ORM models for CLERK database."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class UserProfile(Base):
    """User profile linked to Supabase Auth.

    This table is populated via a database trigger when users sign up
    through Supabase Auth. The id matches auth.users.id.
    """

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owned_kits: Mapped[list["ReasoningKit"]] = relationship(
        back_populates="owner", lazy="selectin"
    )
    created_versions: Mapped[list["KitVersion"]] = relationship(
        back_populates="created_by_user", lazy="selectin"
    )
    execution_runs: Mapped[list["ExecutionRun"]] = relationship(
        back_populates="user", lazy="selectin"
    )


class ReasoningKit(Base):
    """A reasoning kit (main entity).

    Reasoning kits are the top-level entity containing versioned
    collections of resources and workflow steps.
    """

    __tablename__ = "reasoning_kits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kit_versions.id", use_alter=True, ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped["UserProfile | None"] = relationship(
        back_populates="owned_kits", lazy="selectin"
    )
    versions: Mapped[list["KitVersion"]] = relationship(
        back_populates="kit",
        foreign_keys="KitVersion.kit_id",
        lazy="selectin",
        order_by="KitVersion.version_number.desc()",
    )
    current_version: Mapped["KitVersion | None"] = relationship(
        foreign_keys=[current_version_id],
        post_update=True,
        lazy="selectin",
    )


class KitVersion(Base):
    """A version of a reasoning kit.

    Each version contains a snapshot of resources and workflow steps.
    Versions are immutable once created (except for draft status).
    """

    __tablename__ = "kit_versions"
    __table_args__ = (
        UniqueConstraint("kit_id", "version_number", name="uq_kit_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    kit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_kits.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_message: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    kit: Mapped["ReasoningKit"] = relationship(
        back_populates="versions",
        foreign_keys=[kit_id],
        lazy="selectin",
    )
    created_by_user: Mapped["UserProfile | None"] = relationship(
        back_populates="created_versions", lazy="selectin"
    )
    resources: Mapped[list["Resource"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Resource.resource_number",
    )
    workflow_steps: Mapped[list["WorkflowStep"]] = relationship(
        back_populates="version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WorkflowStep.step_number",
    )
    execution_runs: Mapped[list["ExecutionRun"]] = relationship(
        back_populates="version", lazy="selectin"
    )


class Resource(Base):
    """A resource file in a kit version.

    Resources are files (text, PDF, Excel, etc.) that can be referenced
    in workflow steps using {resource_N} placeholders.
    """

    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint("version_id", "resource_number", name="uq_resource_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kit_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_number: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(127))
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    version: Mapped["KitVersion"] = relationship(
        back_populates="resources", lazy="selectin"
    )

    @property
    def resource_id(self) -> str:
        """Get the resource_id for placeholder resolution."""
        return f"resource_{self.resource_number}"


class WorkflowStep(Base):
    """An instruction step in a kit version.

    Workflow steps are executed sequentially. Each step's prompt can
    reference resources ({resource_N}) and previous outputs ({workflow_N}).
    """

    __tablename__ = "workflow_steps"
    __table_args__ = (
        UniqueConstraint("version_id", "step_number", name="uq_step_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kit_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    version: Mapped["KitVersion"] = relationship(
        back_populates="workflow_steps", lazy="selectin"
    )

    @property
    def output_id(self) -> str:
        """Get the output_id for this step."""
        return f"workflow_{self.step_number}"


class ExecutionRun(Base):
    """A single execution run of a reasoning kit.

    Tracks the execution of a kit version, including timing and status.
    """

    __tablename__ = "execution_runs"
    __table_args__ = (
        CheckConstraint(
            "storage_mode IN ('transparent', 'anonymous')", name="ck_storage_mode"
        ),
        CheckConstraint(
            "status IN ('running', 'paused', 'completed', 'failed')", name="ck_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("kit_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
    )
    storage_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    version: Mapped["KitVersion"] = relationship(
        back_populates="execution_runs", lazy="selectin"
    )
    user: Mapped["UserProfile | None"] = relationship(
        back_populates="execution_runs", lazy="selectin"
    )
    step_executions: Mapped[list["StepExecution"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="StepExecution.step_number",
    )


class StepExecution(Base):
    """Execution result for a single workflow step.

    Stores the input, output, evaluation, and metrics for each step.
    Data storage depends on the run's storage_mode:
    - transparent: full text in input_text/output_text
    - anonymous: character counts in input_char_count/output_char_count
    """

    __tablename__ = "step_executions"
    __table_args__ = (
        UniqueConstraint("run_id", "step_number", name="uq_step_execution"),
        CheckConstraint(
            "evaluation_score IS NULL OR (evaluation_score >= 0 AND evaluation_score <= 100)",
            name="ck_evaluation_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    input_text: Mapped[str | None] = mapped_column(Text)
    input_char_count: Mapped[int | None] = mapped_column(Integer)
    output_text: Mapped[str | None] = mapped_column(Text)
    output_char_count: Mapped[int | None] = mapped_column(Integer)
    evaluation_score: Mapped[int | None] = mapped_column(Integer)
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    run: Mapped["ExecutionRun"] = relationship(
        back_populates="step_executions", lazy="selectin"
    )


class UserKitBookmark(Base):
    """A user's bookmark/save of a community kit.

    Allows users to add community kits to their "My Kits" view
    without being the owner.
    """

    __tablename__ = "user_kit_bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "kit_id", name="uq_user_kit_bookmark"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    kit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reasoning_kits.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    user: Mapped["UserProfile"] = relationship(lazy="selectin")
    kit: Mapped["ReasoningKit"] = relationship(lazy="selectin")


class EmbeddingCache(Base):
    """System-wide cache for text embeddings.
    
    Stores the OpenAI embeddings for chunks of text to avoid recomputing
    them across different runs or users.
    """

    __tablename__ = "embedding_cache"

    text_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

