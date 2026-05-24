# LLM Explanation Agent

The LLM Explanation Agent enriches deterministic validation output with human-readable explanations, impact analysis, and remediation plans.

## Core Principle

The LLM does not decide whether the dataset passes or fails.

```text
Deterministic Engine → PASS / FAIL
LLM Explanation Agent → Explanation / Impact / Recommendation
```

## Responsibilities

The LLM Explanation Agent can:

- Summarize detected issues
- Explain likely causes
- Classify business and technical impacts
- Propose remediation plans
- Generate PySpark or SQL correction examples
- Generate provider communication messages
- Generate pull request descriptions

## Input

The agent receives structured deterministic output.

Example:

```json
{
  "status": "FAIL",
  "issues": [
    {
      "severity": "CRITICAL",
      "type": "MISSING_COLUMN",
      "column": "email",
      "message": "Required column email is missing",
      "suggestion": "Column mail may be a rename candidate"
    }
  ]
}
```

## Output

```json
{
  "summary": "The dataset does not respect the expected contract.",
  "probableCauses": [
    "The producer may have renamed email to mail without versioning the contract."
  ],
  "impacts": [
    "Spark or Iceberg ingestion may fail.",
    "Downstream joins using email may be broken.",
    "PII controls may not be applied correctly."
  ],
  "correctionPlan": [
    "Confirm whether mail replaces email.",
    "Rename mail to email before ingestion if the change is accidental.",
    "Update the contract to version 1.1.0 if the change is intentional."
  ]
}
```

## Example Prompt Template

```text
You are a data quality and data contract assistant.

Your task is to explain validation issues produced by a deterministic validation engine.

Rules:
- Do not change the validation status.
- Do not invent issues that are not in the input.
- Explain the likely cause.
- Explain business and technical impact.
- Propose safe remediation steps.
- Generated code must be treated as a proposal.

Validation report:
{{validation_report_json}}
```

## LLM Disabled Mode

When LLM is disabled, the system should still return:

- validation status
- issues
- deterministic suggestions
- generated code from rule-based templates

This makes the project usable without external API keys.

## Safe Usage

Do not send secrets, credentials, or sensitive raw data to the LLM.

Recommended approach:

- Send schema and issue metadata
- Avoid sending full rows
- Mask sample values when needed
- Redact PII in prompts
