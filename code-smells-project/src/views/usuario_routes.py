"""Rotas de Usuário e autenticação."""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    blueprint = Blueprint("usuarios", __name__)

    @blueprint.get("/usuarios")
    def listar_usuarios():
        corpo, status = controller.listar()
        return jsonify(corpo), status

    @blueprint.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        corpo, status = controller.buscar_por_id(usuario_id)
        return jsonify(corpo), status

    @blueprint.post("/usuarios")
    def criar_usuario():
        corpo, status = controller.criar(request.get_json(silent=True))
        return jsonify(corpo), status

    @blueprint.post("/login")
    def login():
        corpo, status = controller.login(request.get_json(silent=True))
        return jsonify(corpo), status

    return blueprint
