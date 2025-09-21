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
├── creator.py              # Main agent creation and orchestration
├── templates/              # Agent templates
│   ├── agent.py           # Basic agent template
│   └── agent_with_tools.py # Agent with MCP tools template
├── agents/                # Generated agent files
├── agents.yaml           # Agent configuration
├── prompts.py            # AI generation prompts
├── utils.py              # Utilities and logging
├── main.py               # Application entry point
└── pyproject.toml        # Dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
git clone <https://github.com/pushkqr/agent-core>
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

Edit `agents.yaml`:

```yaml
agents:
  - filename: agents/fetcher.py
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

## 🔧 Usage

The Creator agent processes YAML configurations and:

1. **Generates** agent code from templates
2. **Registers** agents with the runtime
3. **Validates** agent health
4. **Executes** workflows with agent communication

