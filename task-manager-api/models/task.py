from database import db
from utils.helpers import agora_utc

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=agora_utc)
    updated_at = db.Column(db.DateTime, default=agora_utc, onupdate=agora_utc)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self, include_overdue=True):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }
        if include_overdue:
            data['overdue'] = self.is_overdue()
        return data

    def validate_status(self, new_status):
        return new_status in VALID_STATUSES

    def validate_priority(self, p):
        return MIN_PRIORITY <= p <= MAX_PRIORITY

    def is_overdue(self):
        if not self.due_date:
            return False
        if self.due_date >= agora_utc():
            return False
        return self.status not in ('done', 'cancelled')
