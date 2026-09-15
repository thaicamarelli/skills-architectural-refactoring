# Guidelines de Arquitetura — Padrão MVC Alvo (Fase 3)

Este é o destino da refatoração. MVC separa responsabilidades em camadas para que cada mudança
tenha um lugar óbvio e cada parte seja testável em isolamento. A ideia central: **uma requisição
flui em uma direção clara** — a View/Route recebe o HTTP, o Controller orquestra, o Model cuida
dos dados e do domínio, e o resultado volta pela mesma rota.

```
Request → View/Route → Controller → Service (opcional) → Model → Banco
                                                    ↓
Response ← View/Route ← Controller ← ───────────────
```

## Responsabilidades de cada camada

### Models (`models/`)
- **Fazem:** encapsular acesso a dados (todas as queries, sempre parametrizadas) e a lógica de
  domínio da entidade (validações da entidade, cálculos, invariantes). Um Model por entidade
  (`produto_model`, `usuario_model`, `pedido_model`...).
- **Não fazem:** conhecer HTTP (nada de `request`/`response`), formatar saída de API, saber que
  existe um framework web.
- Se o projeto usa ORM (ex.: SQLAlchemy), o Model é a classe mapeada — mas ainda deve ter
  comportamento (não deixe a lógica vazar para as rotas).

### Views / Routes (`views/` ou `routes/`)
- **Fazem:** definir os endpoints (método + caminho), extrair dados do `request`, chamar o
  Controller apropriado e devolver o `response` (status + corpo). São a fronteira HTTP, finas.
- **Não fazem:** regra de negócio, SQL, cálculos. Se um handler tem mais que "pegar entrada →
  chamar controller → devolver saída", a lógica está no lugar errado.
- Em Flask, Blueprints por domínio são uma boa forma de View/Route. Em Express, um router por
  domínio (`routes/checkout.routes.js`).

### Controllers (`controllers/`)
- **Fazem:** orquestrar o fluxo de um caso de uso — validar entrada (ou delegar ao validador),
  chamar um ou mais Models/Services na ordem certa, tratar o resultado e montar a resposta lógica
  (dados + status), coordenar transações.
- **Não fazem:** conter SQL cru (isso é do Model) nem detalhes de I/O externo (isso é do Service).
- Um Controller por domínio (`produto_controller`, `pedido_controller`).

### Services (`services/`) — quando houver I/O externo ou regra que cruza entidades
- **Fazem:** integrações externas (e-mail, SMS, gateway de pagamento), regras que envolvem várias
  entidades, orquestrações reutilizáveis. Chamados pelos Controllers.
- **Por quê:** isolam efeitos colaterais para poderem ser trocados/mockados. Notificações e
  pagamento nunca devem morar dentro de uma rota.

### Config (`config/`)
- **Fazem:** centralizar toda a configuração e **segredos lidos de variáveis de ambiente**
  (`os.environ`, `process.env`), com defaults seguros. Chave secreta, credenciais de banco,
  chaves de gateway, flags de debug, host/porta.
- **Regra dura:** zero segredos hardcoded no código. `DEBUG` vem da env e é `False` por padrão.

### Middlewares / Error handling (`middlewares/`)
- **Fazem:** tratamento de erro centralizado (um handler que captura exceções e devolve resposta
  padronizada), logging, CORS, autenticação. Substitui os `try/except` repetidos por rota.

### Entry point / Composition root (`app.py`, `src/app.js`, `main.*`)
- **Fazem:** apenas montar a aplicação — criar o app, carregar config, registrar rotas/blueprints,
  registrar middlewares, subir o servidor. É "cola", não lógica.
- **Não fazem:** definir regra de negócio, SQL ou endpoints inline.

## Estrutura de diretórios de referência

Adapte os nomes à convenção da linguagem, mas mantenha a separação:

```
src/                          (ou raiz, conforme a stack)
├── config/
│   └── settings.*            # config + segredos via env
├── models/
│   ├── <entidade>_model.*
│   └── ...
├── controllers/
│   ├── <dominio>_controller.*
│   └── ...
├── views/  (ou routes/)
│   └── <dominio>_routes.*
├── services/                 # se houver I/O externo / regra cross-entidade
│   └── <algo>_service.*
├── middlewares/
│   └── error_handler.*
└── app.*                     # composition root
```

## Regras de dependência (o que pode chamar o quê)

- Views/Routes → Controllers. **Nunca** Views → Model direto para regra de negócio.
- Controllers → Services e/ou Models.
- Services → Models.
- Models → Banco.
- **A seta nunca aponta para trás:** um Model não importa um Controller; uma camada de baixo não
  conhece uma de cima. Isso é o que mantém o Model testável sem subir o servidor web.

## Como adaptar ao ponto de partida

- **Monólito / God Class:** crie todas as camadas do zero e distribua a lógica por elas.
- **Camadas parciais (já tem `models/`, `routes/`, `services/`):** não recrie o que existe.
  Introduza a camada que falta (quase sempre **Controllers**), mova a regra de negócio das rotas
  para os Controllers, faça as rotas ficarem finas, conecte o `services/` que estava órfão e
  extraia a config. Melhore, não reconstrua.
- Em qualquer caso, o objetivo de aceite é o mesmo: config sem hardcoded, Models abstraindo dados,
  Views/Routes separadas, Controllers concentrando o fluxo, error handling central, entry point
  claro — e a aplicação continuando a funcionar.
