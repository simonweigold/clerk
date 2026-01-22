"""Command-line interface for CLERK."""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .loader import load_reasoning_kit, list_reasoning_kits
from .graph import run_reasoning_kit


def main():
    """Main entry point for the CLI."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="CLERK - Community Library of Executable Reasoning Kits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available reasoning kits")
    list_parser.add_argument(
        "--path",
        type=str,
        default="reasoning_kits",
        help="Base path to search for reasoning kits",
    )

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a reasoning kit")
    run_parser.add_argument(
        "kit",
        type=str,
        help="Name or path of the reasoning kit to run",
    )
    run_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits (if using kit name)",
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

    # Info command
    info_parser = subparsers.add_parser("info", help="Show info about a reasoning kit")
    info_parser.add_argument(
        "kit",
        type=str,
        help="Name or path of the reasoning kit",
    )
    info_parser.add_argument(
        "--base-path",
        type=str,
        default="reasoning_kits",
        help="Base path for reasoning kits (if using kit name)",
    )

    args = parser.parse_args()

    if args.command == "list":
        kits = list_reasoning_kits(args.path)
        if kits:
            print("Available reasoning kits:")
            for kit in kits:
                print(f"  - {kit}")
        else:
            print(f"No reasoning kits found in {args.path}")

    elif args.command == "run":
        kit_path = resolve_kit_path(args.kit, args.base_path)
        try:
            kit = load_reasoning_kit(kit_path)
            outputs = run_reasoning_kit(
                kit,
                evaluate=args.evaluate,
                evaluation_mode=args.mode,
            )
            sys.exit(0)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error running reasoning kit: {e}")
            sys.exit(1)

    elif args.command == "info":
        kit_path = resolve_kit_path(args.kit, args.base_path)
        try:
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

    else:
        parser.print_help()


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


if __name__ == "__main__":
    main()
