import logging

from database import db
from errors import ErroDeValidacao, NaoEncontrado
from models.category import DEFAULT_COLOR, Category
from models.task import Task

logger = logging.getLogger(__name__)


class CategoryController:
    def listar(self):
        result = []
        for c in Category.query.all():
            data = c.to_dict()
            data['task_count'] = Task.query.filter_by(category_id=c.id).count()
            result.append(data)
        return result

    def criar(self, data):
        if not data:
            raise ErroDeValidacao('Dados inválidos')
        name = data.get('name')
        if not name:
            raise ErroDeValidacao('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_COLOR)

        db.session.add(category)
        db.session.commit()
        logger.info('categoria.criada id=%s', category.id)
        return category.to_dict(), 201

    def atualizar(self, cat_id, data):
        cat = db.session.get(Category, cat_id)
        if not cat:
            raise NaoEncontrado('Categoria não encontrada')
        if not data:
            raise ErroDeValidacao('Dados inválidos')

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        db.session.commit()
        logger.info('categoria.atualizada id=%s', cat.id)
        return cat.to_dict()

    def deletar(self, cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            raise NaoEncontrado('Categoria não encontrada')

        db.session.delete(cat)
        db.session.commit()
        logger.info('categoria.deletada id=%s', cat_id)
        return {'message': 'Categoria deletada'}
