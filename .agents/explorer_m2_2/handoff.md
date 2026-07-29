# Relatório de Handoff - Marco 2 (Store & Menu Management)

**Agente:** explorer_m2_2 (teamwork_preview_explorer)  
**Data:** 2026-07-29  
**Tipo:** Hard Handoff (Análise e Design Concluídos)

---

## 1. Observation

- **Repositório e Estrutura Existente:**
  - O projeto utiliza a arquitetura Clean Architecture/DDD sob `C:\Codes\api-rapidao\app`.
  - O diretório `app/domain` contém atualmente apenas o módulo `auth` (`models.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py`).
  - O arquivo `C:\Codes\api-rapidao\PROJECT.md` define no inventário do Marco 2 (linhas 79-80):
    - Feature 3: Gestão de Lojas & Produtos (Cadastro de Lojas, CRUD de produtos por loja (dono), categorias, desativação de produto).
    - Feature 4: Cache de Cardápio (Cache de cardápio no Redis `store:{id}:menu`, invalidação síncrona imediata em edições da loja).
  - O arquivo `C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md` estabelece (linhas 38, 47):
    - Camadas estritas: `Routes -> Service -> Repository -> Model` (com `usecase.py` para orquestração).
    - Regra 1: Métodos CRUD puros em `service.py` e `repository.py` chamam-se obrigatoriamente `post`, `get`, `put`, `delete`.
    - Regra 2: Cross-domain é proibido diretamente entre domínios.
    - Regra 3: Arquivos permitidos no domínio: `model.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, e opcionalmente `usecase.py`.
  - O arquivo `C:\Codes\api-rapidao\tests\test_envelope_challenger.py` confirma que todas as respostas da API devem obrigatoriamente seguir o envelope unificado de resposta:
    - Sucesso: `{"status": "success", "message": "...", "data": ...}`
    - Erro: `{"status": "error", "message": "...", "details": ...}`

---

## 2. Logic Chain

1. **Definição do Domínio `store`:**
   - Com base na análise da estrutura em `app/domain/auth`, o novo domínio deve residir em `app/domain/store` contendo os 6 arquivos permitidos: `models.py`, `schemas.py`, `repository.py`, `service.py`, `usecase.py` e `routes.py`.

2. **Nomenclatura CRUD Pura nos Repositórios e Serviços:**
   - Para atender estritamente à Regra 1 das `INSTRUCTIONS.md`, tanto `StoreRepository` quanto `ProductRepository` em `repository.py`, assim como `StoreService` e `ProductService` em `service.py`, devem nomear seus métodos fundamentais de manipulação como `post`, `get`, `put` e `delete`.
   - Consultas secundárias (ex.: `get_by_owner_id`, `list_by_store_id`, `validate_store_products`) utilizam nomes descritivos em inglês.

3. **Estratégia de Cache e Orquestração (`usecase.py`):**
   - A leitura do cardápio (`get_store_menu`) deve consultar primeiramente o Redis via chave `store:{id}:menu`.
   - Se o Redis retornar um cache miss, o `ProductService` consulta os produtos ativos no banco PostgreSQL, formata a resposta JSON, grava no Redis e a retorna.
   - Qualquer mutação em produto (criação/POST, edição/PUT, remoção/DELETE) deve disparar a invalidação síncrona imediata no Redis chamando `await redis.delete(f"store:{store_id}:menu")` dentro do `StoreUseCase` antes de retornar a resposta HTTP.

4. **Proteção por Papéis e Envelopes HTTP:**
   - Os endpoints em `routes.py` utilizam `Depends(require_role(["store"]))` para garantir que apenas usuários proprietários de loja possam cadastrar a loja e manipular seus produtos.
   - A leitura pública do cardápio em `GET /stores/{store_id}/menu` fica disponível para clientes e lojas.
   - Todas as respostas retornam os envelopes `status: success` / `status: error`.

---

## 3. Caveats

- **Transação Assíncrona e Fallback Redis:** Caso a conexão com o Redis oscile durante a leitura do cardápio, a camada `StoreUseCase` captura a exceção e faz o fallback gracioso direto para a consulta no banco de dados, garantindo disponibilidade da API.
- **Formato da Chave Redis:** A chave deve obrigatoriamente ser formatada como `store:{store_id}:menu`, usando o UUID da loja em minúsculas com hífens.
- **Relacionamento com Usuários (`User`):** A chave estrangeira `owner_id` em `Store` aponta para `users.id` no esquema do banco relacional.

---

## 4. Conclusion

O design técnico do Marco 2 (Store & Menu Management) foi completamente estruturado e validado. Ele atende a todas as especificações do `PROJECT.md`, `ORIGINAL_REQUEST.md`, `INSTRUCTIONS.md` e `REFERENCES.md`. 
O detalhamento completo com código completo para cada camada (`models.py`, `schemas.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py` e atualização de `main.py`) foi documentado no relatório `analysis.md` em `C:\Codes\api-rapidao\.agents\explorer_m2_2\analysis.md`.

---

## 5. Verification Method

Para verificar independentemente a adequação da especificação:
1. **Inspeção de Código/Design:**
   - Ler o arquivo `C:\Codes\api-rapidao\.agents\explorer_m2_2\analysis.md`.
   - Confirmar a existência de `StoreRepository`, `ProductRepository`, `StoreService`, `ProductService` com métodos `post`, `get`, `put`, `delete`.
   - Confirmar a estratégia de cache Redis `store:{id}:menu` e invalidação síncrona `DEL`.
   - Confirmar as dependências de autorização `require_role(["store"])` nas rotas.
2. **Execução Futura de Testes Automatizados:**
   - Após a implementação do Marco 2 pelos implementadores, executar a suíte de testes com `pytest`:
     ```bash
     pytest tests/
     ```
