# Análise de Projeto — Heurísticas de Detecção (Fase 1)

Objetivo desta referência: dar sinais concretos para descobrir **linguagem**, **framework**,
**banco de dados**, **domínio** e **arquitetura atual** de um projeto que você nunca viu. Use os
sinais em ordem de confiança: um arquivo de manifesto (`package.json`, `requirements.txt`) é
prova mais forte do que a extensão de um arquivo solto.

## Índice
- [1. Como explorar o projeto](#1-como-explorar-o-projeto)
- [2. Detecção de linguagem](#2-deteccao-de-linguagem)
- [3. Detecção de framework e versão](#3-deteccao-de-framework-e-versao)
- [4. Detecção de banco de dados](#4-deteccao-de-banco-de-dados)
- [5. Detecção do domínio](#5-deteccao-do-dominio)
- [6. Mapeamento da arquitetura atual](#6-mapeamento-da-arquitetura-atual)
- [7. Contagem de arquivos-fonte](#7-contagem-de-arquivos-fonte)

## 1. Como explorar o projeto

1. Liste a árvore de diretórios ignorando ruído: `node_modules/`, `venv/`, `.venv/`, `__pycache__/`,
   `.git/`, `dist/`, `build/`, arquivos de lock (`package-lock.json`, `poetry.lock`) e bancos
   materializados (`*.db`, `*.sqlite`).
2. Abra primeiro os **arquivos de manifesto** (dependências) e o **entry point** — eles revelam
   stack e estrutura mais rápido do que ler tudo.
3. Só então leia os arquivos-fonte, do maior para o menor (arquivos grandes concentram problemas).

## 2. Detecção de linguagem

| Sinal | Linguagem |
|---|---|
| `*.py`, `requirements.txt`, `pyproject.toml`, `Pipfile` | Python |
| `*.js`/`*.mjs`/`*.ts`, `package.json` | JavaScript/TypeScript (Node.js) |
| `*.rb`, `Gemfile` | Ruby |
| `*.php`, `composer.json` | PHP |
| `*.go`, `go.mod` | Go |
| `*.java`, `pom.xml`, `build.gradle` | Java |

Confirme pela extensão predominante dos arquivos-fonte, não por um único arquivo.

## 3. Detecção de framework e versão

Leia o manifesto de dependências e os imports do entry point.

**Python** (`requirements.txt`, `pyproject.toml`):
- `flask` → Flask. Versão vem da linha `flask==X.Y.Z`. Import: `from flask import Flask`.
- `flask-sqlalchemy` → ORM SQLAlchemy sobre Flask (models como classes `db.Model`).
- `django` → Django. `fastapi` → FastAPI. `flask-cors`, `marshmallow` → dependências de apoio.
- Se não houver versão fixada, procure a versão instalada ou registre "não especificada".

**Node.js** (`package.json` → `dependencies`):
- `express` → Express. Versão no valor (`"express": "^4.18.2"`).
- `koa`, `fastify`, `@nestjs/core` → Koa / Fastify / NestJS.
- Script de boot em `scripts.start` (ex.: `node src/app.js`) indica o entry point.

Registre o framework **com versão** (ex.: `Flask 3.1.1`, `Express ^4.18.2`).

## 4. Detecção de banco de dados

- **Driver nas dependências:** `sqlite3`, `psycopg2`/`psycopg` (Postgres), `mysqlclient`/`pymysql`
  (MySQL), `flask-sqlalchemy`/`sqlalchemy` (ORM), `mongoose`/`mongodb` (MongoDB).
- **String de conexão / arquivo:** `sqlite3.connect("loja.db")`, `sqlite3.Database(':memory:')`,
  `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'`.
- **Tabelas/coleções:** extraia dos `CREATE TABLE ...`, dos modelos ORM (`__tablename__`,
  `db.Column`) ou das queries. Liste os nomes das tabelas encontradas.
- **ORM vs SQL cru:** se há `CREATE TABLE`/`cursor.execute("SELECT ...")`, é SQL manual (procure
  SQL Injection na Fase 2). Se há classes de modelo mapeadas, é ORM.

## 5. Detecção do domínio

Infira o que a aplicação faz a partir de: nomes de tabelas, nomes de rotas/endpoints, e o
vocabulário do código.
- Tabelas `produtos`, `pedidos`, `itens_pedido`, `usuarios` + rotas `/produtos`, `/pedidos` →
  **API de e-commerce**.
- Tabelas `courses`, `enrollments`, `payments`, rota `/api/checkout` → **plataforma de cursos/LMS
  com checkout**.
- Tabelas `tasks`, `categories`, `users`, rotas `/tasks`, `/reports` → **gerenciador de tarefas**.

Descreva o domínio em uma linha, citando as entidades principais.

## 6. Mapeamento da arquitetura atual

Classifique o projeto em um dos padrões abaixo — isso define o quão agressiva a Fase 3 será.

- **Monólito de arquivo único / poucos arquivos:** tudo (rotas + regra de negócio + acesso a
  dados + config) em 1–4 arquivos. Ex.: um `models.py` que faz SQL, validação e formatação.
  Sinal: arquivos enormes, sem pasta de camadas.
- **God Class / God Module:** uma única classe ou módulo concentra responsabilidades demais
  (ex.: uma classe `AppManager` que cria o banco, define rotas e processa pagamento).
- **Camadas parciais:** já existem pastas como `models/`, `routes/`, `services/`, `utils/`, mas
  as fronteiras vazam (regra de negócio dentro das rotas, `services/` que não é usado, model
  anêmico). Aqui a refatoração é de melhoria, não de reconstrução.
- **MVC/limpo:** camadas bem separadas (raro nos alvos legados).

Ao mapear, responda: existe separação de camadas? Onde mora a regra de negócio hoje? Onde mora
o acesso a dados? A configuração está isolada ou hardcoded? Há um entry point claro?

## 7. Contagem de arquivos-fonte

Conte apenas arquivos de código da aplicação (a linguagem detectada), excluindo dependências
instaladas, caches, testes gerados e o próprio diretório `.claude/`. Esse número vai no resumo
da Fase 1 como `Source files: N files analyzed` e deve bater com a realidade do projeto.
