"""Rotas de relatórios."""

from flask import Blueprint, jsonify


def criar_blueprint(controller):
    blueprint = Blueprint("relatorios", __name__)

    @blueprint.get("/relatorios/vendas")
    def relatorio_vendas():
        corpo, status = controller.vendas()
        return jsonify(corpo), status

    return blueprint
