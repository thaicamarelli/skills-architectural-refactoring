"""Rotas de Categoria — extraídas de report_routes.py (SRP: não é relatório)."""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    category_bp = Blueprint('categories', __name__)

    @category_bp.route('/categories', methods=['GET'])
    def get_categories():
        return jsonify(controller.listar()), 200

    @category_bp.route('/categories', methods=['POST'])
    def create_category():
        corpo, status = controller.criar(request.get_json())
        return jsonify(corpo), status

    @category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
    def update_category(cat_id):
        return jsonify(controller.atualizar(cat_id, request.get_json())), 200

    @category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
    def delete_category(cat_id):
        return jsonify(controller.deletar(cat_id)), 200

    return category_bp
