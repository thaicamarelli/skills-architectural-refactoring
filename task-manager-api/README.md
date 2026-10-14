# task-manager-api

API de Task Manager em Python/Flask, refatorada para o padrão MVC pela skill `refactor-arch`.
Diferente dos outros dois projetos-alvo, este já tinha alguma separação de camadas (`models/`,
`routes/`, `services/`, `utils/`) — a refatoração melhorou o que já existia em vez de reconstruir
do zero: introduziu `controllers/` e `config/`, conectou o `NotificationService` que ficava órfão
e separou o CRUD de categorias, que morava dentro de `report_routes.py`.

O relatório de auditoria que originou a refatoração está em
[`reports/audit-task-manager-api.md`](reports/audit-task-manager-api.md) (18 findings).

## Estrutura

```
app.py                          # entry point / composition root
database.py                     # db = SQLAlchemy() (já minimal, mantido)
errors.py                       # exceções de domínio (status HTTP por erro)
seed.py                         # dados de exemplo, idempotente
config/
└── settings.py                 # configuração e segredos via variáveis de ambiente
models/                         # persistência + regra da entidade (reaproveitados)
├── task.py, user.py, category.py
controllers/                    # NOVO — orquestração dos casos de uso
├── task_controller.py, user_controller.py
├── category_controller.py, report_controller.py
routes/                         # fronteira HTTP fina (Blueprints por domínio)
├── task_routes.py, user_routes.py, report_routes.py
└── category_routes.py          # NOVO — CRUD extraído de report_routes.py
services/
└── notification_service.py     # reaproveitado; credenciais via config, agora conectado
middlewares/
└── error_handler.py            # NOVO — tratamento de erro centralizado
utils/
└── helpers.py                  # reaproveitado; imports limpos, process_task_data em uso
```

Regra de dependência: `routes → controllers → models`. Nenhuma camada de baixo importa uma de cima.

## Como rodar

```bash
pip install -r requirements.txt

# Desenvolvimento (chave efêmera gerada no boot)
DEBUG=true python app.py

# Produção: SECRET_KEY é obrigatória — o boot falha sem ela
cp .env.example .env   # preencha SECRET_KEY
python app.py
```

A aplicação sobe em `http://0.0.0.0:5000` (configurável por `HOST`/`PORT`). Com
`SEED_ON_BOOT=true` (padrão do `.env.example`), o banco SQLite é populado automaticamente no
primeiro boot, se estiver vazio — não é mais preciso rodar `python seed.py` manualmente, embora
ainda funcione como script standalone.

Todas as configurações estão documentadas em [`.env.example`](.env.example): `SECRET_KEY`,
`DEBUG`, `HOST`, `PORT`, `DATABASE_URL`, `SEED_ON_BOOT`, `SMTP_HOST/PORT/USER/PASSWORD`.

## Endpoints

Os mesmos da versão original, com as mesmas respostas (exceto as mudanças de comportamento
listadas abaixo):

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Índice da API |
| GET | `/health` | Liveness |
| GET | `/tasks` | Lista tasks (com `overdue` calculado) |
| GET | `/tasks/search` | Busca por `q`, `status`, `priority`, `user_id` |
| GET | `/tasks/stats` | Estatísticas agregadas |
| GET | `/tasks/<id>` | Task por id |
| POST | `/tasks` | Cria task |
| PUT | `/tasks/<id>` | Atualiza task |
| DELETE | `/tasks/<id>` | Remove task |
| GET | `/users` | Lista usuários |
| GET | `/users/<id>` | Usuário por id |
| POST | `/users` | Cria usuário |
| PUT | `/users/<id>` | Atualiza usuário |
| DELETE | `/users/<id>` | Remove usuário (cascade nas tasks dele) |
| GET | `/users/<id>/tasks` | Tasks de um usuário |
| POST | `/login` | Autentica |
| GET | `/categories` | Lista categorias |
| POST | `/categories` | Cria categoria |
| PUT | `/categories/<id>` | Atualiza categoria |
| DELETE | `/categories/<id>` | Remove categoria |
| GET | `/reports/summary` | Relatório geral |
| GET | `/reports/user/<id>` | Relatório por usuário |

## Mudanças de comportamento (intencionais)

Todas correções de achados CRITICAL/HIGH do relatório:

- **Senhas agora são hasheadas** com `werkzeug.security` (antes: MD5 sem salt). Bancos criados
  pela versão antiga não autenticam mais — recrie o banco.
- **`GET /users` e `GET /users/<id>` não devolvem mais o campo `password`.**
- **O token de login é assinado de verdade** (`itsdangerous.URLSafeTimedSerializer` com a
  `SECRET_KEY`), em vez da string fixa e previsível `'fake-jwt-token-' + id`. Não é formato JWT
  (para evitar adicionar uma dependência nova ao projeto), mas é verificável e não-forjável.
- **`SECRET_KEY` não tem mais default hardcoded.** Fora do modo `DEBUG`, o boot falha
  explicitamente se a variável de ambiente não estiver definida — nem como literal no código, nem
  como fallback escondido dentro de `os.environ.get(...)`.
- **Credenciais de SMTP saíram do código-fonte** — ficam vazias por padrão e o envio de e-mail é
  pulado (com aviso no log) se não configuradas, em vez de usar a senha real que estava commitada.
