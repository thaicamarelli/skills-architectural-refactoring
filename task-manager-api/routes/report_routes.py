"""Rotas de relatórios — só leitura de relatórios (CRUD de categorias mora em category_routes.py)."""

from flask import Blueprint, jsonify


def criar_blueprint(controller):
    report_bp = Blueprint('reports', __name__)

    @report_bp.route('/reports/summary', methods=['GET'])
    def summary_report():
        return jsonify(controller.resumo()), 200

    @report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
    def user_report(user_id):
        return jsonify(controller.por_usuario(user_id)), 200

    return report_bp
