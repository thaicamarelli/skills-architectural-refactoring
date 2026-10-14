import logging

from itsdangerous import URLSafeTimedSerializer

from database import db
from errors import Conflito, ErroDeValidacao, NaoAutorizado, NaoEncontrado, Proibido
from models.task import Task
from models.user import VALID_ROLES, User
from utils.helpers import validate_email

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 4


class UserController:
    def __init__(self, secret_key):
        # Token assinado com a SECRET_KEY da aplicação, com expiração — real e
        # verificável, ao contrário do 'fake-jwt-token-<id>' original. Usa
        # itsdangerous (dependência que o próprio Flask já traz) em vez de
        # adicionar uma lib de JWT nova ao projeto.
        self._serializer = URLSafeTimedSerializer(secret_key, salt='task-manager-auth')

    def _gerar_token(self, user_id):
        return self._serializer.dumps({'user_id': user_id})

    def listar(self):
        users = User.query.all()
        contagens = dict(db.session.query(Task.user_id, db.func.count(Task.id)).group_by(Task.user_id).all())

        result = []
        for u in users:
            data = u.to_dict()
            data['task_count'] = contagens.get(u.id, 0)
            result.append(data)
        return result

    def buscar_por_id(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NaoEncontrado('Usuário não encontrado')

        data = user.to_dict()
        data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
        return data

    def criar(self, data):
        if not data:
            raise ErroDeValidacao('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise ErroDeValidacao('Nome é obrigatório')
        if not email:
            raise ErroDeValidacao('Email é obrigatório')
        if not password:
            raise ErroDeValidacao('Senha é obrigatória')
        if not validate_email(email):
            raise ErroDeValidacao('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ErroDeValidacao(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
        if User.query.filter_by(email=email).first():
            raise Conflito('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ErroDeValidacao('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        db.session.add(user)
        db.session.commit()
        logger.info('usuario.criado id=%s email=%s', user.id, user.email)

        return user.to_dict(), 201

    def atualizar(self, user_id, data):
        user = db.session.get(User, user_id)
        if not user:
            raise NaoEncontrado('Usuário não encontrado')
        if not data:
            raise ErroDeValidacao('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not validate_email(data['email']):
                raise ErroDeValidacao('Email inválido')
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise Conflito('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ErroDeValidacao('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ErroDeValidacao('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        logger.info('usuario.atualizado id=%s', user.id)
        return user.to_dict()

    def deletar(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NaoEncontrado('Usuário não encontrado')

        for t in Task.query.filter_by(user_id=user_id).all():
            db.session.delete(t)

        db.session.delete(user)
        db.session.commit()
        logger.info('usuario.deletado id=%s', user_id)
        return {'message': 'Usuário deletado com sucesso'}

    def tasks_do_usuario(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NaoEncontrado('Usuário não encontrado')
        return [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]

    def login(self, data):
        if not data:
            raise ErroDeValidacao('Dados inválidos')

        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise ErroDeValidacao('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise NaoAutorizado('Credenciais inválidas')
        if not user.active:
            raise Proibido('Usuário inativo')

        logger.info('login.sucesso usuario=%s', user.id)
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': self._gerar_token(user.id),
        }
