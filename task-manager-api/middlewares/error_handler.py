import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify({'error': 'Requisição inválida'}), 400

    @app.errorhandler(Exception)
    def handle_uncaught(error):
        logger.exception('Erro não tratado: %s', error)
        return jsonify({'error': 'Erro interno'}), 500
