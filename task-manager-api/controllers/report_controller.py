from datetime import timedelta

from database import db
from errors import NaoEncontrado
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import agora_utc


class ReportController:
    def resumo(self):
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        contagem_por_prioridade = dict(
            db.session.query(Task.priority, db.func.count(Task.id)).group_by(Task.priority).all()
        )
        prioridade_para_rotulo = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}

        tasks = Task.query.all()
        overdue_list = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (agora_utc() - t.due_date).days,
            }
            for t in tasks
            if t.is_overdue()
        ]

        seven_days_ago = agora_utc() - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(Task.status == 'done', Task.updated_at >= seven_days_ago).count()

        # Produtividade por usuário sem N+1: uma query agregada em vez de uma
        # busca de tasks por usuário dentro do laço.
        total_por_usuario = dict(db.session.query(Task.user_id, db.func.count(Task.id)).group_by(Task.user_id).all())
        concluidas_por_usuario = dict(
            db.session.query(Task.user_id, db.func.count(Task.id))
            .filter(Task.status == 'done')
            .group_by(Task.user_id)
            .all()
        )

        user_stats = []
        for u in User.query.all():
            total = total_por_usuario.get(u.id, 0)
            completed = concluidas_por_usuario.get(u.id, 0)
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
            })

        return {
            'generated_at': str(agora_utc()),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                rotulo: contagem_por_prioridade.get(prioridade, 0)
                for prioridade, rotulo in prioridade_para_rotulo.items()
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    def por_usuario(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NaoEncontrado('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        contagem_status = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0

        for t in tasks:
            contagem_status[t.status] = contagem_status.get(t.status, 0) + 1
            if t.priority <= 2:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': contagem_status['done'],
                'pending': contagem_status['pending'],
                'in_progress': contagem_status['in_progress'],
                'cancelled': contagem_status['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((contagem_status['done'] / total) * 100, 2) if total > 0 else 0,
            },
        }
