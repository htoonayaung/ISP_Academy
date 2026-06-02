import pytest

from app.adapters.ai_provider import parse_ai_json_response


def test_parser_handles_fenced_json() -> None:
    parsed = parse_ai_json_response('```json\n{"lab_name": "x"}\n```')

    assert parsed == {"lab_name": "x"}


def test_parser_handles_text_around_json() -> None:
    parsed = parse_ai_json_response('Here is the plan: {"lab_name": "x", "nodes": []} done.')

    assert parsed["lab_name"] == "x"


def test_parser_handles_trailing_commas() -> None:
    parsed = parse_ai_json_response('{"lab_name": "x", "nodes": [],}')

    assert parsed["nodes"] == []


def test_parser_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_ai_json_response("not json at all")
