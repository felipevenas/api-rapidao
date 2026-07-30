# ⚡ Rapidão Delivery API | Plataforma de Delivery e Logística em Tempo Real

> API de alta performance desenvolvida em FastAPI e Python, estruturada sob princípios rígidos de Clean Architecture, Domain-Driven Design (DDD) e SOLID. Plataforma completa de delivery com múltiplos perfis de usuário (cliente, loja, entregador e administrador), autenticação JWT profissional com suporte a revogação (blacklist em Redis), máquina de estados estrita para pedidos, cálculo de frete por geolocalização (Fórmula de Haversine com cache em Redis), enfileiramento de tarefas assíncronas via Celery/Redis e observabilidade com logs estruturados.

![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.4-3781B8?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.0-4169E1?logo=postgresql&logoColor=white)
![Workflow](https://img.shields.io/badge/Workflow-Trunk--Based-2ea44f)
![License](https://img.shields.io/badge/license-Propriet%C3%A1ria-red)

---

## 📖 Propósito

A **Rapidão Delivery API** foi desenvolvida como solução de backend para o ecossistema de delivery e logística (Tema 6). Ela gerencia todo o ciclo de vida de um pedido de entrega, desde o cadastro e autenticação de usuários em diferentes papéis, listagem de lojas e cardápios com cache inteligente, cálculo dinâmico de frete por geolocalização, até o acompanhamento do pedido por uma máquina de estados estrita e auditável.

---

## 🌟 Funcionalidades Focadas na Robustez

- **Clean Architecture & DDD**: Arquitetura orientada a domínios em `app/domain/` com camadas de responsabilidade bem definidas: `Routes -> Service -> Repository -> Model`, unificadas por `UseCase` para orquestração cross-domain.
- **Autenticação JWT Profissional & RBAC**: Suporte a múltiplos perfis de acesso (`client`, `store`, `deliverer` e `admin` com super-acesso). Rota de perfil `/auth/me`, renovação via refresh token e revogação em tempo real (`POST /auth/logout`) gravando na blacklist do Redis com TTL dinâmico.
- **Gerenciamento de Lojas & Cardápios com Cache**: Lojas administram seus produtos e os clientes consultam cardápios servidos via cache Redis (`store:{id}:menu`), invalidados instantaneamente em mutes de produtos.
- **Cálculo de Frete por Geolocalização**: Cálculo da distância geográfica entre cliente e loja utilizando a **Fórmula de Haversine** e precificação dinâmica. Resultados de distância são mantidos em cache Redis (`distance:{lat1}:{lng1}:{lat2}:{lng2}`) com TTL de 10 minutos para alta performance.
- **Máquina de Estados Estrita para Pedidos**: Controle rigoroso das transições de status (`pendente -> em_preparo -> em_rota -> entregue` / `cancelado`), garantindo snapshots de preços dos produtos e validação de permissão de cada ator no fluxo.
- **Atribuição Atômica de Entregador**: Seleção e reserva do entregador disponível mais próximo da loja via trava pessimista SQL (`SELECT FOR UPDATE`) para evitar condições de corrida em atribuições concorrentes.
- **Tarefas Assíncronas com Celery & Redis**: Worker assíncrono para tarefas de background (como cancelamento periódico de pedidos antigos parados via Celery Beat) e enfileiramento resiliente.

- **Observabilidade Estruturada**: Logger com injeção automática de `correlation_id` (requisições HTTP FastAPI) e `task_id` (tarefas Celery) via ContextVars assíncronos.
- **Script Utilitário de DX**: Inclui um script centralizador `run.py` para controlar todas as ações do ecossistema Docker Compose, migrações Alembic e suíte de testes com um único comando.

---

## 📁 Estrutura do Projeto

```
api-rapidao/
├── alembic/                      # Histórico e scripts de migração do banco de dados (Alembic)
├── app/
│   ├── cache/                    # Gerenciador isolado de conexão e pool Redis
│   ├── core/
│   │   ├── config.py             # Configurações Pydantic (carregamento de env)
│   │   ├── logging.py            # Logger estruturado JSON com Correlation ID
│   │   ├── rate_limit.py         # Rate Limiter Sliding Window via Redis
│   │   ├── response.py           # Envelope unificado de respostas JSON (success/error)
│   │   └── security.py           # Autenticação JWT, bcrypt, RBAC e Blacklist Redis
│   ├── db/
│   │   ├── base_class.py         # Base declarativa SQLAlchemy 2.0
│   │   └── session.py            # Engine assíncrono e SessionLocal (asyncpg)
│   ├── domain/                   # Módulos de domínio de negócio (DDD)
│   │   ├── auth/                 # Rotas e regras de autenticação e logout
│   │   ├── user/                 # Gestão cadastral de Usuários e RBAC
│   │   ├── store/                # Cadastro e gestão de Lojas
│   │   ├── product/              # Gestão de Produtos do Cardápio
│   │   ├── freight/              # Serviço de cálculo de frete por Haversine + Redis
│   │   ├── order/                # Pedidos, itens e Máquina de Estados Estrita
│   │   └── delivery/             # Perfil, pings de geolocalização e Atribuição Atômica (FOR UPDATE)

│   ├── worker/                   # Tarefas em segundo plano do Celery Worker/Beat
│   └── main.py                   # Ponto de entrada do FastAPI, Middlewares e Handlers
├── tests/                        # Suíte completa de testes automatizados (Pytest)
├── docker-compose.yml            # Orquestração (FastAPI, Postgres, Redis, Celery, pgAdmin)
├── Dockerfile                    # Dockerfile com Python 3.11 Slim
├── requirements.txt              # Dependências do projeto Python
└── run.py                        # Script CLI unificado de DX (start, migrate, test, etc.)
```

---

## 🏷️ Stack Tecnológica

### Core & Framework
| Tecnologia | Versão | Propósito |
|---|---|---|
| FastAPI | 0.128.x | Framework web assíncrono de alto desempenho para APIs REST |
| Pydantic v2 | 2.10.x | Validação de dados, tipagem estrita e DTOs |
| SQLAlchemy | 2.0.x | ORM assíncrono mapeador de objetos relacionais |
| Alembic | 1.14.x | Gerenciamento de migrações e controle de versão do banco |
| passlib / bcrypt | 4.x | Criptografia segura de senhas de usuários |
| PyJWT | 2.10.x | Emissão e validação de tokens JWT criptografados |
| pytest / httpx | 8.x / 0.28.x | Suíte de testes unitários e de integração assíncronos |

### Banco de Dados, Filas & Infraestrutura
| Componente | Descrição |
|---|---|
| PostgreSQL 16 | Persistência de dados relacionais com UUIDs nativos e asyncpg |
| Redis 7 | Cache de alta velocidade, Blacklist de tokens e Broker do Celery |
| Celery & Beat | Agendamento e execução assíncrona de tarefas de segundo plano |
| Docker Compose | Orquestração simplificada dos serviços locais e containers |

---

## 🚀 Instalação e Execução

### Pré-requisitos
- **Python 3.11** ou superior (se for rodar scripts locais sem Docker)
- **Docker** e **Docker Compose** instalados e em execução

### Setup Local Simples (DX)

```bash
# 1. Clonar o repositório
git clone https://github.com/felipevenas/api-rapidao.git
cd api-rapidao

# 2. Iniciar a aplicação e a infraestrutura (Docker + Migrações + Status)
python run.py start
```

Após a execução, o ecossistema estará ativo. URLs úteis locais:
- **FastAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **pgAdmin 4:** [http://localhost:8081](http://localhost:8081) (Login: `admin@rapidao.com` / Senha: `admin`)
- **Health Check API:** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Suíte de Testes Automatizados

Para executar os 77 testes automatizados de integração e regras de negócio:

```bash
python run.py test
```

---

## 🤝 Contribuição — fluxo Trunk-Based

Este projeto adota o modelo de **Trunk-Based Development**. Feature branches devem ser curtas e mescladas na branch `main` após aprovação em Pull Request.

### Convenções de Commit (Conventional Commits com Escopo)
| Prefixo | Uso | SemVer |
|---|---|---|
| `feat(escopo):` | Nova funcionalidade para o usuário | MINOR |
| `fix(escopo):` | Correção de bug no código | PATCH |
| `chore:` | Ajuste de build, dependências ou configurações | - |
| `docs:` | Atualizações na documentação ou README | - |
| `style:` | Ajustes visuais de logs, layout ou formatação | - |
| `refactor(escopo):` | Refatoração interna de código | - |

---

## 📄 Licença

Software proprietário — todos os direitos reservados.
**&copy; 2026 Rapidão Delivery API**
