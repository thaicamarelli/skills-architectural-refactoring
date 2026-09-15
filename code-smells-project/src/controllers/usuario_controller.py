"""Controller de Usuário: cadastro, consulta e autenticação."""

import logging

from src.errors import ErroDeValidacao, NaoAutorizado, NaoEncontrado


class UsuarioController:
    def __init__(self, model, logger=None):
        self.model = model
        self.logger = logger or logging.getLogger(__name__)

    def listar(self):
        usuarios = self.model.listar()
        return {"dados": usuarios, "sucesso": True}, 200

    def buscar_por_id(self, usuario_id):
        usuario = self.model.buscar_por_id(usuario_id)
        if not usuario:
            raise NaoEncontrado("Usuário não encontrado")
        return {"dados": usuario, "sucesso": True}, 200

    def criar(self, dados):
        if not dados:
            raise ErroDeValidacao("Dados inválidos")

        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not nome or not email or not senha:
            raise ErroDeValidacao("Nome, email e senha são obrigatórios")

        usuario_id = self.model.criar(nome, email, senha)
        self.logger.info("usuario.criado id=%s", usuario_id)
        return {"dados": {"id": usuario_id}, "sucesso": True}, 201

    def login(self, dados):
        if not dados:
            raise ErroDeValidacao("Dados inválidos")

        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            raise ErroDeValidacao("Email e senha são obrigatórios")

        usuario = self.model.autenticar(email, senha)
        if not usuario:
            self.logger.warning("login.falhou email=%s", email)
            raise NaoAutorizado("Email ou senha inválidos")

        self.logger.info("login.sucesso usuario=%s", usuario["id"])
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
