"""Main entry point for CLERK - can be used for direct execution."""

from dotenv import load_dotenv

from src.clerk.loader import load_reasoning_kit
from src.clerk.graph import run_reasoning_kit


def main():
    """Run the demo reasoning kit."""
    load_dotenv()
    
    kit = load_reasoning_kit("reasoning_kits/demo")
    outputs = run_reasoning_kit(kit)
    return outputs


if __name__ == "__main__":
    main()


