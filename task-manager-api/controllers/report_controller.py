from collections import defaultdict
from datetime import datetime, timedelta, timezone

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import calculate_percentage


def summary_report():
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    all_tasks = Task.query.all()

    tasks_by_status = defaultdict(int)
    tasks_by_priority = defaultdict(int)
    tasks_by_user = defaultdict(list)
    overdue_list = []

    for task in all_tasks:
        tasks_by_status[task.status] += 1
        tasks_by_priority[task.priority] += 1
        if task.user_id:
            tasks_by_user[task.user_id].append(task)
        if task.is_overdue():
            overdue_list.append({
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (datetime.now(timezone.utc) - task.due_date.replace(tzinfo=timezone.utc)).days,
            })

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    user_stats = []
    for user in User.query.all():
        user_tasks = tasks_by_user.get(user.id, [])
        total = len(user_tasks)
        completed = sum(1 for task in user_tasks if task.status == 'done')
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    report = {
        'generated_at': str(datetime.now(timezone.utc)),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': tasks_by_status['pending'],
            'in_progress': tasks_by_status['in_progress'],
            'done': tasks_by_status['done'],
            'cancelled': tasks_by_status['cancelled'],
        },
        'tasks_by_priority': {
            'critical': tasks_by_priority[1],
            'high': tasks_by_priority[2],
            'medium': tasks_by_priority[3],
            'low': tasks_by_priority[4],
            'minimal': tasks_by_priority[5],
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
    return report, 200


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {'error': 'Usuário não encontrado'}, 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    counts_by_status = defaultdict(int)
    overdue = 0
    high_priority = 0

    for task in tasks:
        counts_by_status[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    total = len(tasks)
    done = counts_by_status['done']

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': counts_by_status['pending'],
            'in_progress': counts_by_status['in_progress'],
            'cancelled': counts_by_status['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total),
        },
    }
    return report, 200
