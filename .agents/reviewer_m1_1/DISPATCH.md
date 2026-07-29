## 2026-07-28T21:49:14Z
MISSÃO: Fazer uma revisão rigorosa de arquitetura e código para o Marco 1 (Core Infra & Auth) implementado sob C:\Codes\api-rapidao\.app.

DOCUMENTOS A CONSULTAR:
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md
- C:\Codes\api-rapidao\.agents\worker_m1\handoff.md

VERIFICAÇÕES EXIGIDAS:
1. Layout de Código: Verificar se .app/ é a raiz e se core/, domain/, main.py e tests/ estão no topo de .app/ (SEM a pasta redundante app/).
2. Clean Architecture e DDD: Verificar camadas `Routes -> Service -> Repository -> Model` em `domain/auth/`. Confirmar que não há imports cross-domain fora de `usecase.py`.
3. Nomenclatura CRUD: Confirmar que `repository.py` e `service.py` usam os métodos `post`, `get`, `put`, `delete` para operações CRUD puras.
4. Envelopes de Resposta: Confirmar que respostas de sucesso usam `{"status": "success", "message": "...", "data": ...}` e respostas de erro usam `{"status": "error", "message": "...", "details": ...}`.
5. Segurança e RBAC: Verificar se bcrypt hash e JWT access/refresh token e a dependência `require_role` estão funcionais.
6. Testes: Executar `python -m pytest -v` no diretório `C:\Codes\api-rapidao\.app` e reportar o resultado.

## 2026-07-29T00:50:42Z
**Context**: Atualização do caminho raiz da aplicação.
**Content**: ATENÇÃO: A pasta raiz da aplicação foi ajustada de `C:\Codes\api-rapidao\.app` para `C:\Codes\api-rapidao\app`.
Por favor, realizem a revisão / testes diretamente no diretório `C:\Codes\api-rapidao\app`.
**Action**: Validar a aplicação no novo caminho `C:\Codes\api-rapidao\app`.

