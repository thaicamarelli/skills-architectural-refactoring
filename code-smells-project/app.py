"""Entry point da aplicação: só carrega a config e sobe o servidor."""

from src.app import create_app
from src.config.settings import settings

app = create_app(settings)

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
