from flask import Blueprint, jsonify

from controllers import report_controller

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    result, status = report_controller.summary_report()
    return jsonify(result), status


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    result, status = report_controller.user_report(user_id)
    return jsonify(result), status
