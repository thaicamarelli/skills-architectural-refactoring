"""Model de Pedido: persistência do pedido, dos itens e da baixa de estoque.

A criação do pedido é uma operação multi-passo e roda dentro de uma transação
explícita com rollback. A leitura usa JOIN em vez de uma query por item.
"""

from src.errors import RegraDeNegocioViolada

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
STATUS_INICIAL = "pendente"
PRODUTO_DESCONHECIDO = "Desconhecido"

SQL_PEDIDOS_COM_ITENS = """
    SELECT pedido.id            AS pedido_id,
           pedido.usuario_id    AS usuario_id,
           pedido.status        AS status,
           pedido.total         AS total,
           pedido.criado_em     AS criado_em,
           item.produto_id      AS produto_id,
           item.quantidade      AS quantidade,
           item.preco_unitario  AS preco_unitario,
           produto.nome         AS produto_nome
    FROM pedidos pedido
    LEFT JOIN itens_pedido item ON item.pedido_id = pedido.id
    LEFT JOIN produtos produto  ON produto.id = item.produto_id
    {filtro}
    ORDER BY pedido.id, item.id
"""


def _agrupar_por_pedido(linhas):
    """Converte o resultado achatado do JOIN na estrutura pedido -> itens."""
    pedidos = {}
    ordem = []

    for linha in linhas:
        pedido_id = linha["pedido_id"]
        if pedido_id not in pedidos:
            pedidos[pedido_id] = {
                "id": pedido_id,
                "usuario_id": linha["usuario_id"],
                "status": linha["status"],
                "total": linha["total"],
                "criado_em": linha["criado_em"],
                "itens": [],
            }
            ordem.append(pedido_id)

        if linha["produto_id"] is None:
            continue

        pedidos[pedido_id]["itens"].append({
            "produto_id": linha["produto_id"],
            "produto_nome": linha["produto_nome"] or PRODUTO_DESCONHECIDO,
            "quantidade": linha["quantidade"],
            "preco_unitario": linha["preco_unitario"],
        })

    return [pedidos[pedido_id] for pedido_id in ordem]


class PedidoModel:
    def __init__(self, provedor_conexao):
        self._provedor_conexao = provedor_conexao

    @property
    def db(self):
        return self._provedor_conexao()

    def listar(self):
        linhas = self.db.execute(SQL_PEDIDOS_COM_ITENS.format(filtro="")).fetchall()
        return _agrupar_por_pedido(linhas)

    def listar_por_usuario(self, usuario_id):
        sql = SQL_PEDIDOS_COM_ITENS.format(filtro="WHERE pedido.usuario_id = ?")
        linhas = self.db.execute(sql, (usuario_id,)).fetchall()
        return _agrupar_por_pedido(linhas)

    def criar(self, usuario_id, itens):
        """Cria pedido, itens e baixa de estoque em uma única transação.

        A baixa usa `WHERE estoque >= ?` e verifica `rowcount`, de forma que a
        checagem e o débito acontecem no mesmo passo — duas requisições
        concorrentes não conseguem vender o mesmo estoque.
        """
        conexao = self.db

        if not conexao.in_transaction:
            conexao.execute("BEGIN IMMEDIATE")

        try:
            total = 0
            precos = {}

            for item in itens:
                produto_id = item["produto_id"]
                produto = conexao.execute(
                    "SELECT id, nome, preco FROM produtos WHERE id = ?", (produto_id,)
                ).fetchone()
                if produto is None:
                    raise RegraDeNegocioViolada("Produto " + str(produto_id) + " não encontrado")
                precos[produto_id] = produto["preco"]
                total = total + (produto["preco"] * item["quantidade"])

            cursor = conexao.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_INICIAL, total),
            )
            pedido_id = cursor.lastrowid

            for item in itens:
                produto_id = item["produto_id"]
                quantidade = item["quantidade"]

                conexao.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, produto_id, quantidade, precos[produto_id]),
                )

                baixa = conexao.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                    (quantidade, produto_id, quantidade),
                )
                if baixa.rowcount == 0:
                    nome = conexao.execute(
                        "SELECT nome FROM produtos WHERE id = ?", (produto_id,)
                    ).fetchone()
                    raise RegraDeNegocioViolada(
                        "Estoque insuficiente para " + (nome["nome"] if nome else str(produto_id))
                    )

            conexao.commit()
            return {"pedido_id": pedido_id, "total": total}

        except Exception:
            conexao.rollback()
            raise

    def atualizar_status(self, pedido_id, novo_status):
        conexao = self.db
        conexao.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        conexao.commit()
        return True

    def resumo_vendas(self):
        """Agregados crus do relatório — sem regra de desconto, que é do domínio de vendas."""
        linha = self.db.execute("""
            SELECT COUNT(*)                                                  AS total_pedidos,
                   COALESCE(SUM(total), 0)                                   AS faturamento,
                   COALESCE(SUM(CASE WHEN status = 'pendente'  THEN 1 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = 'aprovado'  THEN 1 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 END), 0) AS cancelados
            FROM pedidos
        """).fetchone()

        return {
            "total_pedidos": linha["total_pedidos"],
            "faturamento": linha["faturamento"],
            "pendentes": linha["pendentes"],
            "aprovados": linha["aprovados"],
            "cancelados": linha["cancelados"],
        }

    def contar(self):
        return self.db.execute("SELECT COUNT(*) AS total FROM pedidos").fetchone()["total"]
