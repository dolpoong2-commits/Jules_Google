import os
import asyncio
import logging
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process a natural language task and pass it to OpenClaw/OpenGoat."""
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        return

    task = update.message.text
    await update.message.reply_text(f"Task received. Dispatching to OpenClaw...\n\nTask: {task}")

    # Here we invoke OpenClaw CLI or Antigravity via subprocess.
    # Assumes openclaw is installed and available in path.
    # Adjust the command flag based on the actual CLI of OpenClaw/OpenGoat.
    try:
        # Note: Running LLM agents can take time. In a real production bot,
        # you'd run this asynchronously or in a task queue to avoid blocking the bot.
        # For this setup, we use asyncio.create_subprocess_exec to securely pass arguments

        process = await asyncio.create_subprocess_exec(
            'openclaw', 'execute', task,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            result = stdout.decode('utf-8')
            if len(result) > 4000:
                result = result[:4000] + "\n...[Output truncated]"
            await update.message.reply_text(f"Task completed successfully:\n\n{result}")
        else:
            error_msg = stderr.decode('utf-8')
            await update.message.reply_text(f"Task failed with error:\n\n{error_msg}")

    except Exception as e:
        logger.error(f"Error executing task: {e}")
        await update.message.reply_text(f"An internal error occurred while executing the task: {e}")

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