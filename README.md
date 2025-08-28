# Cluely Agents

A collection of runnable email-first AI agents. Each agent lives in its own subdirectory and can be configured with a system prompt and API keys.

## Prerequisites

- Python 3.11+
- AgentMail API key (`AGENTMAIL_API_KEY`)
- OpenAI API key (`OPENAI_API_KEY`)
- **For Production**: Webhook URL (`WEBHOOK_URL`) for receiving AgentMail webhooks
- **For Local Development**: Ngrok account/token (optional)

## Common Setup

1. Choose an agent directory (e.g., `cluely-ben-agent/`).
2. Create a `.env` file in that agent directory with at least:

   ```sh
   AGENTMAIL_API_KEY=your-agentmail-api-key
   OPENAI_API_KEY=your-openai-api-key
   INBOX_USERNAME=your-inbox-username
   DISPLAY_NAME=Your Agent Name

   # For production deployment (Render, Railway, etc.):
   WEBHOOK_URL=https://your-app.onrender.com

   # For local development with ngrok (uncomment ngrok code in main.py):
   # NGROK_AUTHTOKEN=your-ngrok-authtoken
   # WEBHOOK_DOMAIN=your-custom-domain.ngrok-free.app  # optional
   ```

3. Optionally add a `system_prompt.txt` file in the agent directory to customize the agent’s behavior and tone.
4. From the agent directory, create and activate a virtual environment and install deps:
   ```sh
   uv venv
   source .venv/bin/activate
   uv pip install .
   ```

## Running an Agent

From the specific agent directory:

```sh
python main.py
```

- Agents typically read configuration from `.env` and, if present, `system_prompt.txt`.
- The agent will automatically create an AgentMail inbox and webhook using the configured URL.

### For Local Development with Ngrok

1. Install ngrok: `pip install pyngrok` (or add to requirements.txt)
2. In `main.py`, uncomment the ngrok import and ngrok setup block
3. Comment out the `WEBHOOK_URL` line and use the ngrok-generated URL instead
4. Set `NGROK_AUTHTOKEN` in your `.env` file

### For Production Deployment

- Set `WEBHOOK_URL` to your deployed app's URL
- The ngrok code will be ignored since it's commented out

## Repository Layout

- `cluely-ben-agent/` – Example agent implementation
- Additional agents can be added as sibling directories, each with its own `main.py`, `pyproject.toml`, `requirements.txt`, and optional `system_prompt.txt`.

## Deploying to Render

1. Connect your `cluely-agents` repository to Render
2. Create a new Web Service with these settings:
   - **Root Directory**: `cluely-ben-agent` (or your agent's directory)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
3. Set environment variables in Render dashboard:
   - `AGENTMAIL_API_KEY`
   - `OPENAI_API_KEY`
   - `WEBHOOK_URL` (use your Render app URL, e.g., `https://your-app.onrender.com`)
   - `INBOX_USERNAME`
   - `DISPLAY_NAME`
4. Deploy and your agent will be live!

## Adding a New Agent

1. Create a new directory at the repo root (e.g., `my-new-agent/`).
2. Include at minimum:
   - `main.py` – entry point
   - `requirements.txt` or `pyproject.toml`
   - Optional: `system_prompt.txt`, `README.md`
3. Follow the Common Setup and Running steps above.

## Security

- Do not commit `.env` or secrets. The root `.gitignore` is configured to ignore `.env` and `system_prompt.txt` in all subdirectories.
- Rotate keys regularly and use separate keys per environment.

## Contributing

- Open a PR adding a new agent or improving existing ones.
- Keep each agent self-contained.
