================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1150 lines of code

## Summary
CRITICAL: 4 | HIGH: 1 | MEDIUM: 8 | LOW: 5

## Findings

### [CRITICAL] Credenciais hardcoded — SECRET_KEY
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está fixado no código-fonte em vez de vir de variável de ambiente, apesar de `python-dotenv` já estar nas dependências (requirements.txt:6) e não ser usado.
Impact: Qualquer pessoa com acesso ao repositório tem a chave usada para assinar sessão/tokens; não é possível rotacionar o segredo sem novo deploy nem diferenciar dev/produção.
Recommendation: Mover para um módulo de config que lê `os.environ['SECRET_KEY']` (via `python-dotenv` em dev), falhando o boot se ausente em produção.

### [CRITICAL] Credenciais hardcoded — SMTP
File: services/notification_service.py:7-10
Description: `email_host`, `email_port`, `email_user` e `email_password` (`'senha123'`) estão hardcoded no `__init__` de `NotificationService`.
Impact: Vazamento da senha de e-mail real do serviço no versionamento; qualquer alteração de credencial exige editar e redeployar código.
Recommendation: Externalizar para config/env (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`) injetada no serviço, nunca literal no arquivo.

### [CRITICAL] Hashing de senha quebrado (MD5 sem salt)
File: models/user.py:27-32
Description: `set_password`/`check_password` usam `hashlib.md5(pwd.encode()).hexdigest()` — MD5 é criptograficamente quebrado, sem salt, e permite ataques de rainbow table/força bruta em massa.
Impact: Vazamento do banco (`tasks.db`) expõe todas as senhas dos usuários com esforço computacional mínimo para reverter.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já disponível via Flask) ou `bcrypt`/`argon2`, com salt automático.

### [CRITICAL] Senha exposta nas respostas da API
File: models/user.py:16-25 (to_dict), usado em routes/user_routes.py:86, 129, 209
Description: `User.to_dict()` inclui o campo `password` (o hash) e é devolvido diretamente em `create_user`, `update_user` e `login` — inclusive o campo `token` do login é uma string fixa `'fake-jwt-token-' + str(user.id)`, sem autenticação real.
Impact: O hash da senha de todo usuário trafega em toda resposta de criação/atualização/login, facilitando ataques offline; o "token" é previsível e forjável por qualquer chamador que saiba o `user_id`.
Recommendation: Remover `password` de `to_dict()` (ou criar um `to_public_dict()` sem esse campo) e substituir o token fake por um mecanismo real (JWT assinado com a `SECRET_KEY` vinda de config, ou `flask-jwt-extended`).

### [HIGH] Fat Controller — geração de relatório dentro das rotas
File: routes/report_routes.py:12-155
Description: `summary_report` (12-101) e `user_report` (103-155) calculam contagens por status/prioridade, detectam atraso iterando `Task.query.all()` em Python e computam produtividade por usuário — tudo dentro do handler HTTP, sem passar por Model/Service.
Impact: Lógica de relatório não é reutilizável nem testável isoladamente do Flask; qualquer mudança de regra de negócio exige mexer na camada de transporte HTTP.
Recommendation: Extrair para um `ReportService`/método de Model (`Task.get_summary()`, `Task.get_user_report(user_id)`) que a rota apenas chama e serializa.

### [MEDIUM] Query N+1
File: routes/task_routes.py:41-57 (get_tasks); routes/report_routes.py:53-68 (user_stats)
Description: `get_tasks` busca `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do laço de cada task; `summary_report` busca `Task.query.filter_by(user_id=u.id)` dentro do laço de cada usuário.
Impact: O número de queries cresce linearmente com tasks/usuários, degradando performance conforme a base cresce.
Recommendation: Usar `joinedload`/`selectinload` do SQLAlchemy ou uma única query com `IN (...)` e montar o resultado em memória.

### [MEDIUM] Validação duplicada entre create e update, e helper morto
File: routes/task_routes.py:96-114 (create_task) vs 166-184 (update_task); utils/helpers.py:57-108 (process_task_data)
Description: As mesmas regras (`title` entre 3 e 200 chars, `status` em lista fixa, `priority` entre 1 e 5) estão copiadas em `create_task` e `update_task`. `utils/helpers.py` já tem `process_task_data` implementando essa validação de forma centralizada, mas a função nunca é importada/chamada em nenhuma rota.
Impact: As duas cópias podem divergir com o tempo (já divergem: `update_task` não trata `priority` não-inteira com try/except como `process_task_data` faz); o código morto confunde sobre qual é a validação "oficial".
Recommendation: Chamar `process_task_data` (movido para o Model/Service) a partir de `create_task` e `update_task`, eliminando a duplicação.

### [MEDIUM] Tratamento de erro que engole exceções
File: routes/task_routes.py:62; routes/report_routes.py:186, 207, 221; routes/user_routes.py:130, 149
Description: Vários blocos usam `except:` genérico (sem capturar/logar a exceção) para devolver um erro 500 padrão, escondendo a causa raiz.
Impact: Erros de banco, de tipo ou de integridade ficam indistinguíveis em produção; debugging depende de reproduzir manualmente.
Recommendation: Centralizar tratamento de erro em um error handler do Flask (`@app.errorhandler`), logando a exceção original e retornando resposta padronizada.

### [MEDIUM] Lógica de "overdue" duplicada em 4 lugares
File: routes/task_routes.py:30-39, 71-80; routes/report_routes.py:34-43, 132-135; routes/user_routes.py:171-180 (vs models/task.py:50-60)
Description: O cálculo "task está atrasada se tem due_date no passado e status não é done/cancelled" está reescrito manualmente em 5 pontos diferentes, apesar de `Task.is_overdue()` já existir no model e nunca ser chamado.
Impact: Qualquer ajuste na regra (ex.: adicionar um novo status terminal) precisa ser replicado em 5 lugares — alto risco de divergência silenciosa.
Recommendation: Remover as reimplementações e usar `task.is_overdue()` em todos os pontos.

### [MEDIUM] Configuração acoplada / debug ligado
File: app.py:11, 33
Description: `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'` está fixo no código e `app.run(debug=True, host='0.0.0.0', port=5000)` liga o modo debug do Flask incondicionalmente.
Impact: `debug=True` expõe o debugger interativo do Werkzeug (execução de código arbitrário) se exposto além de localhost, além de vazar stack traces; a URI do banco não pode variar por ambiente sem editar código.
Recommendation: Ler `DATABASE_URL` e `FLASK_DEBUG` de variáveis de ambiente/config, com `debug` desligado por padrão fora de desenvolvimento.

### [MEDIUM] Responsabilidade fora do módulo — CRUD de categorias em "reports"
File: routes/report_routes.py:157-223
Description: `get_categories`, `create_category`, `update_category` e `delete_category` (um CRUD completo de outro recurso) estão dentro de `report_routes.py`/`report_bp`, que deveria conter apenas leitura de relatórios.
Impact: Viola SRP a nível de módulo — quem procura o CRUD de categorias não vai olhar em "reports"; dificulta versionar/testar os dois recursos de forma independente.
Recommendation: Mover para um `category_routes.py`/`category_bp` próprio, registrado em `app.py` como os demais blueprints.

### [MEDIUM] API deprecated — `datetime.utcnow()`
File: models/task.py:15-16; models/category.py:11; models/user.py:14; routes/task_routes.py:31; routes/report_routes.py:35, 45, 50; routes/user_routes.py:172; seed.py:66-75 (o padrão se repete em praticamente todo uso de datas do projeto)
Description: `datetime.utcnow()` é usado como default de coluna e em comparações de data; a função está deprecated desde o Python 3.12 por retornar datetime "naive" (sem timezone).
Impact: Em runtimes mais novos o uso emite `DeprecationWarning` hoje e será removido futuramente; comparações entre naive e aware datetimes lançam `TypeError` se qualquer parte do código migrar para timezone-aware.
Recommendation: Trocar por `datetime.now(timezone.utc)` de forma consistente em models e rotas.

### [MEDIUM] API deprecated — `Model.query.get(id)`
File: routes/task_routes.py:67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213 (padrão repetido em todas as rotas que buscam por id)
Description: O projeto usa a API legada `Model.query.get(id)` do SQLAlchemy (estilo "legacy query"), desencorajada desde a 2.0.
Impact: Estilo legado será removido em versões futuras do SQLAlchemy; mistura mal com padrões 2.0 (`select()`/`db.session`) caso o projeto evolua.
Recommendation: Substituir por `db.session.get(Model, id)` em todos os pontos.

### [LOW] `print` como logging
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24
Description: Eventos de criação/atualização/erro são registrados com `print(...)` em vez de um logger configurável.
Impact: Sem níveis (info/error), sem destino configurável (arquivo/stdout estruturado), polui a saída padrão e não integra com observabilidade.
Recommendation: Usar `logging`/`app.logger` com níveis apropriados.

### [LOW] Camada de serviço não conectada (código morto)
File: services/notification_service.py:1-49
Description: `NotificationService` (envio de e-mail em `notify_task_assigned`/`notify_task_overdue`) existe mas nenhuma rota ou model a importa/instancia — não há nenhuma chamada a essa classe no projeto.
Impact: Funcionalidade aparentemente implementada (notificação de tasks) não funciona de fato; confunde quem lê a estrutura de pastas assumindo que notificações estão ativas.
Recommendation: Conectar o serviço no fluxo de `create_task`/atualização de status (chamado pelo Controller), ou remover se não fizer parte do escopo atual.

### [LOW] Imports não usados
File: app.py:7 (`os, sys, json`); routes/task_routes.py:7 (`json, os, sys, time`); routes/user_routes.py:6 (`hashlib, json`); routes/report_routes.py:8 (`json`); utils/helpers.py:3-7 (`os, json, sys, math, hashlib`)
Description: Vários imports não são referenciados em nenhum ponto dos respectivos arquivos.
Impact: Ruído que sugere dependências/uso que não existem de fato, dificultando entender o que o módulo realmente precisa.
Recommendation: Remover os imports não usados.

### [LOW] Magic numbers repetidos em vez das constantes já definidas
File: routes/task_routes.py:96, 99, 113-114, 182-183; routes/user_routes.py:64, 115 (vs utils/helpers.py:110-116)
Description: Limites como título entre 3 e 200, prioridade entre 1 e 5, senha mínima de 4 caracteres estão hardcoded diretamente nas rotas, apesar de `utils/helpers.py` já definir `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` etc. — constantes que nenhum outro arquivo importa.
Impact: Mudar uma regra de negócio (ex.: senha mínima) exige caçar todos os literais espalhados; as constantes existentes viram documentação morta.
Recommendation: Importar e usar as constantes de `utils/helpers.py` (ou movê-las para o Model/Service correspondente) em vez de repetir os literais.

### [LOW] Nomenclatura críptica em variáveis de laço
File: routes/report_routes.py:33, 55, 59; routes/task_routes.py:16, 268
Description: Variáveis de uma letra (`t` para task, `u` para user, `c`/`cat` para category) e agregados como `p1`..`p5` (report_routes.py:24-28) tornam o código menos legível sem contexto adicional.
Impact: Aumenta a carga cognitiva ao revisar/manter o código, especialmente em laços aninhados com múltiplas entidades.
Recommendation: Renomear para nomes de domínio (`task`, `user`, `category`, `count_by_priority[1]` etc.).

================================
Total: 18 findings
================================
