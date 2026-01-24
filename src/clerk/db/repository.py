"""Repository classes for database operations.

Provides async CRUD operations for all database entities using
the repository pattern for clean separation of concerns.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    ExecutionRun,
    KitVersion,
    ReasoningKit,
    Resource,
    StepExecution,
    UserProfile,
    WorkflowStep,
)


class UserProfileRepository:
    """Repository for user profile operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> UserProfile | None:
        """Get a user profile by ID.

        Args:
            user_id: The user's UUID (matches auth.users.id)

        Returns:
            User profile or None if not found
        """
        stmt = select(UserProfile).where(UserProfile.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: UUID,
        display_name: str | None = None,
        is_premium: bool = False,
    ) -> UserProfile:
        """Create a new user profile.

        Args:
            user_id: The user's UUID from Supabase Auth
            display_name: Optional display name
            is_premium: Whether the user has premium access

        Returns:
            Created user profile
        """
        profile = UserProfile(
            id=user_id,
            display_name=display_name,
            is_premium=is_premium,
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update(
        self,
        user_id: UUID,
        display_name: str | None = None,
        is_premium: bool | None = None,
    ) -> UserProfile | None:
        """Update a user profile.

        Args:
            user_id: The user's UUID
            display_name: New display name (None to keep current)
            is_premium: New premium status (None to keep current)

        Returns:
            Updated profile or None if not found
        """
        profile = await self.get_by_id(user_id)
        if profile is None:
            return None

        if display_name is not None:
            profile.display_name = display_name
        if is_premium is not None:
            profile.is_premium = is_premium

        profile.updated_at = datetime.utcnow()
        await self.session.flush()
        return profile


class ReasoningKitRepository:
    """Repository for reasoning kit operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, kit_id: UUID) -> ReasoningKit | None:
        """Get a kit by ID with current version loaded.

        Args:
            kit_id: The kit's UUID

        Returns:
            Reasoning kit or None if not found
        """
        stmt = (
            select(ReasoningKit)
            .where(ReasoningKit.id == kit_id)
            .options(
                selectinload(ReasoningKit.current_version).selectinload(
                    KitVersion.resources
                ),
                selectinload(ReasoningKit.current_version).selectinload(
                    KitVersion.workflow_steps
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> ReasoningKit | None:
        """Get a kit by its URL-friendly slug.

        Args:
            slug: The kit's unique slug

        Returns:
            Reasoning kit with current version, resources, and steps loaded
        """
        stmt = (
            select(ReasoningKit)
            .where(ReasoningKit.slug == slug)
            .options(
                selectinload(ReasoningKit.current_version).selectinload(
                    KitVersion.resources
                ),
                selectinload(ReasoningKit.current_version).selectinload(
                    KitVersion.workflow_steps
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_public(self) -> list[ReasoningKit]:
        """List all public reasoning kits.

        Returns:
            List of public reasoning kits (without version details)
        """
        stmt = (
            select(ReasoningKit)
            .where(ReasoningKit.is_public == True)  # noqa: E712
            .order_by(ReasoningKit.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_owner(self, owner_id: UUID) -> list[ReasoningKit]:
        """List all kits owned by a user.

        Args:
            owner_id: The owner's UUID

        Returns:
            List of reasoning kits owned by the user
        """
        stmt = (
            select(ReasoningKit)
            .where(ReasoningKit.owner_id == owner_id)
            .order_by(ReasoningKit.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        slug: str,
        name: str,
        description: str | None = None,
        owner_id: UUID | None = None,
        is_public: bool = True,
    ) -> ReasoningKit:
        """Create a new reasoning kit.

        Args:
            slug: URL-friendly unique identifier
            name: Display name
            description: Optional description
            owner_id: Optional owner user ID
            is_public: Whether the kit is publicly visible

        Returns:
            Created reasoning kit
        """
        kit = ReasoningKit(
            slug=slug,
            name=name,
            description=description,
            owner_id=owner_id,
            is_public=is_public,
        )
        self.session.add(kit)
        await self.session.flush()
        return kit

    async def update(
        self,
        kit_id: UUID,
        name: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> ReasoningKit | None:
        """Update a reasoning kit.

        Args:
            kit_id: The kit's UUID
            name: New name (None to keep current)
            description: New description (None to keep current)
            is_public: New visibility (None to keep current)

        Returns:
            Updated kit or None if not found
        """
        kit = await self.get_by_id(kit_id)
        if kit is None:
            return None

        if name is not None:
            kit.name = name
        if description is not None:
            kit.description = description
        if is_public is not None:
            kit.is_public = is_public

        kit.updated_at = datetime.utcnow()
        await self.session.flush()
        return kit

    async def delete(self, kit_id: UUID) -> bool:
        """Delete a reasoning kit and all its versions.

        Args:
            kit_id: The kit's UUID

        Returns:
            True if deleted, False if not found
        """
        kit = await self.get_by_id(kit_id)
        if kit is None:
            return False

        await self.session.delete(kit)
        await self.session.flush()
        return True

    async def search(
        self,
        query: str,
        include_private: bool = False,
        owner_id: UUID | None = None,
    ) -> list[ReasoningKit]:
        """Search kits by name, description, or resource content.

        Args:
            query: Search query string
            include_private: Whether to include private kits
            owner_id: If set with include_private, only show this user's private kits

        Returns:
            List of matching reasoning kits
        """
        # Basic search on name and description
        search_pattern = f"%{query}%"
        search_condition = ReasoningKit.name.ilike(
            search_pattern
        ) | ReasoningKit.description.ilike(search_pattern)

        if not include_private:
            # Only public kits matching search
            stmt = (
                select(ReasoningKit)
                .where(search_condition)
                .where(ReasoningKit.is_public == True)  # noqa: E712
                .order_by(ReasoningKit.name)
                .limit(50)
            )
        elif owner_id is not None:
            # Public OR owned by this user, matching search
            stmt = (
                select(ReasoningKit)
                .where(search_condition)
                .where(
                    (ReasoningKit.is_public == True)  # noqa: E712
                    | (ReasoningKit.owner_id == owner_id)
                )
                .order_by(ReasoningKit.name)
                .limit(50)
            )
        else:
            # All kits matching search (admin mode)
            stmt = (
                select(ReasoningKit)
                .where(search_condition)
                .order_by(ReasoningKit.name)
                .limit(50)
            )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class KitVersionRepository:
    """Repository for kit version operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, version_id: UUID) -> KitVersion | None:
        """Get a version by ID with resources and steps loaded.

        Args:
            version_id: The version's UUID

        Returns:
            Kit version or None if not found
        """
        stmt = (
            select(KitVersion)
            .where(KitVersion.id == version_id)
            .options(
                selectinload(KitVersion.resources),
                selectinload(KitVersion.workflow_steps),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_kit(self, kit_id: UUID) -> list[KitVersion]:
        """List all versions for a kit.

        Args:
            kit_id: The kit's UUID

        Returns:
            List of versions ordered by version number descending
        """
        stmt = (
            select(KitVersion)
            .where(KitVersion.kit_id == kit_id)
            .order_by(KitVersion.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version_number(self, kit_id: UUID) -> int:
        """Get the latest version number for a kit.

        Args:
            kit_id: The kit's UUID

        Returns:
            Latest version number, or 0 if no versions exist
        """
        stmt = select(func.max(KitVersion.version_number)).where(
            KitVersion.kit_id == kit_id
        )
        result = await self.session.execute(stmt)
        max_version = result.scalar_one_or_none()
        return max_version or 0

    async def create(
        self,
        kit_id: UUID,
        commit_message: str | None = None,
        created_by: UUID | None = None,
        is_draft: bool = False,
    ) -> KitVersion:
        """Create a new version for a kit.

        Args:
            kit_id: The kit's UUID
            commit_message: Optional commit message
            created_by: Optional creator user ID
            is_draft: Whether this is a draft version

        Returns:
            Created kit version
        """
        # Get next version number
        latest = await self.get_latest_version_number(kit_id)
        version_number = latest + 1

        version = KitVersion(
            kit_id=kit_id,
            version_number=version_number,
            commit_message=commit_message,
            created_by=created_by,
            is_draft=is_draft,
        )
        self.session.add(version)
        await self.session.flush()

        # Update kit's current_version_id if not a draft
        if not is_draft:
            stmt = select(ReasoningKit).where(ReasoningKit.id == kit_id)
            result = await self.session.execute(stmt)
            kit = result.scalar_one()
            kit.current_version_id = version.id
            kit.updated_at = datetime.utcnow()
            await self.session.flush()

        return version

    async def add_resource(
        self,
        version_id: UUID,
        resource_number: int,
        filename: str,
        storage_path: str,
        mime_type: str | None = None,
        extracted_text: str | None = None,
        file_size_bytes: int | None = None,
    ) -> Resource:
        """Add a resource to a version.

        Args:
            version_id: The version's UUID
            resource_number: The resource number (1, 2, 3, ...)
            filename: Original filename
            storage_path: Path in Supabase Storage
            mime_type: MIME type of the file
            extracted_text: Extracted text content for search
            file_size_bytes: File size in bytes

        Returns:
            Created resource
        """
        resource = Resource(
            version_id=version_id,
            resource_number=resource_number,
            filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            extracted_text=extracted_text,
            file_size_bytes=file_size_bytes,
        )
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def add_workflow_step(
        self,
        version_id: UUID,
        step_number: int,
        prompt_template: str,
    ) -> WorkflowStep:
        """Add a workflow step to a version.

        Args:
            version_id: The version's UUID
            step_number: The step number (1, 2, 3, ...)
            prompt_template: The instruction prompt template

        Returns:
            Created workflow step
        """
        step = WorkflowStep(
            version_id=version_id,
            step_number=step_number,
            prompt_template=prompt_template,
        )
        self.session.add(step)
        await self.session.flush()
        return step


class ExecutionRepository:
    """Repository for execution run operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, run_id: UUID) -> ExecutionRun | None:
        """Get an execution run by ID.

        Args:
            run_id: The run's UUID

        Returns:
            Execution run with step executions loaded
        """
        stmt = (
            select(ExecutionRun)
            .where(ExecutionRun.id == run_id)
            .options(selectinload(ExecutionRun.step_executions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_version(self, version_id: UUID) -> list[ExecutionRun]:
        """List all execution runs for a kit version.

        Args:
            version_id: The version's UUID

        Returns:
            List of execution runs ordered by start time descending
        """
        stmt = (
            select(ExecutionRun)
            .where(ExecutionRun.version_id == version_id)
            .order_by(ExecutionRun.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[ExecutionRun]:
        """List recent execution runs for a user.

        Args:
            user_id: The user's UUID
            limit: Maximum number of runs to return

        Returns:
            List of execution runs ordered by start time descending
        """
        stmt = (
            select(ExecutionRun)
            .where(ExecutionRun.user_id == user_id)
            .order_by(ExecutionRun.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        version_id: UUID,
        storage_mode: str,
        user_id: UUID | None = None,
    ) -> ExecutionRun:
        """Create a new execution run.

        Args:
            version_id: The kit version's UUID
            storage_mode: Either "transparent" or "anonymous"
            user_id: Optional user ID

        Returns:
            Created execution run
        """
        run = ExecutionRun(
            version_id=version_id,
            user_id=user_id,
            storage_mode=storage_mode,
            status="running",
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_step_execution(
        self,
        run_id: UUID,
        step_number: int,
        input_text: str | None = None,
        input_char_count: int | None = None,
        output_text: str | None = None,
        output_char_count: int | None = None,
        evaluation_score: int | None = None,
        model_used: str | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> StepExecution:
        """Add a step execution to a run.

        Args:
            run_id: The run's UUID
            step_number: The step number
            input_text: Full input text (transparent mode)
            input_char_count: Input character count (anonymous mode)
            output_text: Full output text (transparent mode)
            output_char_count: Output character count (anonymous mode)
            evaluation_score: Optional evaluation score (0-100)
            model_used: LLM model used
            tokens_used: Total tokens used
            latency_ms: Execution latency in milliseconds

        Returns:
            Created step execution
        """
        step = StepExecution(
            run_id=run_id,
            step_number=step_number,
            input_text=input_text,
            input_char_count=input_char_count,
            output_text=output_text,
            output_char_count=output_char_count,
            evaluation_score=evaluation_score,
            model_used=model_used,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def complete_run(
        self,
        run_id: UUID,
        error: str | None = None,
    ) -> ExecutionRun | None:
        """Mark a run as completed or failed.

        Args:
            run_id: The run's UUID
            error: Error message if failed (None for success)

        Returns:
            Updated run or None if not found
        """
        run = await self.get_by_id(run_id)
        if run is None:
            return None

        run.status = "failed" if error else "completed"
        run.completed_at = datetime.utcnow()
        run.error_message = error

        await self.session.flush()
        return run

    async def update_step_evaluation(
        self,
        run_id: UUID,
        step_number: int,
        evaluation_score: int,
    ) -> StepExecution | None:
        """Update the evaluation score for a step.

        Args:
            run_id: The run's UUID
            step_number: The step number
            evaluation_score: Evaluation score (0-100)

        Returns:
            Updated step execution or None if not found
        """
        stmt = (
            select(StepExecution)
            .where(StepExecution.run_id == run_id)
            .where(StepExecution.step_number == step_number)
        )
        result = await self.session.execute(stmt)
        step = result.scalar_one_or_none()

        if step is None:
            return None

        step.evaluation_score = evaluation_score
        await self.session.flush()
        return step
