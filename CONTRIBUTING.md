# 🤝 Contribuindo para a Rapidão Delivery API

Obrigado por querer contribuir com a **Rapidão Delivery API**! Este documento orienta o processo de desenvolvimento para manter o projeto organizado e altamente sustentável.

---

## 🛠️ Setup de Desenvolvimento

### 1. Clonar e Inicializar o Ambiente
Recomendamos o uso direto do Docker para evitar ter que instalar o PostgreSQL e o Redis na sua máquina local:

```bash
# Clone o repositório
git clone https://github.com/felipevenas/api-rapidao.git
cd api-rapidao

# Inicialize o banco de dados e os containers de forma automática
python run.py start
```

### 2. Acessando os logs e monitoramento
Enquanto desenvolve novas features, mantenha o terminal de logs ativos para diagnosticar exceptions e retornos:
```bash
python run.py logs
```

---

## 🛤️ Estrutura de Branches

Adotamos a abordagem de **Trunk-Based Development**. As branches de funcionalidades devem ser criadas a partir de `main`, serem de curta duração e mescladas rapidamente de volta à `main` após aprovação em Pull Request.

Os nomes de branches devem ser escritos **em português** e seguir o padrão de nomenclatura:
- `funcionalidade/nome-da-feature`: Para novas implementações.
- `correcao/nome-do-bug`: Para correções de falhas de código ou segurança.
- `documentacao/nome-do-arquivo`: Para atualizações em manuais ou markdown.
- `melhoria/ajuste-infra`: Para refatorações e melhorias de setup.

**Exemplo:** `funcionalidade/calculo-frete-haversine` ou `correcao/ajuste-token-swagger`.

---

## ✍️ Convenções de Commit

Nossos commits são escritos **em português** com os prefixos estruturados para clareza no histórico do Git (Conventional Commits com escopo):

| Prefixo | Uso | Exemplo |
|---|---|---|
| `feat(escopo):` | Nova funcionalidade para o usuário | `feat(order): adiciona máquina de estados estrita para pedidos` |
| `fix(escopo):` | Correção de bug no código | `fix(auth): corrige formato do token para autenticação no Swagger` |
| `chore:` | Tarefas de build, dependências ou configurações | `chore: adiciona dependência python-multipart` |
| `docs:` | Atualizações na documentação ou README | `docs: atualiza guia de instalação no README.md` |
| `style:` | Formatação de código ou ajustes em logs (sem mudar comportamento) | `style: ajusta quebras de linha nos modelos do domínio order` |
| `refactor(escopo):` | Refatoração interna de código para melhor legibilidade/performance | `refactor(freight): otimiza chave de cache Redis para Haversine` |

---

## 🧪 Rodando Testes

Antes de submeter qualquer código, verifique se a suíte de testes unitários e de integração continua passando com sucesso (atualmente 77/77 testes):

```bash
# Executa a suíte de testes de forma direta
pytest
```

Se precisar criar novos cenários de testes, adicione-os na pasta `tests/` com o prefixo `test_`.

---

## 📦 Banco de Dados e Migrações (Alembic)

Sempre que alterar os modelos do banco de dados (arquivos `models.py` sob a pasta `app/domain/`), você deve gerar uma migração correspondente do Alembic:

```bash
# 1. Crie a migração (via script CLI de DX)
python run.py migrate -m "sua_descricao_em_portugues"

# Ou via docker-compose diretamente:
docker-compose exec app alembic revision --autogenerate -m "sua_descricao_em_portugues"

# 2. Aplique a migração no banco de dados local
docker-compose exec app alembic upgrade head
```

Verifique se a migração foi gerada corretamente na pasta `alembic/versions/` e adicione-a ao commit.
