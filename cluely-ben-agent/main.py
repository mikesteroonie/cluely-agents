from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from threading import Thread
import uuid
# import ngrok  # Uncomment for local development with ngrok

from flask import Flask, request, Response

from agentmail import AgentMail
from agentmail_toolkit.openai import AgentMailToolkit
from agents import WebSearchTool, Agent, Runner

port = int(os.getenv("PORT", 8080))
username = os.getenv("INBOX_USERNAME")
display_name = os.getenv("DISPLAY_NAME")
inbox = f"{username}@agentmail.to"
# domain = os.getenv("WEBHOOK_DOMAIN")  # Optional: set a custom ngrok domain

if not username:
    print("⚠️  WARNING: INBOX_USERNAME is not set!")
    print("   Make sure your .env file contains: INBOX_USERNAME=ben-cluely")

client_id = "ben-cluely-agent-1"

# === NGROK SETUP (for local development) ===
# Uncomment the following block to use ngrok for local development:
#
# print(f"🚀 Starting ngrok tunnel on port {port}...")
# if domain:
#     listener = ngrok.forward(port, domain=domain, authtoken_from_env=True)
# else:
#     listener = ngrok.forward(port, authtoken_from_env=True)
# 
# webhook_url = listener.url()
# print(f"🌐 Ngrok tunnel URL: {webhook_url}")


# === NGROK SETUP (for local development) ===
# try:
#     with open("system_prompt.txt", "r") as f:
#         system_prompt = f.read()
#     instructions = system_prompt.strip().replace("{inbox}", inbox_address)
#     print("✅ System prompt loaded from system_prompt.txt")
# except FileNotFoundError:
#     print("⚠️  WARNING: system_prompt.txt file not found!")


webhook_url = os.getenv("WEBHOOK_URL")

app = Flask(__name__)

client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

inbox_obj = client.inboxes.create(username=username, display_name=display_name, client_id=client_id) 
inbox_address = f"{username}@agentmail.to"


webhook = client.webhooks.create(
    url=webhook_url,
    inbox_ids=[inbox_obj.inbox_id],
    event_types=["message.received"],
    client_id="ben-cluely-agent-webhook",
)

system_prompt = os.getenv("SYSTEM_PROMPT")
if system_prompt:
    instructions = system_prompt.strip().replace("{inbox}", inbox_address)
    print("System prompt loaded from environment variable")
else:
    print("WARNING: SYSTEM_PROMPT environment variable not set!")


agent = Agent(
    name="Ben Cluely Agent",
    instructions=instructions,
    tools=AgentMailToolkit(client).get_tools() + [WebSearchTool()],
)

@app.route("/", methods=["POST"])
def receive_webhook_root():
    import sys
    print("🔔 WEBHOOK RECEIVED!", flush=True)
    print(f"📧 Webhook payload: {request.json}", flush=True)
    sys.stdout.flush()
    Thread(target=process_webhook, args=(request.json,)).start()
    return Response(status=200)

@app.route("/", methods=["GET"])
def root_get():
    return Response("Ben Cluely Agent Webhook Endpoint", status=200)


def process_webhook(payload):
    import sys
    email = payload["message"]
    thread_id = email.get("thread_id")
    
    print(f"📬 Email from: {email.get('from', 'Unknown')}", flush=True)
    print(f"📝 Subject: {email.get('subject', '(No subject)')}", flush=True)
    print(f"🔗 Thread ID: {thread_id or 'None'}", flush=True)
    sys.stdout.flush()
    
    try:
        thread = client.inboxes.threads.get(inbox_id=inbox_obj.inbox_id, thread_id=thread_id)
        print(f"🔍 DEBUG: Fetched thread {thread_id} with {len(thread.messages)} messages")
        
        thread_context = []
        for msg in thread.messages:
            # In AgentMail, messages from external senders are "user" messages
            # Messages sent from your inbox are "assistant" messages
            message_content = msg.text or msg.html or "No content"
            
            # Check if this message is from an external sender (not from your inbox)
            if hasattr(msg, 'from_') and msg.from_ and not msg.from_.endswith('@agentmail.to'):
                thread_context.append({"role": "user", "content": message_content})
            else:
                # This is a message from your inbox (assistant)
                thread_context.append({"role": "assistant", "content": message_content})
        
        print(f"🔍 DEBUG: Thread context has {len(thread_context)} messages")
        
    except Exception as e:
        print(f"⚠️  Error fetching thread {thread_id}: {e}")
        thread_context = []

    # Include attachment info if present
    attachments_info = ""
    if email.get("attachments"):
        attachments_info = "\nAttachments:\n"
        for att in email["attachments"]:
            attachments_info += f"- {att['filename']} (ID: {att['attachment_id']}, Type: {att['content_type']}, Size: {att['size']} bytes)\n"
    
    prompt = f"""
From: {email.get("from", "Unknown sender")}
Subject: {email.get("subject", "(No subject)")}
Body:\n{email.get("text", "(No text content)")}
{attachments_info}

IMPORTANT FOR TOOL CALLS:
- THREAD_ID: {email.get("thread_id", "N/A")}
- MESSAGE_ID: {email.get("message_id", "N/A")}

Use these EXACT values when calling get_thread and get_attachment tools.
"""
    
    print("Prompt:\n\n", prompt, "\n")
    print(f"🔍 DEBUG: Sending {len(thread_context)} context messages to agent")
    for i, ctx in enumerate(thread_context):
        print(f"   Context {i}: {ctx['role']} - {ctx['content'][:100]}...")

    # Pass the actual thread context to the agent
    try:
        response = asyncio.run(Runner.run(agent, thread_context + [{"role": "user", "content": prompt}]))
        print(f"✅ Agent response: {response.final_output}", flush=True)
        sys.stdout.flush()
        
        # Check if response contains error-like text
        if "error" in response.final_output.lower() or "here it goes" in response.final_output.lower():
            print("⚠️  WARNING: Response contains potential error text!", flush=True)
            sys.stdout.flush()
            
    except Exception as e:
        print(f"❌ ERROR running agent: {e}")
        return

   
    client.inboxes.messages.reply(
        inbox_id=inbox_obj.inbox_id,
        message_id=email["message_id"],
        html=response.final_output,
    )
      


if __name__ == "__main__":
    print(f"Inbox: {inbox_address}\n")
    print(f"Starting server on port {port}")

    app.run(host="0.0.0.0", port=port)
