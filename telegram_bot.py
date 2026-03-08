import os
import asyncio
import json
import logging
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

# LLM Configuration (using the local LiteLLM proxy routing to Exaone-32B)
LLM_MODEL = "openai/exaone-32b"
LLM_API_BASE = "http://localhost:4000/v1"
LLM_API_KEY = "sk-1234"

async def ask_llm(prompt: str, system_prompt: str, json_format: bool = False) -> str:
    """Helper function to call the local LLM."""
    try:
        kwargs = {
            "model": LLM_MODEL,
            "api_base": LLM_API_BASE,
            "api_key": LLM_API_KEY,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        if json_format:
            kwargs["response_format"] = {"type": "json_object"}

        response = await litellm.acompletion(**kwargs)
        content = response.choices[0].message.content

        # Clean up Markdown JSON blocks
        if json_format:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()

        return content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise e

# --- 5-Tier Agent Roles ---

async def antigravity_planning(task_description: str) -> dict:
    """
    Tier 2: AntiGravity (Planning/Structuring)
    Responsible for software architecture, tech stack selection, and overall system design.
    """
    system_prompt = """You are AntiGravity, the Chief System Architect.
Your role is to analyze the user's software request and design a robust, scalable system architecture.
You DO NOT write code. You define the structure, tech stack, DB schema, and high-level components.
Output your architecture as a JSON object with keys: "architecture_summary", "tech_stack", "components", "database_schema"."""

    try:
        result = await ask_llm(task_description, system_prompt, json_format=True)
        return json.loads(result)
    except Exception:
        return {"architecture_summary": "Fallback architecture plan due to error."}

async def opengoat_delegation(architecture_plan: dict) -> list[dict]:
    """
    Tier 3: OpenGoat (Role Delegation & Task Breakdown)
    Breaks down the AntiGravity architecture into actionable, atomic tasks assigned to specific roles.
    """
    system_prompt = """You are OpenGoat, the Agile Project Manager.
Based on the provided system architecture, break the project down into atomic coding tasks.
Assign each task to a specific developer role (e.g., 'Frontend', 'Backend', 'Database').
Output a JSON list of objects. Each object must have: 'role', 'task_name', 'detailed_instruction'.
Example: [{"role": "Backend", "task_name": "Setup Express Server", "detailed_instruction": "Create server.js and install express"}]"""

    prompt = f"System Architecture:\n{json.dumps(architecture_plan, indent=2)}\n\nGenerate the atomic task list."

    try:
        result = await ask_llm(prompt, system_prompt, json_format=True)
        tasks = json.loads(result)
        if isinstance(tasks, dict) and 'tasks' in tasks:
            return tasks['tasks'] # Handle cases where LLM wraps it in a dict
        return tasks if isinstance(tasks, list) else []
    except Exception:
        return [{"role": "General", "task_name": "Implement architecture", "detailed_instruction": "Follow standard practices."}]

async def cursor_implementation(task: dict, mcp_context: str) -> str:
    """
    Tier 4 & 5: Cursor (Implementation/Refactoring) + MCP (Tools/Data Access)
    Actually writes the code and interacts with the system using OpenClaw CLI loaded with MCP tools.
    """
    # We use OpenClaw CLI as the execution engine for the 'Cursor' role, injecting MCP.
    instruction = f"Role: {task.get('role', 'Developer')}\nTask: {task.get('task_name', 'Coding')}\nDetails: {task.get('detailed_instruction', '')}\n\nProject Context:\n{mcp_context}"

    process = await asyncio.create_subprocess_exec(
        'openclaw', 'execute', '--mcp-config', 'mcp_config.json', instruction,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return stdout.decode('utf-8')
    else:
        raise Exception(f"Implementation failed:\n{stderr.decode('utf-8')}")


# --- Telegram Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if update.effective_user.id != AUTHORIZED_USER_ID: return
    await update.message.reply_text("👋 OpenClaw Orchestrator Ready.\nSend me a complex project description.")

async def openclaw_reception(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Tier 1: OpenClaw (Reception/Command)
    The entry point that receives the user request and directs the entire flow.
    """
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID: return

    user_request = update.message.text
    await update.message.reply_text("🦅 **OpenClaw (Command)**: Request received. Initiating multi-agent workflow...")

    try:
        # Phase 1: Planning
        await update.message.reply_text("🌌 **AntiGravity (Planning)**: Designing system architecture and structure...")
        architecture = await antigravity_planning(user_request)

        arch_summary = json.dumps(architecture, indent=2)
        if len(arch_summary) > 3000: arch_summary = arch_summary[:3000] + "..."
        await update.message.reply_text(f"✅ Architecture Designed:\n```json\n{arch_summary}\n```", parse_mode='Markdown')

        # Phase 2: Breakdown & Delegation
        await update.message.reply_text("🐐 **OpenGoat (Delegation)**: Breaking down architecture into assigned tasks...")
        task_list = await opengoat_delegation(architecture)

        if not task_list:
            await update.message.reply_text("❌ OpenGoat failed to generate tasks.")
            return

        task_summary = "\n".join([f"- [{t.get('role')}] {t.get('task_name')}" for t in task_list])
        await update.message.reply_text(f"✅ Tasks Delegated:\n{task_summary}")

        # Phase 3 & 4: Implementation & Tools
        await update.message.reply_text("💻 **Cursor & MCP (Implementation)**: Starting execution phase...")

        project_context = f"Global Architecture Summary: {architecture.get('architecture_summary', 'N/A')}\n"

        for i, task in enumerate(task_list):
            step_msg = f"⏳ Executing ({i+1}/{len(task_list)}): {task.get('task_name')}..."
            await update.message.reply_text(step_msg)

            try:
                # Execution invokes the MCP tools
                result = await cursor_implementation(task, project_context)

                # Update context for the next agent
                project_context += f"\nCompleted '{task.get('task_name')}': Success."

                display_result = result[:3500] + "\n...[Truncated]" if len(result) > 3500 else result
                await update.message.reply_text(f"✅ {task.get('task_name')} Completed:\n\n{display_result}")

            except Exception as e:
                await update.message.reply_text(f"❌ Error during '{task.get('task_name')}':\n{e}")
                # Optional: Add self-healing retry logic here
                break

        await update.message.reply_text("🎉 **OpenClaw (Command)**: Project workflow complete!")

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        await update.message.reply_text(f"🚨 Critical failure in workflow: {e}")

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set.")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, openclaw_reception))

    logger.info("Starting OpenClaw Multi-Agent Orchestrator...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()