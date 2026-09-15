"""Rotas de Produto — fronteira HTTP: extrai a entrada, chama o controller, devolve a resposta."""

from flask import Blueprint, jsonify, request


def criar_blueprint(controller):
    blueprint = Blueprint("produtos", __name__)

    @blueprint.get("/produtos")
    def listar_produtos():
        corpo, status = controller.listar()
        return jsonify(corpo), status

    @blueprint.get("/produtos/busca")
    def buscar_produtos():
        corpo, status = controller.buscar(
            termo=request.args.get("q", ""),
            categoria=request.args.get("categoria"),
            preco_min=request.args.get("preco_min"),
            preco_max=request.args.get("preco_max"),
        )
        return jsonify(corpo), status

    @blueprint.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        corpo, status = controller.buscar_por_id(produto_id)
        return jsonify(corpo), status

    @blueprint.post("/produtos")
    def criar_produto():
        corpo, status = controller.criar(request.get_json(silent=True))
        return jsonify(corpo), status

    @blueprint.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        corpo, status = controller.atualizar(produto_id, request.get_json(silent=True))
        return jsonify(corpo), status

    @blueprint.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        corpo, status = controller.deletar(produto_id)
        return jsonify(corpo), status

    return blueprint
