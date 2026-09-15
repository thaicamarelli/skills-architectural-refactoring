================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 7 | HIGH: 5 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] SQL Injection
File: models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-166, 174, 188, 192, 220, 224, 279-281, 289-297
Description: Todas as 14 funções de acesso a dados montam SQL por concatenação de string. Casos mais graves: login_usuario concatena email e senha direto no WHERE (models.py:109-111), buscar_produtos monta o LIKE com o termo do usuário (models.py:291) e criar_produto/criar_usuario interpolam texto livre no INSERT (models.py:47-50, 126-129). Nenhuma query usa placeholders "?".
Impact: POST /login com {"email": "' OR '1'='1", "senha": "' OR '1'='1"} autentica como qualquer usuário; GET /produtos/busca?q=%'; DROP TABLE produtos;-- destrói o banco. Acesso total de leitura e escrita para qualquer chamador anônimo.
Recommendation: Mover o acesso a dados para Models por domínio e usar exclusivamente queries parametrizadas (cursor.execute("... WHERE id = ?", (id,))), inclusive na busca dinâmica.

### [CRITICAL] Endpoint perigoso / execução arbitrária
File: app.py:59-78
Description: A rota POST /admin/query recebe uma string SQL no corpo do request e a executa sem autenticação, sem allowlist e sem restrição de comando (cursor.execute(query), linha 69), commitando quando não é SELECT.
Impact: Qualquer pessoa na rede executa DROP TABLE, lê a tabela usuarios inteira com as senhas ou altera preços e pedidos. É RCE sobre o banco exposto via HTTP.
Recommendation: Remover a rota por completo. Necessidades administrativas legítimas viram endpoints específicos e parametrizados, protegidos por autenticação.

### [CRITICAL] Endpoint perigoso / operação destrutiva sem autenticação
File: app.py:47-57
Description: POST /admin/reset-db apaga itens_pedido, pedidos, produtos e usuarios (linhas 51-54) com quatro DELETEs sem WHERE, sem verificação de identidade ou de ambiente, com SQL escrito dentro do handler da rota.
Impact: Uma única requisição anônima zera a base — perda total e irreversível de dados.
Recommendation: Remover a rota do runtime. Se o reset é útil em desenvolvimento, movê-lo para um script CLI de seed, fora das rotas HTTP.

### [CRITICAL] Credenciais / segredos hardcoded
File: app.py:7-8, database.py:75-79
Description: SECRET_KEY fixada como "minha-chave-super-secreta-123" (app.py:7) e seed gravando um admin com senha "admin123" (database.py:76), além de "123456" e "senha123".
Impact: A chave está versionada no Git — quem tem o repositório forja sessões/tokens assinados. As credenciais de admin são públicas e idênticas em toda instalação.
Recommendation: Extrair para um módulo config/ que lê de variáveis de ambiente, com .env.example documentando as chaves e falha explícita no boot se SECRET_KEY não estiver definida fora de desenvolvimento.

### [CRITICAL] Segredo exposto na resposta da API
File: controllers.py:276-290
Description: O /health devolve no JSON "secret_key": "minha-chave-super-secreta-123" (linha 289), além de "debug": True, "db_path": "loja.db" e "ambiente": "producao" — valores fixos escritos à mão, não lidos da config real.
Impact: A chave secreta vaza para qualquer cliente que chame um endpoint público de health check, incluindo bots e monitoramento externo.
Recommendation: Reduzir o /health a liveness e conectividade do banco. Nenhum segredo, caminho de arquivo ou flag de configuração na resposta.

### [CRITICAL] Senhas em texto puro (sem hashing)
File: models.py:105-120, 122-131, database.py:75-83
Description: criar_usuario grava a senha crua no INSERT (models.py:126-129) e login_usuario autentica comparando a senha em texto dentro do próprio SQL (109-111). get_todos_usuarios e get_usuario_por_id ainda incluem a coluna senha no dicionário retornado (linhas 84 e 99), que vai direto para a resposta de GET /usuarios.
Impact: GET /usuarios expõe as senhas de todos os usuários sem autenticação; um vazamento do arquivo loja.db entrega todas as credenciais em claro.
Recommendation: Hashear com werkzeug.security.generate_password_hash na criação e validar com check_password_hash no login (sem senha no SQL). Remover o campo senha de toda serialização. MUDANÇA DE COMPORTAMENTO: senhas já existentes no banco deixam de funcionar e o seed passa a gravar hashes.

### [CRITICAL] God Class / God Module
File: models.py:1-314
Description: Um módulo de 314 linhas concentra acesso a dados, regra de negócio e formatação de resposta para quatro domínios: produtos (4-70), usuários e autenticação (72-131), pedidos com cálculo de total e baixa de estoque (133-233) e relatório de vendas com regra de desconto (235-273).
Impact: Impossível testar um domínio em isolamento; qualquer alteração em pedidos toca o mesmo arquivo que produtos e autenticação. Viola SRP e é a raiz da maioria dos outros achados.
Recommendation: Quebrar em Models por domínio (produto, usuario, pedido) responsáveis só por persistência, movendo cálculo de pedido, desconto e agregações do relatório para Controllers/Services.

### [HIGH] Regra de negócio no Controller (fat controller)
File: controllers.py:24-62, 64-96, 237-255
Description: criar_produto tem 30 linhas de validação e regra inline — faixas de preço/estoque, tamanho do nome e a lista de categorias válidas dentro do handler (linha 52). atualizar_produto repete o bloco (72-90) e atualizar_status_pedido embute a máquina de estados do pedido como lista literal (242) mais as reações a cada status (247-250).
Impact: As regras de domínio ficam presas ao ciclo request/response — não são reutilizáveis por um job ou CLI, e testá-las exige subir o Flask.
Recommendation: Mover validação e regras para os Models/Services (categorias e status como constantes de domínio); o Controller recebe o request, delega e traduz o resultado em resposta HTTP.

### [HIGH] Estado global mutável
File: database.py:4-11
Description: A conexão vive em variável de módulo (db_connection = None, linha 4), é escrita via global (linha 8) e criada com check_same_thread=False (linha 10) para ser compartilhada entre todas as threads do servidor.
Impact: Requisições concorrentes dividem um único cursor/transação — commits de uma request podem persistir escritas parciais de outra, com falhas não determinísticas sob carga. Também impede testes isolados.
Recommendation: Trocar pelo padrão de conexão por request (flask.g + teardown_appcontext) exposta por uma função de fábrica, sem variável global mutável.

### [HIGH] Efeitos colaterais / integrações embutidas no fluxo HTTP
File: controllers.py:208-210, 247-250
Description: Depois de criar o pedido, o controller "envia" e-mail, SMS e push via print (208-210); em atualizar_status_pedido, as notificações de aprovação e cancelamento também são print dentro do handler (247-250).
Impact: A integração não pode ser trocada, desativada nem mockada, e um dia vira I/O real bloqueando a resposta HTTP. O texto "Devolver estoque" na linha 250 revela uma regra de negócio que nunca é executada.
Recommendation: Criar services/notification_service.py com interface única (notificar_pedido_criado, notificar_status), chamada pelo Controller, usando logger em vez de print.

### [HIGH] Ausência de camada de acesso a dados
File: app.py:49-55, 66-76, controllers.py:266-274
Description: Apesar de existir models.py, há SQL na camada HTTP: os DELETEs de /admin/reset-db (app.py:51-54), o execute arbitrário de /admin/query (app.py:69) e os quatro SELECT COUNT(*) do health check dentro do controller (controllers.py:268-274).
Impact: Não existe ponto único de verdade para persistência — mudanças de schema exigem caçar SQL em três arquivos de camadas diferentes.
Recommendation: Todo acesso ao banco passa pelos Models. O health check chama um método de Model (ping/contagens) em vez de abrir cursor próprio.

### [HIGH] Falta de transação em operação multi-passo
File: models.py:133-169
Description: criar_pedido insere o pedido (148-151), depois insere item e atualiza estoque por item (157-166), commitando só no final (168) — sem rollback explícito e sem tratamento de falha. Valida estoque num primeiro laço (139-146) e debita num segundo, e devolve erro de negócio como dicionário {"erro": ...} (143, 145) em vez de exceção.
Impact: Uma exceção no meio do segundo laço deixa pedido criado com itens faltando e estoque parcialmente debitado. Entre validação e débito, duas requisições concorrentes vendem o mesmo estoque (estoque negativo).
Recommendation: Envolver a operação em transação com try/except + rollback, unificar validação e débito num único passo (UPDATE ... SET estoque = estoque - ? WHERE id = ? AND estoque >= ?, checando rowcount) e sinalizar erro de negócio com exceção de domínio tratada pelo handler central.

### [MEDIUM] Query N+1
File: models.py:171-201, 203-233
Description: get_pedidos_usuario e get_todos_pedidos percorrem os pedidos e, para cada um, abrem cursor novo para buscar os itens (187-189 e 219-221) e, para cada item, mais um cursor para buscar o nome do produto (191-193 e 223-225).
Impact: GET /pedidos com 50 pedidos de 3 itens dispara ~200 queries. O custo cresce com pedidos × itens.
Recommendation: Buscar itens e nomes com um único SELECT usando JOIN (itens_pedido JOIN produtos) filtrado por pedido_id IN (...), agrupando em memória.

### [MEDIUM] Validação ausente ou duplicada
File: controllers.py:28-54, 72-90, 146-165, 188-201
Description: O bloco de validação de produto está copiado quase idêntico em criar_produto (28-54) e atualizar_produto (72-90), mas já divergiu: a atualização não valida tamanho do nome nem categoria. Em contrapartida, criar_usuario (153-158) não valida formato de e-mail, força de senha nem duplicidade, e criar_pedido (195-201) não valida o formato dos itens — models.criar_pedido acessa item["produto_id"] sem checar, gerando 500 em vez de 400.
Impact: As duas cópias já se comportam diferente para a mesma entidade, e entradas malformadas viram erro 500 com stack interna em vez de resposta de validação.
Recommendation: Centralizar a validação por entidade em um único validador/método de Model reutilizado por criar e atualizar, e validar a estrutura dos itens antes de chamar o Model.

### [MEDIUM] Tratamento de erro que engole exceções
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Description: As 16 funções do controller repetem o mesmo except Exception as e: return jsonify({"erro": str(e)}), 500, devolvendo a mensagem interna ao cliente e registrando (quando registra) via print. Não há handler central nem distinção entre erro de negócio e falha inesperada.
Impact: Detalhes internos (nomes de tabela, SQL, caminhos) vazam na resposta; a causa raiz não fica em log estruturado; erro de validação vindo do Model é classificado como 500.
Recommendation: Registrar error handlers centrais (@app.errorhandler) com resposta padronizada, criar exceções de domínio (NotFound, ValidationError) e remover os try/except repetidos dos controllers.

### [MEDIUM] Configuração acoplada / debug ligado em produção
File: app.py:8, 88, database.py:5
Description: app.config["DEBUG"] = True (app.py:8) e app.run(host="0.0.0.0", port=5000, debug=True) (linha 88) fixam o modo debug no código; host, porta e o caminho do banco (db_path = "loja.db", database.py:5) também são literais. CORS(app) (app.py:9) libera qualquer origem.
Impact: Com debug=True o Werkzeug expõe o console interativo — execução remota de Python em qualquer host que consiga acionar uma exceção. Nada disso é ajustável por ambiente sem editar código.
Recommendation: Concentrar em config/settings.py lendo de env (DEBUG, HOST, PORT, DATABASE_PATH, CORS_ORIGINS) com default seguro (DEBUG=False) e origens de CORS explícitas.

### [MEDIUM] API Deprecated / padrão obsoleto
File: database.py:7-11, models.py:105-131
Description: Duas ocorrências. (1) A conexão SQLite global compartilhada com check_same_thread=False (database.py:10) é o padrão legado desencorajado no Flask — o equivalente moderno é conexão por request em flask.g com teardown_appcontext. (2) A autenticação compara senha em texto (models.py:109-111) enquanto a stack já traz werkzeug.security (dependência obrigatória do Flask): o equivalente moderno é generate_password_hash/check_password_hash. A varredura por APIs removidas/deprecated do Python 3.12+ (datetime.utcnow, from collections import Mapping, imp, adaptadores default de data do sqlite3) e do Flask 3 (before_first_request, flask.escape, flask.Markup) não encontrou ocorrências neste projeto.
Impact: O padrão de conexão global impede rodar sob servidor multi-thread/multi-worker com segurança; a auth caseira é o vetor dos achados CRITICAL de senha.
Recommendation: Migrar a conexão para o ciclo de vida do app context e substituir a comparação de senha pelas funções de werkzeug.security.

### [LOW] print como logging
File: app.py:56, 83-86, controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
Description: 19 chamadas de print fazem o papel de log — rastreio de execução ("Listando N produtos"), erros ("ERRO CRITICO ao criar pedido"), eventos de negócio e as notificações simuladas. Nenhum logger é configurado.
Impact: Sem níveis, timestamp ou destino configurável; erro e informação se misturam no stdout e somem em produção.
Recommendation: Configurar o logging padrão em config/ e trocar os print por logger.info/logger.error.

### [LOW] Magic numbers e strings soltas
File: models.py:256-262, controllers.py:47-52, 242
Description: As faixas de desconto do relatório usam limiares e percentuais anônimos (10000/0.1, 5000/0.05, 1000/0.02, models.py:257-262). No controller, len(nome) < 2 e > 200 (47-50), a lista de categorias válidas (52) e a lista de status de pedido (242) aparecem como literais no meio do fluxo.
Impact: A intenção das faixas não é explícita e alterá-las exige caçar números no meio da lógica, com risco de divergência.
Recommendation: Extrair para constantes nomeadas no domínio (FAIXAS_DESCONTO, CATEGORIAS_VALIDAS, STATUS_PEDIDO, NOME_MIN/NOME_MAX).

### [LOW] Imports não usados / código morto
File: models.py:2, database.py:2
Description: import sqlite3 em models.py:2 nunca é referenciado (o módulo só usa get_db()), e import os em database.py:2 também não é usado — ironicamente é a biblioteca que resolveria o db_path hardcoded logo abaixo.
Impact: Ruído que sugere dependências inexistentes e confunde sobre onde a conexão é criada.
Recommendation: Remover os imports órfãos durante a reorganização dos módulos.

### [LOW] Nomenclatura ruim / variáveis crípticas
File: models.py:187-193, 219-225, 24, 65, controllers.py:14, 98
Description: Cursores numerados sequencialmente (cursor2, cursor3) descrevem a ordem de criação, não o propósito; prod e row são genéricos; e o parâmetro id (models.py:24, 65; controllers.py:14, 98) sombreia a builtin id do Python em toda a cadeia de produtos e usuários.
Impact: Aumenta a carga cognitiva nos laços aninhados e mascara a builtin dentro dessas funções.
Recommendation: Renomear para o que o dado representa (cursor_itens, cursor_produto, produto, produto_id/usuario_id) ao mover o código para os Models por domínio.

================================
Total: 21 findings
================================
