"""Exceções de domínio — substituem os `except:` genéricos espalhados nas rotas."""


class ErroDeAplicacao(Exception):
    status_http = 500

    def __init__(self, mensagem, status_http=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if status_http is not None:
            self.status_http = status_http


class ErroDeValidacao(ErroDeAplicacao):
    status_http = 400


class NaoEncontrado(ErroDeAplicacao):
    status_http = 404


class Conflito(ErroDeAplicacao):
    status_http = 409


class NaoAutorizado(ErroDeAplicacao):
    status_http = 401


class Proibido(ErroDeAplicacao):
    status_http = 403
