# Criação de Skills — Refatoração Arquitetural Automatizada

> **Nota:** Este README documenta o meu processo de resolução do desafio, entregável exigido pelo
> enunciado. O texto original do desafio pode ser consultado no repositório-base
> ([devfullcycle/mba-ia-refactor-projects-skill](https://github.com/devfullcycle/mba-ia-refactor-projects-skill)),
> mantido aqui como remoto `upstream`.

## Análise Manual

Antes de escrever a skill, li o código dos três projetos para entender os problemas que ela
precisaria detectar. Os achados abaixo foram confirmados depois pelo relatório de auditoria gerado
pela própria skill (Fase 2), disponível na íntegra em `reports/audit-project-{1,2,3}.md` — aqui
apresento uma seleção representativa, com a severidade e a justificativa de por que cada um importa.

### Projeto 1 — code-smells-project (Python/Flask, API de E-commerce)

Relatório completo: [`reports/audit-project-1.md`](reports/audit-project-1.md).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | SQL Injection generalizado | `models.py` (14 funções, ex.: linha 28, 109-111) | Todo acesso a dados é montado por concatenação de string, sem parâmetros. Um `email`/`senha` malicioso no `/login` autentica como qualquer usuário; a busca de produtos aceita `DROP TABLE` no meio do termo pesquisado. |
| CRITICAL | Endpoint de execução SQL arbitrária | `app.py:59-78` (`/admin/query`) | A rota executa qualquer SQL recebido no corpo da requisição, sem autenticação — é RCE sobre o banco exposto via HTTP. |
| CRITICAL | Credenciais hardcoded | `app.py:7-8` (`SECRET_KEY`), `database.py:75-79` (senha do admin) | A chave de assinatura e as credenciais de admin ficam versionadas no Git, iguais em toda instalação. |
| CRITICAL | Senhas em texto puro | `models.py:105-131` | Senha é gravada e comparada crua no SQL; `GET /usuarios` ainda devolve a coluna `senha` na resposta — um vazamento do banco expõe todas as credenciais direto. |
| CRITICAL | God Module | `models.py:1-314` | Um único arquivo de 314 linhas concentra SQL, regra de negócio e formatação de 4 domínios (produtos, usuários, pedidos, relatório) — impossível testar ou alterar uma parte sem risco às outras. |
| HIGH | Fat Controller | `controllers.py:24-96` | Validação e regra de negócio (faixas de preço, categorias válidas) ficam presas dentro do handler HTTP, duplicadas entre criar e atualizar. |
| HIGH | Estado global mutável | `database.py:4-11` | A conexão SQLite vive numa variável de módulo compartilhada entre threads (`global db_connection`), gerando condição de corrida sob concorrência. |
| MEDIUM | Query N+1 | `models.py:171-233` | Listar pedidos dispara uma query por item e uma por produto dentro de laços aninhados — o custo cresce como pedidos × itens. |
| MEDIUM | Validação ausente/duplicada | `controllers.py:28-90, 188-201` | O bloco de validação de produto já divergiu entre criar e atualizar; a criação de pedido não valida a forma dos itens e vira erro 500 em vez de 400. |
| LOW | `print` como logging | 19 ocorrências em `app.py`/`controllers.py` | Sem níveis nem destino configurável — mistura eventos de negócio, erro e debug no stdout. |
| LOW | Magic numbers | `models.py:256-262`, `controllers.py:47-52, 242` | Faixas de desconto, limites de nome e status válidos aparecem como literais soltos no meio da lógica, sem nome que explique a intenção. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

Relatório completo: [`reports/audit-project-2.md`](reports/audit-project-2.md).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Credenciais hardcoded | `src/utils.js:1-7` | `dbPass` e a chave de produção do gateway de pagamento (`pk_live_...`) ficam literais no código-fonte versionado. |
| CRITICAL | Hashing de senha quebrado (crypto caseira) | `src/utils.js:17-23` | `badCrypto` não é hash: repete Base64 10.000 vezes e corta o resultado — reversível e de entropia baixíssima, dá falsa sensação de segurança. |
| CRITICAL | God Class | `src/AppManager.js:1-141` | `AppManager` cria o schema, define rotas, processa pagamento e acessa dados — tudo em uma classe só, sem nenhuma camada separada. |
| CRITICAL | Endpoint destrutivo sem autenticação | `src/AppManager.js:131-137` (`DELETE /api/users/:id`) | Qualquer chamador não autenticado apaga qualquer conta do sistema. |
| CRITICAL | Dado sensível em log | `src/AppManager.js:45` | O número completo do cartão de crédito e a chave do gateway são gravados juntos em `console.log` — violação direta de PCI-DSS. |
| HIGH | Callback hell sem transação | `src/AppManager.js:50-63` | Matrícula → pagamento → auditoria são três `db.run` aninhados sem transação; uma falha no meio deixa o banco inconsistente. |
| HIGH | Deleção deixando registros órfãos | `src/AppManager.js:131-137` | O próprio comentário do código admite: "matrículas e pagamentos ficaram sujos no banco" após deletar um usuário. |
| MEDIUM | API deprecated — `sqlite3` callback puro | `src/AppManager.js` (uso disseminado) | O estilo 100% callback gera o pyramid-of-doom visto no checkout; o equivalente moderno é uma API baseada em Promises. |
| MEDIUM | Query N+1 no relatório financeiro | `src/AppManager.js:92-124` | Para cada curso busca matrículas, e para cada matrícula busca usuário e pagamento — `O(cursos × matrículas)` queries. |
| LOW | Nomenclatura críptica | `src/AppManager.js:29-33` | O corpo do checkout é desestruturado em `u`, `e`, `p`, `cid`, `cc` — nomes de uma letra para dados sensíveis de domínio. |
| LOW | Código morto | `src/utils.js:10, 25` | `totalRevenue` é declarado e exportado, mas nunca incrementado nem lido em lugar nenhum. |

### Projeto 3 — task-manager-api (Python/Flask, já com camadas parciais)

Relatório completo: [`reports/audit-project-3.md`](reports/audit-project-3.md).

| Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|
| CRITICAL | Credenciais hardcoded (SECRET_KEY e SMTP) | `app.py:13`; `services/notification_service.py:7-10` | A chave de sessão e a senha de e-mail do serviço estão fixas no código, mesmo com `python-dotenv` já disponível e não usado. |
| CRITICAL | Hashing de senha quebrado (MD5 sem salt) | `models/user.py:27-32` | MD5 sem salt é reversível em massa via rainbow table — um vazamento do banco expõe todas as senhas com esforço mínimo. |
| CRITICAL | Senha exposta na API + token falso | `models/user.py:16-25`, usado em `routes/user_routes.py:86,129,209` | `to_dict()` devolve o hash da senha em toda resposta de criar/atualizar/login, e o "token" de login é a string previsível `'fake-jwt-token-' + id`. |
| HIGH | Fat Controller nos relatórios | `routes/report_routes.py:12-155` | Contagens, detecção de atraso e produtividade por usuário são calculadas dentro do handler HTTP, sem nenhum Model/Service — mesmo o projeto já tendo camadas. |
| MEDIUM | Validação duplicada + helper morto | `routes/task_routes.py:96-114, 166-184`; `utils/helpers.py:57-108` | As mesmas regras de validação estão copiadas em criar/atualizar, enquanto a função `process_task_data` que já as centraliza nunca é chamada. |
| MEDIUM | Lógica de "overdue" duplicada em 4 lugares | `task_routes.py`, `report_routes.py`, `user_routes.py` vs `models/task.py:50-60` | A regra de atraso está reimplementada manualmente em 5 pontos, apesar de `Task.is_overdue()` já existir e nunca ser usado — risco alto de divergência silenciosa. |
| MEDIUM | CRUD de categorias dentro do módulo de relatórios | `routes/report_routes.py:157-223` | Um recurso inteiro (categorias) mora dentro do blueprint de relatórios, violando SRP a nível de módulo. |
| LOW | API deprecated — `datetime.utcnow()` e `Model.query.get(id)` | Espalhado em models, routes e seed | Padrões desencorajados desde Python 3.12 / SQLAlchemy 2.0, com equivalentes modernos diretos (`datetime.now(timezone.utc)`, `db.session.get`). |
| LOW | Camada de serviço desconectada | `services/notification_service.py:1-49` | `NotificationService` existe e parece funcional, mas nenhuma rota o importa — funcionalidade "fantasma". |
| LOW | Magic numbers ignorando constantes já definidas | `routes/task_routes.py`, `routes/user_routes.py` vs `utils/helpers.py:110-116` | Limites de título, prioridade e senha estão hardcoded nas rotas mesmo com as constantes correspondentes já definidas e não importadas em `helpers.py`. |

---

## Construção da Skill

A skill vive em `.claude/skills/refactor-arch/` — copiada, sem alterações, para dentro dos três
projetos. Ela é composta pelo `SKILL.md` (o orquestrador, obrigatório e com nome fixo pelo
enunciado) e cinco arquivos de referência em `references/`, cada um cobrindo uma das áreas de
conhecimento exigidas.

### Estrutura do SKILL.md

O `SKILL.md` não contém nenhum conhecimento específico de stack — só orquestra três fases
sequenciais e aponta para a referência certa em cada uma:

| Fase | O que faz | Referência lida |
|---|---|---|
| 1. Análise | Detecta linguagem, framework, banco e arquitetura atual; imprime o resumo | `project-analysis.md` |
| 2. Auditoria | Cruza o código com o catálogo, gera o relatório, **para e pede confirmação** | `antipattern-catalog.md` + `report-template.md` |
| 3. Refatoração | Reestrutura para MVC e valida boot + endpoints | `mvc-architecture.md` + `refactoring-playbook.md` |

Decisões de design deliberadas:

- **Conhecimento fica nas referências, não no SKILL.md.** O orquestrador diz "leia X no início da
  Fase Y" em vez de embutir heurísticas de Python ou Node diretamente — é isso que permite copiar
  a pasta inteira para um projeto de stack diferente sem editar uma linha.
- **O portão de confirmação é uma regra do SKILL.md, não uma sugestão.** A Fase 2 é
  explicitamente somente leitura e a Fase 3 só roda depois de um "sim" textual — isso apareceu
  como requisito não-negociável do desafio, então virou um "princípio que vale para todas as
  fases" logo no topo do arquivo, não um passo isolado que poderia ser pulado.
- **Evidência em vez de opinião.** Cada finding exige `arquivo:linha`. Isso força o agente a citar
  o trecho real em vez de generalizar ("SQL Injection" sem dizer onde não conta).
- **"Adapte-se ao ponto de partida" como princípio explícito.** `code-smells-project` é um
  monólito de 4 arquivos; `task-manager-api` já tem `models/`, `routes/`, `services/`. O SKILL.md
  instrui a Fase 3 a reaproveitar camadas existentes em vez de reconstruir — sem essa instrução, a
  tendência natural do agente seria aplicar a mesma transformação agressiva nos dois casos.

### Arquivos de referência

- **`project-analysis.md`** — heurísticas de detecção em ordem de confiança (manifesto de
  dependências > imports do entry point > extensão de arquivo solto), com tabelas de sinais por
  linguagem/framework/banco e uma classificação de arquitetura em 4 níveis (monólito → God
  Class/Module → camadas parciais → MVC limpo), usada para calibrar o quão agressiva a Fase 3
  deve ser.
- **`antipattern-catalog.md`** — 15 anti-patterns (5 CRITICAL, 5 HIGH, 5 MEDIUM, 4 LOW) mais uma
  seção dedicada a **APIs deprecated** (Python e Node.js), cada entrada com sinal de detecção
  acionável, não descrição vaga. Critérios de inclusão abaixo.
- **`report-template.md`** — formato exato do relatório (cabeçalho, `## Summary`, `## Findings`
  ordenados por severidade, rodapé com total), com um exemplo preenchido para calibrar tom e
  granularidade da Descrição/Impacto/Recomendação.
- **`mvc-architecture.md`** — responsabilidades de cada camada (Models/Views-Routes/
  Controllers/Services/Config/Middlewares), a regra de dependência ("a seta nunca aponta para
  trás") e como adaptar a mesma estrutura-alvo tanto a um monólito quanto a um projeto com
  camadas parciais.
- **`refactoring-playbook.md`** — 12 transformações concretas (antes/depois), cada uma
  referenciando qual entrada do catálogo resolve, cobrindo desde segredos hardcoded e SQL
  Injection até APIs deprecated.

### Anti-patterns incluídos e por quê

O catálogo foi calibrado pela leitura manual dos três projetos, não escrito antes de olhar o
código: cada entrada existe porque apareceu em pelo menos um dos projetos-alvo.

- **CRITICAL** (segurança/arquitetura que destroem separação de responsabilidades): credenciais
  hardcoded, SQL Injection, endpoint perigoso/execução arbitrária, senha em texto puro ou hashing
  quebrado, God Class/Module — os cinco apareceram nos três projetos, em formas diferentes (SQL
  Injection por concatenação no projeto 1, `badCrypto` caseiro no projeto 2, MD5 sem salt no
  projeto 3).
- **HIGH** (trava manutenção/teste): fat controller, estado global mutável, side effects
  embutidos no fluxo HTTP, ausência de camada de dados, operação multi-passo sem transação —
  escolhidos porque cada um tem uma correção estrutural clara (mover para Model/Service/Controller
  certo), diferente dos CRITICAL que são principalmente correções de segurança.
- **MEDIUM/LOW**: Query N+1, validação duplicada, erro engolido, config acoplada/debug ligado,
  print como log, magic numbers, nomenclatura ruim, código morto — smells de qualidade que os três
  projetos compartilham em proporções diferentes (o projeto 3, já com camadas, tem proporcionalmente
  mais MEDIUM de duplicação/organização do que CRITICAL de arquitetura).
- **APIs deprecated** entrou como seção própria (exigência do desafio) com tabelas específicas por
  ecossistema: `datetime.utcnow()` e `Model.query.get(id)` apareceram de fato espalhados no
  projeto 3; `sqlite3` callback puro no projeto 2.

### Como garanti que a skill é agnóstica de tecnologia

- Nenhum arquivo de referência assume uma linguagem por padrão — todas as tabelas de sinais têm
  colunas/entradas paralelas para Python e Node (e cobrem Ruby/PHP/Go/Java em `project-analysis.md`
  por completude, mesmo sem projeto-alvo nessas stacks).
- A prova real foi copiar a **mesma pasta**, sem editar nada, para os três projetos e rodar
  `/refactor-arch` em cada um. A Fase 1 identificou corretamente Flask nos projetos 1 e 3 e
  Express no projeto 2; a Fase 3 produziu `src/controllers/`, `src/models/`, `src/views|routes/`
  em Python e `src/controllers/`, `src/models/`, `src/routes/` em Node — mesma forma, convenção de
  nomes da linguagem.
- O princípio "adapte-se ao ponto de partida" evitou o erro mais provável de uma skill
  "agnóstica de tecnologia" mal calibrada: tratar todo projeto como o pior caso. No projeto 3, a
  Fase 3 manteve `models/`, `routes/`, `services/`, `utils/` já existentes e só adicionou a camada
  que faltava (`controllers/`) e o `config/`, em vez de recriar tudo do zero como fez no projeto 1
  (monólito de 4 arquivos).

### Desafios encontrados e como resolvi

- **Risco de a Fase 2 pular a confirmação.** A primeira versão do fluxo já deixava claro o "pare e
  peça confirmação", mas reforcei no início do `SKILL.md` como princípio geral (não só um passo da
  Fase 2) depois de notar que era fácil interpretar "gerar relatório" como incluindo já aplicar as
  correções óbvias. Testei isso ao vivo no projeto 1: a skill imprimiu o relatório completo e
  parou exatamente no `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` antes de tocar
  em qualquer arquivo.
- **Transação e concorrência no fluxo de pedido/checkout.** O playbook não tinha, na primeira
  versão, um exemplo de "checar e debitar estoque no mesmo passo" — só "envolva em transação". Sem
  isso, uma implementação ingênua ainda permitiria duas requisições concorrentes venderem o mesmo
  estoque entre a validação e o débito. Adicionei ao T5/T7 o padrão
  `UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?` checando `rowcount`, usado
  de fato na refatoração do projeto 1 (pedidos) e do projeto 2 (matrícula/pagamento/auditoria).
- **Projeto 3 sendo "parcialmente organizado" sem estar correto.** A tentação natural seria a
  skill concluir "já tem `models/`/`routes/`, está OK" e não encontrar findings suficientes. O
  catálogo teve que ser explícito sobre smells que só aparecem em código já em camadas (model
  anêmico, service órfão nunca importado, lógica de negócio ainda presa nas rotas apesar de
  existir uma pasta de models) — foi o que permitiu a Fase 2 achar 18 findings no projeto 3 mesmo
  com a estrutura de pastas já parecendo razoável à primeira vista.
- **Ambiente sem as dependências instaladas.** Nenhum dos três projetos tinha `node_modules`/venv
  prontos neste ambiente; a validação da Fase 3 exigiu `npm install`/criar venv +
  `pip install -r requirements.txt` antes de poder rodar o boot real. Documentei isso como parte
  do "Como Executar" abaixo em vez de assumir que a validação passaria sem checar.

## Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | Arquivos (antes) | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python/Flask | 4 | 7 | 5 | 5 | 4 | **21** |
| 2 — ecommerce-api-legacy | Node/Express | 3 | 5 | 6 | 3 | 4 | **18** |
| 3 — task-manager-api | Python/Flask (parcial) | 15 | 4 | 1 | 8 | 5 | **18** |

Os três batem o critério de aceite (≥5 findings, ≥1 CRITICAL/HIGH) com folga. Vale notar o
perfil diferente do projeto 3: menos CRITICAL de arquitetura (já tinha camadas) e mais MEDIUM —
exatamente o padrão esperado para um projeto "parcialmente organizado" descrito no enunciado.

### Antes / depois da estrutura

**Projeto 1 — code-smells-project**
```
Antes (4 arquivos, monólito)          Depois (MVC completo)
app.py       (rotas + 2 endpoints     src/
             admin com SQL inline)      config/ (settings, database, seed, logging)
controllers.py (292 linhas,             models/ (produto, usuario, pedido)
             validação + orquestração)  controllers/ (produto, usuario, pedido, relatorio, health)
models.py    (314 linhas, SQL cru       views/ (produto, usuario, pedido, relatorio, system routes)
             de 4 domínios)             services/ (notification)
database.py  (conexão global)           middlewares/ (error_handler)
                                       app.py (composition root)
                                     app.py (entry point, raiz)
```
`/admin/query` e `/admin/reset-db` foram removidos (endpoints destrutivos sem autenticação).

**Projeto 2 — ecommerce-api-legacy**
```
Antes (3 arquivos)                    Depois (MVC completo)
src/app.js                            src/
src/AppManager.js (141 linhas: schema,   config/settings.js
  rotas, checkout, pagamento, SQL)       db/ (connection, schema, seed)
src/utils.js (config hardcoded,          models/ (User, Course, Enrollment, Payment, AuditLog, Report)
  badCrypto, cache global)               controllers/ (checkout, financialReport, user)
                                         routes/ (checkout, financialReport, users, index)
                                         services/ (password, payment, logger)
                                         middlewares/ (asyncHandler, errorHandler, requireAdmin)
```
`badCrypto` foi substituído por `bcryptjs`; `financial-report` e `DELETE /users/:id` passaram a
exigir `x-admin-key` (antes eram públicos).

**Projeto 3 — task-manager-api**
```
Antes (camadas parciais, regra ainda presa nas rotas)   Depois (camadas completas)
app.py, database.py, seed.py                            app.py, database.py, seed.py
models/ (task, user, category)                          config/ (settings)
routes/ (task, user, report — + CRUD de categoria        controllers/ (task, user, category, report) [novo]
  misturado dentro de report_routes.py)                  models/ (task, user, category — com to_dict sem senha)
services/ (notification, nunca conectado)                routes/ (task, user, category, report — finas)
utils/ (helpers com constantes nunca importadas)          middlewares/ (error_handler) [novo]
                                                          services/ (notification, agora conectado)
```
Aqui a Fase 3 **não recriou** `models/`/`routes/`/`services/`/`utils/` — introduziu a camada que
faltava (`controllers/`), moveu a lógica de relatório para lá, conectou o `NotificationService`
órfão e separou o CRUD de categorias em seu próprio módulo.

### Checklist de validação

Preenchido para os três projetos (validação executada de fato: boot real + requisições via
`curl`, não inspeção estática).

**Projeto 1 — code-smells-project**
```
### Fase 1 — Análise
[x] Linguagem detectada corretamente (Python 3.13)
[x] Framework detectado corretamente (Flask 3.1.1)
[x] Domínio descrito corretamente (E-commerce: produtos, usuários, pedidos)
[x] Número de arquivos condiz com a realidade (4 files analyzed)

### Fase 2 — Auditoria
[x] Relatório segue o template
[x] Cada finding tem arquivo e linhas exatos
[x] Findings ordenados por severidade
[x] Mínimo de 5 findings (21 encontrados)
[x] Detecção de APIs deprecated incluída
[x] Skill pausou e pediu confirmação [y/n] antes de qualquer alteração

### Fase 3 — Refatoração
[x] Estrutura MVC (config/models/controllers/views/services/middlewares)
[x] Config sem hardcoded (SECRET_KEY via env, falha o boot se ausente fora de DEBUG)
[x] Models abstraindo dados (queries parametrizadas, fim do SQL Injection)
[x] Views/Routes finas (Blueprints por domínio)
[x] Controllers concentram o fluxo
[x] Error handling centralizado (@app.errorhandler)
[x] Entry point claro (app.py → src/app.py:create_app)
[x] Aplicação inicia sem erros (venv + pip install + python app.py)
[x] Endpoints originais respondem (17 endpoints testados via curl)
```

**Projeto 2 — ecommerce-api-legacy**
```
### Fase 1 — Análise
[x] Linguagem detectada corretamente (JavaScript/Node.js)
[x] Framework detectado corretamente (Express ^4.18.2)
[x] Domínio descrito corretamente (LMS com checkout: cursos, matrículas, pagamentos)
[x] Número de arquivos condiz com a realidade (3 files analyzed)

### Fase 2 — Auditoria
[x] Relatório segue o template
[x] Cada finding tem arquivo e linhas exatos
[x] Findings ordenados por severidade
[x] Mínimo de 5 findings (18 encontrados)
[x] Detecção de APIs deprecated incluída (sqlite3 callback puro)
[x] Skill pausou e pediu confirmação antes de qualquer alteração

### Fase 3 — Refatoração
[x] Estrutura MVC (config/db/models/controllers/routes/services/middlewares)
[x] Config sem hardcoded (dbPass, chave de pagamento e ADMIN_API_KEY via .env)
[x] Models abstraindo dados (User, Course, Enrollment, Payment, AuditLog)
[x] Views/Routes finas (routers por domínio)
[x] Controllers concentram o fluxo (checkout, financialReport, user)
[x] Error handling centralizado (errorHandler + asyncHandler)
[x] Entry point claro (src/app.js monta tudo)
[x] Aplicação inicia sem erros (npm install + node src/app.js)
[x] Endpoints originais respondem (checkout, financial-report, delete de usuário testados)
```

**Projeto 3 — task-manager-api**
```
### Fase 1 — Análise
[x] Linguagem detectada corretamente (Python 3 + Flask 3.0.0/SQLAlchemy 3.1.1)
[x] Framework detectado corretamente
[x] Domínio descrito corretamente (Task Manager: tasks, categorias, usuários)
[x] Número de arquivos condiz com a realidade (15 files analyzed)

### Fase 2 — Auditoria
[x] Relatório segue o template
[x] Cada finding tem arquivo e linhas exatos
[x] Findings ordenados por severidade
[x] Mínimo de 5 findings (18 encontrados, mesmo já tendo camadas parciais)
[x] Detecção de APIs deprecated incluída (datetime.utcnow(), Model.query.get(id))
[x] Skill pausou e pediu confirmação antes de qualquer alteração

### Fase 3 — Refatoração
[x] Estrutura MVC melhorada, não recriada (controllers/ adicionado; models/routes/services/utils reaproveitados)
[x] Config sem hardcoded (SECRET_KEY e credenciais SMTP via env)
[x] Models abstraindo dados (User.to_dict() sem mais o campo password)
[x] Views/Routes finas (regra de relatório movida para controllers/report_controller.py)
[x] Controllers concentram o fluxo (task, user, category, report)
[x] Error handling centralizado (middlewares/error_handler.py)
[x] Entry point claro (app.py)
[x] Aplicação inicia sem erros (venv + pip install + python app.py)
[x] Endpoints originais respondem (tasks, users, login, categories, reports testados)
```

### Logs das aplicações rodando após a refatoração

Capturados ao vivo durante a validação (boot real + `curl`), não simulados.

**Projeto 1 — code-smells-project**
```
$ python app.py
2026-09-10 20:21:03 INFO loja | seed: usuários de exemplo criados com a senha de SEED_SENHA_PADRAO
2026-09-10 20:21:03 INFO loja | aplicacao.montada debug=True banco=loja.db
 * Serving Flask app 'src.app'
 * Running on http://127.0.0.1:5055

$ curl http://127.0.0.1:5055/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -X POST http://127.0.0.1:5055/login -d '{"email":"' OR '1'='1","senha":"' OR '1'='1"}'
{"erro":"Email ou senha inválidos","sucesso":false}   # [401] — SQL Injection não funciona mais

$ curl -X POST http://127.0.0.1:5055/admin/query -d '{"sql":"SELECT * FROM usuarios"}'
{"erro":"The requested URL was not found on the server...","sucesso":false}   # [404] — rota removida

$ curl -X POST http://127.0.0.1:5055/pedidos -d '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":1},{"produto_id":6,"quantidade":999}]}'
{"erro":"Estoque insuficiente para Cadeira Gamer","sucesso":false}   # [400] — rollback: estoque e contagem de pedidos ficam intactos
```

**Projeto 2 — ecommerce-api-legacy**
```
$ node src/app.js
{"level":"info","message":"server.started","meta":{"port":3000}}

$ curl -X POST http://localhost:3000/api/checkout -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}   # [200]

$ curl http://localhost:3000/api/admin/financial-report
{"error":"Não autorizado"}   # [401] — antes era público

$ curl http://localhost:3000/api/admin/financial-report -H "x-admin-key: $ADMIN_KEY"
[{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}, ...]   # [200]

$ curl -X DELETE http://localhost:3000/api/users/999 -H "x-admin-key: $ADMIN_KEY"
Usuário e registros dependentes (matrículas e pagamentos) removidos.   # [200] — sem mais órfãos
```

**Projeto 3 — task-manager-api**
```
$ python app.py
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5066

$ curl http://127.0.0.1:5066/users
[{"active":true,"email":"joao@email.com","id":1,"name":"João Silva","role":"admin", ...}]
# nenhum campo "password" na resposta

$ curl -X POST http://127.0.0.1:5066/login -d '{"email":"joao@email.com","password":"1234"}'
{"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxfQ...","user":{...}}   # [200] — token real, não mais "fake-jwt-token-1"

$ curl -X PUT http://127.0.0.1:5066/tasks/1 -d '{"title":"a","priority":99}'
{"error":"Título deve ter entre 3 e 200 caracteres"}   # [400]

$ curl http://127.0.0.1:5066/reports/summary
{"overview":{"total_categories":6,"total_tasks":11,"total_users":5}, "overdue":{"count":1,...}, ...}   # [200]
```

### Comportamento nas três stacks

A mesma pasta `refactor-arch/`, sem edição, produziu resultado correto nos três casos, mas com
intensidade de mudança proporcional ao estado inicial — exatamente o que o princípio "adapte-se ao
ponto de partida" pretendia gerar: reconstrução total no projeto 1 (monólito), reconstrução total
também no projeto 2 (God Class equivalente ao monólito em outra stack) e uma refatoração
incremental no projeto 3, que preservou nomes e módulos que já faziam sentido.

Mudanças de comportamento intencionais (documentadas nos READMEs de cada projeto), todas
correções de findings CRITICAL: rotas administrativas destrutivas removidas ou protegidas por
chave, senhas passam a ser hasheadas (bancos antigos com senha em texto puro deixam de
autenticar), e nenhuma resposta de API volta a expor senha, hash de senha ou segredo de
configuração.

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado e autenticado.
- Runtime de cada stack: Python 3.11+ (projetos 1 e 3) e Node.js 18+ (projeto 2).

### Rodar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask
cd code-smells-project
claude "/refactor-arch"
# Fase 2 imprime o relatório e pede: Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
# responda "y" para prosseguir com a Fase 3

# Projeto 2 — Node.js/Express (a pasta da skill já foi copiada para dentro do projeto)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — Python/Flask com camadas parciais (skill também copiada)
cd ../task-manager-api
claude "/refactor-arch"
```

Rode sempre a partir da raiz de cada projeto (onde fica `.claude/`), em modo interativo — a Fase 2
depende de responder `[y/n]` no terminal.

### Como validar que a refatoração funcionou

**Projeto 1 e 3 (Python/Flask):**
```bash
cd code-smells-project   # ou task-manager-api
python -m venv .venv && .venv/Scripts/activate   # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha SECRET_KEY (obrigatória fora de DEBUG=true)
python app.py
```
Em outro terminal, confira o boot e alguns endpoints:
```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/produtos          # projeto 1
curl http://127.0.0.1:5000/tasks             # projeto 3
```

**Projeto 2 (Node.js/Express):**
```bash
cd ecommerce-api-legacy
npm install
cp .env.example .env   # preencha DB_PASS, PAYMENT_GATEWAY_KEY, ADMIN_API_KEY
npm start
```
```bash
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Teste","eml":"teste@teste.com","pwd":"1234","c_id":1,"card":"4111222233334444"}'
```
Ou use as requisições prontas em `ecommerce-api-legacy/api.http`.

Em todos os casos, um boot sem stack trace + respostas 200/201 nos endpoints principais confirma
o checklist de validação da Fase 3.

