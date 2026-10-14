"""Rotas de Task — fronteira HTTP fina: extrai o request, chama o controller, devolve a resposta.

Fábrica de blueprint em vez de estado global mutável: o controller é injetado no
composition root (app.py) e fica fechado no escopo das funções da rota.
"""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    task_bp = Blueprint('tasks', __name__)

    @task_bp.route('/tasks', methods=['GET'])
    def get_tasks():
        return jsonify(controller.listar()), 200

    @task_bp.route('/tasks/search', methods=['GET'])
    def search_tasks():
        resultado = controller.buscar(
            termo=request.args.get('q', ''),
            status=request.args.get('status', ''),
            priority=request.args.get('priority', ''),
            user_id=request.args.get('user_id', ''),
        )
        return jsonify(resultado), 200

    @task_bp.route('/tasks/stats', methods=['GET'])
    def task_stats():
        return jsonify(controller.estatisticas()), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        return jsonify(controller.buscar_por_id(task_id)), 200

    @task_bp.route('/tasks', methods=['POST'])
    def create_task():
        corpo, status = controller.criar(request.get_json())
        return jsonify(corpo), status

    @task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        return jsonify(controller.atualizar(task_id, request.get_json())), 200

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        return jsonify(controller.deletar(task_id)), 200

    return task_bp
