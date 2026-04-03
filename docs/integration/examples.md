# Integration Examples

Working examples of Clerk integration patterns.

---

## FastAPI Example

The complete FastAPI integration example is available in the repository:

```
examples/fastapi-integration/
├── main.py           # FastAPI app with Clerk mounted
├── requirements.txt  # Dependencies
└── README.md         # Setup instructions
```

This example demonstrates:

- Mounting Clerk at a subpath (`/clerk`)
- Custom authentication integration
- Calling Clerk's API from your routes
- Running reasoning kits programmatically

### Quick Start

```bash
cd examples/fastapi-integration
pip install -r requirements.txt
python main.py
```

Visit:

- Your app: `http://localhost:8000/`
- Clerk UI: `http://localhost:8000/clerk`
- API docs: `http://localhost:8000/clerk/api/openapi.json`

---

## Other Framework Examples

### Django Integration (Coming Soon)

A complete Django example showing:

- Async view integration
- Database model synchronization
- Custom middleware for auth

Planned for a future release. Track progress on GitHub.

### Flask Integration (Coming Soon)

A Flask example demonstrating:

- Application factory pattern
- Blueprint integration
- Background task execution

Planned for a future release. Track progress on GitHub.

---

## Minimal Code Examples

### Execute a Kit Programmatically

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import run_reasoning_kit

# Load and run
kit = load_reasoning_kit("./my-kit")
result = run_reasoning_kit(kit)
print(result)
```

### List Kits from Database

```python
import asyncio
from openclerk.db import get_async_session, ReasoningKitRepository

async def list_kits():
    async with get_async_session() as session:
        repo = ReasoningKitRepository(session)
        kits = await repo.list_public()
        return [k.slug for k in kits]

kits = asyncio.run(list_kits())
print(kits)
```

### Stream Kit Execution

```python
from openclerk.loader import load_reasoning_kit
from openclerk.graph import stream_reasoning_kit

async def stream_kit():
    kit = load_reasoning_kit("./my-kit")
    async for event in stream_reasoning_kit(kit):
        print(event)

import asyncio
asyncio.run(stream_kit())
```

---

## Next Steps

- **[Integration Guide](./README.md)** — Detailed embedding guide
- **[API Reference](./api-reference.md)** — Complete API documentation
- Clone the repository and explore `examples/fastapi-integration/`

---

## Contributing Examples

Have an integration example to share? We'd love to add it!

1. Create a new directory under `examples/`
2. Include a `README.md` with setup instructions
3. Submit a pull request

See [Contributing Guide](../contributing/README.md) for details.
