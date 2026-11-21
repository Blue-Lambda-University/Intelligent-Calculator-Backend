# Backend classroom labs

1. Trace a `POST /api/v1/calculate` through Pydantic, expression parser, persistence and JSON response.
2. Introduce a division-by-zero regression and watch Pytest reject it.
3. Extend a scientific function and add positive/negative test cases.
4. Inspect `/docs` and compare OpenAPI request/response contracts.
5. Start the stdio FastMCP server; inspect available tools using an MCP client.
6. Introduce a synthetic vulnerable dependency in a disposable branch; inspect pip-audit and Trivy findings.
7. Build/push an image in Jenkins and deploy to staging.
8. Inject a failing readiness probe into a disposable staging release, observe rollout failure, and execute rollback.

Instructor note: Jenkins `Deploy staging` changes image tag without automatically undoing an unhealthy release. `scripts/rollback.sh` is the manual recovery exercise. Protect main and require Jenkins checks to pass.
