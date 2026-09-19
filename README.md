# Claude Code + LiteLLM + NVIDIA NIM Proxy

A hosted multi-tenant AI proxy service that routes Claude Code 
through NVIDIA NIM's free inference API using LiteLLM as the 
protocol translator.

## Architecture

Claude Code → strip_proxy.py (:4001) → LiteLLM (:4000) → NVIDIA NIM


## Files
- `strip_proxy.py` — Custom Flask proxy that authenticates customers,
  strips unsupported Anthropic params, normalizes model names, and 
  tracks usage per customer in SQLite
- `config.yaml` — LiteLLM configuration for model routing and fallbacks

## Installation
```bash
pip install 'litellm[proxy]' flask requests gunicorn
```

## Usage
```bash
# Terminal 1
litellm --config config.yaml --port 4000

# Terminal 2
python strip_proxy.py

# Claude Code alias
alias claude-ai='ANTHROPIC_API_KEY="your-nim-key" ANTHROPIC_BASE_URL="http://your-server" claude'
```

## Deployment
Deployed on GCP e2-micro us-central1 Always Free tier — $0/month.
Full Terraform: github.com/abhicyber/claude-nim-oci-terraform

## Author
Abhishek Banerjee · linkedin.com/in/abhicyber

## License
© 2026 Abhishek Banerjee. All rights reserved.
