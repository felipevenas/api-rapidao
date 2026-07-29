# Original User Request

## Initial Request — 2026-07-29T00:40:15Z

<USER_REQUEST>
O objetivo é desenvolver o backend de uma plataforma de delivery ("Rapidão") com três perfis de usuário (cliente, loja e entregador), incluindo autenticação JWT, máquina de estados de pedidos, atribuição automática concorrente de entregadores, cálculo de frete por geolocalização, cache com Redis, tarefas assíncronas com Celery e atualizações em tempo real via WebSockets. Toda a solução deve ser construída do zero a partir da pasta `.app/` do repositório, seguindo o padrão de arquitetura Clean Architecture/DDD.

Working directory: C:\Codes\api-rapidao\.app
Integrity mode: benchmark

## Instruções Especiais de Execução
- A cada ciclo de trabalho, o time de agentes deve ler atentamente os arquivos `C:\Codes\api-rapidao\.gemini\INSTRUCTIONS.md` e `C:\Codes\api-rapidao\.gemini\REFERENCES.md` para garantir o alinhamento com as regras arquiteturais, nomenclatura de CRUD, imports proibidos e padrões técnicos definidos.
- Respeitar a estrutura organizada sob o diretório `C:\Codes\api-rapidao\.app`.

## Requirements

### R1. Arquitetura e Organização do Projeto
- O backend deve ser desenvolvido em Python com FastAPI, PostgreSQL (SQLAlchemy 2.0 assíncrono), Celery (Redis como broker), Redis (cache e rate limit) e WebSockets.
- Toda a base de código deve estar contida no diretório `C:\Codes\api-rapidao\.app`. A estrutura geral de pastas deve seguir as diretrizes do `api-boilerplate` (`app/domain/{nome}/` com camadas `Routes -> Service -> Repository -> Model`).
- Não são permitidos imports cross-domain diretos, exceto se orquestrados por arquivos `usecase.py` no domínio de origem do fluxo.
- Nomes técnicos em inglês e comentários/commits em português do Brasil.

### R2. Autenticação e Usuários (Construídos do Zero)
- Construir a base de autenticação JWT própria (access e refresh tokens) e gerenciamento de papéis (cliente, loja, entregador) do zero.
- Armazenar senhas com hash bcrypt.
- Proteger rotas usando a dependência `require_role` correspondente ao papel do usuário.

### R3. Gerenciamento de Lojas e Cardápios
- Lojas cadastram, editam e removem produtos. Os produtos possuem nome, descrição, preço, categoria e disponibilidade.
- Clientes consultam o cardápio da loja. O cardápio retornado deve vir de um cache Redis (`store:{id}:menu`), invalidado imediatamente após alterações feitas pela loja nos produtos.

### R4. Pedidos e Máquina de Estados
- Clientes criam pedidos com produtos de uma única loja. O pedido nasce no status `pendente`.
- Controlar estritamente a máquina de estados do pedido:
  - `pendente -> em_preparo` (ação da loja)
  - `em_preparo -> em_rota` (atribuição automática do sistema)
  - `em_rota -> entregue` (ação do entregador atribuído)
  - Cancelamento (`pendente -> cancelado` ou `em_preparo -> cancelado` pelo cliente ou loja).
- Transições de estados inválidas devem ser sumariamente rejeitadas com erro apropriado.

### R5. Frete e Geolocalização
- Calcular a distância geográfica entre a loja e o cliente com base nas coordenadas de latitude e longitude.
- Calcular o frete a partir dessa distância.
- Resultados de cálculos de distância consultados recentemente devem vir de cache no Redis (`distance:{lat1}:{lng1}:{lat2}:{lng2}`) com TTL de 10 minutos.

### R6. Atribuição de Entregadores (Concorrência e Fila)
- Buscar entregadores disponíveis dentro de um raio da loja para atribuição quando o pedido estiver pronto (`em_preparo -> em_rota`).
- A atribuição deve ser atômica. Usar estratégias como lock pessimista (`SELECT FOR UPDATE` no banco) ou lock otimista para evitar que dois pedidos reservem o mesmo entregador simultaneamente.
- Se não houver entregador disponível, o pedido deve aguardar em fila para reprocessamento periódico.

### R7. Infraestrutura de Testes e Tarefas Assíncronas (Celery)
- Configurar ambiente completo de infraestrutura via Docker Compose contendo PostgreSQL, Redis e um worker Celery.
- O Celery deve orquestrar:
  - `assign_deliverer`: atribuição atômica de entregador.
  - `calculate_freight`: cálculo de frete assíncrono.
  - `notify_status_change`: envio de notificações de mudança de status de pedidos (WebSocket).
  - `expire_stale_orders`: cancelamento periódico de pedidos antigos parados.
- Testes automatizados (pytest) de concorrência e integração rodando dentro do ecossistema do Docker Compose para assegurar que a máquina de estados e o matching de entregadores funcionem sem condições de corrida.

### R8. Notificações, Rate Limit e Outbox
- Atualizações em tempo real via WebSockets (com Redis Pub/Sub) notificando as partes envolvidas.
- Rate limit no Redis protegendo rotas críticas de login e criação de pedidos, além de limite global.
- Logs estruturados contendo `correlation_id` para requisições HTTP e `task_id` para tarefas Celery.
- Padrão Outbox implementado para garantir envio resiliente de eventos de status do pedido.

## Acceptance Criteria

### Infraestrutura e Setup
- [ ] O projeto possui um `docker-compose.yml` funcional que sobe os serviços de PostgreSQL, Redis, app (FastAPI) e Celery worker.
- [ ] Toda a estrutura de pastas e códigos está isolada dentro do diretório `C:\Codes\api-rapidao\.app`.

### Autenticação e Segurança
- [ ] Cadastro e login com JWT e papéis funcionam corretamente e rotas restritas são barradas para papéis incompatíveis.

### Lojas e Cardápios
- [ ] Modificação de produtos no cardápio de uma loja invalida imediatamente o cache Redis e subsequentes requisições de clientes batem no cache atualizado.

### Fluxo de Pedidos e Concorrência
- [ ] A máquina de estados rejeita transições inválidas (ex: `em_rota -> cancelado`).
- [ ] Um teste automatizado concorre por um único entregador disponível para dois pedidos simultâneos, comprovando que apenas um é associado e o outro permanece pendente ou é redirecionado.

### Testes de Integração e Celery
- [ ] A suíte de testes de integração roda com sucesso e valida o fluxo completo (criação de pedido, cálculo de frete assíncrono, atribuição de entregador concorrente e transições de status).
</USER_REQUEST>

## Follow-up — 2026-07-29T00:46:53Z

Atenção equipe: O usuário corrigiu a estrutura de pastas da aplicação.
Não deve existir a subpasta 'app/' dentro da pasta '.app/'.
A pasta '.app/' é a raiz do projeto backend. Portanto, as pastas 'core/', 'domain/', 'main.py' e outros arquivos devem residir DIRETAMENTE sob '.app/'.

Exemplo de estrutura correta:
.app/
├── core/
│   ├── config.py
│   ├── database.py
│   └── ...
├── domain/
│   ├── auth/
│   └── ...
├── main.py
├── docker-compose.yml
├── requirements.txt
└── ...

Por favor, ajustem imediatamente a criação dos arquivos e a estrutura atual. Certifiquem-se de que os imports nos arquivos Python reflitam essa mudança (por exemplo, usar 'from core.config import ...' ou imports relativos, em vez de 'from app.core.config import ...', já que '.app' contendo um ponto não é um nome de pacote Python importável diretamente). Mova quaisquer arquivos existentes de '.app/app/' para '.app/' e delete a pasta redundante '.app/app/'.

## Follow-up — 2026-07-29T00:50:10Z

Atenção equipe: Nova correção estrutural solicitada pelo usuário.
A pasta raiz da aplicação deve se chamar 'app' e NÃO '.app'.
Ou seja, o diretório onde todos os arquivos da solução residem (incluindo core/, domain/, main.py, docker-compose.yml, tests/, etc.) deve ser 'C:\Codes\api-rapidao\app'.

Por favor:
1. Renomeiem o diretório 'C:\Codes\api-rapidao\.app' para 'C:\Codes\api-rapidao\app'.
2. Atualizem o Working Directory para 'C:\Codes\api-rapidao\app'.
3. Ajustem quaisquer configurações, caminhos nos scripts, arquivos de configuração do docker-compose e do dockerfile que façam referência a '.app' para apontar para 'app'.
4. Certifiquem-se de que os imports nos arquivos Python permaneçam corretos após essa renomeação da pasta raiz. Se a pasta raiz se chama 'app', dependendo de onde o projeto for executado (por exemplo, dentro da própria pasta 'app/'), os imports serão 'from core.config import ...'. Se for executado de fora, pode ser 'from app.core.config import ...'. Ajustem conforme a forma como vocês configuraram a execução e os testes.

Façam esses ajustes imediatamente na infraestrutura e nos arquivos.

## Follow-up — 2026-07-29T00:57:00Z

Atenção equipe: O usuário reorganizou fisicamente a estrutura do repositório.
Os arquivos de infraestrutura ('Dockerfile', 'docker-compose.yml', 'docker-compose.test.yml', 'requirements.txt') e a pasta de testes ('tests/') foram movidos para a raiz do repositório ('C:\Codes\api-rapidao\').
A pasta 'app/' agora contém apenas o pacote de código da aplicação (subpastas 'core/', 'domain/' e o arquivo 'main.py').

Por favor, realizem os seguintes ajustes urgentes:
1. O diretório de execução e infraestrutura passa a ser a raiz do repositório ('C:\Codes\api-rapidao\'), e o pacote contendo o código é 'app/'.
2. Corrijam o 'Dockerfile' e o 'docker-compose.yml'/'docker-compose.test.yml' para que localizem corretamente os módulos. Como o código está dentro de 'app/', os comandos no Docker Compose devem apontar para 'app.main:app' (ex: 'command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload') e para 'app.core.celery.celery_app' (ex: 'command: celery -A app.core.celery.celery_app worker --loglevel=info'), ou o PYTHONPATH deve incluir '/app/app' no container.
3. Ajustem as referências e imports nos testes em 'tests/' na raiz para que importem a partir do pacote 'app' (ex: 'from app.core...' ou 'from app.domain...').
4. Atualizem os caminhos internos nos seus scripts e logs de controle.

Essa mudança é fundamental para que o Docker Compose e os testes rodem com sucesso na raiz do projeto.



