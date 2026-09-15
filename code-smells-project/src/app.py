"""Composition root: monta a aplicação e liga as camadas. Nenhuma regra mora aqui."""

from flask import Flask
from flask_cors import CORS

from src.config import database, seed
from src.config.logging_config import configurar_logging
from src.config.settings import settings as settings_padrao
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_handler import registrar_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views import (
    pedido_routes,
    produto_routes,
    relatorio_routes,
    system_routes,
    usuario_routes,
)


def preparar_banco(settings, logger):
    """Cria o schema e (opcionalmente) popula o banco, com conexão própria e efêmera."""
    conexao = database.criar_conexao(settings.DATABASE_PATH)
    try:
        database.criar_schema(conexao)
        if settings.SEED_ON_BOOT:
            seed.popular(conexao, logger)
    finally:
        conexao.close()


def create_app(settings=None):
    settings = settings or settings_padrao
    logger = configurar_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.SECRET_KEY,
        DEBUG=settings.DEBUG,
        DATABASE_PATH=settings.DATABASE_PATH,
    )

    CORS(app, origins=settings.CORS_ORIGINS)
    database.registrar_ciclo_de_vida(app)
    preparar_banco(settings, logger)

    # Models recebem o provedor de conexão (uma conexão por request), não uma global.
    produto_model = ProdutoModel(database.obter_conexao)
    usuario_model = UsuarioModel(database.obter_conexao)
    pedido_model = PedidoModel(database.obter_conexao)

    notification_service = NotificationService(logger)

    produto_controller = ProdutoController(produto_model, logger)
    usuario_controller = UsuarioController(usuario_model, logger)
    pedido_controller = PedidoController(pedido_model, notification_service, logger)
    relatorio_controller = RelatorioController(pedido_model, logger)
    health_controller = HealthController(
        produto_model, usuario_model, pedido_model, settings.VERSAO_API, logger
    )

    registrar_error_handlers(app, logger)

    app.register_blueprint(produto_routes.criar_blueprint(produto_controller))
    app.register_blueprint(usuario_routes.criar_blueprint(usuario_controller))
    app.register_blueprint(pedido_routes.criar_blueprint(pedido_controller))
    app.register_blueprint(relatorio_routes.criar_blueprint(relatorio_controller))
    app.register_blueprint(system_routes.criar_blueprint(health_controller, settings.VERSAO_API))

    logger.info("aplicacao.montada debug=%s banco=%s", settings.DEBUG, settings.DATABASE_PATH)
    return app
