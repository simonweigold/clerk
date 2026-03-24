# FAQ

Frequently asked questions about Clerk.

---

## Installation Issues

### Q: Installation fails with "No module named 'clerk'"

**A:** Make sure you're installing the correct package:

```bash
# Correct
pip install clerk-framework

# Incorrect (different package)
pip install clerk
```

Also verify your Python version (3.13+ required):

```bash
python --version
```

### Q: UV installation fails

**A:** Ensure UV is installed first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then try:

```bash
uv tool install clerk-framework
```

---

## Kit Format Questions

### Q: What file types are supported for resources?

**A:** Clerk supports:

- **Text files:** `.txt`, `.md`, `.py`, `.js`, etc.
- **Data files:** `.csv`, `.json`, `.yaml`, `.yml`
- **Documents:** `.pdf` (text extracted automatically)

All files are converted to text for processing by the LLM.

### Q: Can I have more than 9 resources or steps?

**A:** Yes! Clerk supports any number of resources and workflow steps. They're numbered sequentially: `resource_1`, `resource_2`, ..., `resource_99`, etc.

### Q: How do I reference resources in instructions?

**A:** Use the placeholder syntax with curly braces:

```
{resource_1}    # First resource
{resource_2}    # Second resource
{workflow_1}    # Output from step 1
{workflow_2}    # Output from step 2
```

---

## LLM Requirements

### Q: What LLM provider does Clerk use?

**A:** Clerk uses LangChain and supports multiple providers:

- OpenAI (default)
- Anthropic Claude
- Local models via Ollama
- Other LangChain-compatible providers

### Q: How do I configure my API key?

**A:** Set your API key as an environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file in your project root:

```
OPENAI_API_KEY=sk-...
```

### Q: Can I use a local LLM?

**A:** Yes! Configure Clerk to use Ollama or other local providers by setting the appropriate environment variables. See the [Integration Guide](../integration/README.md) for details.

---

## Running Workflows

### Q: How do I pass dynamic data at runtime?

**A:** Mark resources as dynamic when creating them. Clerk will prompt for file paths when running:

```bash
clerk run my-kit
# Clerk prompts: "Enter file path for resource_3 (data.txt):"
```

### Q: Can I run kits from the database?

**A:** Yes! If you've configured a database:

```bash
# List database kits
clerk list

# Run a database kit
clerk run kit-name

# Run a local kit instead
clerk run my-kit --local
```

### Q: How do I debug a failing workflow?

**A:** Use the evaluation mode to see step-by-step output:

```bash
clerk run my-kit --evaluate
```

This lets you review each step's output before continuing.

---

## Database & Sync

### Q: Do I need a database to use Clerk?

**A:** No! Clerk works perfectly with local file-based kits. The database is optional and enables:

- Sharing kits across teams
- Version control for kits
- Web UI access

### Q: How do I sync kits between local and database?

**A:** Use the sync commands:

```bash
# Push local kit to database
clerk sync push my-kit -m "Initial version"

# Pull kit from database to local
clerk sync pull my-kit

# Compare local and database
clerk sync list
```

---

## Getting More Help

Can't find your question? Check:

- **[Core Concepts](concepts.md)** — Detailed concept explanations
- **[GitHub Issues](https://github.com/your-org/clerk/issues)** — Community support
- **[Integration Guide](../integration/README.md)** — Embedding and API docs
