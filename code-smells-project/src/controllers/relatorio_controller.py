"""Controller de Relatórios: aplica as regras de venda sobre os agregados do Model."""

import logging

# Faixas de desconto: (faturamento mínimo, percentual aplicado).
# Avaliadas da maior para a menor — a primeira que couber vence.
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))
CASAS_DECIMAIS = 2


def calcular_desconto(faturamento):
    for faturamento_minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return faturamento * percentual
    return 0


class RelatorioController:
    def __init__(self, pedido_model, logger=None):
        self.pedido_model = pedido_model
        self.logger = logger or logging.getLogger(__name__)

    def vendas(self):
        resumo = self.pedido_model.resumo_vendas()

        faturamento = resumo["faturamento"]
        total_pedidos = resumo["total_pedidos"]
        desconto = calcular_desconto(faturamento)

        relatorio = {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
            "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
            "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos > 0 else 0,
        }

        return {"dados": relatorio, "sucesso": True}, 200
