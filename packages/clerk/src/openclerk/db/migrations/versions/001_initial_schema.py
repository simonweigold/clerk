"""Initial schema with all tables and RLS policies.

Revision ID: 001
Revises: None
Create Date: 2026-01-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and RLS policies."""

    # ==========================================================================
    # USER PROFILES
    # ==========================================================================
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # ==========================================================================
    # REASONING KITS
    # ==========================================================================
    op.create_table(
        "reasoning_kits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        # current_version_id added after kit_versions table
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Index for listing public kits
    op.create_index(
        "idx_reasoning_kits_public", "reasoning_kits", ["is_public", "name"]
    )

    # Index for owner lookup
    op.create_index("idx_reasoning_kits_owner", "reasoning_kits", ["owner_id"])

    # ==========================================================================
    # KIT VERSIONS
    # ==========================================================================
    op.create_table(
        "kit_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "kit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reasoning_kits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("commit_message", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default="false"),
        sa.UniqueConstraint("kit_id", "version_number", name="uq_kit_version"),
    )

    # Now add current_version_id to reasoning_kits
    op.add_column(
        "reasoning_kits",
        sa.Column(
            "current_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kit_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ==========================================================================
    # RESOURCES
    # ==========================================================================
    op.create_table(
        "resources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kit_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource_number", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(127), nullable=True),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("version_id", "resource_number", name="uq_resource_number"),
    )

    # Full-text search index on extracted text
    op.execute(
        """
        CREATE INDEX idx_resources_text_search 
        ON resources 
        USING GIN (to_tsvector('english', COALESCE(extracted_text, '')))
        """
    )

    # ==========================================================================
    # WORKFLOW STEPS
    # ==========================================================================
    op.create_table(
        "workflow_steps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kit_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("prompt_template", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("version_id", "step_number", name="uq_step_number"),
    )

    # ==========================================================================
    # EXECUTION RUNS
    # ==========================================================================
    op.create_table(
        "execution_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("kit_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("storage_mode", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'running'"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "storage_mode IN ('transparent', 'anonymous')", name="ck_storage_mode"
        ),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed')", name="ck_status"
        ),
    )

    # Index for user's runs
    op.create_index(
        "idx_execution_runs_user", "execution_runs", ["user_id", "started_at"]
    )

    # Index for version's runs
    op.create_index(
        "idx_execution_runs_version", "execution_runs", ["version_id", "started_at"]
    )

    # ==========================================================================
    # STEP EXECUTIONS
    # ==========================================================================
    op.create_table(
        "step_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("execution_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_char_count", sa.Integer(), nullable=True),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("output_char_count", sa.Integer(), nullable=True),
        sa.Column("evaluation_score", sa.Integer(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("run_id", "step_number", name="uq_step_execution"),
        sa.CheckConstraint(
            "evaluation_score IS NULL OR (evaluation_score >= 0 AND evaluation_score <= 100)",
            name="ck_evaluation_score",
        ),
    )

    # ==========================================================================
    # SUPABASE AUTH INTEGRATION
    # ==========================================================================

    # Create trigger function to auto-create user_profile on signup
    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.handle_new_user()
        RETURNS TRIGGER AS $$
        BEGIN
            INSERT INTO public.user_profiles (id, display_name, created_at, updated_at)
            VALUES (
                NEW.id,
                COALESCE(NEW.raw_user_meta_data->>'display_name', NEW.email),
                NOW(),
                NOW()
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
    )

    # Create trigger on auth.users table
    op.execute(
        """
        CREATE OR REPLACE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW
        EXECUTE FUNCTION public.handle_new_user();
        """
    )

    # ==========================================================================
    # ROW LEVEL SECURITY POLICIES
    # ==========================================================================

    # Enable RLS on all tables
    for table in [
        "user_profiles",
        "reasoning_kits",
        "kit_versions",
        "resources",
        "workflow_steps",
        "execution_runs",
        "step_executions",
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # ---- User Profiles ----
    # Users can read their own profile
    op.execute(
        """
        CREATE POLICY "Users can view own profile"
        ON user_profiles FOR SELECT
        USING (auth.uid() = id)
        """
    )

    # Users can update their own profile
    op.execute(
        """
        CREATE POLICY "Users can update own profile"
        ON user_profiles FOR UPDATE
        USING (auth.uid() = id)
        """
    )

    # ---- Reasoning Kits ----
    # Anyone can view public kits
    op.execute(
        """
        CREATE POLICY "Public kits are viewable by everyone"
        ON reasoning_kits FOR SELECT
        USING (is_public = true)
        """
    )

    # Owners can view their own private kits
    op.execute(
        """
        CREATE POLICY "Owners can view own kits"
        ON reasoning_kits FOR SELECT
        USING (owner_id = auth.uid())
        """
    )

    # Authenticated users can create kits
    op.execute(
        """
        CREATE POLICY "Authenticated users can create kits"
        ON reasoning_kits FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL)
        """
    )

    # Owners can update their kits
    op.execute(
        """
        CREATE POLICY "Owners can update own kits"
        ON reasoning_kits FOR UPDATE
        USING (owner_id = auth.uid())
        """
    )

    # Owners can delete their kits
    op.execute(
        """
        CREATE POLICY "Owners can delete own kits"
        ON reasoning_kits FOR DELETE
        USING (owner_id = auth.uid())
        """
    )

    # ---- Kit Versions ----
    # Versions inherit kit visibility
    op.execute(
        """
        CREATE POLICY "Versions viewable if kit is viewable"
        ON kit_versions FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM reasoning_kits
                WHERE reasoning_kits.id = kit_versions.kit_id
                AND (reasoning_kits.is_public = true OR reasoning_kits.owner_id = auth.uid())
            )
        )
        """
    )

    # Kit owners can create versions
    op.execute(
        """
        CREATE POLICY "Kit owners can create versions"
        ON kit_versions FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM reasoning_kits
                WHERE reasoning_kits.id = kit_versions.kit_id
                AND reasoning_kits.owner_id = auth.uid()
            )
        )
        """
    )

    # ---- Resources ----
    # Resources inherit version visibility
    op.execute(
        """
        CREATE POLICY "Resources viewable if version is viewable"
        ON resources FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM kit_versions
                JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                WHERE kit_versions.id = resources.version_id
                AND (reasoning_kits.is_public = true OR reasoning_kits.owner_id = auth.uid())
            )
        )
        """
    )

    # Kit owners can manage resources
    op.execute(
        """
        CREATE POLICY "Kit owners can manage resources"
        ON resources FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM kit_versions
                JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                WHERE kit_versions.id = resources.version_id
                AND reasoning_kits.owner_id = auth.uid()
            )
        )
        """
    )

    # ---- Workflow Steps ----
    # Steps inherit version visibility
    op.execute(
        """
        CREATE POLICY "Steps viewable if version is viewable"
        ON workflow_steps FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM kit_versions
                JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                WHERE kit_versions.id = workflow_steps.version_id
                AND (reasoning_kits.is_public = true OR reasoning_kits.owner_id = auth.uid())
            )
        )
        """
    )

    # Kit owners can manage steps
    op.execute(
        """
        CREATE POLICY "Kit owners can manage steps"
        ON workflow_steps FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM kit_versions
                JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                WHERE kit_versions.id = workflow_steps.version_id
                AND reasoning_kits.owner_id = auth.uid()
            )
        )
        """
    )

    # ---- Execution Runs ----
    # Users can view their own runs
    op.execute(
        """
        CREATE POLICY "Users can view own runs"
        ON execution_runs FOR SELECT
        USING (user_id = auth.uid())
        """
    )

    # Anonymous runs are viewable by kit owners (for analytics)
    op.execute(
        """
        CREATE POLICY "Kit owners can view anonymous runs"
        ON execution_runs FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM kit_versions
                JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                WHERE kit_versions.id = execution_runs.version_id
                AND reasoning_kits.owner_id = auth.uid()
            )
        )
        """
    )

    # Authenticated users can create runs
    op.execute(
        """
        CREATE POLICY "Authenticated users can create runs"
        ON execution_runs FOR INSERT
        WITH CHECK (auth.uid() IS NOT NULL)
        """
    )

    # Users can update their own runs
    op.execute(
        """
        CREATE POLICY "Users can update own runs"
        ON execution_runs FOR UPDATE
        USING (user_id = auth.uid())
        """
    )

    # ---- Step Executions ----
    # Step executions inherit run visibility
    op.execute(
        """
        CREATE POLICY "Step executions viewable if run is viewable"
        ON step_executions FOR SELECT
        USING (
            EXISTS (
                SELECT 1 FROM execution_runs
                WHERE execution_runs.id = step_executions.run_id
                AND (
                    execution_runs.user_id = auth.uid()
                    OR EXISTS (
                        SELECT 1 FROM kit_versions
                        JOIN reasoning_kits ON reasoning_kits.id = kit_versions.kit_id
                        WHERE kit_versions.id = execution_runs.version_id
                        AND reasoning_kits.owner_id = auth.uid()
                    )
                )
            )
        )
        """
    )

    # Run owners can create step executions
    op.execute(
        """
        CREATE POLICY "Run owners can create step executions"
        ON step_executions FOR INSERT
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM execution_runs
                WHERE execution_runs.id = step_executions.run_id
                AND execution_runs.user_id = auth.uid()
            )
        )
        """
    )

    # Run owners can update step executions
    op.execute(
        """
        CREATE POLICY "Run owners can update step executions"
        ON step_executions FOR UPDATE
        USING (
            EXISTS (
                SELECT 1 FROM execution_runs
                WHERE execution_runs.id = step_executions.run_id
                AND execution_runs.user_id = auth.uid()
            )
        )
        """
    )


def downgrade() -> None:
    """Drop all tables and policies."""

    # Drop RLS policies (they're dropped automatically with tables)

    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users")
    op.execute("DROP FUNCTION IF EXISTS public.handle_new_user()")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("step_executions")
    op.drop_table("execution_runs")
    op.drop_table("workflow_steps")
    op.drop_table("resources")

    # Remove current_version_id FK before dropping kit_versions
    op.drop_column("reasoning_kits", "current_version_id")
    op.drop_table("kit_versions")

    op.drop_table("reasoning_kits")
    op.drop_table("user_profiles")
