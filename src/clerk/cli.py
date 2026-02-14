"""Command-line interface for CLERK."""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from .db.config import get_config
from .graph import run_reasoning_kit
from .loader import (
    LoadedKit,
    get_kit_info_from_db,
    list_reasoning_kits,
    list_reasoning_kits_from_db,
    load_reasoning_kit,
    load_reasoning_kit_from_db,
)


def main() -> None:
    """Main entry point for the CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="CLERK - Community Library of Executable Reasoning Kits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # =========================================================================
    # LIST COMMAND
    # =========================================================================
    list_parser = subparsers.add_parser("list", help="List available reasoning kits")
    list_parser.add_argument(
        "--local",
        action="store_true",
        help="List from local filesystem instead of database",
    )
    list_parser.add_argument(
        "--path",
        type=str,
        default="reasoning_kits",
        help="Base path for local reasoning kits",
    )

    # =========================================================================
    # RUN COMMAND
    # =========================================================================
    run_parser = subparsers.add_parser("run", help="Run a reasoning kit")
    run_parser.add_argument(
        "kit",
        type=str,
        help="Name/slug of the reasoning kit to run",
    )
    run_parser.add_argument(
        "--local",
        action="store_true",
        help="Load from local filesystem instead of database",
    )
    run_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for local reasoning kits",
    )
    run_parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Enable step-by-step evaluation prompts",
    )
    run_parser.add_argument(
        "--mode",
        choices=["transparent", "anonymous"],
        default="transparent",
        help="Evaluation mode: 'transparent' stores full text, 'anonymous' stores char counts",
    )

    # =========================================================================
    # INFO COMMAND
    # =========================================================================
    info_parser = subparsers.add_parser("info", help="Show info about a reasoning kit")
    info_parser.add_argument(
        "kit",
        type=str,
        help="Name/slug of the reasoning kit",
    )
    info_parser.add_argument(
        "--local",
        action="store_true",
        help="Load from local filesystem instead of database",
    )
    info_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for local reasoning kits",
    )

    # =========================================================================
    # DB COMMAND GROUP
    # =========================================================================
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_subparsers = db_parser.add_subparsers(
        dest="db_command", help="Database commands"
    )

    # db migrate
    db_migrate_parser = db_subparsers.add_parser(
        "migrate", help="Apply pending database migrations"
    )
    db_migrate_parser.add_argument(
        "--revision",
        type=str,
        default="head",
        help="Target revision (default: head)",
    )

    # db status
    db_subparsers.add_parser("status", help="Show migration status")

    # db setup
    db_subparsers.add_parser(
        "setup", help="Setup database (run migrations + create storage bucket)"
    )

    # =========================================================================
    # SYNC COMMAND GROUP
    # =========================================================================
    sync_parser = subparsers.add_parser(
        "sync", help="Sync reasoning kits between local and database"
    )
    sync_subparsers = sync_parser.add_subparsers(
        dest="sync_command", help="Sync commands"
    )

    # sync push
    sync_push_parser = sync_subparsers.add_parser(
        "push", help="Push a local kit to database"
    )
    sync_push_parser.add_argument("kit", type=str, help="Name of the local kit to push")
    sync_push_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for local reasoning kits",
    )
    sync_push_parser.add_argument(
        "--message",
        "-m",
        type=str,
        help="Commit message for this version",
    )

    # sync pull
    sync_pull_parser = sync_subparsers.add_parser(
        "pull", help="Pull a kit from database to local"
    )
    sync_pull_parser.add_argument(
        "kit", type=str, help="Slug of the kit to pull from database"
    )
    sync_pull_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for local reasoning kits",
    )

    # sync list
    sync_subparsers.add_parser("list", help="Compare local and database kits")

    # =========================================================================
    # KIT COMMAND GROUP
    # =========================================================================
    kit_parser = subparsers.add_parser(
        "kit", help="Create and manage reasoning kit definitions"
    )
    kit_subparsers = kit_parser.add_subparsers(dest="kit_command", help="Kit commands")

    # kit create
    kit_create_parser = kit_subparsers.add_parser(
        "create", help="Create a new reasoning kit"
    )
    kit_create_parser.add_argument("name", type=str, help="Name of the kit to create")
    kit_create_parser.add_argument(
        "--description",
        type=str,
        help="Description of the kit",
    )
    kit_create_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit delete
    kit_delete_parser = kit_subparsers.add_parser(
        "delete", help="Delete a reasoning kit"
    )
    kit_delete_parser.add_argument("name", type=str, help="Name of the kit to delete")
    kit_delete_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )
    kit_delete_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )

    # kit add-resource
    kit_add_resource_parser = kit_subparsers.add_parser(
        "add-resource", help="Add a resource to a reasoning kit"
    )
    kit_add_resource_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_add_resource_parser.add_argument(
        "--file",
        type=str,
        help="Path to resource file",
    )
    kit_add_resource_parser.add_argument(
        "--content",
        type=str,
        help="Inline content for resource",
    )
    kit_add_resource_parser.add_argument(
        "--filename",
        type=str,
        help="Filename for inline content (required with --content)",
    )
    kit_add_resource_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit add-step
    kit_add_step_parser = kit_subparsers.add_parser(
        "add-step", help="Add a workflow step to a reasoning kit"
    )
    kit_add_step_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_add_step_parser.add_argument(
        "--file",
        type=str,
        help="Path to instruction file",
    )
    kit_add_step_parser.add_argument(
        "--prompt",
        type=str,
        help="Inline prompt text for step",
    )
    kit_add_step_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit edit-resource
    kit_edit_resource_parser = kit_subparsers.add_parser(
        "edit-resource", help="Edit a resource in a reasoning kit"
    )
    kit_edit_resource_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_edit_resource_parser.add_argument(
        "number", type=int, help="Resource number to edit"
    )
    kit_edit_resource_parser.add_argument(
        "--file",
        type=str,
        help="Path to new resource file",
    )
    kit_edit_resource_parser.add_argument(
        "--content",
        type=str,
        help="New inline content for resource",
    )
    kit_edit_resource_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit edit-step
    kit_edit_step_parser = kit_subparsers.add_parser(
        "edit-step", help="Edit a workflow step in a reasoning kit"
    )
    kit_edit_step_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_edit_step_parser.add_argument("number", type=int, help="Step number to edit")
    kit_edit_step_parser.add_argument(
        "--file",
        type=str,
        help="Path to new instruction file",
    )
    kit_edit_step_parser.add_argument(
        "--prompt",
        type=str,
        help="New inline prompt text for step",
    )
    kit_edit_step_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit delete-resource
    kit_delete_resource_parser = kit_subparsers.add_parser(
        "delete-resource", help="Delete a resource from a reasoning kit"
    )
    kit_delete_resource_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_delete_resource_parser.add_argument(
        "number", type=int, help="Resource number to delete"
    )
    kit_delete_resource_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # kit delete-step
    kit_delete_step_parser = kit_subparsers.add_parser(
        "delete-step", help="Delete a workflow step from a reasoning kit"
    )
    kit_delete_step_parser.add_argument("kit", type=str, help="Name of the kit")
    kit_delete_step_parser.add_argument(
        "number", type=int, help="Step number to delete"
    )
    kit_delete_step_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits",
    )

    # =========================================================================
    # PARSE AND DISPATCH
    # =========================================================================
    args = parser.parse_args()

    if args.command == "list":
        _cmd_list(args)
    elif args.command == "run":
        _cmd_run(args)
    elif args.command == "info":
        _cmd_info(args)
    elif args.command == "db":
        _cmd_db(args)
    elif args.command == "sync":
        _cmd_sync(args)
    elif args.command == "kit":
        _cmd_kit(args)
    else:
        parser.print_help()


# =============================================================================
# LIST COMMAND
# =============================================================================


def _cmd_list(args: argparse.Namespace) -> None:
    """Handle the list command."""
    if args.local:
        # List from local filesystem
        kits = list_reasoning_kits(args.path)
        if kits:
            print("Available local reasoning kits:")
            for kit in sorted(kits):
                print(f"  - {kit}")
        else:
            print(f"No reasoning kits found in {args.path}")
    else:
        # List from database
        config = get_config()
        if not config.is_database_configured:
            print(
                "Database not configured. Use --local flag or configure DATABASE_URL."
            )
            print("Falling back to local listing...")
            kits = list_reasoning_kits(args.path)
            if kits:
                print("Available local reasoning kits:")
                for kit in sorted(kits):
                    print(f"  - {kit}")
            else:
                print(f"No reasoning kits found in {args.path}")
            return

        try:
            kits = asyncio.run(list_reasoning_kits_from_db())
            if kits:
                print("Available reasoning kits:")
                for kit in kits:
                    desc = f" - {kit['description']}" if kit["description"] else ""
                    print(f"  - {kit['slug']}: {kit['name']}{desc}")
            else:
                print("No public reasoning kits found in database")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            print("Use --local flag to list local kits instead.")
            sys.exit(1)


# =============================================================================
# RUN COMMAND
# =============================================================================


def _cmd_run(args: argparse.Namespace) -> None:
    """Handle the run command."""
    from uuid import UUID

    try:
        kit = None
        db_version_id: UUID | None = None
        save_to_db = False

        if args.local:
            # Load from local filesystem
            kit_path = resolve_kit_path(args.kit, args.base_path)
            kit = load_reasoning_kit(kit_path)
        else:
            # Try database first
            config = get_config()
            if config.is_database_configured:
                try:
                    loaded = asyncio.run(load_reasoning_kit_from_db(args.kit))
                    kit = loaded.kit
                    db_version_id = loaded.version_id
                    save_to_db = True  # Enable DB tracking for DB-loaded kits
                except FileNotFoundError:
                    # Fall back to local
                    print(f"Kit '{args.kit}' not found in database, trying local...")
                    kit_path = resolve_kit_path(args.kit, args.base_path)
                    kit = load_reasoning_kit(kit_path)
            else:
                # No database configured, use local
                kit_path = resolve_kit_path(args.kit, args.base_path)
                kit = load_reasoning_kit(kit_path)

        run_reasoning_kit(
            kit,
            evaluate=args.evaluate,
            evaluation_mode=args.mode,
            save_to_db=save_to_db,
            db_version_id=db_version_id,
        )
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running reasoning kit: {e}")
        sys.exit(1)


# =============================================================================
# INFO COMMAND
# =============================================================================


def _cmd_info(args: argparse.Namespace) -> None:
    """Handle the info command."""
    try:
        if args.local:
            # Load from local filesystem
            kit_path = resolve_kit_path(args.kit, args.base_path)
            kit = load_reasoning_kit(kit_path)
            print(f"\nReasoning Kit: {kit.name}")
            print(f"Path: {kit.path}")
            print(f"\nResources ({len(kit.resources)}):")
            for key, resource in kit.resources.items():
                print(f"  {key}. {resource.resource_id} ({resource.file})")
            print(f"\nWorkflow Steps ({len(kit.workflow)}):")
            for key, step in kit.workflow.items():
                print(f"  {key}. {step.output_id} ({step.file})")
        else:
            # Try database first
            config = get_config()
            if config.is_database_configured:
                info = asyncio.run(get_kit_info_from_db(args.kit))
                if info:
                    _print_db_kit_info(info)
                    return
                # Fall back to local
                print(f"Kit '{args.kit}' not found in database, trying local...")

            kit_path = resolve_kit_path(args.kit, args.base_path)
            kit = load_reasoning_kit(kit_path)
            print(f"\nReasoning Kit: {kit.name}")
            print(f"Path: {kit.path}")
            print(f"\nResources ({len(kit.resources)}):")
            for key, resource in kit.resources.items():
                print(f"  {key}. {resource.resource_id} ({resource.file})")
            print(f"\nWorkflow Steps ({len(kit.workflow)}):")
            for key, step in kit.workflow.items():
                print(f"  {key}. {step.output_id} ({step.file})")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _print_db_kit_info(info: dict) -> None:
    """Print formatted database kit info."""
    print(f"\nReasoning Kit: {info['name']}")
    print(f"Slug: {info['slug']}")
    if info["description"]:
        print(f"Description: {info['description']}")
    print(f"Public: {'Yes' if info['is_public'] else 'No'}")
    print(f"Created: {info['created_at']}")
    print(f"Updated: {info['updated_at']}")

    version = info.get("current_version")
    if version:
        print(f"\nCurrent Version: v{version['version_number']}")
        if version["commit_message"]:
            print(f"Commit: {version['commit_message']}")

        print(f"\nResources ({len(version['resources'])}):")
        for r in version["resources"]:
            size = f" ({r['file_size_bytes']} bytes)" if r["file_size_bytes"] else ""
            print(f"  {r['number']}. {r['filename']}{size}")

        print(f"\nWorkflow Steps ({len(version['workflow_steps'])}):")
        for s in version["workflow_steps"]:
            print(f"  {s['number']}. {s['output_id']}")
    else:
        print("\nNo published version available")


# =============================================================================
# DB COMMAND
# =============================================================================


def _cmd_db(args: argparse.Namespace) -> None:
    """Handle database management commands."""
    if args.db_command == "migrate":
        _db_migrate(args.revision)
    elif args.db_command == "status":
        _db_status()
    elif args.db_command == "setup":
        _db_setup()
    else:
        print("Usage: clerk db [migrate|status|setup]")
        sys.exit(1)


def _db_migrate(revision: str = "head") -> None:
    """Run database migrations."""
    import os

    from alembic import command
    from alembic.config import Config

    # Find alembic.ini
    migrations_dir = Path(__file__).parent / "db" / "migrations"
    alembic_ini = migrations_dir / "alembic.ini"

    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    # Get database URL
    config = get_config()
    db_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL or DATABASE_URL_DIRECT must be set")
        sys.exit(1)

    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    print(f"Running migrations to {revision}...")
    try:
        command.upgrade(alembic_cfg, revision)
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)


def _db_status() -> None:
    """Show migration status."""
    import os

    from alembic import command
    from alembic.config import Config

    migrations_dir = Path(__file__).parent / "db" / "migrations"
    alembic_ini = migrations_dir / "alembic.ini"

    if not alembic_ini.exists():
        print(f"Error: alembic.ini not found at {alembic_ini}")
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL or DATABASE_URL_DIRECT must be set")
        sys.exit(1)

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    print("Migration status:")
    try:
        command.current(alembic_cfg, verbose=True)
    except Exception as e:
        print(f"Error checking status: {e}")
        sys.exit(1)


def _db_setup() -> None:
    """Full database setup: migrations + storage bucket."""
    print("Setting up CLERK database...")
    print()

    # Run migrations
    print("1. Running database migrations...")
    _db_migrate("head")
    print()

    # Create storage bucket
    print("2. Creating storage bucket...")
    try:
        from .db.storage import ensure_bucket_exists

        ensure_bucket_exists(use_service_key=True)
    except Exception as e:
        print(f"Warning: Could not create storage bucket: {e}")
        print(
            "You may need to create the 'reasoning-kits' bucket manually in Supabase."
        )
    print()

    print("Database setup complete!")


# =============================================================================
# SYNC COMMAND
# =============================================================================


def _cmd_sync(args: argparse.Namespace) -> None:
    """Handle sync commands."""
    if args.sync_command == "push":
        asyncio.run(_sync_push(args.kit, args.base_path, args.message))
    elif args.sync_command == "pull":
        asyncio.run(_sync_pull(args.kit, args.base_path))
    elif args.sync_command == "list":
        asyncio.run(_sync_list(args))
    else:
        print("Usage: clerk sync [push|pull|list]")
        sys.exit(1)


async def _sync_push(kit_name: str, base_path: str, message: str | None) -> None:
    """Push a local kit to database."""
    from .db import (
        KitVersionRepository,
        ReasoningKitRepository,
        StorageService,
        detect_mime_type,
        extract_text,
        get_async_session,
    )
    from .db.text_extraction import get_file_size

    # Load local kit
    kit_path = resolve_kit_path(kit_name, base_path)
    local_kit = load_reasoning_kit(kit_path)
    kit_path = Path(kit_path)

    print(f"Pushing '{local_kit.name}' to database...")

    async with get_async_session() as session:
        kit_repo = ReasoningKitRepository(session)
        version_repo = KitVersionRepository(session)

        # Check if kit exists
        slug = kit_name.lower().replace(" ", "-").replace("_", "-")
        db_kit = await kit_repo.get_by_slug(slug)

        if db_kit is None:
            # Create new kit
            print(f"Creating new kit with slug: {slug}")
            db_kit = await kit_repo.create(
                slug=slug,
                name=local_kit.name,
                description=None,
                is_public=True,
            )
        else:
            print(f"Updating existing kit: {slug}")

        # Create new version
        version = await version_repo.create(
            kit_id=db_kit.id,
            commit_message=message,
        )
        print(f"Created version {version.version_number}")

        # Upload resources
        storage = StorageService(use_service_key=True)
        print("Uploading resources...")

        for num, resource in local_kit.resources.items():
            resource_file = kit_path / resource.file
            if resource_file.exists():
                # Detect mime type and extract text
                mime_type = detect_mime_type(resource_file)
                extracted_text = extract_text(resource_file, mime_type)
                file_size = get_file_size(resource_file)

                # Upload to storage
                storage_path = storage.upload_resource(
                    kit_id=db_kit.id,
                    version_id=version.id,
                    filename=resource.file,
                    file_path=resource_file,
                )

                # Add to database
                await version_repo.add_resource(
                    version_id=version.id,
                    resource_number=int(num),
                    filename=resource.file,
                    storage_path=storage_path,
                    mime_type=mime_type,
                    extracted_text=extracted_text,
                    file_size_bytes=file_size,
                )
                print(f"  - Uploaded {resource.file}")

        # Add workflow steps
        print("Adding workflow steps...")
        for num, step in local_kit.workflow.items():
            await version_repo.add_workflow_step(
                version_id=version.id,
                step_number=int(num),
                prompt_template=step.prompt,
            )
            print(f"  - Added step {num}")

    print(
        f"\nSuccessfully pushed '{local_kit.name}' as version {version.version_number}"
    )


async def _sync_pull(slug: str, base_path: str) -> None:
    """Pull a kit from database to local filesystem."""
    from .db import StorageService, get_async_session, ReasoningKitRepository

    print(f"Pulling '{slug}' from database...")

    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        db_kit = await repo.get_by_slug(slug)

        if db_kit is None:
            print(f"Error: Kit '{slug}' not found in database")
            sys.exit(1)

        if db_kit.current_version is None:
            print(f"Error: Kit '{slug}' has no published version")
            sys.exit(1)

        version = db_kit.current_version

        # Create local directory
        kit_dir = Path(base_path) / slug
        kit_dir.mkdir(parents=True, exist_ok=True)

        # Download resources
        storage = StorageService()
        print("Downloading resources...")

        for resource in version.resources:
            content = storage.download_resource(resource.storage_path)
            resource_file = kit_dir / resource.filename
            resource_file.write_bytes(content)
            print(f"  - Downloaded {resource.filename}")

        # Write instruction files
        print("Writing instruction files...")
        for step in version.workflow_steps:
            instruction_file = kit_dir / f"instruction_{step.step_number}.txt"
            instruction_file.write_text(step.prompt_template)
            print(f"  - Created instruction_{step.step_number}.txt")

    print(f"\nSuccessfully pulled '{slug}' to {kit_dir}")


async def _sync_list(args: argparse.Namespace) -> None:
    """Compare local and database kits."""
    # Get local kits
    local_kits = set(list_reasoning_kits("reasoning_kits"))

    # Get database kits
    config = get_config()
    db_kits: set[str] = set()

    if config.is_database_configured:
        try:
            kits = await list_reasoning_kits_from_db()
            db_kits = {k["slug"] for k in kits}
        except Exception as e:
            print(f"Warning: Could not connect to database: {e}")

    # Compare
    only_local = local_kits - db_kits
    only_db = db_kits - local_kits
    both = local_kits & db_kits

    print("Reasoning Kit Sync Status")
    print("=" * 40)

    if both:
        print("\nIn both local and database:")
        for kit in sorted(both):
            print(f"  [=] {kit}")

    if only_local:
        print("\nOnly in local (push to sync):")
        for kit in sorted(only_local):
            print(f"  [L] {kit}")

    if only_db:
        print("\nOnly in database (pull to sync):")
        for kit in sorted(only_db):
            print(f"  [D] {kit}")

    if not (both or only_local or only_db):
        print("\nNo reasoning kits found.")


# =============================================================================
# HELPERS
# =============================================================================


def resolve_kit_path(kit: str, base_path: str) -> Path:
    """Resolve a kit name or path to an absolute path."""
    # Check if it's already a valid path with instruction files
    kit_path = Path(kit)
    if kit_path.exists() and list(kit_path.glob("instruction_*.txt")):
        return kit_path

    # Try as a name under base_path
    kit_path = Path(base_path) / kit
    if kit_path.exists():
        return kit_path

    # Return as-is and let the loader handle the error
    return Path(kit)


# =============================================================================
# KIT COMMAND GROUP - HELPER FUNCTIONS
# =============================================================================


def validate_kit_name(name: str) -> bool:
    """Validate that kit name is filesystem-safe.

    Args:
        name: Kit name to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    # Allow alphanumeric, hyphens, underscores
    pattern = r"^[a-z0-9_-]+$"
    return bool(re.match(pattern, name.lower()))


def get_next_resource_number(kit_path: Path) -> int:
    """Get the next available resource number in a kit.

    Args:
        kit_path: Path to the reasoning kit directory

    Returns:
        Next available resource number (1-indexed)
    """
    resource_files = list(kit_path.glob("resource_*.*"))
    if not resource_files:
        return 1

    # Extract numbers from existing resources
    numbers = []
    for f in resource_files:
        match = re.search(r"resource_(\d+)\.", f.name)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers) + 1 if numbers else 1


def get_next_step_number(kit_path: Path) -> int:
    """Get the next available step number in a kit.

    Args:
        kit_path: Path to the reasoning kit directory

    Returns:
        Next available step number (1-indexed)
    """
    instruction_files = list(kit_path.glob("instruction_*.txt"))
    if not instruction_files:
        return 1

    # Extract numbers from existing instructions
    numbers = []
    for f in instruction_files:
        match = re.search(r"instruction_(\d+)\.txt", f.name)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers) + 1 if numbers else 1


def find_resource_file(kit_path: Path, number: int) -> Path | None:
    """Find a resource file by number.

    Args:
        kit_path: Path to the reasoning kit directory
        number: Resource number to find

    Returns:
        Path to resource file if found, None otherwise
    """
    pattern = f"resource_{number}.*"
    matches = list(kit_path.glob(pattern))
    return matches[0] if matches else None


def find_step_file(kit_path: Path, number: int) -> Path | None:
    """Find a step file by number.

    Args:
        kit_path: Path to the reasoning kit directory
        number: Step number to find

    Returns:
        Path to step file if found, None otherwise
    """
    step_file = kit_path / f"instruction_{number}.txt"
    return step_file if step_file.exists() else None


# =============================================================================
# KIT COMMAND GROUP - COMMAND HANDLERS
# =============================================================================


def _cmd_kit(args: argparse.Namespace) -> None:
    """Handle kit management commands."""
    if args.kit_command == "create":
        _kit_create(args)
    elif args.kit_command == "delete":
        _kit_delete(args)
    elif args.kit_command == "add-resource":
        _kit_add_resource(args)
    elif args.kit_command == "add-step":
        _kit_add_step(args)
    elif args.kit_command == "edit-resource":
        _kit_edit_resource(args)
    elif args.kit_command == "edit-step":
        _kit_edit_step(args)
    elif args.kit_command == "delete-resource":
        _kit_delete_resource(args)
    elif args.kit_command == "delete-step":
        _kit_delete_step(args)
    else:
        print(
            "Usage: clerk kit [create|delete|add-resource|add-step|edit-resource|edit-step|delete-resource|delete-step]"
        )
        sys.exit(1)


def _kit_create(args: argparse.Namespace) -> None:
    """Create a new reasoning kit."""
    kit_name = args.name.lower().replace(" ", "-")

    # Validate kit name
    if not validate_kit_name(kit_name):
        print(f"Error: Invalid kit name '{kit_name}'")
        print(
            "Kit names must contain only lowercase letters, numbers, hyphens, and underscores"
        )
        sys.exit(1)

    # Create kit directory
    kit_path = Path(args.base_path) / kit_name
    if kit_path.exists():
        print(f"Error: Kit '{kit_name}' already exists at {kit_path}")
        sys.exit(1)

    try:
        kit_path.mkdir(parents=True, exist_ok=False)
        print(f"Created reasoning kit: {kit_name}")
        print(f"Location: {kit_path}")

        if args.description:
            print(f"Description: {args.description}")
            # Note: Description is not stored for file-based kits,
            # but will be used when syncing to database

        print("\nNext steps:")
        print(f"  - Add resources: clerk kit add-resource {kit_name} --file <path>")
        print(f"  - Add workflow steps: clerk kit add-step {kit_name} --prompt <text>")
        print(f"  - View kit info: clerk info {kit_name}")

    except Exception as e:
        print(f"Error creating kit: {e}")
        sys.exit(1)


def _kit_delete(args: argparse.Namespace) -> None:
    """Delete a reasoning kit."""
    import shutil

    kit_path = Path(args.base_path) / args.name

    if not kit_path.exists():
        print(f"Error: Kit '{args.name}' not found at {kit_path}")
        sys.exit(1)

    # Confirm deletion unless --force flag is used
    if not args.force:
        response = input(f"Are you sure you want to delete '{args.name}'? [y/N]: ")
        if response.lower() not in ["y", "yes"]:
            print("Deletion cancelled")
            return

    try:
        shutil.rmtree(kit_path)
        print(f"Deleted reasoning kit: {args.name}")
    except Exception as e:
        print(f"Error deleting kit: {e}")
        sys.exit(1)


def _kit_add_resource(args: argparse.Namespace) -> None:
    """Add a resource to a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        print(f"Create it first: clerk kit create {args.kit}")
        sys.exit(1)

    # Validate that either --file or --content is provided
    if not args.file and not args.content:
        print("Error: Either --file or --content must be provided")
        sys.exit(1)

    if args.content and not args.filename:
        print("Error: --filename is required when using --content")
        sys.exit(1)

    if args.file and args.content:
        print("Error: Cannot use both --file and --content")
        sys.exit(1)

    # Get next resource number
    resource_num = get_next_resource_number(kit_path)

    try:
        if args.file:
            # Copy from file
            source_path = Path(args.file)
            if not source_path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)

            extension = source_path.suffix or ".txt"
            dest_path = kit_path / f"resource_{resource_num}{extension}"

            import shutil

            shutil.copy2(source_path, dest_path)
            print(f"Added resource_{resource_num} from {args.file}")

        else:
            # Create from inline content
            extension = Path(args.filename).suffix or ".txt"
            dest_path = kit_path / f"resource_{resource_num}{extension}"
            dest_path.write_text(args.content)
            print(f"Added resource_{resource_num} with inline content")

        print(f"Resource file: {dest_path.name}")
        print(f"Reference in steps as: {{resource_{resource_num}}}")

    except Exception as e:
        print(f"Error adding resource: {e}")
        sys.exit(1)


def _kit_add_step(args: argparse.Namespace) -> None:
    """Add a workflow step to a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        print(f"Create it first: clerk kit create {args.kit}")
        sys.exit(1)

    # Validate that either --file or --prompt is provided
    if not args.file and not args.prompt:
        print("Error: Either --file or --prompt must be provided")
        sys.exit(1)

    if args.file and args.prompt:
        print("Error: Cannot use both --file and --prompt")
        sys.exit(1)

    # Get next step number
    step_num = get_next_step_number(kit_path)

    try:
        dest_path = kit_path / f"instruction_{step_num}.txt"

        if args.file:
            # Copy from file
            source_path = Path(args.file)
            if not source_path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)

            import shutil

            shutil.copy2(source_path, dest_path)
            print(f"Added instruction_{step_num} from {args.file}")

        else:
            # Create from inline prompt
            dest_path.write_text(args.prompt)
            print(f"Added instruction_{step_num} with inline prompt")

        print(f"Step file: {dest_path.name}")
        print(f"Output available as: {{workflow_{step_num}}}")

    except Exception as e:
        print(f"Error adding step: {e}")
        sys.exit(1)


def _kit_edit_resource(args: argparse.Namespace) -> None:
    """Edit a resource in a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        sys.exit(1)

    # Validate that either --file or --content is provided
    if not args.file and not args.content:
        print("Error: Either --file or --content must be provided")
        sys.exit(1)

    if args.file and args.content:
        print("Error: Cannot use both --file and --content")
        sys.exit(1)

    # Find existing resource file
    existing_file = find_resource_file(kit_path, args.number)
    if not existing_file:
        print(f"Error: Resource {args.number} not found in kit '{args.kit}'")
        sys.exit(1)

    try:
        if args.file:
            # Replace with content from file
            source_path = Path(args.file)
            if not source_path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)

            # Keep same filename/extension
            import shutil

            shutil.copy2(source_path, existing_file)
            print(f"Updated resource_{args.number} from {args.file}")

        else:
            # Replace with inline content
            existing_file.write_text(args.content)
            print(f"Updated resource_{args.number} with inline content")

        print(f"Resource file: {existing_file.name}")

    except Exception as e:
        print(f"Error editing resource: {e}")
        sys.exit(1)


def _kit_edit_step(args: argparse.Namespace) -> None:
    """Edit a workflow step in a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        sys.exit(1)

    # Validate that either --file or --prompt is provided
    if not args.file and not args.prompt:
        print("Error: Either --file or --prompt must be provided")
        sys.exit(1)

    if args.file and args.prompt:
        print("Error: Cannot use both --file and --prompt")
        sys.exit(1)

    # Find existing step file
    existing_file = find_step_file(kit_path, args.number)
    if not existing_file:
        print(f"Error: Step {args.number} not found in kit '{args.kit}'")
        sys.exit(1)

    try:
        if args.file:
            # Replace with content from file
            source_path = Path(args.file)
            if not source_path.exists():
                print(f"Error: File not found: {args.file}")
                sys.exit(1)

            import shutil

            shutil.copy2(source_path, existing_file)
            print(f"Updated instruction_{args.number} from {args.file}")

        else:
            # Replace with inline prompt
            existing_file.write_text(args.prompt)
            print(f"Updated instruction_{args.number} with inline prompt")

        print(f"Step file: {existing_file.name}")

    except Exception as e:
        print(f"Error editing step: {e}")
        sys.exit(1)


def _kit_delete_resource(args: argparse.Namespace) -> None:
    """Delete a resource from a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        sys.exit(1)

    # Find existing resource file
    existing_file = find_resource_file(kit_path, args.number)
    if not existing_file:
        print(f"Error: Resource {args.number} not found in kit '{args.kit}'")
        sys.exit(1)

    try:
        existing_file.unlink()
        print(f"Deleted resource_{args.number} from '{args.kit}'")
        print(
            f"Note: Remaining resources are NOT renumbered to preserve workflow references"
        )

    except Exception as e:
        print(f"Error deleting resource: {e}")
        sys.exit(1)


def _kit_delete_step(args: argparse.Namespace) -> None:
    """Delete a workflow step from a reasoning kit."""
    kit_path = Path(args.base_path) / args.kit

    if not kit_path.exists():
        print(f"Error: Kit '{args.kit}' not found at {kit_path}")
        sys.exit(1)

    # Find existing step file
    existing_file = find_step_file(kit_path, args.number)
    if not existing_file:
        print(f"Error: Step {args.number} not found in kit '{args.kit}'")
        sys.exit(1)

    try:
        existing_file.unlink()
        print(f"Deleted instruction_{args.number} from '{args.kit}'")
        print(f"Note: Remaining steps are NOT renumbered to preserve workflow order")

    except Exception as e:
        print(f"Error deleting step: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
