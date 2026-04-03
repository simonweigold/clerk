# API Reference

Complete reference for Clerk's REST API.

---

## OpenAPI Specification

Clerk provides a complete OpenAPI 3.0 specification that describes all available endpoints, request/response schemas, and authentication requirements.

### Accessing the Spec

The OpenAPI specification is available at:

```
GET /api/openapi.json
```

Fetch it with curl:

```bash
curl http://localhost:8000/api/openapi.json | jq .
```

Or download it:

```bash
curl http://localhost:8000/api/openapi.json -o openapi.json
```

### Using the Spec

The OpenAPI spec enables:

- **Postman:** Import the spec to create a complete collection
- **Swagger UI:** Load the spec in Swagger Editor for interactive docs
- **Client Generation:** Generate typed API clients for any language
- **Testing:** Validate requests/responses against the schema

### Postman Import

1. Open Postman
2. Click **Import** → **Link**
3. Enter: `http://localhost:8000/api/openapi.json`
4. Click **Import**

### Swagger UI

Visit Swagger's online editor and paste the spec URL:

```
https://editor.swagger.io/?url=http://localhost:8000/api/openapi.json
```

---

## Key Endpoints

### Kits

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/kits` | List all public kits |
| `POST` | `/api/kits` | Create a new kit |
| `GET` | `/api/kits/{slug}` | Get kit details |
| `PUT` | `/api/kits/{slug}` | Update kit metadata |
| `DELETE` | `/api/kits/{slug}` | Delete a kit |

### Kit Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/kits/{slug}/execute` | Execute a kit (streaming) |
| `GET` | `/api/executions/{id}` | Get execution status |
| `GET` | `/api/executions/{id}/output` | Get execution output |

### Resources & Steps

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/kits/{slug}/resources` | Add a resource |
| `PUT` | `/api/kits/{slug}/resources/{id}` | Update a resource |
| `DELETE` | `/api/kits/{slug}/resources/{id}` | Delete a resource |
| `POST` | `/api/kits/{slug}/steps` | Add a workflow step |
| `PUT` | `/api/kits/{slug}/steps/{id}` | Update a step |
| `DELETE` | `/api/kits/{slug}/steps/{id}` | Delete a step |

### Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/docs` | List available documentation |
| `GET` | `/api/docs/{slug}` | Get documentation content |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/auth/me` | Get current user |
| `GET` | `/api/auth/login` | Initiate OAuth login |
| `GET` | `/api/auth/callback` | OAuth callback |
| `POST` | `/api/auth/logout` | Logout |

---

## Response Format

All API responses follow a consistent format:

### Success

```json
{
  "ok": true,
  "data": { ... }
}
```

### Error

```json
{
  "ok": false,
  "error": "Error message"
}
```

### Streaming

Execution endpoints return Server-Sent Events (SSE):

```
event: step_start
data: {"step": 1, "total": 3}

event: token
data: {"token": "Hello"}

event: step_complete
data: {"step": 1, "output": "..."}

event: complete
data: {"final_output": "..."}
```

---

## Authentication

Most endpoints require authentication via session cookie:

1. Login via `/api/auth/login` (initiates OAuth flow)
2. Session cookie is set after successful callback
3. Include cookie with subsequent requests

Public endpoints (no auth required):

- `GET /api/kits` — List public kits
- `GET /api/kits/{slug}` — Get public kit details
- `GET /api/docs/*` — Documentation
- `GET /api/openapi.json` — OpenAPI spec
- `GET /health` — Health check

---

## Rate Limits

Currently, no rate limits are enforced. Limits may be added in future versions for shared instances.

---

## Learn More

- **[Integration Guide](./README.md)** — Embedding Clerk in your app
- **[Integration Examples](./examples.md)** — Working code samples
- OpenAPI spec: `/api/openapi.json`
