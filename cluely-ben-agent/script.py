from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
import time
from datetime import datetime

from agentmail import AgentMail
from agentmail_toolkit.openai import AgentMailToolkit
from agents import WebSearchTool, Agent, Runner

username = os.getenv("INBOX_USERNAME")
inbox_address = f"{username}@agentmail.to"

if not username:
    print("⚠️  WARNING: INBOX_USERNAME is not set!")
    print("   Make sure your .env file contains: INBOX_USERNAME=hiring-test")
    exit(1)

client_id = "hiring-agent-1"

client = AgentMail(api_key=os.getenv("AGENTMAIL_API_KEY"))

print(f"🔍 Setting up inbox for {inbox_address}")
inbox_obj = client.inboxes.create(username=username, client_id=client_id) 
print(f"✅ Inbox ready: {inbox_obj.inbox_id}")

system_prompt = open("system_prompt.txt", "r").read()
if system_prompt:
    instructions = system_prompt.strip().replace("{inbox}", inbox_address)
    print("System prompt loaded from environment variable")
else:
    print("WARNING: SYSTEM_PROMPT environment variable not set!")
    # Fallback to a basic prompt
    instructions = f"You are a hiring agent for the inbox {inbox_address}. Help candidates with their applications."


agent = Agent(
    name="Hiring Agent",
    instructions=instructions,
    tools=AgentMailToolkit(client).get_tools() + [WebSearchTool()],
)

def process_thread(thread_item):
    """Process a single thread and send a reply"""
    thread_id = thread_item.thread_id
    
    print(f"\n🔍 Processing thread {thread_id}")
    print(f"📧 Subject: {thread_item.subject}")
    
    # Fetch the full thread to get messages
    try:
        thread = client.inboxes.threads.get(
            inbox_id=inbox_obj.inbox_id, 
            thread_id=thread_id
        )
        print(f"💬 Messages: {len(thread.messages)}")
    except Exception as e:
        print(f"❌ Error fetching thread {thread_id}: {e}")
        return False
    
    # Detect if the job/role details block has already been sent in this thread
    has_already_sent_job_block = False
    for _m in thread.messages:
        _content = (_m.text or _m.html or "")
        if (
            "For legal reasons I am copy pasting the details of the role" in _content
            or "<strong>Role:</strong> Founding Engineer" in _content
        ):
            has_already_sent_job_block = True
            break
    
    # Build thread context from existing messages
    thread_context = []
    last_user_message = None
    
    for msg in thread.messages:
        # In AgentMail, messages from external senders are "user" messages
        # Messages sent from your inbox are "assistant" messages
        message_content = msg.text or msg.html or "No content"
        
        # Check if this message is from an external sender (not from your inbox)
        if hasattr(msg, 'from_') and msg.from_ and not msg.from_.endswith('@agentmail.to'):
            thread_context.append({"role": "user", "content": message_content})
            last_user_message = msg
        else:
            # This is a message from your inbox (assistant)
            thread_context.append({"role": "assistant", "content": message_content})
    
    if not last_user_message:
        print("⚠️  No user message found in thread")
        return False
    
    # Create prompt with the latest user message details
    prompt = f"""
From: {getattr(last_user_message, 'from_', 'Unknown')}
Subject: {thread.subject}
Body: {last_user_message.text or last_user_message.html or 'No content'}

IMPORTANT FOR TOOL CALLS:
- THREAD_ID: {thread_id}
- MESSAGE_ID: {last_user_message.message_id}

Use these EXACT values when calling get_thread and get_attachment tools.
"""

    # Guardrail: Only include the role/company/benefits block once per thread
    if has_already_sent_job_block:
        prompt += (
            "\nThe role/company/benefits block has ALREADY been sent earlier in this thread. "
            "Do NOT include or repeat that block again. Respond with ONLY a concise follow-up question "
            "based on the candidate's resume and prior messages."
        )
    else:
        prompt += (
            "\nThis is the FIRST reply in this thread that includes the role/company/benefits block. "
            "Include that block exactly once as specified by your instructions, then ask ONE concise question."
        )
    
    print(f"📝 Processing message from: {getattr(last_user_message, 'from_', 'Unknown')}")
    
    try:
        # Generate response using agent
        response = asyncio.run(Runner.run(agent, thread_context + [{"role": "user", "content": prompt}]))
        print(f"✅ Generated response ({len(response.final_output)} chars)")
        
        # Send reply
        client.inboxes.messages.reply(
            inbox_id=inbox_obj.inbox_id,
            message_id=last_user_message.message_id,
            html=response.final_output,
        )
        
        print(f"📤 Reply sent for thread {thread_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing thread {thread_id}: {e}")
        return False

def main():
    """Main function to process all unreplied threads"""
    print(f"\n🚀 Starting batch processing for {inbox_address}")
    print("=" * 50)
    
    try:
        # Fetch all threads without 'sent' label
        threads = client.inboxes.threads.list(
            inbox_id=inbox_obj.inbox_id,
            labels=[]  # Get threads without specific labels
        )
        
        print(f"📊 Found {len(threads.threads)} total threads")
        
        # Filter threads that don't have 'sent' label
        unreplied_threads = []
        for thread in threads.threads:
            thread_labels = getattr(thread, 'labels', [])
            if 'sent' not in thread_labels:
                unreplied_threads.append(thread)
        
        print(f"📋 Found {len(unreplied_threads)} threads without 'sent' label")
        
        if not unreplied_threads:
            print("✅ No threads to process. All caught up!")
            return
        
        # Process each unreplied thread
        processed = 0
        errors = 0
        
        for i, thread in enumerate(unreplied_threads, 1):
            print(f"\n[{i}/{len(unreplied_threads)}] Processing thread...")
            success = process_thread(thread)
            
            if success:
                processed += 1
            else:
                errors += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 BATCH PROCESSING COMPLETE")
        print(f"✅ Successfully processed: {processed}")
        print(f"❌ Errors: {errors}")
        print(f"📧 Inbox: {inbox_address}")
        
    except Exception as e:
        print(f"❌ Error fetching threads: {e}")

if __name__ == "__main__":
    main()
