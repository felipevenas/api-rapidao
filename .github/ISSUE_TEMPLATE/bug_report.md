---
name: 🐞 Bug report
about: Create a report to help us identify and fix problems in the API.
title: 'fix: [short description]'
labels: bug
assignees: ''
---

## Bug description

A clear and concise description of the bug.

## Steps to reproduce

1. Open Swagger at `http://localhost:8000/docs` or call the endpoint `...`
2. Use the method/route `...`
3. Check the Docker logs with `python run.py logs`
4. Observe the returned error or the exception in the logs

## Expected behavior

A clear and concise description of what you expected to happen.

## Actual behavior

What actually happened, including the HTTP status, response envelope, and any error code.

## Logs or visual evidence

If applicable, paste the full FastAPI/Celery exception or structured log lines. Include the `X-Correlation-ID` value when available. Redact tokens, passwords, and personal data.

## Environment

- OS: [e.g. Windows 11, Ubuntu 22.04]
- Docker / Docker Compose version: [e.g. Docker Desktop 4.25]
- Python version: [e.g. 3.11.9]
- API commit or branch: [e.g. `main` at `79d6c1a`]
- User role: [e.g. `client`, `store`, `deliverer`, `admin`]
- Are PostgreSQL and Redis running? [yes/no]

## Privacy or security impact

Does this bug expose personal data, bypass authorization, or allow a state-machine transition that should be denied?

- [ ] No
- [ ] Yes — describe the impact. For an active vulnerability, do **not** continue in this public issue; follow `SECURITY.md` instead.

## Additional context

Any other context, request payload, or reproduction notes.
