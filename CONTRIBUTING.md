# Contributing to the Rapidão Delivery API 🤝

Thank you for contributing to the **Rapidão Delivery API**. This document describes how to set up the project, make changes, and submit them without breaking the domain rules that keep the API reliable.

---

## Golden rule

**The order state machine and the RBAC matrix are the contract.** Never write `order.status` directly from a route, script, or ad-hoc query. Every transition must go through `OrderService.update_status` (or a use case that delegates to it), and every protected action must be authorized by the API — never only by a client application.

If a change requires a new transition, update `VALID_TRANSITIONS` and the actor permission checks together, add tests for both the allowed and the denied cases, and document the change in `CHANGELOG.md`.

---

## Development setup

### Prerequisites

- **Python 3.11+** for `run.py` and local execution.
- **Docker Desktop** with Docker Compose for PostgreSQL, Redis, Celery, and pgAdmin.
- **Git**.

### 1. Clone and start the stack

```powershell
git clone https://github.com/felipevenas/api-rapidao.git
cd api-rapidao
python run.py start
```

`run.py` creates `.venv`, installs `requirements.txt`, builds the Compose stack, waits for PostgreSQL and Redis, applies Alembic migrations, and tails logs.

> **Do not copy `.env.example` to `.env` before the first Compose run.** The Compose file injects `rapidao_user` / `rapidao_pass` into the API containers, while `.env.example` uses `postgres` / `postgres` for local, non-container runs. Mixing them makes the database and the API disagree.

### 2. Run only the infrastructure for local development

```powershell
docker-compose up -d postgres redis
```

Then create `.env`, point it at the host-mapped ports (`5433` for PostgreSQL, `6380` for Redis), and start Uvicorn:

```dotenv
POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_USER=rapidao_user
POSTGRES_PASSWORD=rapidao_pass
POSTGRES_DB=rapidao_db
REDIS_HOST=localhost
REDIS_PORT=6380
```

```powershell
uvicorn app.main:app --reload --port 8000
```

### 3. Follow the logs

```powershell
python run.py logs
python run.py logs app
```

Structured logs are JSON and include `correlation_id` and `task_id`. Use the `X-Correlation-ID` response header to correlate a request with its log lines.

---

## Branch naming

This project uses **trunk-based development**. Branches must be short-lived, created from `main`, and merged back through a pull request.

| Prefix | Use |
|---|---|
| `feat/<short-description>` | New user-facing behavior |
| `bug/<short-description>` | Bug or security fix |
| `chore/<short-description>` | Build, dependencies, tooling, or configuration |
| `docs/<short-description>` | Documentation and README updates |
| `style/<short-description>` | Formatting or log text without behavior change |
| `refactor/<short-description>` | Internal restructuring without behavior change |
| `test/<short-description>` | Test-only changes |

Use lowercase, hyphen-separated descriptions in English. Example: `feat/atomic-courier-assignment` or `bug/token-blacklist-ttl`.

---

## Commit conventions

Use **Conventional Commits in English**, with a scope when the change is domain-specific.

| Prefix | Use | SemVer | Example |
|---|---|---|---|
| `feat(scope):` | New user-facing capability | MINOR | `feat(order): add strict cancellation transition` |
| `fix(scope):` | Bug fix | PATCH | `fix(auth): revoke access token on logout` |
| `docs:` | Documentation | — | `docs: standardize README and governance in English` |
| `style:` | Formatting or log wording | — | `style(order): normalize log messages` |
| `refactor(scope):` | Internal refactor | — | `refactor(freight): extract cache key builder` |
| `test(scope):` | Tests only | — | `test(delivery): cover concurrent assignment` |
| `chore:` | Build, dependencies, tooling | — | `chore: pin asyncpg range` |

Keep commits atomic: one logical change per commit, with a body that explains **why** when the reason is not obvious.

---

## Architecture rules

The repository follows a domain-oriented layered design. Keep the dependency direction intact:

```text
routes.py  →  usecase.py  →  service.py  →  repository.py  →  models.py
```

### 1. Respect layer boundaries

- **Routes** handle HTTP, dependency injection, and `ValueError` to HTTP status mapping. They must not contain business rules.
- **Use cases** are the only place for cross-domain orchestration. If order creation needs store, product, and freight, that coordination belongs in `OrderUseCase`.
- **Services** own domain validation and decisions. Raise `ValueError` for rule violations; routes translate it.
- **Repositories** own SQLAlchemy queries and `flush()` calls. They must not contain HTTP or domain policy.
- **Models** are persistence definitions. Do not import routes into models or repositories.

### 2. Do not import across domains directly

`app/domain/order/` must not import `app/domain/store/repository.py`. Cross-domain work goes through the other domain's service or a use case, as the existing code does.

### 3. Keep I/O typed with Pydantic schemas

Routes accept `*Create` / `*Update` schemas and return `*Read` schemas. Do not return raw ORM objects to clients.

### 4. Preserve the response envelope

Use `success_response(...)` and `error_response(...)` from `app/core/response.py`. Do not return bare dictionaries with a different shape from a new route.

### 5. Respect the state machine

Add transitions only in `VALID_TRANSITIONS`. Update `OrderService._validate_transition_permission` for the actor matrix. Add tests for:
- the allowed actor and edge;
- an unauthorized actor;
- an invalid edge (for example, `entregue → pendente`).

### 6. Treat Redis as an optional accelerator

Existing cache, rate-limit, and blacklist code catches Redis failures and degrades gracefully. New Redis calls must follow the same pattern so the API still boots and serves requests when Redis is down. Do not introduce a hard startup dependency on Redis without an explicit architectural decision.

### 7. Keep money and distance rounding explicit

Freight uses `round(value, 2)` at calculation boundaries. If you introduce a new monetary field, state its rounding rule and keep it consistent with the existing formulas. The current code uses `float`; do not silently change to `Decimal` without a migration and a compatibility plan.

### 8. Timestamps

Follow the convention of the module you touch. New cross-cutting work should prefer timezone-aware UTC timestamps. Do not mix naive and aware datetimes in the same calculation.

---

## Database and migrations

Alembic is the source of truth for the schema.

1. Change the SQLAlchemy model under `app/domain/<domain>/models.py`.
2. Make sure the model is imported in `alembic/env.py` so autogenerate can see it.
3. Generate a revision:

```powershell
docker-compose exec app alembic revision --autogenerate -m "add_courier_index"
```

4. Review the generated file in `alembic/versions/`. Autogenerate is a starting point, not a guarantee.
5. Apply and test it:

```powershell
docker-compose exec -T app alembic upgrade head
```

Rules:

- **Applied migrations are immutable.** Never edit a revision that has shipped. Create a new one.
- Use a clear snake_case message.
- Add indexes and constraints deliberately; do not rely on application checks for invariants that the database can enforce.
- Test both `upgrade head` and, when practical, `downgrade` on a disposable database.

---

## Testing

Run the suite before opening a pull request:

```powershell
pytest -q
```

Or use the Docker test stack:

```powershell
python run.py test
```

The suite uses an in-memory SQLite database and disables Redis (`tests/conftest.py`). This means:

- tests are fast and isolated;
- PostgreSQL-specific behavior such as `SELECT ... FOR UPDATE` is **not** covered;
- if your change depends on PostgreSQL semantics, add a focused integration test or document why it cannot be covered by the current suite.

Add new tests under `tests/` with the `test_` prefix. Prefer behavior-focused names:

```python
async def test_courier_assignment_rejects_order_in_transit(client):
    ...
```

---

## Quality gates

| Gate | Command | Required |
|---|---|---|
| Test suite | `pytest -q` | Yes |
| Compose syntax | `docker-compose config` | Yes when Compose files change |
| Migrations | `alembic upgrade head` | Yes when models change |
| Python syntax | `python -m compileall -q app` | Recommended |
| Secret scan | Manual review of the diff | Yes |

There is currently **no CI workflow, linter, formatter, type checker, or coverage threshold** configured in the repository. Do not claim a gate that does not exist. If you add one, update this section and the README.

---

## Security and privacy

- Never commit `.env`, real JWTs, database passwords, private keys, or production URLs.
- Use only development placeholders in `.env.example`.
- Do not weaken `require_role`, the state machine, or ownership checks to make a client flow easier.
- Validate authorization on the server. A hidden button is not an access control.
- Be careful with logs: do not log tokens, passwords, full e-mail addresses in bulk, or unredacted request bodies.
- If you find a vulnerability, follow [`SECURITY.md`](SECURITY.md) and report it privately. Do not open a public issue with an exploit.

Known access-control gaps are listed in the README under [Known Limitations](README.md#known-limitations-mvp-trade-offs). Fixing one is a high-value contribution; include regression tests and update the limitation list.

---

## Pull request process

1. Create a branch from `main` using the naming convention above.
2. Keep the change focused; split unrelated refactors into separate pull requests.
3. Update `CHANGELOG.md` under `[Unreleased]` when the change is user-visible.
4. Run the quality gates.
5. Open the pull request using [`.github/pull_request_template.md`](.github/pull_request_template.md).
6. Self-review the diff before requesting review. Remove debug prints, commented-out code, and unrelated formatting changes.
7. Address review comments with new commits; do not force-push over a review in progress unless the maintainer asks.

### Definition of Done

- [ ] The change is described in the pull request and linked to an issue when applicable.
- [ ] Business rules live in the service or use case layer, not in the route.
- [ ] RBAC and the order state machine still hold; denied paths are tested.
- [ ] `pytest -q` passes.
- [ ] New behavior has tests.
- [ ] Model changes include an Alembic revision.
- [ ] `CHANGELOG.md` is updated for user-visible changes.
- [ ] No secrets, credentials, or personal data are included.
- [ ] Documentation (`README.md`, `docs/`, docstrings) is updated when behavior changes.

---

## Questions

Open a discussion or a documentation issue. For security matters, use the private channel described in [`SECURITY.md`](SECURITY.md).
