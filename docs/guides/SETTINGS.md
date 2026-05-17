# Settings

DataContract Guard should be configurable through environment variables.

---

## Example `.env`

```env
ENV=dev
LOG_LEVEL=INFO

# API
API_HOST=127.0.0.1
API_PORT=8093

# Security
ALLOWED_ROOTS=./examples,./tmp
MAX_INPUT_FILE_SIZE_MB=50
MAX_REQUEST_BODY_MB=60

# LLM, optional
LLM_ENABLED=false
OPENAI_API_KEY=
LLM_MODEL=gpt-4.1-mini

# Output
DEFAULT_OUTPUT_FORMAT=json
```

---

## General Settings

| Variable | Default | Description |
|---|---|---|
| `ENV` | `dev` | Runtime environment |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEFAULT_OUTPUT_FORMAT` | `json` | Default report format |

---

## API Settings

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `127.0.0.1` | API bind host |
| `API_PORT` | `8093` | API port |

---

## Security Settings

| Variable | Default | Description |
|---|---|---|
| `ALLOWED_ROOTS` | `./examples` | Comma-separated allowed read roots |
| `MAX_INPUT_FILE_SIZE_MB` | `50` | Max input file size |
| `MAX_REQUEST_BODY_MB` | `60` | Max API request body size |

---

## LLM Settings

| Variable | Default | Description |
|---|---|---|
| `LLM_ENABLED` | `false` | Enable or disable LLM explanation |
| `OPENAI_API_KEY` | empty | OpenAI API key, when OpenAI is used |
| `LLM_MODEL` | provider-specific | Model name |

---

## Recommended Production Practices

- Do not store API keys in the repository
- Use AWS Secrets Manager, GitLab CI variables, or another secret manager
- Keep `LLM_ENABLED=false` by default
- Use explicit allow-lists for file access
- Log trace IDs, not secrets
