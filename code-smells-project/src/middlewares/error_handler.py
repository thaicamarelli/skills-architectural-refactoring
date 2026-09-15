"""Tratamento de erro central.

Substitui os `try/except Exception` repetidos em cada handler: erros de domínio
viram a resposta com o status certo, e qualquer falha inesperada é registrada no
log e devolvida como mensagem genérica — sem vazar detalhes internos.
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.errors import ErroDeAplicacao


def _resposta(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def registrar_error_handlers(app, logger=None):
    logger = logger or logging.getLogger(__name__)

    @app.errorhandler(ErroDeAplicacao)
    def tratar_erro_de_dominio(erro):
        logger.info("erro.dominio status=%s mensagem=%s", erro.status_http, erro.mensagem)
        return _resposta(erro.mensagem, erro.status_http)

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        return _resposta(erro.description, erro.code)

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        logger.exception("erro.inesperado: %s", erro)
        return _resposta("Erro interno", 500)
