# Security Policy 🛡️

## Supported versions

Only the latest state of the `main` branch receives active security fixes. There are no maintained release branches or long-term support versions at this time.

| Version | Supported |
|---|---|
| `>= 0.1.0` (current `main`) | ✅ Yes |
| `< 0.1.0` | ❌ No |

Version numbers follow the entries in [`CHANGELOG.md`](CHANGELOG.md). The repository does not publish tagged releases yet; `main` is the supported line.

---

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Use one of these private channels:

1. **GitHub private advisory (preferred):**
   [Open a private security advisory](https://github.com/felipevenas/api-rapidao/security/advisories/new)
2. **E-mail:** `felipevenas@gmail.com` with the subject `[SECURITY] api-rapidao`.

Include:

- a clear description of the issue and the affected component;
- the exact steps to reproduce, or a proof of concept;
- the impact you believe is possible (data exposure, privilege escalation, denial of service, etc.);
- the version, commit, or branch you tested;
- any suggested fix or mitigation, if you have one.

Do **not** include real personal data, production credentials, or third-party secrets in the report. Redact tokens and passwords.

### Response expectations

- We aim to acknowledge the report within **48 hours**.
- We will confirm the issue, agree on a disclosure timeline, and keep you informed while a fix is prepared.
- Please give us a reasonable window to release a fix before publishing details.

---

## Security scope

The following areas are especially relevant to this API. Reports about them are high priority.

### Authentication and token lifecycle

- JWT signing, algorithm confusion, and secret handling.
- Access/refresh token type confusion.
- Redis blacklist bypass on logout.
- Token replay after logout or user deactivation.
- Password hashing with bcrypt and credential enumeration.

### Authorization and access control

- `require_role` bypasses and the `admin` super-access behavior.
- IDOR on orders, stores, products, users, couriers, and notifications.
- Store ownership checks on store and product mutations.
- Order visibility rules by role.
- Public or unauthenticated routes that expose data:
  - `POST /users`
  - `GET /notifications/orders/{order_id}`
  - `GET /notifications/unprocessed`
  - `WS /ws/orders/{order_id}`
- Self-registration with the `admin` role.

### Order and delivery integrity

- Bypassing the strict order state machine.
- Moving an order to `entregue` without the assigned courier.
- Assigning a courier to an order in an invalid state.
- Race conditions in courier assignment.
- Tampering with price snapshots, freight values, or totals.

### Data, infrastructure, and secrets

- SQL injection through SQLAlchemy or raw SQL.
- Redis key injection or cache poisoning.
- Outbox payloads leaking personal data.
- Secrets committed to the repository or baked into images.
- Dependency vulnerabilities in `requirements.txt` or base images.
- Rate-limit bypass and fail-open behavior when Redis is unavailable.

### Denial of service

- Unbounded queries or payloads.
- Expensive freight or menu requests without limits.
- WebSocket connection exhaustion.
- Celery task flooding.

---

## Known security-relevant limitations

These are known MVP gaps, documented openly so that reporters and users can prioritize:

- The public registration endpoint accepts the `role` field without an allow-list and can create an `admin` user.
- `POST /users` is public and creates users without authentication.
- `GET /users` and `GET /users/{id}` expose user records to any authenticated role.
- Notification read endpoints and the order WebSocket room have no authentication or authorization.
- `OrderUseCase._validate_access` allows any `store` user to read any order.
- Refresh tokens are stateless and are not revoked on logout; only the presented access token is blacklisted.
- Password changes through `PUT /users/{id}` are currently ignored by the service layer.
- Rate limiting and token blacklist checks fail open when Redis is unreachable.
- The default `JWT_SECRET` in `config.py` and `.env.example` is a development placeholder and is not safe for production.
- Docker Compose contains development credentials and runs Uvicorn with `--reload`.

Reports that demonstrate a practical impact from any of these are welcome. Please do not test against production data or accounts you do not own.

---

## Out of scope

- Vulnerabilities that require a compromised host, browser, or Docker daemon.
- Missing TLS or security headers in the local Compose stack.
- Development credentials that are clearly labeled as local-only, unless they are reachable in a deployed environment.
- Automated scanner output without a reproducible impact.
- Social engineering, physical access, or spam.
- Denial of service caused by intentionally unbounded local load tests.

---

## Resolution process

Once a vulnerability is confirmed:

1. We reproduce it on a private branch and assess severity and affected versions.
2. We develop and test the fix, including a regression test when practical.
3. We merge the fix into `main` through a private or coordinated pull request.
4. We publish a patched version or commit and document the change in [`CHANGELOG.md`](CHANGELOG.md).
5. We credit the reporter in the advisory unless they prefer to remain anonymous.
6. We publish a GitHub security advisory after users have had a reasonable window to update.

There is no bug bounty program. We still gratefully acknowledge responsible reports.

---

## Safe harbor

We will not pursue legal action against researchers who:

- test only against their own local deployment or accounts they own;
- avoid accessing, modifying, or exfiltrating real user data;
- stop testing and report immediately upon discovering a real data exposure;
- do not publicly disclose the issue before a coordinated fix is available.

This safe harbor does not authorize testing against third-party infrastructure or production systems without explicit written permission.
