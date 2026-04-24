# AI Telegram Consultant (Atomy)

An asynchronous Telegram bot built with **aiogram 3**, using the `gpt-4.1-mini` model (via direct OpenRouter API calls) and a local vector knowledge base (FAISS).

The bot:

* answers based on a vector knowledge base
* uses direct HTTP requests to the OpenRouter Chat Completions API
* enforces a rate limit of 10 messages per 10 minutes per user
* automatically resets limits
* stores chat history in `memory.json` in the current working directory
* keeps the last 20 history messages per user
* writes logs to the `logs/` folder in the current working directory, split into general and error logs
* is ready for fast deployment via Docker
* runs in webhook mode (without long polling)

---

## Technologies

* Python 3.13+
* aiogram 3
* OpenRouter Chat Completions API (without SDK)
* FAISS (langchain)
* uv
* Docker

---

## Local Run via Cloudflare Tunnel (uv)

### Clone the repository

```bash
git clone https://github.com/lambda19-auto/p_atomy.git
```

### Create and activate a virtual environment

```bash
uv venv
source .venv/bin/activate
```

### Install dependencies

```bash
uv sync
```
---

### Configure variables

The project already includes:

```
.env.example
```

Create a working `.env`:

```bash
cp .env.example .env
```

and fill it with:

```
OPENROUTER_API_KEY=your_key
tg_token=your_token
WEBHOOK_HOST=https://your-domain.example
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=strong_random_secret
APP_HOST=0.0.0.0
APP_PORT=8080
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

Where:
* `OPENROUTER_API_KEY` is used both for response generation and for building embeddings for user queries
* the memory file is always named `memory.json` and is created in the current working directory
* logs are always written to the `logs/` directory in the current working directory
* on startup, two files are created: `*-all-*.log` (all events) and `*-error-*.log` (errors only)
* the bot stores the last 20 messages per user (fixed default value)

---

### Start the bot

```bash
cd ai
uv run python main.py
```

Where:
* `WEBHOOK_HOST` is a public HTTPS domain (or tunnel) reachable by Telegram.
* `WEBHOOK_PATH` is the webhook endpoint path (default: `/telegram/webhook`).
* `WEBHOOK_SECRET` is the secret for the `X-Telegram-Bot-Api-Secret-Token` header.
* `APP_HOST` and `APP_PORT` are the local HTTP server address and port (default: `0.0.0.0:8080`).

### Start Cloudflare Tunnel

Run the tunnel in a separate terminal:

```bash
cloudflared tunnel --url http://localhost:8080
```

Then:

1. Take the generated URL like `https://abc123.trycloudflare.com`.
2. Set it in `.env` as `WEBHOOK_HOST`.
3. Restart the bot (`Ctrl+C` and run `uv run python main.py` again) so the webhook is set to the new address.
4. Check availability:

```bash
curl https://<your-tunnel-domain>/health
```

Expected response: `ok`.

### If the bot does not respond via Tunnel

If the bot does not respond through Cloudflare Tunnel, check:

1. The tunnel is running and proxies to the correct local app port, for example:

```bash
cloudflared tunnel --url http://localhost:8080
```

2. In `.env`, set the full new HTTPS tunnel address in `WEBHOOK_HOST` (for example, `https://abc123.trycloudflare.com`).
3. After changing the tunnel address, restart the bot so it calls `set_webhook` again.
4. Check `WEBHOOK_SECRET`: the value in `.env` must match what the bot sends to Telegram when setting the webhook.
5. Make sure the health endpoint is reachable from outside:

```bash
curl https://<your-tunnel-domain>/health
```

Expected response: `ok`.

---

## Deployment via Docker (recommended)

A ready-to-use image is published on Docker Hub.

### Pull the image

```bash
docker pull lambda19main/p_atomy:1.0.0
```

---

### Run the container

```bash
mkdir -p docker-data
docker run -d \
  --name atomy-bot \
  --restart unless-stopped \
  -p 8080:8080 \
  -v $(pwd)/docker-data:/data \
  -e OPENROUTER_API_KEY=your_key \
  -e tg_token=your_token \
  -e WEBHOOK_HOST=https://your-domain.example \
  -e WEBHOOK_PATH=/telegram/webhook \
  -e WEBHOOK_SECRET=strong_random_secret \
  -e APP_HOST=0.0.0.0 \
  -e APP_PORT=8080 \
  -e OPENROUTER_MODEL=openai/gpt-4.1-mini \
  lambda19main/p_atomy:1.0.0
```

#### Important

* `--restart unless-stopped` ensures automatic restart on failure
* environment variables are passed directly via `-e`
* the `.env` file is not used inside the container
* with `-v $(pwd)/docker-data:/data`, memory is persisted on the host as `docker-data/memory.json`
* with `-v $(pwd)/docker-data:/data`, logs are persisted on the host in `docker-data/logs/` even if the container crashes/is recreated
* the image is ready to run without additional build steps

---

## Request Limiting

* 10 messages per user
* 10-minute window
* when the limit is exceeded, the bot notifies the user
* limits reset automatically

---

