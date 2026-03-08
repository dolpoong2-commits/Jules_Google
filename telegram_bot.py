import os
import asyncio
import json
import logging
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import litellm

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Security: Only allow commands from the authorized user
AUTHORIZED_USER_ID = int(os.environ.get("TELEGRAM_USER_ID", "0"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Unauthorized user.")
        return

    await update.message.reply_text(
        "Hello! I am your Local LLM Agent Manager.\n"
        "Send me coding tasks, and I will dispatch them to OpenClaw / Antigravity via NadirClaw/LiteLLM on this machine.\n\n"
        "Example: `Create a Python script that scrapes Hacker News.`"
    )

async def generate_plan(task_description: str) -> list[str]:
    """Uses LiteLLM to break down a complex prompt into sequential, iterative sub-tasks."""
    # We use the local litellm proxy to call the 32B model.
    # It acts as a project manager to avoid context limits.
    prompt = f"""You are an expert AI software architect.
Break down the following complex user request into a sequence of small, manageable coding steps.
Your output MUST be a valid JSON list of strings. Each string is a distinct instruction for a coding agent.
Example for 'Make a todo app': ["Initialize a Node.js project", "Create the Express server", "Create a basic HTML frontend"]

User Request: {task_description}

Return ONLY the raw JSON list."""

    try:
        response = await litellm.acompletion(
            model="openai/exaone-32b", # LiteLLM alias
            api_base="http://localhost:4000/v1", # LiteLLM Proxy
            api_key="sk-1234",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        plan_str = response.choices[0].message.content

        # Strip markdown blocks if the LLM wrapped the JSON
        if plan_str.startswith("```json"):
            plan_str = plan_str.strip("```json").strip("```").strip()
        elif plan_str.startswith("```"):
            plan_str = plan_str.strip("```").strip()

        return json.loads(plan_str)
    except Exception as e:
        logger.error(f"Planning failed: {e}. Falling back to single step.")
        return [task_description]

async def execute_subtask(subtask: str, context_message: str = "") -> str:
    """Executes a single subtask using OpenClaw."""
    full_prompt = subtask
    if context_message:
        full_prompt = f"Context from previous steps:\n{context_message}\n\nCurrent Task:\n{subtask}"

    process = await asyncio.create_subprocess_exec(
        'openclaw', 'execute', '--mcp-config', 'mcp_config.json', full_prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return stdout.decode('utf-8')
    else:
        raise Exception(f"Subtask failed:\n{stderr.decode('utf-8')}")

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process a natural language task, break it down iteratively, and pass it to OpenClaw."""
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        return

    task = update.message.text
    await update.message.reply_text("🤔 Planning... Breaking down the request to avoid context limits.")

    try:
        plan = await generate_plan(task)

        plan_summary = "\n".join([f"{i+1}. {step}" for i, step in enumerate(plan)])
        await update.message.reply_text(f"✅ Generated Plan:\n\n{plan_summary}\n\nDispatching to OpenClaw iteratively...")

        # Execute iteratively
        accumulated_context = ""
        for i, subtask in enumerate(plan):
            await update.message.reply_text(f"⏳ Executing Step {i+1}/{len(plan)}:\n{subtask}")

            result = await execute_subtask(subtask, accumulated_context)

            # Truncate output for telegram
            display_result = result
            if len(display_result) > 4000:
                display_result = display_result[:4000] + "\n...[Output truncated]"

            await update.message.reply_text(f"✅ Step {i+1} completed:\n\n{display_result}")

            # Save short summary for next step context (to prevent context blooming)
            # In a real setup, we might ask the LLM to summarize `result`
            accumulated_context += f"\n- Completed: {subtask}"

        await update.message.reply_text("🎉 All steps completed successfully!")

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        await update.message.reply_text(f"An error occurred: {e}")

def main() -> None:
    """Start the bot."""
    # Get the token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # on non command i.e message - process the task
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()