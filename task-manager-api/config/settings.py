"""Configuração central, lida de variáveis de ambiente (T1 do playbook).

Nenhum segredo obrigatório tem valor fixo como fallback. Fora do modo de
desenvolvimento (DEBUG=false), a ausência de SECRET_KEY falha o boot com uma
mensagem clara — nunca cai silenciosamente em um valor fixo, nem literal nem
escondido dentro de um default de os.environ.get(...).
"""

import os
import secrets

from dotenv import load_dotenv

load_dotenv()


class ConfiguracaoInvalida(RuntimeError):
    """Configuração obrigatória ausente ou inválida no boot."""


def _ler_bool(nome, padrao=False):
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ('1', 'true', 'yes', 'on')


def _resolver_secret_key(debug):
    chave = os.environ.get('SECRET_KEY', '').strip()
    if chave:
        return chave
    if debug:
        # Chave efêmera: só vale enquanto o processo de desenvolvimento vive.
        return secrets.token_urlsafe(32)
    raise ConfiguracaoInvalida(
        "SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY "
        "(veja .env.example) ou rode com DEBUG=true em desenvolvimento."
    )


class Settings:
    DEBUG = _ler_bool('DEBUG', padrao=False)
    SECRET_KEY = _resolver_secret_key(DEBUG)

    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', '5000'))

    # Credenciais de SMTP: sem default que finja ser um segredo real. Ficam
    # vazias se não configuradas — o envio de notificação por e-mail é best
    # effort (NotificationService já trata falha de envio) e não é pré-
    # requisito para o boot da API, diferente de SECRET_KEY.
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    SEED_ON_BOOT = _ler_bool('SEED_ON_BOOT', padrao=False)


settings = Settings()
