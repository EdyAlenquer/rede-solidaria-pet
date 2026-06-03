"""Testes do logging estruturado (JSON) e da aplicação do nível configurado."""

import json
import logging

from app.core.logging import JsonFormatter, configurar_logging
from app.core.request_context import definir_request_id


def test_json_formatter_emite_campos_basicos() -> None:
    """O formatter serializa timestamp, level, logger e message em JSON."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.teste",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="ola %s",
        args=("mundo",),
        exc_info=None,
    )

    saida = json.loads(formatter.format(record))

    assert saida["level"] == "INFO"
    assert saida["logger"] == "app.teste"
    assert saida["message"] == "ola mundo"
    assert "timestamp" in saida
    assert "request_id" not in saida


def test_json_formatter_inclui_request_id_quando_presente() -> None:
    """Quando o record tem `request_id`, ele aparece no JSON emitido."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.teste",
        level=logging.WARNING,
        pathname=__file__,
        lineno=10,
        msg="aviso",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc-123"

    saida = json.loads(formatter.format(record))

    assert saida["request_id"] == "abc-123"


def test_json_formatter_usa_request_id_do_contexto() -> None:
    """Sem `request_id` no record, o formatter usa o request-id do contexto."""
    formatter = JsonFormatter()
    definir_request_id("ctx-id-789")
    try:
        record = logging.LogRecord(
            name="app.teste",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="mensagem",
            args=(),
            exc_info=None,
        )
        saida = json.loads(formatter.format(record))
    finally:
        definir_request_id("")

    assert saida["request_id"] == "ctx-id-789"


def test_json_formatter_serializa_excecao() -> None:
    """Records com `exc_info` incluem o traceback no campo `exception`."""
    formatter = JsonFormatter()
    try:
        raise ValueError("falha de exemplo")
    except ValueError:
        record = logging.LogRecord(
            name="app.teste",
            level=logging.ERROR,
            pathname=__file__,
            lineno=10,
            msg="erro",
            args=(),
            exc_info=logging.sys.exc_info(),
        )

    saida = json.loads(formatter.format(record))

    assert "exception" in saida
    assert "ValueError" in saida["exception"]


def test_configurar_logging_aplica_nivel_no_root_logger() -> None:
    """`LOG_LEVEL` passa a ter efeito real: o root logger fica no nível configurado."""
    root = logging.getLogger()
    nivel_original = root.level
    handlers_originais = list(root.handlers)
    try:
        configurar_logging("DEBUG")
        assert root.level == logging.DEBUG

        configurar_logging("WARNING")
        assert root.level == logging.WARNING
    finally:
        root.handlers = handlers_originais
        root.setLevel(nivel_original)


def test_configurar_logging_usa_json_formatter() -> None:
    """Após configurar, o handler do root usa o `JsonFormatter`."""
    root = logging.getLogger()
    handlers_originais = list(root.handlers)
    nivel_original = root.level
    try:
        configurar_logging("INFO")
        assert root.handlers, "esperava ao menos um handler no root"
        assert any(isinstance(h.formatter, JsonFormatter) for h in root.handlers)
    finally:
        root.handlers = handlers_originais
        root.setLevel(nivel_original)
