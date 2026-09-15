"""Exceções de domínio.

Substituem os dicionários `{"erro": ...}` devolvidos pelos models e os
`try/except Exception` repetidos nos controllers: cada erro carrega seu próprio
status HTTP e é traduzido em resposta pelo error handler central.
"""


class ErroDeAplicacao(Exception):
    """Erro esperado, com status HTTP próprio e mensagem segura para o cliente."""

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


class RegraDeNegocioViolada(ErroDeAplicacao):
    status_http = 400


class NaoAutorizado(ErroDeAplicacao):
    status_http = 401
