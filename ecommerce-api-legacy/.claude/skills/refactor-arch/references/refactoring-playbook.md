# Playbook de Refatoração (Fase 3)

Transformações concretas para eliminar cada anti-pattern do catálogo, com exemplos antes/depois.
Cada padrão indica qual entrada do catálogo ele resolve. Os exemplos são ilustrativos — adapte à
stack e ao código real, preservando o comportamento observável (mesmos endpoints, mesmas respostas).

## Índice
- [T1. Segredos hardcoded → módulo de config via env](#t1)
- [T2. SQL Injection → queries parametrizadas no Model](#t2)
- [T3. God Class/Module → camadas MVC](#t3)
- [T4. Regra de negócio na rota → Controller](#t4)
- [T5. Estado global mutável → injeção de dependência](#t5)
- [T6. Side effects na rota → camada de Service](#t6)
- [T7. Query N+1 → JOIN / batch / eager loading](#t7)
- [T8. try/except repetido → error handler central](#t8)
- [T9. Senha em texto puro / cripto quebrada → hashing forte](#t9)
- [T10. Validação duplicada → validador único](#t10)
- [T11. print → logging; magic numbers → constantes](#t11)
- [T12. API deprecated → equivalente moderno](#t12)

---

<a id="t1"></a>
## T1. Segredos hardcoded → módulo de config via env
Resolve **C1, M5**.

**Antes (Flask):**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**Depois (`config/settings.py`):**
```python
import os

class Settings:
    SECRET_KEY = os.environ["SECRET_KEY"]                 # sem default para segredo
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")

settings = Settings()
```
```python
# app.py
from config.settings import settings
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```
**Node (`config/settings.js`):**
```js
module.exports = {
  port: process.env.PORT || 3000,
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
};
```
Adicione um `.env.example` documentando as variáveis e garanta que `.env` está no `.gitignore`.

---

<a id="t2"></a>
## T2. SQL Injection → queries parametrizadas no Model
Resolve **C2** (e move para **H4**).

**Antes:**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
```
**Depois (`models/produto_model.py`):**
```python
class ProdutoModel:
    def __init__(self, db):
        self.db = db

    def get_by_id(self, id):
        cur = self.db.execute("SELECT * FROM produtos WHERE id = ?", (id,))
        return cur.fetchone()

    def create(self, nome, email):
        cur = self.db.execute(
            "INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email)
        )
        self.db.commit()
        return cur.lastrowid
```
Para filtros dinâmicos, monte a lista de placeholders — nunca concatene o valor:
```python
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)"); params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?"); params.append(categoria)
sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses)
cur = self.db.execute(sql, params)
```

---

<a id="t3"></a>
## T3. God Class/Module → camadas MVC
Resolve **C5, H4**.

**Antes:** `AppManager` cria o banco, registra rotas e processa pagamento; ou `models.py` faz SQL
+ validação + cálculo + formatação para 4 entidades.

**Depois:** quebre por responsabilidade e por domínio.
```
src/
├── config/settings.py
├── models/produto_model.py        # só dados de produto
├── models/pedido_model.py         # só dados de pedido
├── controllers/produto_controller.py
├── controllers/pedido_controller.py
├── views/routes.py                # endpoints finos
├── services/notification_service.py
├── middlewares/error_handler.py
└── app.py                         # composition root
```
Mova cada função para a camada certa: query → Model; orquestração → Controller; endpoint → View;
integração → Service. O `app.py` final só monta tudo.

---

<a id="t4"></a>
## T4. Regra de negócio na rota → Controller
Resolve **H1**.

**Antes (rota calcula desconto e monta relatório):**
```python
def relatorio_vendas():
    # ... várias queries e regras de desconto dentro do handler ...
    if faturamento > 10000: desconto = faturamento * 0.1
    ...
    return jsonify(...)
```
**Depois:**
```python
# models/pedido_model.py  → dados
def resumo_vendas(self):
    ...  # queries agregadas, retorna números crus

# controllers/relatorio_controller.py  → regra + orquestração
from config.settings import settings
def relatorio_vendas(pedido_model):
    dados = pedido_model.resumo_vendas()
    dados["desconto"] = calcular_desconto(dados["faturamento"])
    return dados, 200

# views/routes.py  → só HTTP
@app.route("/relatorios/vendas")
def rota_relatorio():
    dados, status = relatorio_controller.relatorio_vendas(pedido_model)
    return jsonify({"dados": dados, "sucesso": True}), status
```

---

<a id="t5"></a>
## T5. Estado global mutável → injeção de dependência
Resolve **H2**.

**Antes:**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None: db_connection = sqlite3.connect(...)
    return db_connection
```
```js
let globalCache = {};
let totalRevenue = 0;
```
**Depois:** crie a dependência uma vez no composition root e injete-a.
```python
# config/database.py
def create_connection(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# app.py
db = create_connection(settings.DB_PATH)
produto_model = ProdutoModel(db)           # injeta a conexão
```
Estado mutável (cache, contadores) vira responsabilidade de um Service com escopo definido, não
uma variável de módulo compartilhada por toda a aplicação.

---

<a id="t6"></a>
## T6. Side effects na rota → camada de Service
Resolve **H3**.

**Antes:**
```python
print("ENVIANDO EMAIL: Pedido criado")
print("ENVIANDO SMS: ...")
```
```js
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
**Depois (`services/notification_service.py`):**
```python
class NotificationService:
    def __init__(self, logger, mailer):
        self.logger = logger
        self.mailer = mailer

    def pedido_criado(self, pedido):
        self.mailer.send(pedido.usuario_email, "Pedido criado", ...)
        self.logger.info("notification.pedido_criado", pedido_id=pedido.id)
```
```python
# controller chama o service; a rota não sabe que e-mail existe
notification_service.pedido_criado(pedido)
```
Nunca logue dados sensíveis (número de cartão, chave de gateway). Pagamento também é Service, com
a chave vinda da config (T1), mockável em teste.

---

<a id="t7"></a>
## T7. Query N+1 → JOIN / batch / eager loading
Resolve **M1**.

**Antes (uma query por item, dentro de laços):**
```python
for row in pedidos:
    itens = db.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        prod = db.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**Depois (uma query com JOIN):**
```python
sql = """
    SELECT p.id AS pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, pr.nome
    FROM pedidos p
    JOIN itens_pedido ip ON ip.pedido_id = p.id
    JOIN produtos pr ON pr.id = ip.produto_id
"""
rows = db.execute(sql).fetchall()   # agrupa em memória por pedido_id
```
**ORM (SQLAlchemy) — eager loading:**
```python
from sqlalchemy.orm import joinedload
tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
```

---

<a id="t8"></a>
## T8. try/except repetido → error handler central
Resolve **M3**.

**Antes (cada rota repete):**
```python
try:
    ...
except Exception as e:
    return jsonify({"erro": str(e)}), 500
```
**Depois (Flask — handler central em `middlewares/error_handler.py`):**
```python
def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle(e):
        app.logger.exception(e)
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Não encontrado"}), 404
```
**Express (middleware de erro tem 4 args, registrado por último):**
```js
function errorHandler(err, req, res, next) {
  console.error(err);
  res.status(err.status || 500).json({ error: "Erro interno" });
}
app.use(errorHandler);
```
As rotas deixam de precisar de try/except genérico; erros de negócio lançam exceções tratadas
no ponto central.

---

<a id="t9"></a>
## T9. Senha em texto puro / cripto quebrada → hashing forte
Resolve **C4** (cruza com T12).

**Antes:**
```python
cursor.execute("... VALUES ('" + senha + "')")           # texto puro
```
```js
function badCrypto(pwd){ let h=""; for(let i=0;i<10000;i++){ h+=Buffer.from(pwd).toString('base64').substring(0,2);} return h.substring(0,10); }
```
**Depois (Python — `werkzeug.security` ou `bcrypt`):**
```python
from werkzeug.security import generate_password_hash, check_password_hash
hash = generate_password_hash(senha)           # no cadastro
ok = check_password_hash(user["senha"], senha) # no login
```
**Node (`bcrypt`):**
```js
const bcrypt = require("bcrypt");
const hash = await bcrypt.hash(pwd, 12);
const ok = await bcrypt.compare(pwd, user.pass);
```
Nunca retorne a coluna de senha em respostas de API — selecione colunas explicitamente ou remova
o campo antes de serializar. Avise o usuário: senhas existentes precisarão ser redefinidas.

---

<a id="t10"></a>
## T10. Validação duplicada → validador único
Resolve **M2, M4**.

**Antes:** `criar_produto` e `atualizar_produto` repetem os mesmos `if preco < 0`, `len(nome)...`.

**Depois (um validador reutilizado por ambos os fluxos):**
```python
# models/produto_model.py  (ou um schema/validators.py)
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")

def validar_produto(dados):
    erros = []
    if not dados.get("nome") or not (2 <= len(dados["nome"]) <= 200):
        erros.append("Nome deve ter entre 2 e 200 caracteres")
    if dados.get("preco", 0) < 0:
        erros.append("Preço não pode ser negativo")
    if dados.get("categoria", "geral") not in CATEGORIAS_VALIDAS:
        erros.append("Categoria inválida")
    return erros
```
Se o projeto já usa uma lib de schema (ex.: `marshmallow`), prefira defini-lo lá. O Controller
chama o validador; a rota não repete regras.

---

<a id="t11"></a>
## T11. print → logging; magic numbers → constantes
Resolve **L1, L2, L3, L4**.

**Antes:**
```python
print("Produto criado com ID: " + str(id))
if faturamento > 10000: desconto = faturamento * 0.1
```
**Depois:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("produto.criado", extra={"produto_id": id})

# config/settings.py  → limiares nomeados
DESCONTO_FAIXAS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
```
Renomeie variáveis crípticas (`u`→`usuario`, `cc`→`cartao`, `e`→`email`) e remova imports/código
morto (`import os, sys, json, time` sem uso; camadas nunca conectadas).

---

<a id="t12"></a>
## T12. API deprecated → equivalente moderno
Resolve a seção **APIs Deprecated** do catálogo.

| Antes (deprecated) | Depois (moderno) |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `Model.query.get(id)` (SQLAlchemy) | `db.session.get(Model, id)` |
| `from collections import Mapping` | `from collections.abc import Mapping` |
| `new Buffer(x)` / `Buffer(x)` | `Buffer.from(x)` / `Buffer.alloc(n)` |
| `url.parse(s)` | `new URL(s)` |
| `crypto.createCipher` | `crypto.createCipheriv` |
| MD5/SHA1/cripto caseira p/ senha | `bcrypt`/`argon2` / `werkzeug.security` (ver T9) |

**Exemplo:**
```python
# antes
from datetime import datetime
ts = datetime.utcnow()
user = User.query.get(user_id)
# depois
from datetime import datetime, timezone
ts = datetime.now(timezone.utc)
user = db.session.get(User, user_id)
```
Ao trocar uma API, rode o boot da aplicação (passo de validação da Fase 3) para confirmar que
nada quebrou com a substituição.
