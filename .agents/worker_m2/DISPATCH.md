## 2026-07-28T21:57:06Z
Você é o worker_m2 (teamwork_preview_worker).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\worker_m2

MISSÃO: Implementar o Marco 2 (Store & Menu Management) no diretório C:\Codes\api-rapidao\app a partir das análises e relatórios técnicos dos exploradores do M2.

DOCUMENTOS OBRIGATÓRIOS A LER ANTES DE COMEÇAR:
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md
- C:\Codes\api-rapidao\.agents\explorer_m2_1\analysis.md
- C:\Codes\api-rapidao\.agents\explorer_m2_2\analysis.md
- C:\Codes\api-rapidao\.agents\spec_miner_m2_3\spec_report.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

PROPRIEDADE EXCLUSIVA DE ARQUIVOS (MARCO 2):
Você possui autorização para criar/modificar arquivos em `C:\Codes\api-rapidao\app`:
- `domain/store/__init__.py`
- `domain/store/models.py`
- `domain/store/schemas.py`
- `domain/store/repository.py`
- `domain/store/service.py`
- `domain/store/usecase.py`
- `domain/store/routes.py`
- `main.py` (para registrar os roteadores de /stores e /products)
- `tests/test_store.py`

REGRAS DE ARQUITETURA E IMPLEMENTAÇÃO:
1. Padrão Clean Architecture/DDD: `Routes -> Service -> Repository -> Model`.
2. Proibidos imports cross-domain diretos. Usar a orquestração em `domain/store/usecase.py`.
3. Nomenclatura CRUD rigorosa em `repository.py` e `service.py`: `post`, `get`, `put`, `delete`.
4. Apenas os 6 arquivos permitidos em `domain/store/`: `models.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `usecase.py`.
5. Envelopes de Resposta HTTP unificados:
   - Sucesso: `{ "status": "success", "message": "...", "data": ... }`
   - Erro: `{ "status": "error", "message": "...", "details": ... }`
6. Cache Redis de Cardápio:
   - Chave no Redis: `store:{id}:menu`.
   - Leitura com fallback no banco de dados e gravação em cache.
   - Invalidação síncrona imediata via `DEL store:{store_id}:menu` em qualquer alteração (POST, PUT, DELETE) de produtos.
7. Controle de Acesso (RBAC):
   - Cadastro de loja e gestão de produtos restritos ao papel `store` via `require_role(["store"])`.
   - Consulta de cardápio pública / acessível a clientes.
8. Suíte de Testes Automatizados em `tests/test_store.py`:
   - Escrever testes para cadastro de loja, CRUD de produtos, consulta de cardápio com cache Redis e invalidação imediata via `DEL`.
   - Garantir que a suíte completa de testes (`python -m pytest -v`) seja executada e passe 100%.

SAÍDA ESPERADA:
Crie/modifique os arquivos em `C:\Codes\api-rapidao\app`.
Escreva o relatório de handoff completo em `C:\Codes\api-rapidao\.agents\worker_m2\handoff.md`.
Atualize `C:\Codes\api-rapidao\.agents\worker_m2\progress.md`.
Responda em Português do Brasil e notifique o orquestrador via `send_message` ao concluir.
