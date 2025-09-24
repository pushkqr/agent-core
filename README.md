# Agent Core

A powerful framework for creating, managing, and orchestrating AI agents with dynamic tool integration and workflow communication.

## 🚀 Features

- **Dynamic Agent Generation**: Create AI agents from YAML specifications with AI-powered code generation
- **Tool Integration**: Seamless integration with MCP (Model Context Protocol) servers with robust error handling
- **Agent Communication**: Linear workflow execution with message forwarding and state management
- **Environment Management**: Centralized API key handling with environment variable resolution
- **Health Monitoring**: Built-in agent health checks, error recovery, and graceful fallbacks
- **Template Versioning**: Smart agent regeneration when templates are updated with file modification tracking
- **Security Validation**: Basic code validation for AI-generated agents to prevent dangerous operations
- **Configurable Timeouts**: Customizable workflow timeouts via environment variables
- **Optimized Performance**: Efficient module reloading and reduced redundant operations

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
│   └── agents.yaml       # Agent specifications
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

1. **Validates** YAML configuration and workflow structure
2. **Generates** agent code from templates with security validation
3. **Saves** generated agents to `generated/` directory with version tracking
4. **Registers** agents with the AutoGen runtime with error handling
5. **Validates** agent health and tool dependencies with fallback mechanisms
6. **Executes** workflows with proper state management and timeout handling
7. **Manages** message flow between agents with comprehensive logging

### Key Improvements

- **Error Resilience**: Agents gracefully handle tool failures and continue operation
- **Enhanced Error Reporting**: Detailed error messages with context and debugging information
- **Agent-Specific Timeouts**: Configurable timeouts per agent with detailed timeout reporting
- **Security**: Basic validation prevents dangerous code execution in generated agents
- **Performance**: Optimized module reloading and reduced redundant operations
- **Maintainability**: Clean code structure with shared base classes and type hints
- **Configurability**: Environment-based configuration for timeouts and behavior
- **State Management**: Proper cleanup prevents state pollution between runs


