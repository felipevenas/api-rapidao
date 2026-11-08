# Pull Request

## Description

Provide a clear summary of the change and the problem or feature it addresses.

- Related issue:
- Domain(s) affected:

## Type of change

- [ ] 🚀 New feature (`feat`)
- [ ] 🐞 Bug fix (`fix`)
- [ ] 🔧 Refactor (no behavior change)
- [ ] 📝 Documentation (`docs`)
- [ ] 🎨 Style / formatting / log wording
- [ ] ⚙️ Infrastructure, Docker, dependencies, or tooling (`chore`)

## How was it tested?

Describe the tests and checks you ran, and how a reviewer can reproduce them.

- [ ] **Test suite:** `pytest -q` passes locally.
- [ ] **Docker stack:** `python run.py start` (or `docker-compose up -d`) brings up `app`, `postgres`, `redis`, `celery_worker`, and `celery_beat` healthy.
- [ ] **Logs:** `python run.py logs` shows no database, authentication, or unhandled exceptions.
- [ ] **Migrations:** a new Alembic revision was generated and tested with `alembic upgrade head` (if applicable).
- [ ] **RBAC:** authorized and unauthorized paths were exercised.
- [ ] **Order state machine:** allowed and denied transitions were exercised (if applicable).
- [ ] Other:

## Visual evidence / logs

If applicable, paste terminal output, structured log lines, or Swagger/pgAdmin screenshots. Redact tokens, passwords, and personal data.

## Checklist

- [ ] My code follows the project's layered architecture (`routes → usecase → service → repository → model`).
- [ ] Business rules live in the service or use case layer, not in the route.
- [ ] I changed the order state machine or RBAC only with matching tests.
- [ ] I performed a self-review of my own diff.
- [ ] I commented on complex or non-obvious parts.
- [ ] I updated `CHANGELOG.md` under `[Unreleased]` for user-visible changes.
- [ ] I added or updated tests for the new behavior.
- [ ] Model changes include an Alembic migration; existing migrations were not edited.
- [ ] My changes did not introduce new warnings or errors in the Docker logs.
- [ ] No secrets, credentials, tokens, or personal data are included in this pull request.

## Breaking change?

- [ ] Yes — describe the impact and migration path below.
- [ ] No

## Additional notes

Add anything else the reviewer should know.
