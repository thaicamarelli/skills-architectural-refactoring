import re

from models.task import Task, VALID_STATUSES

VALID_ROLES = ('user', 'admin', 'manager')
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'

EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(email and EMAIL_RE.match(email))


def parse_date(date_string):
    from datetime import datetime

    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def process_task_data(data, existing_task=None):
    result = {}

    if 'title' in data:
        title = (data['title'] or '').strip()
        if not title:
            return None, 'Título não pode ser vazio'
        if not (MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH):
            return None, f'Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres'
        result['title'] = title

    if 'description' in data:
        result['description'] = data['description']

    if 'status' in data:
        if not Task.validate_status(data['status']):
            return None, 'Status inválido'
        result['status'] = data['status']

    if 'priority' in data:
        try:
            priority = int(data['priority'])
        except (TypeError, ValueError):
            return None, 'Prioridade inválida'
        if not Task.validate_priority(priority):
            return None, 'Prioridade deve ser entre 1 e 5'
        result['priority'] = priority

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                return None, 'Data inválida. Use YYYY-MM-DD'
            result['due_date'] = parsed
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        result['tags'] = ','.join(tags) if isinstance(tags, list) else tags

    return result, None


__all__ = [
    'VALID_STATUSES',
    'VALID_ROLES',
    'MAX_TITLE_LENGTH',
    'MIN_TITLE_LENGTH',
    'MIN_PASSWORD_LENGTH',
    'DEFAULT_PRIORITY',
    'DEFAULT_COLOR',
    'calculate_percentage',
    'validate_email',
    'parse_date',
    'process_task_data',
]
