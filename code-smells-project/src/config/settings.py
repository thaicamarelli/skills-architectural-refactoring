"""Configuração central da aplicação, lida de variáveis de ambiente.

Nenhum segredo mora no código. Em produção (DEBUG desligado) a ausência de
SECRET_KEY é erro de boot; em desenvolvimento uma chave efêmera é gerada para
que a aplicação suba sem configuração prévia.
"""

import os
import secrets

VALORES_VERDADEIROS = ("1", "true", "yes", "on")


def _ler_bool(ambiente, chave, padrao=False):
    valor = ambiente.get(chave)
    if valor is None:
        return padrao
    return valor.strip().lower() in VALORES_VERDADEIROS


def _ler_int(ambiente, chave, padrao):
    valor = ambiente.get(chave)
    if valor is None or not valor.strip():
        return padrao
    return int(valor)


class ConfiguracaoInvalida(RuntimeError):
    """Configuração obrigatória ausente ou inválida no boot."""


class Settings:
    def __init__(self, ambiente=None):
        ambiente = ambiente if ambiente is not None else os.environ

        self.DEBUG = _ler_bool(ambiente, "DEBUG", padrao=False)
        self.HOST = ambiente.get("HOST", "127.0.0.1")
        self.PORT = _ler_int(ambiente, "PORT", 5000)
        self.DATABASE_PATH = ambiente.get("DATABASE_PATH", "loja.db")
        self.LOG_LEVEL = ambiente.get("LOG_LEVEL", "DEBUG" if self.DEBUG else "INFO")
        self.VERSAO_API = ambiente.get("VERSAO_API", "1.0.0")
        self.SEED_ON_BOOT = _ler_bool(ambiente, "SEED_ON_BOOT", padrao=True)

        origens = ambiente.get("CORS_ORIGINS", "*").strip()
        self.CORS_ORIGINS = "*" if origens == "*" else [o.strip() for o in origens.split(",") if o.strip()]

        self.SECRET_KEY = self._resolver_secret_key(ambiente)

    def _resolver_secret_key(self, ambiente):
        chave = ambiente.get("SECRET_KEY", "").strip()
        if chave:
            return chave
        if self.DEBUG:
            # Chave efêmera: válida só enquanto o processo de desenvolvimento vive.
            return secrets.token_urlsafe(32)
        raise ConfiguracaoInvalida(
            "SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY "
            "(veja .env.example) ou rode com DEBUG=true em desenvolvimento."
        )


settings = Settings()
