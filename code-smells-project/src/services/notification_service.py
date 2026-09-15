"""Camada de notificação — isola o I/O externo do fluxo HTTP.

Hoje a implementação apenas registra em log (mesmo comportamento observável dos
prints originais). Trocar por e-mail/SMS reais significa substituir esta classe,
sem tocar em controllers ou rotas.
"""

import logging


class NotificationService:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self.logger.info("notificacao.email pedido=%s usuario=%s", pedido_id, usuario_id)
        self.logger.info("notificacao.sms pedido=%s", pedido_id)
        self.logger.info("notificacao.push pedido=%s", pedido_id)

    def status_alterado(self, pedido_id, status):
        self.logger.info("notificacao.status pedido=%s status=%s", pedido_id, status)
