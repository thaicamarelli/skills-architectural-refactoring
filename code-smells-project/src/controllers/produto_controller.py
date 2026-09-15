"""Controller de Produto: orquestra o caso de uso e monta o corpo da resposta.

Não contém SQL e não conhece o objeto `request` — recebe dados já extraídos
pela camada de rotas.
"""

import logging

from src.errors import ErroDeValidacao, NaoEncontrado
from src.models import produto_model


class ProdutoController:
    def __init__(self, model, logger=None):
        self.model = model
        self.logger = logger or logging.getLogger(__name__)

    def listar(self):
        produtos = self.model.listar()
        self.logger.info("produto.listados total=%s", len(produtos))
        return {"dados": produtos, "sucesso": True}, 200

    def buscar_por_id(self, produto_id):
        produto = self.model.buscar_por_id(produto_id)
        if not produto:
            raise NaoEncontrado("Produto não encontrado")
        return {"dados": produto, "sucesso": True}, 200

    def buscar(self, termo="", categoria=None, preco_min=None, preco_max=None):
        preco_min = self._converter_preco(preco_min, "preco_min")
        preco_max = self._converter_preco(preco_max, "preco_max")

        resultados = self.model.buscar(termo, categoria, preco_min, preco_max)
        return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200

    def criar(self, dados):
        erros = produto_model.validar(dados)
        if erros:
            raise ErroDeValidacao(erros[0])

        produto_id = self.model.criar(
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", produto_model.CATEGORIA_PADRAO),
        )
        self.logger.info("produto.criado id=%s", produto_id)
        return {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}, 201

    def atualizar(self, produto_id, dados):
        if not self.model.buscar_por_id(produto_id):
            raise NaoEncontrado("Produto não encontrado")

        erros = produto_model.validar(dados)
        if erros:
            raise ErroDeValidacao(erros[0])

        self.model.atualizar(
            produto_id,
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", produto_model.CATEGORIA_PADRAO),
        )
        self.logger.info("produto.atualizado id=%s", produto_id)
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200

    def deletar(self, produto_id):
        if not self.model.buscar_por_id(produto_id):
            raise NaoEncontrado("Produto não encontrado")

        self.model.deletar(produto_id)
        self.logger.info("produto.deletado id=%s", produto_id)
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200

    @staticmethod
    def _converter_preco(valor, campo):
        if not valor:
            return None
        try:
            return float(valor)
        except (TypeError, ValueError):
            raise ErroDeValidacao("Parâmetro " + campo + " deve ser um número")
