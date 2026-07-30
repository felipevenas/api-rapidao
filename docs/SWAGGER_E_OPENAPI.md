# 🛠️ Documentação Swagger UI, ReDoc e Tipagem TypeScript

## 1. Documentação Interativa Local

A API disponibiliza documentação interativa automatizada em conformidade com a especificação **OpenAPI 3.0**:

- **Swagger UI**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON)**: [`http://localhost:8000/api/v1/openapi.json`](http://localhost:8000/api/v1/openapi.json)

---

## 2. Geração Automática de Tipos TypeScript no Frontend

Para garantir **Type-Safety estrito** no Frontend (React/TypeScript), você pode gerar os tipos automaticamente a partir do esquema OpenAPI fornecido pela API.

### Passo a Passo:

1. No projeto Frontend, instale a biblioteca `openapi-typescript`:
```bash
npm install -D openapi-typescript
```

2. Adicione o script de geração no `package.json` do Frontend:
```json
"scripts": {
  "generate:types": "openapi-typescript http://localhost:8000/api/v1/openapi.json --output src/types/api.ts"
}
```

3. Execute o comando para gerar o arquivo de tipos `src/types/api.ts`:
```bash
npm run generate:types
```

---

## 3. Exemplo de Uso de Tipos Gerados no Client HTTP (Axios / Fetch)

```typescript
import type { paths } from './types/api';

type OrderResponse = paths['/api/v1/orders']['post']['responses']['201']['content']['application/json'];
type StoreList = paths['/api/v1/stores']['get']['responses']['200']['content']['application/json'];
```
