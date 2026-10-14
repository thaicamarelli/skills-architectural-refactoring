"""Tratamento de erro central — substitui os `except:` repetidos nas rotas."""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import ErroDeAplicacao

logger = logging.getLogger(__name__)


def registrar_error_handlers(app):
    @app.errorhandler(ErroDeAplicacao)
    def tratar_erro_de_dominio(erro):
        logger.info("erro.dominio status=%s mensagem=%s", erro.status_http, erro.mensagem)
        return jsonify({'error': erro.mensagem}), erro.status_http

    @app.errorhandler(HTTPException)
    def tratar_erro_http(erro):
        return jsonify({'error': erro.description}), erro.code

    @app.errorhandler(Exception)
    def tratar_erro_inesperado(erro):
        logger.exception("erro.inesperado: %s", erro)
        return jsonify({'error': 'Erro interno'}), 500
