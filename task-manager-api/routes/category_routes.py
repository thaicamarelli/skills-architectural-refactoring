from flask import Blueprint, request, jsonify

from controllers import category_controller

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    result, status = category_controller.list_categories()
    return jsonify(result), status


@category_bp.route('/categories', methods=['POST'])
def create_category():
    result, status = category_controller.create_category(request.get_json())
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    result, status = category_controller.update_category(cat_id, request.get_json())
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    result, status = category_controller.delete_category(cat_id)
    return jsonify(result), status
