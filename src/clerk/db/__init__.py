"""Database layer for CLERK.

This module provides:
- Supabase PostgreSQL integration via SQLAlchemy async
- Supabase Storage for binary file management
- Alembic migrations for schema management
- Repository pattern for data access
"""

from .config import get_async_session, get_supabase_client
from .models import (
    Base,
    ExecutionRun,
    KitVersion,
    ReasoningKit,
    Resource,
    StepExecution,
    UserKitBookmark,
    UserProfile,
    WorkflowStep,
)
from .repository import (
    BookmarkRepository,
    ExecutionRepository,
    KitVersionRepository,
    ReasoningKitRepository,
    UserProfileRepository,
)
from .storage import StorageService, ensure_bucket_exists
from .text_extraction import (
    detect_mime_type,
    detect_mime_type_from_filename,
    extract_text,
    extract_text_from_bytes,
)

__all__ = [
    # Config
    "get_async_session",
    "get_supabase_client",
    # Models
    "Base",
    "ExecutionRun",
    "KitVersion",
    "ReasoningKit",
    "Resource",
    "StepExecution",
    "UserProfile",
    "WorkflowStep",
    # Repositories
    "BookmarkRepository",
    "ExecutionRepository",
    "KitVersionRepository",
    "ReasoningKitRepository",
    "UserProfileRepository",
    # Storage
    "StorageService",
    "ensure_bucket_exists",
    # Text extraction
    "detect_mime_type",
    "detect_mime_type_from_filename",
    "extract_text",
    "extract_text_from_bytes",
]
