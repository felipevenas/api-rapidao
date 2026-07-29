## 2026-07-29T00:55:43Z
<USER_REQUEST>
Você é o explorer_m2_2 (teamwork_preview_explorer).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\explorer_m2_2

MISSÃO: Investigar e projetar a camada de serviços, repositórios, casos de uso, rotas e a estratégia de cache Redis para o Marco 2 (Store & Menu Management) sob C:\Codes\api-rapidao\app.

DOCUMENTOS A CONSULTAR:
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md

TAREFAS DE INVESTIGAÇÃO:
1. Repositórios (`repository.py`): StoreRepository e ProductRepository com métodos CRUD puros (`post`, `get`, `put`, `delete`).
2. Serviços de Domínio (`service.py`): StoreService e ProductService com métodos CRUD puros (`post`, `get`, `put`, `delete`).
3. Estratégia de Cache do Cardápio Redis:
   - Chave: `store:{id}:menu`
   - Leitura do cardápio: checa chave no Redis. Se não existir, consulta DB, formata o JSON do cardápio e grava no Redis.
   - Invalidação síncrona imediata: Qualquer alteração (POST, PUT, DELETE) nos produtos da loja executa `DEL store:{store_id}:menu` no Redis.
4. Casos de Uso (`usecase.py`): Orquestração de busca de cardápio com cache Redis e invalidação no cadastro/edição/deleção.
5. Rotas FastAPI (`routes.py`): `/stores` e `/products` com envelopes de resposta unificados (`status: success`/`error`) e proteção por papel (`require_role(["store"])`).

SAÍDA ESPERADA:
Escreva seu relatório em `C:\Codes\api-rapidao\.agents\explorer_m2_2\analysis.md` e `handoff.md`.
Atualize `progress.md` em seu diretório.
Responda em Português do Brasil e notifique o orquestrador via `send_message`.
</USER_REQUEST>
