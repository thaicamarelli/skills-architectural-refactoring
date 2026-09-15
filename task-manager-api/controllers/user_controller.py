import logging

from database import db
from itsdangerous import URLSafeTimedSerializer
from config.settings import settings
from models.user import User
from models.task import Task
from utils.helpers import validate_email, VALID_ROLES, MIN_PASSWORD_LENGTH

logger = logging.getLogger(__name__)

_token_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt='auth-token')


def _generate_token(user_id):
    return _token_serializer.dumps({'user_id': user_id})


def list_users():
    users = User.query.all()
    result = []
    for user in users:
        data = user.to_dict()
        data['task_count'] = len(user.tasks)
        result.append(data)
    return result, 200


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    data = user.to_dict()
    tasks = Task.query.filter_by(user_id=user_id).all()
    data['tasks'] = [task.to_dict() for task in tasks]
    return data, 200


def create_user(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        return {'error': 'Nome é obrigatório'}, 400
    if not email:
        return {'error': 'Email é obrigatório'}, 400
    if not password:
        return {'error': 'Senha é obrigatória'}, 400
    if not validate_email(email):
        return {'error': 'Email inválido'}, 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return {'error': f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'}, 400
    if role not in VALID_ROLES:
        return {'error': 'Role inválido'}, 400
    if User.query.filter_by(email=email).first():
        return {'error': 'Email já cadastrado'}, 409

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao criar usuário: %s', e)
        return {'error': 'Erro ao criar usuário'}, 500

    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict(), 201


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    if not data:
        return {'error': 'Dados inválidos'}, 400

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            return {'error': 'Email inválido'}, 400
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            return {'error': 'Email já cadastrado'}, 409
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            return {'error': 'Senha muito curta'}, 400
        user.set_password(data['password'])

    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            return {'error': 'Role inválido'}, 400
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao atualizar usuário %s: %s', user_id, e)
        return {'error': 'Erro ao atualizar'}, 500

    return user.to_dict(), 200


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    for task in tasks:
        db.session.delete(task)

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao deletar usuário %s: %s', user_id, e)
        return {'error': 'Erro ao deletar'}, 500

    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()
    return [task.to_dict() for task in tasks], 200


def login(data):
    if not data:
        return {'error': 'Dados inválidos'}, 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return {'error': 'Email e senha são obrigatórios'}, 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return {'error': 'Credenciais inválidas'}, 401
    if not user.active:
        return {'error': 'Usuário inativo'}, 403

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': _generate_token(user.id),
    }, 200
