"""Ciclo de vida da conexão SQLite.

A conexão é criada por request e guardada em `flask.g`, sendo fechada no
teardown do app context. Não existe conexão global mutável: quem precisa de
acesso a dados recebe `obter_conexao` (o provider) por injeção.
"""

import sqlite3

from flask import current_app, g

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)


def criar_conexao(caminho):
    """Abre uma conexão nova. Cada chamador é dono da conexão que recebe."""
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def obter_conexao():
    """Conexão da requisição atual (criada sob demanda, uma por request)."""
    if "conexao_db" not in g:
        g.conexao_db = criar_conexao(current_app.config["DATABASE_PATH"])
    return g.conexao_db


def fechar_conexao(_excecao=None):
    conexao = g.pop("conexao_db", None)
    if conexao is not None:
        conexao.close()


def registrar_ciclo_de_vida(app):
    app.teardown_appcontext(fechar_conexao)


def criar_schema(conexao):
    for comando in SCHEMA:
        conexao.execute(comando)
    conexao.commit()
