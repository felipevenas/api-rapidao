## 2026-07-28T21:57:22Z
<USER_REQUEST>
Você é o worker_reorganize_repo (teamwork_preview_worker).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\worker_reorganize_repo

MISSÃO URGENTE:
Executar a reorganização física do repositório conforme instrução do usuário:
1. Mover/garantir que `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `docker-compose.test.yml` e a pasta `tests/` fiquem na raiz do repositório `C:\Codes\api-rapidao\`.
2. Garantir que a pasta `C:\Codes\api-rapidao\app` contenha o pacote de código (`core/`, `domain/`, `main.py`, `__init__.py`).
3. Ajustar os arquivos de teste em `C:\Codes\api-rapidao\tests\` (`conftest.py`, `test_auth.py`, `test_auth_adversarial.py`, `test_envelope_challenger.py`) para que todos os imports utilizem a sintaxe `from app.core...`, `from app.domain...`, `from app.main...`.
4. Criar `C:\Codes\api-rapidao\app\__init__.py` caso não exista.
5. Ajustar o `docker-compose.yml`, `docker-compose.test.yml` e `Dockerfile` na raiz para rodar o app como `app.main:app` e o Celery worker como `app.core.celery.celery_app`.
6. Executar a suíte de testes automatizada na raiz `C:\Codes\api-rapidao\` via `python -m pytest -v` e confirmar que 100% dos testes passam.

SAÍDA ESPERADA:
Escreva seu relatório em `C:\Codes\api-rapidao\.agents\worker_reorganize_repo\handoff.md`.
Atualize `progress.md` em seu diretório.
Responda em Português do Brasil e notifique o orquestrador via `send_message`.
</USER_REQUEST>
