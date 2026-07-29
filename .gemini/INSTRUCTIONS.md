# INSTRUCTIONS.md

Este arquivo é a referência obrigatória para qualquer desenvolvimento neste repositório, seja por uma pessoa ou por um assistente de IA (Claude Code, Copilot, etc). Antes de escrever qualquer código, leia isto por completo.

Se estiver usando Claude Code, duplique ou renomeie este arquivo para `CLAUDE.md` na raiz do projeto, para que ele seja carregado automaticamente em toda sessão.

---

## 1. Contexto do projeto

Backend do sistema de delivery e logística (Tema 6 do Hackathon entre Amigos), com três perfis de usuário, cliente, loja e entregador, cada um com autenticação própria e painel dedicado. O pedido evolui por uma máquina de estados em tempo real, com atribuição automática de entregador e cálculo de frete por geolocalização.

Documentos de apoio, sempre consultar antes de decidir algo:
- `README.md`, visão geral, setup e stack
- `PRD_Delivery_Backend.md`, requisitos funcionais e não funcionais completos
- `CONTRIBUTING.md`, exemplos práticos de cada regra abaixo
- `CHANGELOG.md`, histórico do que já foi implementado

---

## 2. Stack fixa

- Python com FastAPI
- PostgreSQL, acesso assíncrono via SQLAlchemy 2.0
- JWT (access e refresh token) para autenticação
- Celery com Redis, para tarefas assíncronas
- Redis, para cache e rate limit

Não trocar nenhum item dessa stack sem alinhar antes, mesmo que exista uma alternativa "melhor" na sua avaliação.

---

## 3. Arquitetura, é lei, não sugestão

Camadas fixas, sempre nesta ordem de dependência:

```
Routes -> Service -> Repository -> Model
```

Organização por domínio (DDD) em `app/domain/{nome}/`. Estrutura de pastas geral segue como base o repositório [`felipevenas/api-boilerplate`](https://github.com/felipevenas/api-boilerplate).

---

## 4. Regras obrigatórias, resumo

1. **Nomenclatura de CRUD**, métodos básicos em `service.py` e `repository.py` chamam-se `post`, `get`, `put`, `delete`. Métodos que não são CRUD puro usam nome descritivo em inglês.
2. **Cross-domain é proibido.** Um domínio nunca importa `service`, `repository` ou `model` de outro domínio diretamente. Se precisar orquestrar mais de um domínio, criar `usecase.py` no domínio que inicia o fluxo.
3. **Arquivos permitidos por domínio**, apenas `model.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`, e opcionalmente `usecase.py`. Nada além disso solto na pasta.
4. **Idioma**, comentários, docstrings, commits, README e CHANGELOG sempre em português do Brasil. Nomes de classes, métodos, variáveis e arquivos sempre em inglês.
5. **README e CHANGELOG**, README incrementado a cada feature relevante, CHANGELOG incrementado sempre, a cada PR mergeado.
6. **Conventional Commits**, formato `tipo(escopo): descrição em português`, agrupado por domínio afetado. Tipos, `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `ci`.
7. **CI obrigatório**, todo trabalho só é considerado concluído com o pipeline de `.github/workflows/ci.yml` verde (lint e testes).
8. **PR sempre com template**, usar `.github/pull_request_template.md` para abrir qualquer Pull Request.
9. **SRP como norma**, uma classe ou função muda por um único motivo. Se identificar dois motivos, separar responsabilidade.
10. **SOLID e Clean Code**, aplicar os cinco princípios SOLID de verdade, não só o SRP, nomes claros, funções curtas, sem duplicação entre domínios.

Detalhes e exemplos de código de cada regra estão em `CONTRIBUTING.md`, este arquivo é o resumo executivo, aquele é o manual.

---

## 5. Checklist antes de considerar algo pronto

- [ ] Segue a arquitetura de camadas e a organização por domínio
- [ ] Nomenclatura de CRUD respeitada
- [ ] Nenhum import cross-domain fora de um `usecase.py`
- [ ] Domínio só contém os arquivos permitidos
- [ ] Comentários e mensagens em português do Brasil, nomes técnicos em inglês
- [ ] README e CHANGELOG atualizados
- [ ] Commit(s) no padrão Conventional Commits, por escopo
- [ ] Testes automatizados cobrindo a regra de negócio nova
- [ ] CI passando
- [ ] PR aberto com o template correto

---

## 6. Quando algo não estiver claro

Não assumir e seguir em frente silenciosamente. Melhor parar, revisar o PRD e o CONTRIBUTING, e só então decidir, principalmente em decisões de modelo de dados ou de transição de estado do pedido, que afetam todos os domínios depois.