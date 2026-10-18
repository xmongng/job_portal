"""Chỉ thực thi stored function. Không sinh SELECT/INSERT/UPDATE trực tiếp lên bảng."""

import re
from types import SimpleNamespace
from typing import Any

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

Record = SimpleNamespace


def statement(function: str, params: dict, json_fields: tuple[str, ...] = ()):
    if not re.fullmatch(r"[a-z_][a-z_0-9]*", function) or any(
        not re.fullmatch(r"[a-z_][a-z_0-9]*", key) for key in params
    ):
        raise ValueError("Invalid stored-function identifier")
    # Tên function và tham số là hằng trong code backend, không nhận từ HTTP request.
    query = text(
        f"SELECT * FROM public.{function}({', '.join('p_' + key + ' => :' + key for key in params)})"
    )
    for key, value in params.items():
        if isinstance(value, dict) or key in json_fields:
            query = query.bindparams(bindparam(key, type_=JSONB))
    return query


def one(db: Session, function: str, **params: Any) -> Record | None:
    row = db.execute(statement(function, params), params).mappings().one_or_none()
    return Record(**row) if row is not None else None


def many(db: Session, function: str, **params: Any) -> list[Record]:
    return [Record(**row) for row in db.execute(statement(function, params), params).mappings()]


def execute(
    db: Session, function: str, *, json_fields: tuple[str, ...] = (), **params: Any
) -> None:
    db.execute(statement(function, params, json_fields), params)
