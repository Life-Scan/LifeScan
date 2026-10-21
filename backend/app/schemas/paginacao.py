"""Paginação opcional para manter compatibilidade com os seletores existentes."""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

Item = TypeVar("Item")


class Pagina(BaseModel, Generic[Item]):
    itens: list[Item]
    pagina: int
    tamanho: int
    total: int
    paginas: int


class Paginacao:
    def __init__(
        self,
        pagina: int | None = Query(None, ge=1),
        tamanho: int = Query(20, ge=1, le=100),
    ):
        self.pagina = pagina
        self.tamanho = tamanho


def dados_pagina(itens, pagina: int, tamanho: int, total: int) -> dict:
    return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total, "paginas": max(1, (total + tamanho - 1) // tamanho)}


def paginar(sessao: Session, consulta, parametros: Paginacao):
    if parametros.pagina is None:
        return list(sessao.scalars(consulta).unique())
    total = sessao.scalar(select(func.count()).select_from(consulta.order_by(None).subquery()))
    paginas = max(1, (total + parametros.tamanho - 1) // parametros.tamanho)
    pagina = min(parametros.pagina, paginas)
    itens = list(sessao.scalars(consulta.limit(parametros.tamanho).offset((pagina - 1) * parametros.tamanho)).unique())
    return dados_pagina(itens, pagina, parametros.tamanho, total)
