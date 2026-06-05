"""Logging estruturado em JSON com nível configurável via Settings.

Expõe um `JsonFormatter` que serializa cada `LogRecord` como uma linha JSON
(campos: timestamp, level, logger, message, e, quando presente, request_id e
exception) e a função `configurar_logging`, chamada no startup, que aplica o
nível configurado (`settings.log_level`) ao root logger.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from app.core.request_context import obter_request_id

#: Campos extra (passados via `logger.info(..., extra={...})`) que são promovidos
#: ao topo do JSON quando presentes no record.
_PROMOTED_EXTRAS = ("request_id", "method", "path", "status", "latencia_ms")


class JsonFormatter(logging.Formatter):
    """Formata `LogRecord` como uma linha JSON com campos estruturados.

    Campos sempre presentes: `timestamp` (ISO 8601 UTC), `level`, `logger` e
    `message`. Campos opcionais: `request_id`, `method`, `path`, `status`,
    `latencia_ms` (quando passados via `extra`) e `exception` (quando o record
    carrega `exc_info`).
    """

    def format(self, record: logging.LogRecord) -> str:
        """Serializa o record em JSON.

        Args:
            record: registro de log a formatar.

        Returns:
            Uma string JSON (sem quebras de linha internas) representando o log.
        """
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for campo in _PROMOTED_EXTRAS:
            valor = getattr(record, campo, None)
            if valor is not None:
                payload[campo] = valor
        if "request_id" not in payload:
            request_id = obter_request_id()
            if request_id:
                payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configurar_logging(log_level: str) -> None:
    """Configura o root logger para emitir JSON no nível informado.

    Idempotente: substitui quaisquer handlers anteriores do root por um único
    `StreamHandler` com `JsonFormatter`, garantindo que `LOG_LEVEL` tenha efeito
    real sobre todo o logging da aplicação.

    Args:
        log_level: nível textual (ex.: "DEBUG", "INFO", "WARNING"); valores
            inválidos caem para "INFO".

    Side Effects:
        Reconfigura `logging.getLogger()` (root): ajusta o nível e troca os
        handlers. Não retorna nada.
    """
    nivel = logging.getLevelName(log_level.upper())
    if not isinstance(nivel, int):
        nivel = logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(nivel)
