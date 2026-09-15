"""Rotas de sistema: índice da API e health check."""

from flask import Blueprint, jsonify


def criar_blueprint(health_controller, versao):
    blueprint = Blueprint("sistema", __name__)

    @blueprint.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": versao,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    @blueprint.get("/health")
    def health_check():
        corpo, status = health_controller.checar()
        return jsonify(corpo), status

    return blueprint
