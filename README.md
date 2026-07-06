# privacy-aware-llm-masking

Synthetic demo of a privacy-aware LLM workflow: replace sensitive spans with semantic placeholders, give the model only metadata hints, validate placeholder preservation, and restore values locally.

## Why this exists

Internal operational data is often the most useful source for analysis and LLM-assisted workflows, but it cannot be treated as ordinary prompt text. Before sending any text to an external model, the system needs a clear boundary:

1. detect sensitive spans,
2. replace them with meaningful placeholders,
3. send only role-level metadata to the model,
4. verify the placeholders survived,
5. restore or display values locally under an explicit policy.

This repository is a public, synthetic reconstruction of that design thinking. In real work, I have used masked data for analysis so that internal information can be studied without directly exposing raw sensitive values. This repo does not include any internal company data, customer data, project names, credentials, or production samples.

## Core idea

Naive masking such as `###QT0###` protects the raw value, but it removes the semantic role the model needs for useful translation or summarization. A better prompt boundary is:

```text
{AMOUNT_0}
{BANK_ACCOUNT_0}
{ACCOUNT_HOLDER_0}
{DEADLINE_0}
{EMAIL_0}
{ADDRESS_0}
```

The model sees placeholders and descriptions, not the original values. Restoration is performed locally from an ID-based mapping.

## Demo flow

```text
synthetic Korean sentence
  -> rule-based sensitive span detection
  -> semantic placeholder replacement
  -> metadata hint prompt
  -> no raw-value exposure check
  -> simulated external translation
  -> placeholder validation
  -> local restore
```

The demo intentionally does not call an external LLM API.

## Run

```bash
python3 scripts/run_demo.py
```

The command writes:

```text
examples/semantic_placeholder_run.json
```

## Test

```bash
python3 -m pytest
```

## What this demonstrates

- Privacy-aware prompt construction for LLM workflows
- Internal-data readiness before analytics or LLM automation
- Span-level masking instead of token-by-token replacement
- Semantic placeholders that preserve enough context for a model
- Local restore mapping as the source of truth
- Guardrails for placeholder loss and accidental prompt exposure

## What this is not

- It is not a compliance product.
- It is not a legal guarantee of de-identification.
- It is not a production NER system.
- It does not include real internal data.
- It does not send data to any external model.

## Notes

The example sentence is synthetic. It is shaped like an operational message because the purpose is to demonstrate the boundary design, not to disclose any real data.
