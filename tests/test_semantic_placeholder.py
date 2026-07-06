import json
import subprocess
import sys
from pathlib import Path

from privacy_masking.semantic_placeholder import (
    SAMPLE_SENTENCE,
    build_translation_prompt,
    detect_semantic_spans,
    pii_exposure_check,
    replace_spans,
    restore,
    run_demo,
    validate_placeholders,
)


def test_detects_complete_synthetic_spans():
    spans = detect_semantic_spans(SAMPLE_SENTENCE)
    assert [span.key for span in spans] == [
        "AMOUNT_0",
        "BANK_ACCOUNT_0",
        "ACCOUNT_HOLDER_0",
        "DEADLINE_0",
        "EMAIL_0",
        "ADDRESS_0",
    ]
    assert [span.original for span in spans] == [
        "120만원",
        "샘플은행 000-0000-000",
        "샘플사용자",
        "12월 15일 오후 3시 전까지",
        "sample.user@example.com",
        "서울시 샘플구 데이터로 1길 000호",
    ]


def test_prompt_contains_placeholders_but_not_raw_sensitive_values():
    spans = detect_semantic_spans(SAMPLE_SENTENCE)
    masked_text = replace_spans(SAMPLE_SENTENCE, spans)
    prompt = build_translation_prompt(masked_text, spans)

    assert "{BANK_ACCOUNT_0}" in prompt
    assert "{EMAIL_0}" in prompt
    assert pii_exposure_check(prompt, spans) == {"ok": True, "leaked_values": []}


def test_placeholder_validation_detects_missing_and_extra_tokens():
    expected = ["{A_0}", "{B_0}"]
    assert validate_placeholders(expected, "value {A_0} and {B_0}") == {
        "ok": True,
        "missing": [],
        "extra": [],
    }
    assert validate_placeholders(expected, "value {A_0} and {C_0}") == {
        "ok": False,
        "missing": ["{B_0}"],
        "extra": ["{C_0}"],
    }


def test_placeholder_validation_detects_duplicate_observed_tokens():
    expected = ["{A_0}", "{B_0}"]
    assert validate_placeholders(expected, "value {A_0} {A_0} and {B_0}") == {
        "ok": False,
        "missing": [],
        "extra": ["{A_0}"],
    }


def test_restore_supports_literal_and_display_policy_modes():
    spans = detect_semantic_spans(SAMPLE_SENTENCE)
    translated = "Send {AMOUNT_0} to {BANK_ACCOUNT_0}; email {EMAIL_0}."

    literal = restore(translated, spans, "literal")
    display = restore(translated, spans, "display")

    assert "120만원" in literal
    assert "샘플은행 000-0000-000" in literal
    assert "sample.user@example.com" in literal
    assert "1.2 million won" in display
    assert "Sample Bank account 000-0000-000" in display


def test_run_demo_contract():
    result = run_demo()
    assert result["prompt_pii_exposure_check"]["ok"] is True
    assert result["placeholder_validation"]["ok"] is True
    assert result["notes"] == [
        "No external translation API is called in this demo.",
        "The translator-facing text contains placeholders and type metadata, not raw sensitive values.",
        "Literal and display-aware restoration are local post-processing steps.",
    ]


def test_run_demo_cli_writes_json(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    output_path = tmp_path / "run.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "run_demo.py"),
            "--output",
            str(output_path),
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload == run_demo()
    assert payload["prompt_pii_exposure_check"]["ok"] is True
    assert "Generated" in completed.stdout
    assert str(output_path.resolve()) in completed.stdout
