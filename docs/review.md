# Review: Prompt De-identification for LLM Translation and Analysis

## Problem

The useful data for internal analytics and LLM workflows often contains names, account-like strings, addresses, dates, money amounts, or other sensitive values. Sending the raw text to an external model is the wrong default. The safer pattern is to separate model-facing context from locally restored values.

This note uses a synthetic sentence to contrast three approaches:

1. token-style masking,
2. surrogate or Faker-style replacement,
3. semantic placeholders with local restore mapping.

## Why simple token masking is not enough

Opaque tokens such as `###QT0###` hide the value, but they also hide the role of the value. A model cannot reliably know whether the token is money, a deadline, a name, or an account. Translation and summarization quality can drop because the sentence loses semantic structure.

Token-level masking also breaks multi-token spans. Email addresses, bank-account-like strings, dates, and addresses should be handled as complete spans. If each token is replaced separately, restoration becomes fragile.

## Why surrogate replacement is not enough

Fake values can preserve grammar better than opaque tokens, but they introduce a different risk. A model may rewrite a fake name, normalize an address, alter punctuation, or partially translate the surrogate. If restoration depends on string matching, a small rewrite can break the restore step.

Surrogates are useful for testing and qualitative comparisons, but they should not be the authoritative restore mechanism.

## Recommended pattern

Use semantic placeholders plus local restoration:

```text
{AMOUNT_0}
{BANK_ACCOUNT_0}
{ACCOUNT_HOLDER_0}
{DEADLINE_0}
{EMAIL_0}
{ADDRESS_0}
```

The model-facing prompt includes only the masked text and role descriptions. The raw values remain in a local mapping.

```text
input
  -> span detection
  -> semantic placeholder replacement
  -> metadata hint prompt
  -> model result
  -> placeholder validation
  -> local restore
```

## Internal-data readiness

For internal-data analysis and LLM adoption, the important question is not only whether a model can summarize or translate. The first question is whether the data boundary is clear enough that sensitive values are not casually copied into prompts.

This repo demonstrates that boundary with a synthetic example:

- model-facing text contains placeholders,
- role metadata preserves enough context,
- known detected spans are checked before prompt handoff,
- restore is local and ID-based,
- the demo does not call external APIs; the model step is simulated.

## Limitations

This is a design-pattern demo, not a full privacy system. Production use would need stronger detection, policy review, audit logging, access control, retry behavior for malformed model output, and domain-specific rules for which values can be generalized and which must stay fully hidden.
