# Relatório de Handoff — Validação Empírica Marco 1 (Core Infra & Auth)

**Agente:** `challenger_m1_2` (teamwork_preview_challenger)  
**Data:** 2026-07-28  
**Diretório de Trabalho:** `C:\Codes\api-rapidao\.agents\challenger_m1_2`  
**Alvo de Validação:** `C:\Codes\api-rapidao\.app`  

---

## 1. Observation

- **Execução da Suíte de Testes Existente (`python -m pytest -v`):**
  - **Comando executado:** `python -m pytest -v` sob `C:\Codes\api-rapidao\.app`
  - **Resultado:** 13 testes em `tests/test_auth.py` executados com sucesso (13 passed in 15.38s).
  ```text
  tests/test_auth.py::test_register_client_role PASSED                     [  7%]
  tests/test_auth.py::test_register_store_role PASSED                      [ 15%]
  tests/test_auth.py::test_register_deliverer_role PASSED                  [ 23%]
  tests/test_auth.py::test_register_duplicate_email PASSED                 [ 30%]
  tests/test_auth.py::test_login_success PASSED                            [ 38%]
  tests/test_auth.py::test_login_invalid_password PASSED                   [ 46%]
  tests/test_auth.py::test_login_nonexistent_user PASSED                   [ 53%]
  tests/test_auth.py::test_refresh_token_success PASSED                    [ 61%]
  tests/test_auth.py::test_refresh_token_with_access_token_fails PASSED    [ 69%]
  tests/test_auth.py::test_get_me_success PASSED                           [ 76%]
  tests/test_auth.py::test_get_me_without_token_fails PASSED               [ 84%]
  tests/test_auth.py::test_require_role_authorized PASSED                  [ 92%]
  tests/test_auth.py::test_require_role_unauthorized PASSED                [100%]
  ============================= 13 passed in 15.38s =============================
  ```

- **Verificação da Estrutura Física sob `C:\Codes\api-rapidao\.app`:**
  - Diretórios sob `.app`: `core/`, `domain/`, `tests/`, `.pytest_cache/`, `__pycache__/`.
  - **Não existe** a pasta redundante `app/` sob `C:\Codes\api-rapidao\.app`.
  - A pasta `domain/auth/` contém estritamente os 6 arquivos permitidos (`models.py`, `schemas.py`, `repository.py`, `service.py`, `usecase.py`, `routes.py`).

- **Verificação de Conformidade do Envelope de Resposta HTTP (Sucesso & Erro):**
  - **Envelope de Sucesso (`{"status": "success", "message": "...", "data": ...}`):**
    - `GET /health` -> `{"status": "success", "message": "Rapidão API Operational", "data": {"status": "ok"}}` (Conforme)
    - `POST /auth/register` -> `{"status": "success", "message": "Usuário registrado com sucesso.", "data": ...}` (Conforme)
    - `POST /auth/login` -> `{"status": "success", "message": "Autenticação realizada com sucesso.", "data": ...}` (Conforme)
    - `POST /auth/refresh` -> `{"status": "success", "message": "Token renovado com sucesso.", "data": ...}` (Conforme)
    - `GET /auth/me` -> `{"status": "success", "message": "Perfil recuperado com sucesso.", "data": ...}` (Conforme)
  - **Envelope de Erro (`{"status": "error", "message": "...", "details": ...}`):**
    - `HTTP 400 (Bad Request)` (E-mail duplicado) -> `{"status": "error", "message": "E-mail já cadastrado na plataforma.", "details": null}` (Conforme)
    - `HTTP 401 (Unauthorized)` (Login incorreto) -> `{"status": "error", "message": "Credenciais inválidas.", "details": null}` (Conforme)
    - `HTTP 403 (Forbidden)` (Papel incorreto) -> `{"status": "error", "message": "Acesso negado...", "details": null}` (Conforme)
    - `HTTP 422 (Unprocessable Entity)` (Validação Pydantic) -> `{"status": "error", "message": "Erro de validação nos dados de entrada.", "details": [...]}` (Conforme)
    - **HTTP 404 (Not Found)** (Rota inexistente, ex: `GET /auth/nonexistent-route`) -> **FALHA DE CONFORMIDADE**. Retorna payload cru da Starlette/FastAPI:
      ```json
      {"detail": "Not Found"}
      ```
    - **HTTP 405 (Method Not Allowed)** (Método incorreto, ex: `PUT /auth/register`) -> **FALHA DE CONFORMIDADE**. Retorna payload cru da Starlette/FastAPI:
      ```json
      {"detail": "Method Not Allowed"}
      ```

- **Execução do Harness de Testes de Envelope Adicionado (`tests/test_envelope_challenger.py`):**
  - **Comando:** `python -m pytest -v`
  - **Resultado:** 18 PASSED, 2 FAILED.
  ```text
  FAILED tests/test_envelope_challenger.py::test_not_found_route_envelope - AssertionError: 404 route returned non-compliant envelope: {'detail': 'Not Found'}
  FAILED tests/test_envelope_challenger.py::test_method_not_allowed_route_envelope - AssertionError: 405 route returned non-compliant envelope: {'detail': 'Method Not Allowed'}
  ```

---

## 2. Logic Chain

1. **Análise de Causa Raiz do Envelope Não Conforme (404/405):**
   - No arquivo `C:\Codes\api-rapidao\.app\main.py`, a exceção é registrada com o decorador `@app.exception_handler(HTTPException)`, onde `HTTPException` é importada de `fastapi`.
   - O Starlette (motor subjacente do FastAPI), quando não encontra uma rota (404) ou quando o método HTTP é incompatível (405), dispara diretamente instâncias de `starlette.exceptions.HTTPException`.
   - Como o handler foi registrado especificamente para a classe `fastapi.exceptions.HTTPException` em vez da classe base `starlette.exceptions.HTTPException`, os erros de roteamento internos da Starlette ignoram o `http_exception_handler` e caem no handler padrão da Starlette, que gera respostas com a chave `"detail"` em vez do envelope unificado `{"status": "error", "message": "...", "details": ...}`.

2. **Impacto na Arquitetura e Regras de Negócio:**
   - A especificação exige tratamento padronizado de envelopes HTTP para TODAS as respostas da API. Clientes HTTP que consumirem a API receberão estruturas de JSON distintas dependendo se o erro foi lançado por um endpoint ou pelo roteador.

3. **Avaliação das Demais Exigências:**
   - A remoção da pasta redundante `app/` foi totalmente confirmada sob `.app`.
   - O isolamento Clean Architecture/DDD no domínio `auth` e a nomenclatura de métodos CRUD (`post`, `get`, `put`, `delete`) estão corretos.

---

## 3. Caveats

- **Ambiente de Banco de Dados de Teste**: A suíte de testes roda com SQLite assíncrono em memória (`sqlite+aiosqlite:///:memory:`) mockado no `conftest.py`. A validação com PostgreSQL real e Redis rodando sob Docker Compose fará parte dos testes de integração nos marcos futuros (Marco 6).
- **Sem outras ressalvas**: Todos os aspectos de estrutura e envelopes foram validados empiricamente.

---

## 4. Conclusion

**VEREDITO:** **`REJECT`**

Embora a infraestrutura core, o módulo de autenticação JWT, a estrutura de diretórios Clean Architecture/DDD e a nomenclatura CRUD estejam implementados corretamente, o projeto é **REJEITADO** no Marco 1 devido à quebra de conformidade do envelope de resposta em exceções HTTP 404 e 405 nativas do Starlette.

### Recomendação de Correção para o Implementador:
Em `C:\Codes\api-rapidao\.app\main.py`:
Importar `HTTPException` do Starlette (ex: `from starlette.exceptions import HTTPException as StarletteHTTPException`) e registrar o handler `@app.exception_handler(StarletteHTTPException)` para capturar tanto erros de rotas/métodos quanto exceções disparadas pela aplicação.

---

## 5. Verification Method

Para reproduzir empiricamente as falhas e verificar os resultados:

1. Navegar até o diretório raiz do backend:
   ```powershell
   cd C:\Codes\api-rapidao\.app
   ```

2. Executar a suíte de testes automatizados com `pytest`:
   ```powershell
   python -m pytest -v
   ```

3. **Condições de Invalidação / Sucesso Futuro**:
   - Atualmente, os testes `test_not_found_route_envelope` e `test_method_not_allowed_route_envelope` em `tests/test_envelope_challenger.py` falham comprovando o bug.
   - Após a correção em `main.py`, a suíte completa de 20 testes deve passar com 100% de sucesso (`20 passed`).
