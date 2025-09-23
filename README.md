# Agent Core

A powerful framework for creating, managing, and orchestrating AI agents with dynamic tool integration and workflow communication.

## 🚀 Features

- **Dynamic Agent Generation**: Create AI agents from YAML specifications
- **Tool Integration**: Seamless integration with MCP (Model Context Protocol) servers
- **Agent Communication**: Linear workflow execution with message forwarding
- **Environment Management**: Secure API key handling with environment variable resolution
- **Health Monitoring**: Built-in agent health checks and error recovery
- **Template Versioning**: Automatic agent regeneration when templates are updated
- **Two-Phase Execution**: Reliable agent registration and communication orchestration

## 🛠️ Tech Stack

- **Python 3.8+**
- **AutoGen Core**: Agent framework and message handling
- **AutoGen AgentChat**: AI model integration
- **YAML**: Configuration-driven agent specification
- **MCP**: Tool integration protocol
- **Google Gemini**: AI model backend

## 📁 Project Structure

```
agent-core/
├── src/                   # Source code
│   ├── agents/           # Core agents
│   │   ├── creator.py    # Agent creation and orchestration
│   │   └── end.py        # Workflow endpoint agent
│   ├── templates/        # Agent templates
│   │   ├── agent.py      # Basic agent template
│   │   └── agent_with_tools.py # Agent with MCP tools template
│   └── utils/            # Utilities
│       ├── utils.py      # Core utilities and logging
│       └── prompts.py    # AI generation prompts
├── generated/            # Runtime-generated agents
├── config/               # Configuration files
│   └── agents.yaml       # Agent specifications
├── main.py               # Application entry point
├── workflow_state.py     # Workflow management
└── pyproject.toml        # Dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/pushkqr/agent-core
cd agent-core
uv sync
```

### 2. Environment Setup

Create a `.env` file:

```env
GOOGLE_API_KEY=your_gemini_api_key
BRAVE_API_KEY=your_brave_search_api_key
```

### 3. Configure Agents

Edit `config/agents.yaml`:

```yaml
agents:
  - filename: generated/fetcher.py
    agent_name: fetcher
    description: "An agent that fetches information from the web."
    system_message: "You are an agent that fetches information off the web."
    test_message: "What's the latest AI news?"
    tools:
      - name: fetch_server
        params:
          command: "npx"
          args: ["-y", "@brave/brave-search-mcp-server"]
          env:
            BRAVE_API_KEY: "${BRAVE_API_KEY}"
    output_to: summarizer
```

### 4. Run

```bash
uv run main.py
```

## 🏗️ Architecture

### Directory Organization

- **`src/`**: Core source code with proper Python package structure
  - **`agents/`**: Core agents (Creator, End) that manage the workflow
  - **`templates/`**: Agent templates used for code generation
  - **`utils/`**: Shared utilities, logging, and prompts
- **`generated/`**: Runtime-generated agents (created by Creator)
- **`config/`**: Configuration files (YAML specifications)

### Workflow Execution

The Creator agent processes YAML configurations and:

1. **Generates** agent code from templates in `src/templates/`
2. **Saves** generated agents to `generated/` directory
3. **Registers** agents with the AutoGen runtime
4. **Validates** agent health and dependencies
5. **Executes** workflows with agent communication
6. **Manages** message flow between agents


