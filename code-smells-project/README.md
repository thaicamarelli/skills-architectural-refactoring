# code-smells-project

API de E-commerce em Python/Flask, refatorada para o padrão MVC pela skill `refactor-arch`.

O relatório de auditoria que originou a refatoração está em
[`reports/audit-code-smells-project.md`](reports/audit-code-smells-project.md) (21 findings).

## Estrutura

```
app.py                         # entry point: carrega config e sobe o servidor
src/
├── app.py                     # composition root: monta e liga as camadas
├── errors.py                  # exceções de domínio (status HTTP por erro)
├── config/
│   ├── settings.py            # configuração e segredos via variáveis de ambiente
│   ├── database.py            # conexão por request (flask.g) + schema
│   ├── seed.py                # dados iniciais de desenvolvimento
│   └── logging_config.py      # logging da aplicação
├── models/                    # persistência e regras da entidade (queries parametrizadas)
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/               # orquestração dos casos de uso
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   ├── relatorio_controller.py
│   └── health_controller.py
├── views/                     # fronteira HTTP (Blueprints finos)
│   ├── produto_routes.py
│   ├── usuario_routes.py
│   ├── pedido_routes.py
│   ├── relatorio_routes.py
│   └── system_routes.py
├── services/
│   └── notification_service.py
└── middlewares/
    └── error_handler.py       # tratamento de erro centralizado
```

Regra de dependência: `views → controllers → services/models → banco`. Nenhuma camada de baixo
importa uma de cima.

## Como rodar

```bash
pip install -r requirements.txt

# Desenvolvimento (chave efêmera gerada no boot)
DEBUG=true python app.py

# Produção: SECRET_KEY é obrigatória — o boot falha sem ela
cp .env.example .env   # preencha SECRET_KEY
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configurável por `HOST`/`PORT`). O banco SQLite
(`loja.db`) é criado no primeiro boot e, se estiver vazio, populado com produtos e usuários de
exemplo.

Todas as configurações estão documentadas em [`.env.example`](.env.example): `SECRET_KEY`,
`DEBUG`, `HOST`, `PORT`, `DATABASE_PATH`, `SEED_ON_BOOT`, `SEED_SENHA_PADRAO`, `LOG_LEVEL` e
`CORS_ORIGINS`.

## Endpoints

Os mesmos da versão original, com as mesmas respostas:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Índice da API |
| GET | `/health` | Liveness + contagens |
| GET | `/produtos` | Lista produtos |
| GET | `/produtos/busca` | Busca por `q`, `categoria`, `preco_min`, `preco_max` |
| GET | `/produtos/<id>` | Produto por id |
| POST | `/produtos` | Cria produto |
| PUT | `/produtos/<id>` | Atualiza produto |
| DELETE | `/produtos/<id>` | Remove produto |
| GET | `/usuarios` | Lista usuários |
| GET | `/usuarios/<id>` | Usuário por id |
| POST | `/usuarios` | Cria usuário |
| POST | `/login` | Autentica |
| POST | `/pedidos` | Cria pedido (transacional, com baixa de estoque) |
| GET | `/pedidos` | Lista pedidos com itens |
| GET | `/pedidos/usuario/<id>` | Pedidos de um usuário |
| PUT | `/pedidos/<id>/status` | Atualiza status |
| GET | `/relatorios/vendas` | Relatório de vendas |

## Mudanças de comportamento (intencionais)

A refatoração preserva os endpoints e os payloads, com estas exceções — todas correções de
achados CRITICAL do relatório:

- **`POST /admin/query` e `POST /admin/reset-db` foram removidas** (execução de SQL arbitrário e
  wipe do banco sem autenticação). Passam a responder 404.
- **Senhas agora são hasheadas** (`werkzeug.security`). Bancos criados pela versão antiga, com
  senhas em texto puro, não autenticam mais — recrie o `loja.db`.
- **`GET /usuarios` e `GET /usuarios/<id>` não devolvem mais o campo `senha`.**
- **`GET /health` não devolve mais `secret_key`, `debug`, `db_path` nem `ambiente`.**
- **Respostas de erro passam a incluir `"sucesso": false`** de forma consistente, e falhas
  inesperadas devolvem `{"erro": "Erro interno"}` em vez da mensagem interna da exceção.
- **A validação de produto é a mesma em criar e atualizar** — a atualização, que antes não
  validava tamanho do nome nem categoria, agora valida.
