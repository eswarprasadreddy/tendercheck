import json
import pytest
from unittest.mock import MagicMock

from app.llm.validators import LLMOutputError, extract_json_block, validate_llm_json
from app.schemas.requirement import LLMRequirement, LLMRequirementList
from app.services.requirement_parser import RequirementParser, load_sector_config


def test_extract_json_block():
    raw_markdown = "```json\n{\"requirements\": []}\n```"
    assert extract_json_block(raw_markdown) == '{"requirements": []}'

    raw_plain = '{"requirements": []}'
    assert extract_json_block(raw_plain) == '{"requirements": []}'


def test_load_sector_config():
    # IT hardware sector config loads properly
    config = load_sector_config("it_hardware")
    assert config["sector_id"] == "it_hardware"
    assert "known_certificates" in config
    assert "known_specs" in config
    assert len(config["known_specs"]) >= 5

    # Unknown sector falls back to generic config without crashing
    unknown = load_sector_config("medical_devices")
    assert unknown["sector_id"] == "medical_devices"


def test_parser_extract_success(sample_extracted_requirements_json: str):
    mock_client = MagicMock()
    mock_client.generate_json.return_value = sample_extracted_requirements_json

    parser = RequirementParser(client=mock_client, sector_id="it_hardware")
    requirements = parser.extract(tender_text="Dummy tender text", page_count=3)

    assert len(requirements) >= 10
    categories = {r.category for r in requirements}
    assert "financial" in categories
    assert "technical_spec" in categories
    assert "certification" in categories

    req_types = {r.requirement_type for r in requirements}
    assert "numeric" in req_types
    assert "spec" in req_types
    assert "certification" in req_types

    # Find turnover requirement
    turnover = next(r for r in requirements if r.sector_key == "annual_turnover")
    assert turnover.operator == ">="
    assert turnover.value["amount"] == 15000000.0

    # Find RAM requirement
    ram = next(r for r in requirements if r.sector_key == "ram_gb")
    assert ram.operator == ">="
    assert ram.value["amount"] == 16.0
    assert ram.value["unit"] == "GB"


def test_parser_retries_once_on_invalid_json(sample_extracted_requirements_json: str):
    mock_client = MagicMock()
    # First response is invalid JSON, second response is valid JSON
    mock_client.generate_json.side_effect = [
        "INVALID JSON {not json}",
        sample_extracted_requirements_json,
    ]

    parser = RequirementParser(client=mock_client, sector_id="it_hardware")
    requirements = parser.extract(tender_text="Dummy text", page_count=3)

    assert len(requirements) >= 10
    assert mock_client.generate_json.call_count == 2


def test_parser_fails_after_two_invalid_attempts():
    mock_client = MagicMock()
    # Both responses are invalid
    mock_client.generate_json.side_effect = [
        "INVALID JSON 1",
        "INVALID JSON 2",
    ]

    parser = RequirementParser(client=mock_client, sector_id="it_hardware")
    with pytest.raises(LLMOutputError) as exc_info:
        parser.extract(tender_text="Dummy text", page_count=3)

    assert "LLM returned invalid JSON after 2 attempts" in str(exc_info.value)
    assert mock_client.generate_json.call_count == 2
