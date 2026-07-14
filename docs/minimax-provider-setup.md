# MiniMax Provider Setup

Edict's Model Config includes `minimax/MiniMax-M3` and `minimax/MiniMax-M2.7`. Configure the `minimax` provider in OpenClaw before assigning either model to an agent.

## Authenticate

Use the OpenClaw model authentication flow for your region:

```bash
# Global endpoint
openclaw onboard --auth-choice minimax-global-api

# China endpoint
openclaw onboard --auth-choice minimax-cn-api
```

Run only the command for the region you use. OpenClaw stores the API key in its credential store; Edict does not read or persist the key.

## Select the Endpoint and Protocol

Run one matching command pair. Each pair updates the existing `minimax` provider without replacing other configured models.

### Global OpenAI-compatible

```bash
openclaw config set models.providers.minimax.baseUrl https://api.minimax.io/v1
openclaw config set models.providers.minimax.api openai-completions
```

### Global Anthropic-compatible

```bash
openclaw config set models.providers.minimax.baseUrl https://api.minimax.io/anthropic
openclaw config set models.providers.minimax.api anthropic-messages
```

### China OpenAI-compatible

```bash
openclaw config set models.providers.minimax.baseUrl https://api.minimaxi.com/v1
openclaw config set models.providers.minimax.api openai-completions
```

### China Anthropic-compatible

```bash
openclaw config set models.providers.minimax.baseUrl https://api.minimaxi.com/anthropic
openclaw config set models.providers.minimax.api anthropic-messages
```

Keep the Anthropic-compatible base URL ending in `/anthropic`. The client appends the Messages API request path.

## Verify

```bash
openclaw models list --provider minimax
openclaw gateway restart
```

After the gateway restarts, open Edict's Model Config and select `MiniMax M3` or `MiniMax M2.7` for an agent.
