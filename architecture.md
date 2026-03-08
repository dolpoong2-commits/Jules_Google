# Local LLM Agent Architecture

## Hardware Specifications
- **CPU:** Threadripper 3970x
- **RAM:** 128GB
- **GPUs:** RTX 3090 (24GB) + RTX 4060ti/5060ti (16GB)

## Software Stack
- **OS:** Ubuntu
- **Runtime:** Node.js 22 (via NVM), Python 3.10+, Docker
- **IDE:** Cursor (connected remotely/locally)

## Core Components
1. **Local LLMs:**
   - Exaone 4.0-32b
   - Exaone 1.2b
   - GPT-OSS-20b
   - Hosted using a local inference engine (e.g., vLLM, Ollama, or llama.cpp).

2. **Routing & Proxy (NadirClaw & LiteLLM):**
   - **LiteLLM:** Standardizes all API calls to the OpenAI format, abstracting different backend models.
   - **NadirClaw:** Acts as an intelligent router/proxy. Cuts inference costs/time by routing simple prompts to smaller models (Exaone 1.2b) and complex coding tasks to larger ones (Exaone 32b, GPT-OSS).

3. **Agent Orchestration (OpenClaw, OpenGoat, Antigravity):**
   - **OpenClaw:** Core autonomous AI assistant.
   - **OpenGoat:** Orchestrator to build hierarchical organizations of OpenClaw agents.
   - **Antigravity & AG Manager:** Agent-first development platform to securely oversee terminal and browser actions with granular permissions.

4. **Model Context Protocol (MCP) Server:**
   - Exposes tools to the LLMs/Agents.
   - **Configured Tools (12):**
     1. filesystem (read/write local files)
     2. git (version control operations)
     3. sequential-thinking (step-by-step reasoning)
     4. memory (conversation memory)
     5. context (document search)
     6. github (GitHub integration)
     7. sqlite (local DB queries)
     8. postgres (PostgreSQL queries)
     9. duckduckgo (web search)
     10. searxng (private web search)
     11. arxiv (paper search)
     12. docker (container management)

5. **Interface (Telegram Bot):**
   - A custom Python-based Telegram bot listens for user commands.
   - Relays instructions directly to the Ubuntu system to execute coding tasks via OpenClaw/OpenGoat.

## System Data Flow
1. User sends a command via Telegram from anywhere.
2. The Telegram Bot service running on Ubuntu receives the command.
3. The Bot initializes a task in OpenGoat/OpenClaw or Antigravity.
4. The Agent requests tool executions (via MCP) or generation (via NadirClaw/LiteLLM).
5. NadirClaw evaluates prompt complexity and routes to the appropriate local LLM.
6. Local LLMs generate the response/code.
7. Agent executes terminal commands or file changes securely.
8. Telegram Bot reports the result/status back to the user.
