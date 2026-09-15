import logging

from sqlalchemy.orm import joinedload

from database import db
from datetime import datetime, timezone
from models.task import Task
from models.user import User
from models.category import Category
from services.notification_service import notification_service
from utils.helpers import process_task_data

logger = logging.getLogger(__name__)


def _task_with_relations_dict(task):
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks():
    tasks = Task.query.options(
        joinedload(Task.user), joinedload(Task.category)
    ).all()
    return [_task_with_relations_dict(task) for task in tasks], 200


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404
    return task.to_dict(), 200


def create_task(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    title = data.get('title')
    if not title:
        return {'error': 'Título é obrigatório'}, 400

    fields, error = process_task_data(data)
    if error:
        return {'error': error}, 400

    user_id = data.get('user_id')
    if user_id and not db.session.get(User, user_id):
        return {'error': 'Usuário não encontrado'}, 404

    category_id = data.get('category_id')
    if category_id and not db.session.get(Category, category_id):
        return {'error': 'Categoria não encontrada'}, 404

    task = Task(
        title=fields['title'],
        description=fields.get('description', data.get('description', '')),
        status=fields.get('status', data.get('status', 'pending')),
        priority=fields.get('priority', data.get('priority', 3)),
        user_id=user_id,
        category_id=category_id,
        due_date=fields.get('due_date'),
        tags=fields.get('tags'),
    )

    try:
        db.session.add(task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao criar task: %s', e)
        return {'error': 'Erro ao criar task'}, 500

    logger.info('Task criada: %s - %s', task.id, task.title)

    if task.user_id:
        user = db.session.get(User, task.user_id)
        if user:
            notification_service.notify_task_assigned(user, task)

    return task.to_dict(), 201


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    if not data:
        return {'error': 'Dados inválidos'}, 400

    fields, error = process_task_data(data)
    if error:
        return {'error': error}, 400

    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            return {'error': 'Usuário não encontrado'}, 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            return {'error': 'Categoria não encontrada'}, 404
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in fields:
            setattr(task, field, fields[field])

    task.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao atualizar task %s: %s', task_id, e)
        return {'error': 'Erro ao atualizar'}, 500

    logger.info('Task atualizada: %s', task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return {'error': 'Task não encontrada'}, 404

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao deletar task %s: %s', task_id, e)
        return {'error': 'Erro ao deletar'}, 500

    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(query, status, priority, user_id):
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category))

    if query:
        tasks = tasks.filter(
            db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    results = tasks.all()
    return [task.to_dict() for task in results], 200


def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    overdue_count = sum(1 for task in Task.query.all() if task.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
    return stats, 200
