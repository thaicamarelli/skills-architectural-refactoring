"""Composition root: monta a aplicação e liga as camadas. Nenhuma regra mora aqui."""

import logging

from flask import Flask
from flask_cors import CORS

from config.settings import settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import registrar_error_handlers
from routes.category_routes import criar_blueprint as criar_category_blueprint
from routes.report_routes import criar_blueprint as criar_report_blueprint
from routes.task_routes import criar_blueprint as criar_task_blueprint
from routes.user_routes import criar_blueprint as criar_user_blueprint
from services.notification_service import NotificationService
from utils.helpers import agora_utc

logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = settings.SECRET_KEY

CORS(app)
db.init_app(app)
registrar_error_handlers(app)

notification_service = NotificationService(settings)
task_controller = TaskController(notification_service)
user_controller = UserController(settings.SECRET_KEY)
category_controller = CategoryController()
report_controller = ReportController()

app.register_blueprint(criar_task_blueprint(task_controller))
app.register_blueprint(criar_user_blueprint(user_controller))
app.register_blueprint(criar_report_blueprint(report_controller))
app.register_blueprint(criar_category_blueprint(category_controller))


@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(agora_utc())}


@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}


with app.app_context():
    db.create_all()
    if settings.SEED_ON_BOOT:
        from seed import seed_data
        seed_data()

logger.info('aplicacao.montada debug=%s banco=%s', settings.DEBUG, settings.DATABASE_URL)

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
