"""Model de Usuário: persistência, hashing de senha e autenticação.

A coluna `senha` guarda apenas o hash e nunca é incluída em nenhuma
serialização — as consultas selecionam colunas explícitas em vez de `SELECT *`.
"""

from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"

COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def serializar(linha):
    if linha is None:
        return None
    return {
        "id": linha["id"],
        "nome": linha["nome"],
        "email": linha["email"],
        "tipo": linha["tipo"],
        "criado_em": linha["criado_em"],
    }


class UsuarioModel:
    def __init__(self, provedor_conexao):
        self._provedor_conexao = provedor_conexao

    @property
    def db(self):
        return self._provedor_conexao()

    def listar(self):
        linhas = self.db.execute("SELECT " + COLUNAS_PUBLICAS + " FROM usuarios").fetchall()
        return [serializar(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        linha = self.db.execute(
            "SELECT " + COLUNAS_PUBLICAS + " FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return serializar(linha)

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        conexao = self.db
        cursor = conexao.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        conexao.commit()
        return cursor.lastrowid

    def autenticar(self, email, senha):
        """Busca pelo e-mail e compara o hash. A senha nunca entra na query."""
        linha = self.db.execute(
            "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if linha is None:
            return None
        if not check_password_hash(linha["senha"], senha):
            return None
        return {
            "id": linha["id"],
            "nome": linha["nome"],
            "email": linha["email"],
            "tipo": linha["tipo"],
        }

    def contar(self):
        return self.db.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
