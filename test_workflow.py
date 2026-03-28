import os
import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock LLM API Responses
async def mock_ask_llm(prompt: str, system_prompt: str, json_format: bool = False) -> str:
    # 1. AntiGravity Planning (Tier 2)
    if "Chief System Architect" in system_prompt:
        return json.dumps({
            "architecture_summary": "A simple 4-arithmetic operation calculator application.",
            "tech_stack": ["Python 3.10", "Built-in libraries"],
            "components": ["MathLogicModule", "CLI_Interface"],
            "database_schema": None
        })
    # 2. OpenGoat Delegation (Tier 3)
    elif "Agile Project Manager" in system_prompt:
        return json.dumps([
            {
                "role": "Backend",
                "task_name": "Implement MathLogicModule",
                "detailed_instruction": "Create a python script with functions for add, subtract, multiply, divide."
            },
            {
                "role": "Frontend",
                "task_name": "Create CLI Interface",
                "detailed_instruction": "Create a script that takes user input and uses MathLogicModule to print the result."
            }
        ])
    # 3. QA Consistency Check (Tier 6)
    elif "Lead QA Engineer" in system_prompt:
        # Simulate a success on the first try for simplicity
        return json.dumps({
            "is_consistent": True,
            "feedback": "The output matches the architecture plan perfectly."
        })
    return "{}"

# Mock OpenClaw Execution
async def mock_cursor_implementation(task: dict, mcp_context: str) -> str:
    logger.info(f"    [Mock OpenClaw Execution] Executing Task: {task['task_name']}")
    await asyncio.sleep(0.5) # Simulate work

    if "MathLogicModule" in task['task_name']:
        return "def add(a,b): return a+b\ndef sub(a,b): return a-b\ndef mul(a,b): return a*b\ndef div(a,b): return a/b if b!=0 else 'Error'\n[File math_logic.py saved]"
    else:
        return "import math_logic\nprint(math_logic.add(1, 2))\n[File cli.py saved and executed successfully]"

# The core workflow logic extracted from telegram_bot.py
async def simulate_workflow(user_request: str):
    logger.info(f"🦅 OpenClaw (Command): Request received -> '{user_request}'")
    logger.info("🌌 AntiGravity (Planning): Designing system architecture...")

    arch_str = await mock_ask_llm(user_request, "You are AntiGravity, the Chief System Architect.", json_format=True)
    architecture = json.loads(arch_str)
    logger.info(f"✅ Architecture Designed:\n{json.dumps(architecture, indent=2)}")

    logger.info("🐐 OpenGoat (Delegation): Breaking down architecture...")
    tasks_str = await mock_ask_llm(arch_str, "You are OpenGoat, the Agile Project Manager.", json_format=True)
    task_list = json.loads(tasks_str)
    logger.info(f"✅ Tasks Delegated: {len(task_list)} tasks created.")

    logger.info("💻 Cursor & MCP (Implementation): Starting strict execution phase...")
    project_context = f"Global Architecture: {architecture['architecture_summary']}\n"
    max_retries = 2

    for i, task in enumerate(task_list):
        logger.info(f"⏳ Executing Step {i+1}/{len(task_list)}: {task['task_name']}...")

        success = False
        for attempt in range(max_retries):
            try:
                # 1. Implementation
                result = await mock_cursor_implementation(task, project_context)

                # 2. Consistency Check
                logger.info(f"🔍 QA (Consistency): Verifying '{task['task_name']}'...")
                validation_str = await mock_ask_llm(result, "You are the Lead QA Engineer.", json_format=True)
                validation = json.loads(validation_str)

                if validation.get("is_consistent"):
                    project_context += f"\nCompleted '{task['task_name']}': {result[:50]}..."
                    logger.info(f"✅ Verified & Completed: {task['task_name']}")
                    success = True
                    break
                else:
                    logger.warning(f"⚠️ Consistency Failed: {validation.get('feedback')}. Retrying...")

            except Exception as e:
                logger.error(f"❌ Execution Error: {e}")

        if not success:
            logger.error(f"🚨 Task '{task['task_name']}' failed. Halting workflow.")
            return

    logger.info("🎉 OpenClaw (Command): Project workflow strictly verified and fully complete!")

if __name__ == "__main__":
    asyncio.run(simulate_workflow("간단한 4칙 연산 계산기 만들어줘."))