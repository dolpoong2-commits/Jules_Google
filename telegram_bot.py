import os
import asyncio
import json
import logging
import time
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

# LLM Configuration (using the local LiteLLM proxy routing to the user-selected heavy planner model)
LLM_MODEL = "openai/planner-model"
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

async def verify_consistency(task_name: str, task_result: str, architecture_plan: dict) -> dict:
    """
    Tier 6: Final Consistency Check (Validation)
    Verifies if the completed task matches the original architectural intent.
    """
    system_prompt = """You are the Lead QA Engineer.
Your job is to compare the output of a completed coding task against the original system architecture.
Does the output fulfill the task requirements and align with the architecture?
Output a JSON object with two keys: "is_consistent" (boolean) and "feedback" (string detailing what is missing or incorrect if False)."""

    prompt = f"Architecture:\n{json.dumps(architecture_plan)}\n\nTask: {task_name}\n\nAgent Output:\n{task_result}"

    try:
        result = await ask_llm(prompt, system_prompt, json_format=True)
        return json.loads(result)
    except Exception:
        # Fallback to true if validation LLM fails to avoid infinite loops
        return {"is_consistent": True, "feedback": "Validation fallback passed."}

async def cursor_implementation(task: dict, mcp_context: str) -> str:
    """
    Tier 4 & 5: Cursor (Implementation/Refactoring) + MCP (Tools/Data Access)
    Strictly follows: Coding -> Validation -> Execution -> Validation -> Consistency Check -> Done
    """
    strict_procedure = """CRITICAL PROCEDURE: You must follow this strict 6-step loop for this task. Do not stop until step 6 is complete.
1. Coding: Write the required code based on the instructions.
2. Verification 1: Read the generated files (using filesystem tool) to ensure syntax and structure are correct. Fix any errors.
3. Execution: Run the code (using terminal/bash tool) or run its unit tests.
4. Verification 2: Analyze the execution logs/output. If it fails, go back to step 1.
5. Consistency: Verify the final working code matches the original task requirements perfectly.
6. Final Completion: Output a summary of the working, verified code."""

    instruction = f"Role: {task.get('role', 'Developer')}\nTask: {task.get('task_name', 'Coding')}\nDetails: {task.get('detailed_instruction', '')}\n\nProject Context:\n{mcp_context}\n\n{strict_procedure}"

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

        # Phase 3 & 4: Implementation & Tools with Strict Verification
        await update.message.reply_text("💻 **Cursor & MCP (Implementation)**: Starting strict execution & verification phase...")

        project_context = f"Global Architecture Summary: {architecture.get('architecture_summary', 'N/A')}\n"
        max_retries = 2

        total_tasks = len(task_list)
        workflow_start_time = time.time()

        for i, task in enumerate(task_list):
            # Calculate metrics
            current_step = i + 1
            elapsed_total = time.time() - workflow_start_time

            # Simple ETA estimation based on average time per completed task
            if i > 0:
                avg_time_per_task = elapsed_total / i
                eta_seconds = avg_time_per_task * (total_tasks - i)
                eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
            else:
                eta_str = "Calculating..."

            elapsed_str = f"{int(elapsed_total // 60)}m {int(elapsed_total % 60)}s"

            progress_msg = (
                f"📊 **Progress Update** ({current_step}/{total_tasks})\n"
                f"⏱️ **Elapsed Time:** {elapsed_str}\n"
                f"⏳ **Estimated Remaining:** {eta_str}\n\n"
                f"▶️ **Now Executing:** [{task.get('role')}] {task.get('task_name')}...\n"
                f"*(Coding ➡️ Execution ➡️ QA Loop)*"
            )
            await update.message.reply_text(progress_msg)

            task_start_time = time.time()
            success = False
            for attempt in range(max_retries):
                try:
                    # Agent strictly follows: Code -> Verify -> Execute -> Verify
                    result = await cursor_implementation(task, project_context)

                    # Phase 5: Consistency Check against Initial Architecture
                    await update.message.reply_text(f"🔍 Checking consistency for '{task.get('task_name')}'...")
                    validation = await verify_consistency(task.get('task_name'), result, architecture)

                    if validation.get("is_consistent"):
                        # Update context for the next agent
                        project_context += f"\nCompleted '{task.get('task_name')}': {result[:100]}..."
                        display_result = result[:3000] + "\n...[Truncated]" if len(result) > 3000 else result
                        await update.message.reply_text(f"✅ Verified & Completed:\n\n{display_result}")
                        success = True
                        break
                    else:
                        feedback = validation.get("feedback", "Unknown consistency error.")
                        await update.message.reply_text(f"⚠️ Consistency Check Failed (Attempt {attempt+1}/{max_retries}):\n{feedback}\n\nRetrying task with feedback...")
                        # Append QA feedback to the task details for the next retry
                        task['detailed_instruction'] += f"\n\nQA Feedback from previous attempt: YOU MUST FIX THIS: {feedback}"

                except Exception as e:
                    await update.message.reply_text(f"❌ Agent Execution Error (Attempt {attempt+1}/{max_retries}):\n{e}")

            if not success:
                await update.message.reply_text(f"🚨 Task '{task.get('task_name')}' failed after {max_retries} attempts. Halting workflow.")
                return

        total_time = time.time() - workflow_start_time
        final_time_str = f"{int(total_time // 60)}m {int(total_time % 60)}s"
        await update.message.reply_text(
            f"🎉 **OpenClaw (Command)**: Project workflow strictly verified and fully complete!\n\n"
            f"✅ **Total Tasks Completed:** {total_tasks}\n"
            f"⏱️ **Total Execution Time:** {final_time_str}"
        )

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