# Catálogo de Anti-Patterns (Fase 2)

Cada entrada traz: **sinais de detecção** (o que procurar, de forma acionável), **por que é um
problema**, e a **severidade**. Use os sinais literalmente ao varrer o código; registre cada
ocorrência com `arquivo:linha`.

## Escala de severidade

Baseada em violações de MVC e SOLID e em risco de segurança:

- **CRITICAL** — falha grave de arquitetura ou segurança: expõe dados sensíveis (credenciais
  hardcoded, SQL Injection, senha em texto puro) ou destrói a separação de responsabilidades
  (God Class com banco + regra + roteamento juntos).
- **HIGH** — forte violação de MVC/SOLID que trava manutenção e testes: regra de negócio pesada
  presa em controllers/rotas, acoplamento forte sem injeção de dependência, estado global mutável.
- **MEDIUM** — padronização, duplicação ou performance moderada: queries N+1, validação ausente,
  uso inadequado de middleware, tratamento de erro que engole exceções.
- **LOW** — legibilidade: nomes ruins, magic numbers, imports não usados, `print` como log.

Regra de ouro: se um único achado combina vários problemas (ex.: um arquivo que é God Module
**e** tem SQL Injection), registre-os separadamente — cada um tem sua severidade e correção.

---

## CRITICAL

### C1. Credenciais / segredos hardcoded
**Detecção:** literais de senha, chave ou token no código — `SECRET_KEY = "..."`, `dbPass`,
`paymentGatewayKey = "pk_live_..."`, `email_password = "..."`, strings como `"senha123"`,
`"admin123"`. Também segredos expostos em respostas de API (ex.: um `/health` que devolve a
`secret_key`).
**Por quê:** vaza para o versionamento e para clientes; qualquer um com o repo tem produção.
**Severidade:** CRITICAL.

### C2. SQL Injection (query montada por concatenação)
**Detecção:** SQL construído com `+`, f-string ou interpolação de variável vinda do usuário —
`"... WHERE id = " + str(id)`, `f"... LIKE '%{termo}%'"`, `"... email = '" + email + "'"`.
O oposto seguro são parâmetros: `execute("... WHERE id = ?", [id])`.
**Por quê:** permite ler/alterar/apagar o banco inteiro. Vale para qualquer stack com SQL cru.
**Severidade:** CRITICAL.

### C3. Endpoint perigoso / execução arbitrária
**Detecção:** rota que executa SQL arbitrário recebido no corpo (`/admin/query` que faz
`cursor.execute(request.json["sql"])`) ou faz operação destrutiva sem autenticação
(`/admin/reset-db` que apaga todas as tabelas).
**Por quê:** RCE sobre o banco / destruição de dados por qualquer chamador.
**Severidade:** CRITICAL.

### C4. Senhas em texto puro (sem hashing) ou hashing quebrado
**Detecção:** senha salva/comparada como texto (`INSERT ... senha ...` com o valor cru; login que
compara `senha = '<texto>'`); ou "cripto" caseira/insegura (loop de `base64`, MD5/SHA1 sem salt).
Também senha retornada em respostas (`SELECT * FROM usuarios` que devolve a coluna `senha`).
**Por quê:** vazamento do banco = vazamento de todas as senhas. Auth caseira é sempre furada.
**Severidade:** CRITICAL.

### C5. God Class / God Module
**Detecção:** um único arquivo/classe concentra acesso a dados **+** regra de negócio **+**
roteamento **+** config. Sinais: arquivo com centenas de linhas cobrindo vários domínios; uma
classe (`AppManager`) que cria o schema, registra rotas e processa pagamento; um `models.py` que
faz SQL, validação, cálculo e formatação para 4 entidades.
**Por quê:** impossível testar em isolamento; qualquer mudança arrisca quebrar tudo. Viola SRP.
**Severidade:** CRITICAL.

---

## HIGH

### H1. Regra de negócio no Controller/Rota (fat controller)
**Detecção:** handlers de rota que fazem mais do que orquestrar: cálculos de negócio, montagem de
SQL, regras de desconto, geração de relatório dentro do `def`/callback da rota. Sinal: dezenas de
linhas de lógica entre receber o request e devolver o response.
**Por quê:** a regra fica presa ao HTTP, não é reutilizável nem testável. Viola a separação MVC.
**Severidade:** HIGH.

### H2. Estado global mutável
**Detecção:** conexão de banco em variável global (`db_connection = None` + `global db_connection`),
caches/contadores globais (`globalCache = {}`, `totalRevenue = 0`) escritos em runtime.
**Por quê:** acoplamento oculto, condições de corrida, comportamento dependente de ordem; impede
paralelismo e testes isolados.
**Severidade:** HIGH.

### H3. Efeitos colaterais / integrações embutidas no fluxo HTTP
**Detecção:** envio de e-mail/SMS/push, chamada a gateway de pagamento ou logging de auditoria
feitos direto dentro do handler (às vezes via `print("ENVIANDO EMAIL...")`), sem uma camada de
serviço. Segredos e side effects misturados com a resposta.
**Por quê:** não dá para trocar/mockar a integração; a rota vira responsável por I/O externo.
Deve morar em uma camada de Service chamada pelo Controller.
**Severidade:** HIGH.

### H4. Ausência de camada de acesso a dados / model anêmico
**Detecção:** SQL/queries espalhados por rotas e controllers em vez de concentrados em Models;
ou um Model ORM que só tem colunas e nenhum comportamento, enquanto a lógica dele vive fora.
**Por quê:** duplicação de queries, sem ponto único de verdade para persistência.
**Severidade:** HIGH.

### H5. Callback hell / falta de transação em operação multi-passo
**Detecção:** callbacks aninhados em vários níveis para operações sequenciais no banco
(inserir matrícula → pagamento → auditoria); múltiplos `INSERT/UPDATE` relacionados sem
transação; deletar um registro deixando dependentes órfãos ("matrículas e pagamentos ficaram
sujos no banco").
**Por quê:** ilegível e, sem transação, o banco fica inconsistente se um passo falhar.
**Severidade:** HIGH.

---

## MEDIUM

### M1. Query N+1
**Detecção:** consulta dentro de laço — para cada linha da lista principal, dispara outra query
(ex.: `get_todos_pedidos` que, por pedido, busca itens e, por item, busca o nome do produto;
um relatório que por curso busca matrículas e por matrícula busca usuário e pagamento; listar
tasks e por task buscar `User.query.get()` e `Category.query.get()`).
**Por quê:** explode o número de queries e degrada a performance conforme os dados crescem.
**Correção típica:** JOIN, `IN (...)`, ou eager loading do ORM.
**Severidade:** MEDIUM.

### M2. Validação ausente ou duplicada
**Detecção:** rotas que aceitam entrada sem validar; ou o mesmo bloco de validação copiado em
vários handlers (criar vs atualizar com regras idênticas repetidas). Falta de sanitização.
**Por quê:** dados inválidos chegam ao banco; validação duplicada diverge com o tempo. Deve ser
centralizada (schema/validador ou método do Model).
**Severidade:** MEDIUM.

### M3. Tratamento de erro que engole exceções
**Detecção:** `except:`/`except Exception` que só retorna genérico ou faz `pass`; `try/except`
sem log útil; erro tratado de forma inconsistente rota a rota, sem handler central.
**Por quê:** esconde a causa raiz, dificulta o diagnóstico. Erros devem passar por um handler
central (middleware) com resposta padronizada.
**Severidade:** MEDIUM.

### M4. Lógica duplicada / código repetido (DRY)
**Detecção:** o mesmo cálculo em vários lugares (regra de "overdue" repetida em rotas, model e
relatório; `to_dict` reescrito à mão em cada handler). Blocos copiados entre arquivos.
**Por quê:** manutenção multiplicada e risco de divergência.
**Severidade:** MEDIUM (LOW se for trivial e isolado).

### M5. Configuração acoplada / debug ligado em produção
**Detecção:** `DEBUG = True`, `app.run(debug=True)`, `SQLALCHEMY_TRACK_MODIFICATIONS`, host/porta
e flags fixados no código em vez de virem de config/env.
**Por quê:** `debug=True` expõe stack traces e um console executável em produção; config fixa
impede promover o mesmo build entre ambientes.
**Severidade:** MEDIUM (a exposição de debug em produção pode ser HIGH conforme o contexto).

---

## LOW

### L1. `print` como logging
**Detecção:** `print(...)`/`console.log(...)` para rastrear execução, erros ou eventos.
**Por quê:** sem níveis, sem destino configurável, polui a saída. Use um logger.
**Severidade:** LOW.

### L2. Magic numbers e strings soltas
**Detecção:** números/limiares sem nome no meio da lógica (faixas de desconto `10000`, `5000`;
prioridade `1..5`; `len(nome) > 200`), status como strings repetidas.
**Por quê:** intenção obscura, difícil de ajustar com consistência. Extraia para constantes.
**Severidade:** LOW.

### L3. Nomenclatura ruim / variáveis crípticas
**Detecção:** nomes de uma letra para dados de domínio (`u`, `e`, `p`, `cid`, `cc`), abreviações
opacas, nomes que não dizem o que guardam.
**Por quê:** aumenta a carga cognitiva e o risco de erro.
**Severidade:** LOW.

### L4. Imports não usados / código morto
**Detecção:** imports que não são referenciados (`import os, sys, json, time` sem uso), funções
nunca chamadas, camadas presentes mas não conectadas (um `services/` que ninguém importa).
**Por quê:** ruído, sugere confusão sobre o que está ativo.
**Severidade:** LOW.

---

## APIs Deprecated (detecção obrigatória)

Aponte o uso obsoleto **e** o equivalente moderno. Classifique como MEDIUM por padrão (HIGH se a
API removida quebra em versões recentes da runtime, LOW se é só um aviso).

**Python**
- `datetime.utcnow()` / `datetime.utcfromtimestamp()` — deprecated no Python 3.12+.
  → Use `datetime.now(timezone.utc)` (timezone-aware).
- SQLAlchemy `Model.query.get(id)` (Query API legada) — desencorajado na 2.0.
  → Use `db.session.get(Model, id)`.
- `Model.query` / `Query.get_or_404` no estilo legado → estilo 2.0 com `db.session` / `select()`.
- Import `from collections import Mapping` (removido no 3.10) → `from collections.abc import Mapping`.
- `imp` module → `importlib`.

**Node.js / JavaScript**
- `new Buffer(...)` / `Buffer(...)` — deprecated. → `Buffer.from(...)` / `Buffer.alloc(...)`.
- Módulo `sqlite3` em callback puro para I/O sequencial → padrão baseado em Promises
  (`sqlite`/`better-sqlite3`) ou `util.promisify`; nas versões recentes há `node:sqlite`.
- `require(...)` + CommonJS quando o projeto poderia usar ESM (`import`) — sinalize só se relevante.
- `url.parse()` (legacy) → `new URL()`. `crypto.createCipher` → `createCipheriv`.
- `substr()` → `substring()`/`slice()`.

**Geral**
- Bibliotecas de criptografia caseiras ou hashes fracos (MD5/SHA1 para senha) →
  `bcrypt`/`argon2` (Node) ou `werkzeug.security`/`passlib`/`bcrypt` (Python). (Cruza com C4.)

Se encontrar uma API deprecated não listada aqui, ainda assim reporte-a: descreva o uso, por que
está obsoleta e qual é o substituto recomendado.
