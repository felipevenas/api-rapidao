# Handoff Report - spec_miner_m2_3

**Agente:** `spec_miner_m2_3` (SPECIFICATION MINER)  
**Marco:** Marco 2 - Store & Menu Management  
**Data:** 2026-07-28  

---

## 1. Observation

- **Arquivo `C:\Codes\api-rapidao\PROJECT.md`**:
  - Linhas 9 e 79: Especifica o Bounded Context `store` para Gestão de Lojas, Categorias e Produtos (Cardápio). Define o cache de cardápio no Redis (`store:{id}:menu`) com invalidação síncrona imediata via `DEL` em mutações.
  - Linhas 38-43: Define a estrutura de arquivos em `app/domain/store/`: `models.py`, `repositories.py` (ou `repository.py`), `services.py` (ou `service.py`), `usecase.py`, `routes.py`.
  - Linhas 108-110: Define os contratos de interface cross-domain `validate_store_products(store_id: UUID, product_ids: List[UUID]) -> List[Product]` e `invalidate_menu_cache(store_id: UUID) -> None`.
- **Arquivo `C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md`**:
  - Requisito R3 (linhas 28-30): "Lojas cadastram, editam e removem produtos. Os produtos possuem nome, descrição, preço, categoria e disponibilidade. Clientes consultam o cardápio da loja. O cardápio retornado deve vir de um cache Redis (`store:{id}:menu`), invalidado imediatamente após alterações feitas pela loja nos produtos."
- **Arquivo `C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md`**:
  - Nomenclatura de CRUD: Métodos em `service.py` e `repository.py` chamam-se `post`, `get`, `put`, `delete`.
  - Proibição de imports cross-domain diretos: apenas permitidos via `usecase.py` no domínio de origem.
  - Arquivos permitidos por domínio: apenas `model.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, `usecase.py`.
- **Base de Código em `C:\Codes\api-rapidao\app`**:
  - `core/security.py` (linhas 144-155): Implementa a dependência `require_role(allowed_roles: List[str])` que restringe o acesso por papel (`store`, `client`, `deliverer`).
  - `core/redis.py` (linhas 28-33): Fornece a injeção do cliente Redis `get_redis()`.
  - `domain/auth/schemas.py` (linhas 51-60): Define a estrutura padronizada de envelope `APIResponse` e `ErrorResponse`.

---

## 2. Logic Chain

1. **A partir da Observação em `ORIGINAL_REQUEST.md` (R3) e `PROJECT.md`**: O Marco 2 necessita da criação do Bounded Context `app/domain/store`.
2. **A partir da Observação sobre RBAC (`require_role`)**: As rotas de criação de loja e gerenciamento de produtos devem ser protegidas exigindo o papel `store` via `Depends(require_role(["store"]))`.
3. **A partir da Observação sobre o cache Redis**: O cardápio deve ser armazenado na chave `store:{store_id}:menu`. Qualquer mutação (criação, edição, exclusão/desativação de produto) deve chamar a invalidação síncrona imediata via `DEL store:{store_id}:menu`.
4. **A partir da Observação em `INSTRUCTIONS.md`**: Toda a estrutura do domínio deve seguir rigidamente a convenção de camadas `Routes -> Service -> Repository -> Model`, métodos CRUD com nomes `post`, `get`, `put`, `delete`, e envelopes de resposta `status`, `message`, `data`/`details`.

---

## 3. Caveats

- O domínio `store` ainda não possui arquivos de código criados em `app/domain/store/`. A criação e implementação caberão aos agentes de desenvolvimento (Implementers).
- A tabela `stores` requer campos `latitude` e `longitude`, que serão consumidos posteriormente no Marco 3 para o cálculo de frete (Fórmula de Haversine).
- O campo `category` em `Product` é atualmente uma `String(100)`, simplificando a categorização sem necessidade de uma tabela separada de categorias neste momento.

---

## 4. Conclusion

As especificações do Marco 2 (Store & Menu Management) estão completamente minadas, documentadas e alinhadas com as regras autoritativas do projeto. O relatório `spec_report.md` detalha todas as funcionalidades, contratos de dados, regras de RBAC, invalidação de cache Redis e comportamentos para casos de borda.

---

## 5. Verification Method

Para verificar este relatório:
1. Inspeccionar os arquivos gerados:
   - `C:\Codes\api-rapidao\.agents\spec_miner_m2_3\spec_report.md`
   - `C:\Codes\api-rapidao\.agents\spec_miner_m2_3\handoff.md`
   - `C:\Codes\api-rapidao\.agents\spec_miner_m2_3\progress.md`
2. Confrontar as tabelas de funcionalidades e casos de borda em `spec_report.md` com `C:\Codes\api-rapidao\PROJECT.md` e `C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md`.
