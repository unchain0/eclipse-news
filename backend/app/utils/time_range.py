"""Utilitários para manipulação de intervalos de tempo."""

import re
from datetime import timedelta

from fastapi import HTTPException


def parse_time_range(time_range: str) -> timedelta:
    """Converte string de tempo para timedelta.

    Args:
        time_range: String no formato '{número}{unidade}' onde:
            - número: inteiro positivo
            - unidade: 'h' (horas), 'd' (dias), 'w' (semanas), 'm' (meses ~30 dias)

    Returns:
        timedelta: Objeto representando o período de tempo.

    Raises:
        HTTPException: Se o formato for inválido.

    Examples:
        >>> parse_time_range("1h")
        timedelta(hours=1)
        >>> parse_time_range("7d")
        timedelta(days=7)
        >>> parse_time_range("2w")
        timedelta(weeks=2)
        >>> parse_time_range("3m")
        timedelta(days=90)
    """
    pattern = r"^(\d+)(h|d|w|m)$"
    match = re.match(pattern, time_range.lower())

    if not match:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Formato de time_range inválido: '{time_range}'. "
                "Use o formato: {número}{unidade} (ex: 1h, 7d, 2w, 3m). "
                "Unidades válidas: h (horas), d (dias), w (semanas), m (meses)"
            ),
        )

    value, unit = match.groups()
    value = int(value)

    if value <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"O valor deve ser positivo, recebido: {value}",
        )

    match unit:
        case "h":
            return timedelta(hours=value)
        case "d":
            return timedelta(days=value)
        case "w":
            return timedelta(weeks=value)
        case "m":
            return timedelta(days=value * 30)  # Aproximação de 30 dias por mês
        case _:
            # Nunca deve chegar aqui devido ao regex, mas por segurança
            raise HTTPException(
                status_code=400,
                detail=f"Unidade inválida: '{unit}'",
            )
