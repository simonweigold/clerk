# Core Concepts

Understanding these key concepts will help you build effective reasoning workflows with Clerk.

---

## Reasoning Kits

A **Reasoning Kit** is a reusable, multi-step LLM workflow. Think of it as a recipe that defines:

- What data (resources) the workflow needs
- What steps (instructions) to perform
- How outputs from one step flow into the next

Kits are stored as directories containing resource files and instruction files. This file-based approach makes them easy to version control and share.

### Example Kit Structure

```
my-kit/
├── resource_1.txt      # Input data
├── resource_2.csv      # Additional data
├── instruction_1.txt   # Step 1: Analyze
└── instruction_2.txt   # Step 2: Summarize
```

---

## Resources

**Resources** are the data inputs for your workflow. They can be:

- Text files (`.txt`, `.md`)
- Data files (`.csv`, `.json`)
- Documents (`.pdf` — text extracted automatically)
- Dynamic inputs (prompted at runtime)

Resources are referenced in instructions using placeholders like `{resource_1}`, `{resource_2}`, etc.

### Creating Resources

```bash
# Add from a file
clerk kit add-resource my-kit --file ./data/report.txt

# Add inline content
clerk kit add-resource my-kit --content "Sample data here" --filename sample.txt
```

---

## Instructions

**Instructions** define what the LLM should do at each step. They're plain text files containing prompts that can reference:

- Resources: `{resource_1}`, `{resource_2}`
- Previous step outputs: `{workflow_1}`, `{workflow_2}`

### Example Instruction

```
Analyze the following data and identify three key trends:

{resource_1}

Provide your analysis as bullet points.
```

### Creating Instructions

```bash
# Add from a file
clerk kit add-step my-kit --file ./prompts/analyze.txt

# Add inline prompt
clerk kit add-step my-kit --prompt "Summarize the key findings from: {workflow_1}"
```

---

## Workflows

A **Workflow** is the execution flow of instructions. Steps run sequentially, with each step's output available to subsequent steps.

### Workflow Example

| Step | Instruction | Input | Output |
|------|-------------|-------|--------|
| 1 | Read and analyze data | `{resource_1}` | `{workflow_1}` |
| 2 | Summarize findings | `{workflow_1}` | `{workflow_2}` |
| 3 | Generate recommendations | `{workflow_2}` | Final output |

### Execution Flow

1. Clerk loads all resources
2. Step 1 executes with its instruction (resources replaced with content)
3. Step 1's output is stored as `{workflow_1}`
4. Step 2 executes, with `{workflow_1}` replaced by actual output
5. Process continues through all steps
6. Final output is displayed

---

## Evaluations

**Evaluations** allow you to review and refine workflow execution:

- Step-by-step review of LLM outputs
- Iterative refinement of results
- Anonymous mode for privacy (stores only character counts)

Enable evaluation mode when running:

```bash
clerk run my-kit --evaluate
```

---

## Learn More

- **[Reasoning Kits](../reasoning_kits.md)** — Detailed kit structure and advanced features
- **[User Guide README](./README.md)** — Quick start and installation
- **[FAQ](./faq.md)** — Frequently asked questions
