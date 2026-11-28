# Intelligent Calculator API (separate repository)

FastAPI backend with allowlisted mathematical parsing, scientific operations, offline natural-language calculation, session-scoped history, health/version endpoints and FastMCP tools.

## Local quickstart

- Python 3.11+
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e '.[dev]'`
- `uvicorn app.main:app --reload --port 8000`
- API docs: http://localhost:8000/docs
- Tests: `pytest -q`
- MCP stdio server: `python -m app.mcp_server` (connect an MCP client using stdio)

## Important constraints

This project includes a deterministic, offline natural-language interpreter, not a production external LLM integration. FastMCP exposes calculation tools to MCP clients, and the AI REST endpoint invokes the FastMCP tool through an in-memory MCP Client. The app does not claim a general-purpose autonomous agent. You may add an actual LLM provider using tool-calling after configuring a model provider, credentials, token budgets, and prompt-injection protections.

History uses session header `X-Session-ID`; this is for teaching only, **not authentication**. Never deploy a public multiuser service without proper authentication and authorization. SQLite is intended for local use; use PostgreSQL for multiple staging replicas.

Jenkins requires an agent with python3, Docker CLI/daemon access, Trivy, kubectl; Jenkins credentials IDs `ghcr-push`, `calculator-kubeconfig`; env `STAGING_API_URL` and configured registry/org. Set the repository to a multibranch pipeline. Kubernetes namespace and database Secret must already exist.

## API

- POST `/api/v1/calculate` {"expression":"2+3*4"}
- POST `/api/v1/scientific` {"operation":"sqrt","value":144}
- POST `/api/v1/ai/calculate` {"prompt":"15% of 200"}
- GET/DELETE `/api/v1/history`
- DELETE `/api/v1/history/{id}`
- GET `/health/live`, `/health/ready`, `/api/v1/version`

Refer to `docs/CLASSROOM.md` for labs and `scripts/rollback.sh` for manual recovery.
