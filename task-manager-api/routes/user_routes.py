"""Rotas de Usuário e autenticação."""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    user_bp = Blueprint('users', __name__)

    @user_bp.route('/users', methods=['GET'])
    def get_users():
        return jsonify(controller.listar()), 200

    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id):
        return jsonify(controller.buscar_por_id(user_id)), 200

    @user_bp.route('/users', methods=['POST'])
    def create_user():
        corpo, status = controller.criar(request.get_json())
        return jsonify(corpo), status

    @user_bp.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        return jsonify(controller.atualizar(user_id, request.get_json())), 200

    @user_bp.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        return jsonify(controller.deletar(user_id)), 200

    @user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
    def get_user_tasks(user_id):
        return jsonify(controller.tasks_do_usuario(user_id)), 200

    @user_bp.route('/login', methods=['POST'])
    def login():
        return jsonify(controller.login(request.get_json())), 200

    return user_bp
