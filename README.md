# Agent Core

A powerful framework for creating, managing, and orchestrating AI agents with dynamic tool integration and flexible workflow communication.

## 🚀 Features

- **Dynamic Agent Generation**: Create AI agents from YAML specifications with AI-powered code generation
- **Flexible Input Handling**: Support for both automated workflows (test messages) and interactive user input
- **Tool Integration**: Seamless integration with MCP (Model Context Protocol) servers with robust error handling
- **Agent Communication**: Linear workflow execution with message forwarding and state management
- **Environment Management**: Centralized API key handling with environment variable resolution
- **Health Monitoring**: Built-in agent health checks, error recovery, and graceful fallbacks
- **Template Versioning**: Smart agent regeneration when templates are updated with file modification tracking
- **Security Validation**: Basic code validation for AI-generated agents to prevent dangerous operations
- **Configurable Timeouts**: Customizable workflow timeouts via environment variables
- **Optimized Performance**: Efficient module reloading, reduced redundant operations, and streamlined architecture

## 🛠️ Tech Stack

- **Python 3.12+**: Modern Python with comprehensive type hints
- **AutoGen Core**: Agent framework and message handling
- **AutoGen AgentChat**: AI model integration with tool support
- **YAML**: Configuration-driven agent specification
- **MCP**: Tool integration protocol with error handling
- **Google Gemini**: AI model backend (Gemini 2.5 Flash)
- **Type Hints**: Full type annotation support for better maintainability

## 📁 Project Structure

```
agent-core/
├── src/                   # Source code
│   ├── agents/           # Core agents
│   │   ├── creator.py    # Agent creation, orchestration, and security validation
│   │   ├── start.py      # Workflow initiation agent with input handling
│   │   └── end.py        # Workflow endpoint agent 
│   ├── templates/        # Agent templates with inheritance
│   │   ├── base_agent.py # Base agent class with common functionality
│   │   ├── agent.py      # Simple agent template (inherits from BaseAgent)
│   │   └── agent_with_tools.py # Agent with MCP tools template
│   └── utils/            # Utilities
│       ├── utils.py      # Core utilities, logging, and type definitions
│       └── prompts.py    # AI generation prompts
├── generated/            # Runtime-generated agents (auto-created)
├── config/               # Configuration files
│   └── agents.yaml       # Agent specifications with workflow config
├── main.py               # Application entry point with environment setup
├── workflow_state.py     # Workflow state management with proper cleanup
└── pyproject.toml        # Dependencies and project configuration
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
WORKFLOW_TIMEOUT=300  # Optional: workflow timeout in seconds (default: 300)
DEBUG=false  # Optional: enable debug logging (default: false)
```

### 3. Configure Agents

Edit `config/agents.yaml`:

```yaml
# Workflow configuration
workflow_config:
  input_mode: "test_message"  # Options: "test_message" or "interactive"
  input_prompt: "What would you like me to help you with?"
  input_timeout: 60  # seconds

agents:
  - filename: generated/fetcher.py
    agent_name: fetcher
    description: "An agent that fetches information from the web."
    system_message: "You are an agent that fetches information off the web."
    test_message: "What's the latest AI news?"
    timeout: 45  # Agent-specific timeout in seconds (default: 30)
    tools:
      - name: fetch_server
        params:
          command: "npx"
          args: ["-y", "@brave/brave-search-mcp-server"]
          env:
            BRAVE_API_KEY: "${BRAVE_API_KEY}"
    output_to: summarizer
  - filename: generated/summarizer.py
    agent_name: summarizer
    description: "An agent that summarizes text into concise points."
    system_message: "You are a summarizer agent. Take long text and output concise summaries."
    timeout: 20
```

### 4. Run

```bash
uv run main.py
```

### 5. Debug Mode

For development and debugging, enable debug mode:

```bash
DEBUG=true uv run main.py
```

**Logging Levels:**
- **INFO (default)**: Shows workflow progress, agent completions, and errors only
- **DEBUG**: Shows detailed internal operations, message passing, registration details, and AutoGen Core logs

**Input Modes:**
- **test_message**: Uses predefined test messages for automated workflows
- **interactive**: Prompts user for input with configurable timeout

## 🏗️ Architecture

### Directory Organization

- **`src/`**: Core source code with proper Python package structure
  - **`agents/`**: Core agents (Creator, Start, End) that manage the workflow
  - **`templates/`**: Agent templates used for code generation
  - **`utils/`**: Shared utilities, logging, and prompts
- **`generated/`**: Runtime-generated agents (created by Creator)
- **`config/`**: Configuration files (YAML specifications)

### Workflow Execution

The workflow follows this optimized architecture:

```
main.py → Creator → Start → [Generated Agents] → End
```

1. **Creator Agent**: Processes YAML configurations and generates agent code
2. **Start Agent**: Handles workflow initiation with flexible input modes
3. **Generated Agents**: Execute the actual workflow tasks
4. **End Agent**: Captures final results and signals completion

## 🤝 Contributing

Contributions are welcome! If you'd like to add features, fix bugs, or improve documentation, please open an issue or submit a pull request. For major changes, please discuss them in an issue first to ensure alignment with the project's direction.

## 📚 References & Acknowledgements

- Built on top of [AutoGen Core](https://github.com/microsoft/autogen) and [AutoGen AgentChat](https://github.com/microsoft/autogen/tree/main/autogen/agentchat)


