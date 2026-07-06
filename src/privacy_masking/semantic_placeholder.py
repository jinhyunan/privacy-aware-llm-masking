from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


SAMPLE_SENTENCE = (
    "유선상으로 말씀하신 거래대금 120만원은 샘플은행 000-0000-000 예금주 샘플사용자로 "
    "12월 15일 오후 3시 전까지 송금해주세요. 혹시 문제가 있다면 sample.user@example.com으로 "
    "메일 보내주세요. 제 주소는 서울시 샘플구 데이터로 1길 000호입니다."
)


@dataclass(frozen=True)
class EntitySpan:
    key: str
    label: str
    original: str
    start: int
    end: int
    description: str
    display_restore: str

    @property
    def placeholder(self) -> str:
        return "{" + self.key + "}"


def find_required_span(
    text: str,
    pattern: str,
    key: str,
    label: str,
    description: str,
    display_restore: str,
) -> EntitySpan:
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"Required span not found for {key}: {pattern}")
    return EntitySpan(
        key=key,
        label=label,
        original=match.group(0),
        start=match.start(),
        end=match.end(),
        description=description,
        display_restore=display_restore,
    )


def detect_semantic_spans(text: str) -> list[EntitySpan]:
    spans = [
        find_required_span(
            text,
            r"\d+만원",
            "AMOUNT_0",
            "amount",
            "Korean won amount; do not expose the literal value to the translator.",
            "1.2 million won",
        ),
        find_required_span(
            text,
            r"샘플은행\s+\d{3}-\d{4}-\d{3}",
            "BANK_ACCOUNT_0",
            "bank_account",
            "Synthetic bank account; preserve as an opaque placeholder during translation.",
            "Sample Bank account 000-0000-000",
        ),
        find_required_span(
            text,
            r"(?<=예금주\s)샘플사용자(?=로)",
            "ACCOUNT_HOLDER_0",
            "person_name",
            "Synthetic account holder name; preserve as an opaque placeholder during translation.",
            "Sample User",
        ),
        find_required_span(
            text,
            r"\d{1,2}월\s+\d{1,2}일\s+오후\s+\d{1,2}시\s+전까지",
            "DEADLINE_0",
            "deadline",
            "Transfer deadline; only the semantic role is sent to the translator.",
            "3:00 PM on December 15",
        ),
        find_required_span(
            text,
            r"[A-Za-z0-9._%+-]+@example\.com",
            "EMAIL_0",
            "email",
            "Synthetic email address; preserve as an opaque placeholder during translation.",
            "sample.user@example.com",
        ),
        find_required_span(
            text,
            r"서울시\s+샘플구\s+데이터로\s+1길\s+000호",
            "ADDRESS_0",
            "address",
            "Synthetic Korean mailing address; preserve as an opaque placeholder during translation.",
            "000, Data-ro 1-gil, Sample-gu, Seoul",
        ),
    ]
    return sorted(spans, key=lambda span: span.start)


def replace_spans(text: str, spans: list[EntitySpan]) -> str:
    parts: list[str] = []
    cursor = 0
    for span in spans:
        if span.start < cursor:
            raise ValueError(f"Overlapping span detected: {span}")
        parts.append(text[cursor:span.start])
        parts.append(span.placeholder)
        cursor = span.end
    parts.append(text[cursor:])
    return "".join(parts)


def build_translation_prompt(masked_text: str, spans: list[EntitySpan]) -> str:
    descriptions = "\n".join(f"- {span.placeholder}: {span.description}" for span in spans)
    return (
        "Translate the Korean text into natural English.\n"
        "Keep every placeholder exactly unchanged, including braces.\n"
        "Do not infer, expand, romanize, or fabricate the hidden sensitive values.\n"
        "Use the descriptions only to understand grammar and surrounding context.\n\n"
        f"Placeholder descriptions:\n{descriptions}\n\n"
        f"Text:\n{masked_text}"
    )


def simulated_external_translation(masked_text: str) -> str:
    expected = (
        "유선상으로 말씀하신 거래대금 {AMOUNT_0}은 {BANK_ACCOUNT_0} 예금주 "
        "{ACCOUNT_HOLDER_0}로 {DEADLINE_0} 송금해주세요. 혹시 문제가 있다면 "
        "{EMAIL_0}으로 메일 보내주세요. 제 주소는 {ADDRESS_0}입니다."
    )
    if masked_text != expected:
        raise ValueError("Unexpected masked text shape; update the deterministic translation fixture.")
    return (
        "Please transfer the transaction amount {AMOUNT_0} mentioned over the phone "
        "to {BANK_ACCOUNT_0}, account holder {ACCOUNT_HOLDER_0}, by {DEADLINE_0}. "
        "If there are any issues, please email {EMAIL_0}. My address is {ADDRESS_0}."
    )


def validate_placeholders(expected: list[str], translated_text: str) -> dict[str, object]:
    expected_counts = Counter(expected)
    observed_counts = Counter(re.findall(r"\{[A-Z0-9_]+\}", translated_text))
    missing = [
        token
        for token, count in expected_counts.items()
        if observed_counts[token] < count
    ]
    extra = sorted(
        token
        for token, count in observed_counts.items()
        if count > expected_counts[token]
    )
    return {"ok": not missing and not extra, "missing": missing, "extra": extra}


def restore(translated_text: str, spans: list[EntitySpan], mode: str) -> str:
    restored = translated_text
    for span in spans:
        if mode == "literal":
            value = span.original
        elif mode == "display":
            value = span.display_restore
        else:
            raise ValueError(f"Unknown restore mode: {mode}")
        restored = restored.replace(span.placeholder, value)
    return restored


def pii_exposure_check(text: str, spans: list[EntitySpan]) -> dict[str, object]:
    leaked = [span.original for span in spans if span.original in text]
    return {"ok": not leaked, "leaked_values": leaked}


def run_demo() -> dict[str, object]:
    spans = detect_semantic_spans(SAMPLE_SENTENCE)
    masked_text = replace_spans(SAMPLE_SENTENCE, spans)
    prompt = build_translation_prompt(masked_text, spans)
    translated_with_placeholders = simulated_external_translation(masked_text)
    placeholder_validation = validate_placeholders(
        [span.placeholder for span in spans],
        translated_with_placeholders,
    )

    return {
        "source_sentence": SAMPLE_SENTENCE,
        "detected_spans": [asdict(span) | {"placeholder": span.placeholder} for span in spans],
        "masked_text_sent_to_translator": masked_text,
        "translation_prompt_sent_to_translator": prompt,
        "prompt_pii_exposure_check": pii_exposure_check(prompt, spans),
        "translated_text_received_from_translator": translated_with_placeholders,
        "placeholder_validation": placeholder_validation,
        "literal_local_restore": restore(translated_with_placeholders, spans, "literal"),
        "display_policy_local_restore": restore(translated_with_placeholders, spans, "display"),
        "notes": [
            "No external translation API is called in this demo.",
            "The translator-facing text contains placeholders and type metadata, not raw sensitive values.",
            "Literal and display-aware restoration are local post-processing steps.",
        ],
    }


def write_demo_json(path: Path) -> dict[str, object]:
    result = run_demo()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
