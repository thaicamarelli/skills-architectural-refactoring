import logging

from database import db
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)


def list_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        data = category.to_dict()
        data['task_count'] = Task.query.filter_by(category_id=category.id).count()
        result.append(data)
    return result, 200


def create_category(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    name = data.get('name')
    if not name:
        return {'error': 'Nome é obrigatório'}, 400

    category = Category(
        name=name,
        description=data.get('description', ''),
        color=data.get('color', '#000000'),
    )

    try:
        db.session.add(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao criar categoria: %s', e)
        return {'error': 'Erro ao criar categoria'}, 500

    return category.to_dict(), 201


def update_category(category_id, data):
    category = db.session.get(Category, category_id)
    if not category:
        return {'error': 'Categoria não encontrada'}, 404

    if not data:
        return {'error': 'Dados inválidos'}, 400

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao atualizar categoria %s: %s', category_id, e)
        return {'error': 'Erro ao atualizar'}, 500

    return category.to_dict(), 200


def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        return {'error': 'Categoria não encontrada'}, 404

    try:
        db.session.delete(category)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao deletar categoria %s: %s', category_id, e)
        return {'error': 'Erro ao deletar'}, 500

    return {'message': 'Categoria deletada'}, 200
