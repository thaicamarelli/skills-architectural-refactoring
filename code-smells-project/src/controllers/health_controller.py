"""Controller de health check.

Reporta apenas liveness e conectividade. Nenhum segredo, caminho de arquivo ou
flag de configuração aparece na resposta.
"""

import logging


class HealthController:
    def __init__(self, produto_model, usuario_model, pedido_model, versao, logger=None):
        self.produto_model = produto_model
        self.usuario_model = usuario_model
        self.pedido_model = pedido_model
        self.versao = versao
        self.logger = logger or logging.getLogger(__name__)

    def checar(self):
        contagens = {
            "produtos": self.produto_model.contar(),
            "usuarios": self.usuario_model.contar(),
            "pedidos": self.pedido_model.contar(),
        }
        return {
            "status": "ok",
            "database": "connected",
            "counts": contagens,
            "versao": self.versao,
        }, 200
