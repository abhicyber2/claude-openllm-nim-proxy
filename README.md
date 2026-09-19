# Claude Code + LiteLLM + NVIDIA NIM Proxy

A hosted multi-tenant AI proxy service that routes Claude Code through NVIDIA NIM's free inference API using LiteLLM as the protocol translator.

## Architecture

Claude Code → strip_proxy.py (:4001) → LiteLLM (:4000) → NVIDIA NIM → DeepSeek/Nemotron


## Prerequisites
- Python 3.9+
- NVIDIA NGC API key — get free at [build.nvidia.com](https://build.nvidia.com)
- Claude Code installed: `npm install -g @anthropic-ai/claude-code`

## Installation

### 1. Clone the repo
```bash
git clone https://github.com/abhicyber/claude-litellm-nim-proxy.git
cd claude-litellm-nim-proxy
```

### 2. Install dependencies
```bash
pip3 install 'litellm[proxy]' flask requests gunicorn
```

### 3. Set your NGC API key
```bash
export NGC_API_KEY="nvapi-your-key-here"
```

Add to `~/.zshrc` or `~/.bashrc` to make it permanent.

### 4. Configure LiteLLM
Edit `config.yaml` and set your preferred NIM models.
The default uses `deepseek-ai/deepseek-v4-flash-0731` for all tiers.

### 5. Start LiteLLM (Terminal 1)
```bash
litellm --config config.yaml --port 4000
```

### 6. Start strip_proxy (Terminal 2)
```bash
export ADMIN_KEY="your-admin-key"
python3 strip_proxy.py
```

### 7. Create your first API key
```bash
curl -X POST http://localhost:4001/admin/create-key \
  -H "x-admin-key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "me", "plan": "starter"}'
```

### 8. Add Claude Code alias
Add to `~/.zshrc` or `~/.bashrc`:
```bash
alias claude-ai='ANTHROPIC_API_KEY="nim-your-key-here" \
  ANTHROPIC_BASE_URL="http://localhost:4001" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="claude-opus" \
  ANTHROPIC_DEFAULT_SONNET_MODEL="claude-sonnet" \
  ANTHROPIC_DEFAULT_HAIKU_MODEL="claude-haiku" \
  CLAUDE_CODE_SUBAGENT_MODEL="claude-sonnet" \
  claude'
```

```bash
source ~/.zshrc
claude-ai --print "say hi"
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/v1/messages` | POST | Claude Code proxy |
| `/usage` | GET | Check request usage |
| `/admin/create-key` | POST | Create customer API key |

## Check Usage
```bash
curl http://localhost:4001/usage \
  -H "x-api-key: nim-your-key-here"
```

## Plans

| Plan | Requests/Month | Price |
|---|---|---|
| Starter | 5,000 | $19/mo |
| Team | 25,000 | $49/mo |
| Business | 100,000 | $149/mo |

## Production Deployment
For GCP/OCI deployment with Terraform:
👉 [claude-nim-oci-terraform](https://github.com/abhicyber/claude-nim-oci-terraform)

## Troubleshooting

**"Please run /login"**
```bash
claude logout && rm -f ~/.claude.json
```

**Auth conflict error**
```bash
unset ANTHROPIC_AUTH_TOKEN
```

**Model not found**
Check available NIM models:
```bash
curl https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer $NGC_API_KEY" | python3 -m json.tool | grep '"id"'
```

## Support This Project
⭐ Star this repo if it helped you!
📖 [Full setup guide on Gumroad](https://gumroad.com)
💼 [Hire me for cloud consulting](https://linkedin.com/in/abhicyber)

## Author
Abhishek Banerjee · [linkedin.com/in/abhicyber](https://linkedin.com/in/abhicyber)

## License
© 2026 Abhishek Banerjee. All rights reserved.
This project is not affiliated with Anthropic, NVIDIA, or any other company mentioned herein.
