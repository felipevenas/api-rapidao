## 2026-07-28T21:41:15Z
MISSÃO: Investigar e projetar a estrutura completa de infraestrutura base do projeto sob C:\Codes\api-rapidao\.app conforme especificado em:
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md

TAREFAS DE INVESTIGAÇÃO:
1. Mapear a infraestrutura base necessária sob `.app/`:
   - `requirements.txt` (FastAPI, uvicorn, sqlalchemy 2.0, asyncpg, pydantic, pyjwt, passlib/bcrypt, redis, celery, pytest, etc.)
   - `Dockerfile` e `docker-compose.yml` / `docker-compose.test.yml` (PostgreSQL, Redis, Celery Worker, FastAPI app)
   - `app/core/config.py` (Pydantic Settings para DB_URL, REDIS_URL, JWT_SECRET, ALGORITHM, etc.)
   - `app/core/database.py` (SQLAlchemy 2.0 Async engine, AsyncSession, get_db session generator)
   - `app/core/redis.py` (Cliente Redis assíncrono)
   - `app/core/logging.py` (Log estruturado JSON com correlation_id via ContextVars)
   - `app/core/rate_limit.py` (Sliding Window rate limiter via Redis)
   - `app/main.py` (FastAPI app, middlewares de correlation ID, erro e rate limit)
