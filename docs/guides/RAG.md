# RAG

RAG stands for Retrieval-Augmented Generation.

In DataContract Guard, RAG can enrich the LLM Explanation Agent with internal documentation and data governance knowledge.

---

## Why RAG?

Validation detects problems.

RAG helps explain them using internal knowledge such as:

- Data quality standards
- Naming conventions
- PII policies
- Contract versioning rules
- Iceberg write guidelines
- Previous incident documentation

---

## Example

Detected issue:

```text
email is missing, mail is present
```

RAG retrieves:

```text
Internal rule: email fields are PII and must keep approved naming conventions.
Internal rule: producer-side renames require a contract version bump.
```

LLM explanation:

```text
This change is critical because the field email is classified as PII. If it is renamed to mail without contract versioning, downstream PII detection and masking rules may not apply.
```

---

## Suggested Documents to Index

```text
docs/data-quality-rules.md
docs/naming-conventions.md
docs/pii-policy.md
docs/contract-versioning.md
docs/iceberg-guidelines.md
docs/incident-playbook.md
```

---

## Suggested Stack

For local MVP:

```text
ChromaDB
Sentence Transformers or OpenAI embeddings
Local Markdown documents
```

For production:

```text
Qdrant / Pinecone / Weaviate
OpenAI embeddings or cloud embedding model
Document ingestion pipeline
Access control by workspace/team
```

---

## RAG Flow

```text
Validation Report
      ↓
Extract issue topics
      ↓
Search internal documentation
      ↓
Retrieve relevant chunks
      ↓
LLM Explanation Agent
      ↓
Context-aware explanation
```

---

## Guardrails

RAG content should be:

- versioned
- reviewed
- access-controlled
- cited in the final report when possible

Do not retrieve confidential documents unless the user has permission to access them.
