# Model Context Protocol (MCP)

CLERK provides MCP integration to connect with external LLMs, allowing them to manage and execute Reasoning Kits.

## Overview

The Model Context Protocol (MCP) enables LLMs to:
- Create new Reasoning Kits
- Edit existing Reasoning Kits
- Execute Reasoning Kits

## Commands and Usage

Currently, MCP logic is under development and is primarily intended to allow automated reasoning agents to interface directly with CLERK kits and infrastructure.

See the [CLI sync documentation](cli/sync.md) for how MCP operations might interact with database synchronization in the future.

## Prerequisites

To interact effectively with the MCP integration, the LLM must be instructed via specific prompts to understand the [Reasoning Kit Structure](reasoning_kits.md).
