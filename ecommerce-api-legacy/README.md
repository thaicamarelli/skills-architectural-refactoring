# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
cp .env.example .env   # preencha os valores (ou use os de dev já sugeridos)
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## Estrutura

```
src/
├── config/settings.js        # config + segredos via variáveis de ambiente
├── db/                        # conexão, schema e seed do SQLite
├── models/                    # acesso a dados por entidade (queries parametrizadas)
├── services/                  # senha (bcrypt), pagamento (simulado) e logger
├── controllers/                # orquestram o caso de uso (checkout, relatório, usuários)
├── middlewares/                # auth de admin, error handler central, async handler
├── routes/                     # endpoints HTTP finos
└── app.js                      # composition root
```

## Mudanças de comportamento (correções de segurança)

A refatoração corrigiu problemas de segurança do código legado; os endpoints continuam
respondendo o mesmo *payload* de sucesso, mas com estas diferenças:

- `GET /api/admin/financial-report` e `DELETE /api/users/:id` agora exigem o header
  `x-admin-key` (valor em `ADMIN_API_KEY`, ver `.env.example`). Antes eram públicos.
- Senhas de usuário passam a ser hasheadas com `bcrypt` (antes usavam uma "cripto" caseira
  reversível). Usuários criados antes da migração precisariam redefinir a senha em um cenário real.
- `DELETE /api/users/:id` agora remove em cascata (transação) as matrículas e pagamentos do
  usuário, em vez de deixá-los órfãos no banco.
- Segredos (`DB_PASS`, `PAYMENT_GATEWAY_KEY`, etc.) saíram do código-fonte e vêm de variáveis
  de ambiente (`.env`, não versionado).
- O número de cartão e a chave do gateway de pagamento não são mais gravados em log.
