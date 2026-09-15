"""Model de Produto: persistência e regras da própria entidade.

Não conhece HTTP nem o framework web — recebe um provedor de conexão e devolve
estruturas de dados puras.
"""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_TAMANHO_MINIMO = 2
NOME_TAMANHO_MAXIMO = 200

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def validar(dados):
    """Regras da entidade Produto, usadas tanto na criação quanto na atualização.

    Devolve a lista de mensagens de erro, na ordem em que devem ser reportadas.
    """
    erros = []

    if not dados:
        return ["Dados inválidos"]

    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            erros.append(mensagem)
    if erros:
        return erros

    preco = dados["preco"]
    estoque = dados["estoque"]

    if not isinstance(preco, (int, float)) or isinstance(preco, bool):
        erros.append("Preço deve ser um número")
    elif preco < 0:
        erros.append("Preço não pode ser negativo")

    if not isinstance(estoque, int) or isinstance(estoque, bool):
        erros.append("Estoque deve ser um número inteiro")
    elif estoque < 0:
        erros.append("Estoque não pode ser negativo")

    nome = dados["nome"]
    if not isinstance(nome, str):
        erros.append("Nome deve ser um texto")
    elif len(nome) < NOME_TAMANHO_MINIMO:
        erros.append("Nome muito curto")
    elif len(nome) > NOME_TAMANHO_MAXIMO:
        erros.append("Nome muito longo")

    categoria = dados.get("categoria", CATEGORIA_PADRAO)
    if categoria not in CATEGORIAS_VALIDAS:
        erros.append("Categoria inválida. Válidas: " + str(CATEGORIAS_VALIDAS))

    return erros


def serializar(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "descricao": linha["descricao"],
        "preco": linha["preco"],
        "estoque": linha["estoque"],
        "categoria": linha["categoria"],
        "ativo": linha["ativo"],
        "criado_em": linha["criado_em"],
    }


class ProdutoModel:
    def __init__(self, provedor_conexao):
        self._provedor_conexao = provedor_conexao

    @property
    def db(self):
        return self._provedor_conexao()

    def listar(self):
        linhas = self.db.execute("SELECT " + COLUNAS + " FROM produtos").fetchall()
        return [serializar(linha) for linha in linhas]

    def buscar_por_id(self, produto_id):
        linha = self.db.execute(
            "SELECT " + COLUNAS + " FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return serializar(linha)

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Filtro dinâmico montado com placeholders — nunca com concatenação de valores."""
        condicoes = ["1=1"]
        parametros = []

        if termo:
            condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros.extend(["%" + termo + "%", "%" + termo + "%"])
        if categoria:
            condicoes.append("categoria = ?")
            parametros.append(categoria)
        if preco_min:
            condicoes.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max:
            condicoes.append("preco <= ?")
            parametros.append(preco_max)

        sql = "SELECT " + COLUNAS + " FROM produtos WHERE " + " AND ".join(condicoes)
        linhas = self.db.execute(sql, parametros).fetchall()
        return [serializar(linha) for linha in linhas]

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self.db
        cursor = conexao.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        conexao.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self.db
        conexao.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        conexao.commit()
        return True

    def deletar(self, produto_id):
        conexao = self.db
        conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conexao.commit()
        return True

    def contar(self):
        return self.db.execute("SELECT COUNT(*) AS total FROM produtos").fetchone()["total"]
