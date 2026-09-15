"""Controller de Pedido: valida a entrada, coordena o Model e dispara notificações.

O envio de notificação é delegado ao Service — o controller não sabe se o canal
é e-mail, SMS ou log.
"""

import logging

from src.errors import ErroDeValidacao
from src.models.pedido_model import STATUS_VALIDOS

STATUS_QUE_NOTIFICAM = ("aprovado", "cancelado")


class PedidoController:
    def __init__(self, model, notification_service, logger=None):
        self.model = model
        self.notification_service = notification_service
        self.logger = logger or logging.getLogger(__name__)

    def listar(self):
        return {"dados": self.model.listar(), "sucesso": True}, 200

    def listar_por_usuario(self, usuario_id):
        return {"dados": self.model.listar_por_usuario(usuario_id), "sucesso": True}, 200

    def criar(self, dados):
        if not dados:
            raise ErroDeValidacao("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            raise ErroDeValidacao("Usuario ID é obrigatório")
        if not itens or len(itens) == 0:
            raise ErroDeValidacao("Pedido deve ter pelo menos 1 item")

        self._validar_itens(itens)

        resultado = self.model.criar(usuario_id, itens)
        self.logger.info("pedido.criado id=%s usuario=%s", resultado["pedido_id"], usuario_id)
        self.notification_service.pedido_criado(resultado["pedido_id"], usuario_id)

        return {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }, 201

    def atualizar_status(self, pedido_id, dados):
        novo_status = (dados or {}).get("status", "")

        if novo_status not in STATUS_VALIDOS:
            raise ErroDeValidacao("Status inválido")

        self.model.atualizar_status(pedido_id, novo_status)
        self.logger.info("pedido.status pedido=%s status=%s", pedido_id, novo_status)

        if novo_status in STATUS_QUE_NOTIFICAM:
            self.notification_service.status_alterado(pedido_id, novo_status)

        return {"sucesso": True, "mensagem": "Status atualizado"}, 200

    @staticmethod
    def _validar_itens(itens):
        """Garante a forma dos itens antes de chegar ao Model (antes virava erro 500)."""
        if not isinstance(itens, list):
            raise ErroDeValidacao("Itens deve ser uma lista")

        for posicao, item in enumerate(itens, start=1):
            if not isinstance(item, dict):
                raise ErroDeValidacao("Item " + str(posicao) + " inválido")
            if "produto_id" not in item:
                raise ErroDeValidacao("Item " + str(posicao) + ": produto_id é obrigatório")
            if "quantidade" not in item:
                raise ErroDeValidacao("Item " + str(posicao) + ": quantidade é obrigatória")
            quantidade = item["quantidade"]
            if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
                raise ErroDeValidacao("Item " + str(posicao) + ": quantidade deve ser um inteiro positivo")
