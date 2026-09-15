================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express ^4.18.2
Files:   3 analyzed | ~181 lines of code

## Summary
CRITICAL: 5 | HIGH: 6 | MEDIUM: 3 | LOW: 4

## Findings

### [CRITICAL] Credenciais / segredos hardcoded
File: src/utils.js:1-7
Description: O objeto `config` guarda `dbPass: "senha_super_secreta_prod_123"` e `paymentGatewayKey: "pk_live_1234567890abcdef"` como literais no código-fonte, versionados junto com a aplicação.
Impact: Qualquer pessoa com acesso ao repositório tem a chave de produção do gateway de pagamento e a senha de banco; não há como rotacionar o segredo sem reeditar código.
Recommendation: Mover todos os segredos para variáveis de ambiente (`process.env.PAYMENT_GATEWAY_KEY`, etc.), lidas por um módulo de config dedicado, com `.env` fora do versionamento.

### [CRITICAL] Hashing de senha quebrado (crypto caseira)
File: src/utils.js:17-23 (uso em src/AppManager.js:68)
Description: `badCrypto` não é um hash — repete a codificação Base64 da senha 10.000 vezes e corta o resultado em 10 caracteres, um algoritmo reversível e de baixíssima entropia usado para "proteger" a senha do usuário.
Impact: Senhas armazenadas ficam trivialmente recuperáveis; um vazamento do banco expõe as senhas reais de todos os usuários.
Recommendation: Substituir por `bcrypt`/`argon2` no Model de usuário, com salt automático e custo configurável, no momento da criação/atualização do usuário.

### [CRITICAL] God Class
File: src/AppManager.js:1-141
Description: A classe `AppManager` concentra a criação do schema e seed do banco (`initDb`), o roteamento HTTP (`setupRoutes`), a orquestração de pagamento/matrícula e o acesso a dados via SQL inline — tudo em um único arquivo/classe.
Impact: Não há como testar regra de negócio isoladamente do Express ou do SQLite; qualquer alteração em uma rota arrisca quebrar as outras, e o arquivo tende a crescer indefinidamente.
Recommendation: Quebrar em Models (users, courses, enrollments, payments), Controllers (checkout, financial-report, users) e Routes finas, conforme `mvc-architecture.md`.

### [CRITICAL] Endpoint destrutivo sem autenticação
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga qualquer usuário pelo `id` da URL sem nenhuma verificação de autenticação, autorização ou identidade de quem chama.
Impact: Qualquer chamador não autenticado pode apagar qualquer conta do sistema, incluindo contas de outros usuários.
Recommendation: Adicionar middleware de autenticação/autorização antes do handler e validar que o solicitante tem permissão sobre o recurso (dono da conta ou admin).

### [CRITICAL] Exposição de dados sensíveis em log
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão de crédito recebido no request junto com a chave secreta do gateway de pagamento em texto puro no log.
Impact: Qualquer pessoa com acesso aos logs (arquivo, stdout, agregador de logs) obtém dados de cartão (violação de PCI-DSS) e a chave de produção do gateway.
Recommendation: Nunca logar PAN de cartão nem segredos; se necessário, logar apenas um identificador não sensível (últimos 4 dígitos) através de um logger estruturado, nunca a chave de config.

### [HIGH] Regra de negócio no Controller/Rota (fat controller) — checkout
File: src/AppManager.js:28-78
Description: O handler de `POST /api/checkout` faz validação de entrada, busca de curso, busca/criação de usuário, hashing de senha, decisão de aprovação de pagamento e gravação de matrícula/pagamento/auditoria, tudo dentro do callback da rota.
Impact: A regra de checkout não é reutilizável fora do HTTP nem testável sem subir o Express; qualquer mudança de regra de negócio exige mexer no roteamento.
Recommendation: Extrair a orquestração para um `CheckoutController`/`CheckoutService` que chama Models de `User`, `Course`, `Enrollment` e `Payment`; a rota deve só receber o request e delegar.

### [HIGH] Regra de negócio no Controller/Rota (fat controller) — financial-report
File: src/AppManager.js:80-129
Description: O handler de `GET /api/admin/financial-report` monta manualmente a agregação de receita por curso, iterando e somando pagamentos dentro do próprio callback de rota, com contadores (`coursesPending`, `enrPending`) para saber quando finalizar a resposta.
Impact: A lógica de relatório fica acoplada ao ciclo de vida do request/response, impossível de reutilizar (ex.: gerar o mesmo relatório via job agendado) ou testar sem mocks de Express.
Recommendation: Mover a agregação para um `ReportService`/Model que retorna os dados já calculados; o Controller apenas chama o serviço e serializa a resposta.

### [HIGH] Estado global mutável
File: src/utils.js:9-10
Description: `globalCache = {}` e `totalRevenue = 0` são variáveis de módulo mutáveis, escritas em runtime por `logAndCache` durante o processamento de requests concorrentes.
Impact: Sem isolamento entre requests, há corrida de dados sob concorrência e comportamento dependente da ordem de chamadas; dificulta testes determinísticos.
Recommendation: Remover o cache global ad-hoc; se um cache for necessário, usar uma instância injetada (ex.: um serviço de cache) escopada corretamente, não uma variável de módulo compartilhada.

### [HIGH] Callback hell sem transação em operação multi-passo (checkout)
File: src/AppManager.js:50-63
Description: A sequência matrícula → pagamento → log de auditoria é feita com três `db.run` aninhados em callbacks, sem transação; se o segundo ou terceiro insert falhar, o primeiro já foi persistido.
Impact: Uma falha no meio do fluxo deixa o banco inconsistente (matrícula sem pagamento registrado, por exemplo) e o código é difícil de ler/manter.
Recommendation: Envolver os três inserts em uma transação (`BEGIN`/`COMMIT`/`ROLLBACK` ou equivalente via driver com Promises) dentro do Model/Service de checkout, com rollback automático em erro.

### [HIGH] Deleção deixando registros órfãos
File: src/AppManager.js:131-137
Description: O próprio comentário da resposta admite o problema: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` — o DELETE remove só a linha de `users`, sem tratar `enrollments`/`payments` relacionados.
Impact: O banco acumula matrículas e pagamentos apontando para `user_id` inexistente, quebrando relatórios (como o financial-report) e integridade referencial.
Recommendation: Fazer a exclusão dentro de uma transação que também remove ou reatribui os registros dependentes (ou usar `ON DELETE CASCADE`/soft delete), centralizado no Model de `User`.

### [HIGH] Ausência de camada de acesso a dados
File: src/AppManager.js:12-137
Description: Todo `CREATE TABLE`, `INSERT`, `SELECT`, `DELETE` do sistema está espalhado dentro de `initDb`/`setupRoutes`; não existe nenhum Model que encapsule o acesso a `users`, `courses`, `enrollments` ou `payments`.
Impact: A mesma query (ex.: buscar curso ativo) pode ser reescrita de formas diferentes em pontos diferentes com o tempo; não há ponto único de verdade para persistência.
Recommendation: Criar Models por entidade (`User`, `Course`, `Enrollment`, `Payment`) com métodos parametrizados, e fazer Controllers/Services dependerem só dos Models.

### [MEDIUM] Query N+1 no relatório financeiro
File: src/AppManager.js:92-124
Description: Para cada curso, busca as matrículas; para cada matrícula, busca o usuário e o pagamento em queries separadas dentro de loops aninhados (`forEach` dentro de `forEach`).
Impact: O número de queries cresce como `O(cursos × matrículas)`; com poucos dados hoje, mas degrada rapidamente conforme a base cresce.
Recommendation: Substituir por `JOIN`s (courses ⋈ enrollments ⋈ users ⋈ payments) ou por buscas em lote com `IN (...)`, agregando em memória uma única vez.

### [MEDIUM] API deprecated: sqlite3 callback-based
File: src/AppManager.js (uso em todo o arquivo, ex.: linhas 12-16, 37, 50, 83); package.json:11
Description: O driver `sqlite3` é usado no estilo 100% callback (`db.run(sql, params, cb)`, `db.get(...)`, `db.all(...)`), gerando o pyramid of doom visto nas rotas de checkout e financial-report.
Impact: Fluxos sequenciais/transacionais ficam ilegíveis e propensos a erro (esquecer de tratar `err`, perder o encadeamento correto).
Recommendation: Migrar para uma API baseada em Promises (`sqlite` package sobre `sqlite3`, `better-sqlite3`, ou `util.promisify` dos métodos do driver) e usar `async/await` nos Models/Controllers.

### [MEDIUM] Ausência de autenticação/autorização em endpoint admin
File: src/AppManager.js:80
Description: `GET /api/admin/financial-report` está sob o prefixo `/admin` mas não verifica nenhuma credencial, token ou papel de usuário antes de expor receita e dados de alunos.
Impact: Qualquer chamador não autenticado consegue ler dados financeiros e de matrícula de todos os cursos.
Recommendation: Proteger rotas `/admin/*` com um middleware de autenticação + checagem de papel (role) antes do Controller.

### [LOW] `console.log` como logging
File: src/utils.js:13; src/AppManager.js:45
Description: Eventos de aplicação (cache, processamento de pagamento) são registrados via `console.log`, sem níveis (info/warn/error) nem destino configurável.
Impact: Não é possível filtrar por severidade nem redirecionar/desligar logs por ambiente; em produção isso vira ruído (além do já citado vazamento de dados sensíveis).
Recommendation: Adotar um logger (ex.: `pino`/`winston`) com níveis e formatação estruturada, plugado como dependência dos Services.

### [LOW] Nomenclatura críptica de variáveis
File: src/AppManager.js:29-33
Description: A entrada do checkout é desestruturada em `u`, `e`, `p`, `cid`, `cc` — nomes de uma ou duas letras para `usuário`, `email`, `senha`, `id do curso` e `cartão`.
Impact: Aumenta o esforço para entender o fluxo e o risco de trocar um parâmetro por outro em manutenções futuras.
Recommendation: Renomear para nomes de domínio (`username`, `email`, `password`, `courseId`, `cardNumber`) ao desestruturar `req.body`.

### [LOW] Magic strings/numbers
File: src/AppManager.js:15, 21, 46, 54, 108
Description: Status de pagamento são strings soltas repetidas (`'PAID'`, `'DENIED'`, `1`/`0` para `active`), e a aprovação do pagamento depende de um literal mágico (`cc.startsWith("4")`) sem nenhuma constante nomeada.
Impact: Divergência entre grafias/valores ao longo do tempo (ex.: um lugar usar `'Paid'`) e regra de aprovação obscura para quem lê o código pela primeira vez.
Recommendation: Extrair para constantes/enum (`PAYMENT_STATUS.PAID`, `PAYMENT_STATUS.DENIED`) e documentar a regra de simulação de aprovação no Service de pagamento.

### [LOW] Código morto
File: src/utils.js:10, 25
Description: `totalRevenue` é declarado, inicializado em `0` e exportado, mas nunca é incrementado ou lido em nenhum outro arquivo do projeto.
Impact: Ruído no módulo de config/utils e falsa impressão de que existe um acumulador de receita funcionando.
Recommendation: Remover `totalRevenue`; se um total de receita for necessário, calculá-lo sob demanda a partir do Model de `Payment`.

================================
Total: 18 findings
================================
