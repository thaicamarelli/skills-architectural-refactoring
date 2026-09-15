"""Configuração do logging da aplicação — substitui os prints espalhados."""

import logging


def configurar_logging(nivel="INFO"):
    logging.basicConfig(
        level=getattr(logging, str(nivel).upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    )
    return logging.getLogger("loja")
