import logging

from database import db
from errors import ErroDeValidacao, NaoEncontrado
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import process_task_data

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, notification_service=None):
        self.notification_service = notification_service

    def listar(self):
        """Corrige a Query N+1 do relatório original: busca users/categories em lote
        (não um SELECT por task) em vez de deixar cada `to_dict` disparar uma query."""
        tasks = Task.query.all()

        user_ids = {t.user_id for t in tasks if t.user_id}
        category_ids = {t.category_id for t in tasks if t.category_id}
        users_by_id = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}
        categories_by_id = (
            {c.id: c for c in Category.query.filter(Category.id.in_(category_ids)).all()} if category_ids else {}
        )

        result = []
        for t in tasks:
            data = t.to_dict()
            data['user_name'] = users_by_id[t.user_id].name if t.user_id in users_by_id else None
            data['category_name'] = categories_by_id[t.category_id].name if t.category_id in categories_by_id else None
            result.append(data)
        return result

    def buscar_por_id(self, task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise NaoEncontrado('Task não encontrada')
        return task.to_dict()

    def buscar(self, termo='', status='', priority='', user_id=''):
        tasks = Task.query

        if termo:
            tasks = tasks.filter(db.or_(Task.title.like(f'%{termo}%'), Task.description.like(f'%{termo}%')))
        if status:
            tasks = tasks.filter(Task.status == status)
        if priority:
            tasks = tasks.filter(Task.priority == int(priority))
        if user_id:
            tasks = tasks.filter(Task.user_id == int(user_id))

        return [t.to_dict() for t in tasks.all()]

    def criar(self, data):
        if not data:
            raise ErroDeValidacao('Dados inválidos')
        if not data.get('title'):
            raise ErroDeValidacao('Título é obrigatório')

        campos, erro = process_task_data(data)
        if erro:
            raise ErroDeValidacao(erro)

        user = None
        if data.get('user_id'):
            user = db.session.get(User, data['user_id'])
            if not user:
                raise NaoEncontrado('Usuário não encontrado')

        if data.get('category_id') and not db.session.get(Category, data['category_id']):
            raise NaoEncontrado('Categoria não encontrada')

        task = Task()
        task.title = campos['title']
        task.description = campos.get('description', data.get('description', ''))
        task.status = campos.get('status', 'pending')
        task.priority = campos.get('priority', data.get('priority', 3))
        task.user_id = data.get('user_id')
        task.category_id = data.get('category_id')
        task.due_date = campos.get('due_date')
        if 'tags' in campos:
            task.tags = campos['tags']

        db.session.add(task)
        db.session.commit()
        logger.info('task.criada id=%s titulo=%s', task.id, task.title)

        if user and self.notification_service:
            self.notification_service.notify_task_assigned(user, task)

        return task.to_dict(), 201

    def atualizar(self, task_id, data):
        task = db.session.get(Task, task_id)
        if not task:
            raise NaoEncontrado('Task não encontrada')
        if not data:
            raise ErroDeValidacao('Dados inválidos')

        campos, erro = process_task_data(data, existing_task=task)
        if erro:
            raise ErroDeValidacao(erro)

        if 'user_id' in data:
            if data['user_id'] and not db.session.get(User, data['user_id']):
                raise NaoEncontrado('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not db.session.get(Category, data['category_id']):
                raise NaoEncontrado('Categoria não encontrada')
            task.category_id = data['category_id']

        for campo in ('title', 'description', 'status', 'priority'):
            if campo in campos:
                setattr(task, campo, campos[campo])
        if 'due_date' in campos:
            task.due_date = campos['due_date']
        if 'tags' in campos:
            task.tags = campos['tags']

        db.session.commit()
        logger.info('task.atualizada id=%s', task.id)
        return task.to_dict()

    def deletar(self, task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise NaoEncontrado('Task não encontrada')

        db.session.delete(task)
        db.session.commit()
        logger.info('task.deletada id=%s', task_id)
        return {'message': 'Task deletada com sucesso'}

    def estatisticas(self):
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())

        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
