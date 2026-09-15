"""Rotas de Pedido."""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    blueprint = Blueprint("pedidos", __name__)

    @blueprint.post("/pedidos")
    def criar_pedido():
        corpo, status = controller.criar(request.get_json(silent=True))
        return jsonify(corpo), status

    @blueprint.get("/pedidos")
    def listar_todos_pedidos():
        corpo, status = controller.listar()
        return jsonify(corpo), status

    @blueprint.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        corpo, status = controller.listar_por_usuario(usuario_id)
        return jsonify(corpo), status

    @blueprint.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        corpo, status = controller.atualizar_status(pedido_id, request.get_json(silent=True))
        return jsonify(corpo), status

    return blueprint
