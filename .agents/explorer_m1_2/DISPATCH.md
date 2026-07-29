## 2026-07-28T21:41:15Z
Você é o explorer_m1_2 (teamwork_preview_explorer).
Seu diretório de trabalho é: C:\Codes\api-rapidao\.agents\explorer_m1_2

MISSÃO: Investigar e projetar o módulo de Autenticação e Usuários (`auth`) sob C:\Codes\api-rapidao\.app conforme especificado em:
- C:\Codes\api-rapidao\PROJECT.md
- C:\Codes\api-rapidao\.agents\ORIGINAL_REQUEST.md
- C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md
- C:\Codes\api-rapidao\.gemini\REFERENCES.md

TAREFAS DE INVESTIGAÇÃO:
1. Mapear o domínio `auth` sob `C:\Codes\api-rapidao\.app\app\domain\auth/` e componentes de segurança em `app/core/security.py`:
   - Modelo User (`models.py`): UUID id, email, password_hash, full_name, role (enum: `client`, `store`, `deliverer`), is_active, created_at, updated_at.
   - Schemas Pydantic (`schemas.py`): UserCreate, UserResponse, TokenResponse, RefreshTokenRequest, LoginRequest.
   - Hashing e JWT em `app/core/security.py`: `get_password_hash`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`.
   - Repositório (`repository.py`): CRUD básico (post, get, put, delete) + busca por email.
   - Serviço de Domínio (`service.py`): Lógica de negócio de autenticação, hashing, verificação de credenciais, geração de tokens.
   - Caso de Uso (`usecase.py`): Fluxos de registro, login e refresh token.
   - Rotas FastAPI (`routes.py`): `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`.
   - Dependência `require_role(allowed_roles)` para autorização por papel.

SAÍDA ESPERADA:
Escreva um relatório detalhado de análise e plano de implementação do domínio auth em `C:\Codes\api-rapidao\.agents\explorer_m1_2\analysis.md` e `handoff.md`.
Atualize periodicamente `C:\Codes\api-rapidao\.agents\explorer_m1_2\progress.md`.
Responda em Português do Brasil e envie mensagem ao orquestrador ao finalizar.
