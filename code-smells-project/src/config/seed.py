"""Dados iniciais de desenvolvimento.

Roda apenas quando o banco está vazio. As senhas dos usuários de exemplo vêm de
`SEED_SENHA_PADRAO`; se a variável não estiver definida, uma senha aleatória é
gerada e registrada no log — nenhuma credencial fica escrita no código.
"""

import logging
import os
import secrets

from werkzeug.security import generate_password_hash

PRODUTOS_INICIAIS = [
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
]

USUARIOS_INICIAIS = [
    ("Admin", "admin@loja.com", "admin"),
    ("João Silva", "joao@email.com", "cliente"),
    ("Maria Santos", "maria@email.com", "cliente"),
]


def popular(conexao, logger=None):
    """Insere os dados de exemplo se ainda não houver produtos. Idempotente."""
    logger = logger or logging.getLogger(__name__)

    ja_populado = conexao.execute("SELECT COUNT(*) AS total FROM produtos").fetchone()["total"] > 0
    if ja_populado:
        return False

    conexao.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_INICIAIS,
    )

    senha = os.environ.get("SEED_SENHA_PADRAO", "").strip()
    if senha:
        origem_da_senha = "SEED_SENHA_PADRAO"
    else:
        senha = secrets.token_urlsafe(12)
        origem_da_senha = "gerada"

    conexao.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, tipo in USUARIOS_INICIAIS],
    )
    conexao.commit()

    if origem_da_senha == "gerada":
        logger.warning(
            "seed: senha aleatória gerada para os usuários de exemplo: %s "
            "(defina SEED_SENHA_PADRAO para escolher a sua)",
            senha,
        )
    else:
        logger.info("seed: usuários de exemplo criados com a senha de SEED_SENHA_PADRAO")

    return True
