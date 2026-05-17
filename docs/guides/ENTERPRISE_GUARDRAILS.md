# Enterprise Guardrails

DataContract Guard should be safe to run in enterprise environments.

---

## Principle

The agent should explain and recommend.  
It should not perform dangerous production actions without explicit approval.

---

## Filesystem Safety

Recommended controls:

- Restrict reads to configured allowed roots
- Reject path traversal attempts
- Reject absolute paths outside approved roots
- Limit file size
- Clean temporary files after processing

Example rules:

```text
Allowed: ./examples/customers.csv
Rejected: ../../etc/passwd
Rejected: /var/secrets/token
```

---

## Container Safety

Recommended Docker settings:

```yaml
read_only: true
tmpfs:
  - /tmp
cap_drop:
  - ALL
security_opt:
  - no-new-privileges:true
```

---

## LLM Safety

The LLM must not be the source of truth for validation.

Safe responsibilities:

- Explain validation issues
- Summarize impact
- Generate remediation proposals
- Generate communication messages

Unsafe responsibilities:

- Decide `PASS` or `FAIL` alone
- Modify contracts automatically
- Write into production tables
- Delete files
- Execute arbitrary SQL

---

## Secrets Management

Never expose secrets in prompts, logs, reports, or error messages.

Recommended approach:

- Use environment variables only for local development
- Use secret managers in production
- Redact secrets in logs
- Avoid sending secrets to LLM providers

---

## Human-in-the-Loop

Require human validation for sensitive actions:

- Updating a contract version
- Approving breaking changes
- Writing to production
- Creating Jira tickets automatically
- Sending provider emails automatically

---

## Logging and Tracing

Log:

- `traceId`
- request status
- validation duration
- number of issues
- severity counts
- LLM token usage if enabled

Do not log:

- secrets
- full sensitive data rows
- API keys
- credentials

---

## Recommended Production Checklist

- [ ] Allowed roots configured
- [ ] Max file size configured
- [ ] Read-only container enabled
- [ ] Secrets stored outside the repo
- [ ] LLM optional and disabled by default
- [ ] Trace IDs enabled
- [ ] Tests included in CI/CD
- [ ] Human approval required for sensitive actions
