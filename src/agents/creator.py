import os
import sys
import importlib
import logging
import json
from autogen_core import MessageContext, RoutedAgent, message_handler, TRACE_LOGGER_NAME, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.utils import utils
import yaml
import re
from src.utils.prompts import Prompts

logger = logging.getLogger("main")



class Creator(RoutedAgent):

    def __init__(self, name) -> None:
        super().__init__(name)
        system_message = Prompts.get_creator_system_message()
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=system_message)

    def get_generation_prompt(self, description: str, system_message: str, template_file: str) -> str:
        prompt = Prompts.get_creator_prompt(description, system_message)

        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template


    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.debug(f"Creator received message: {message.content}")
        
        try:
            config = yaml.safe_load(message.content)
        except yaml.YAMLError as e:
            await self.send_message(utils.Message(content=f"YAML parse error: {e}", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")
        
        if "agents" not in config or not isinstance(config["agents"], list):
            await self.send_message(utils.Message(content="Error: YAML must have a top-level 'agents' list.", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")

        agents = config.get("agents", [])
        workflow_config = config.get("workflow_config", {})
        all_errors = []
        registered_agents = {}

        workflow_error = Creator.validate_workflow(agents)

        if workflow_error:
            await self.send_message(utils.Message(content=f"❌ Workflow validation errors:\n{workflow_error}", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")

        if not agents:
            await self.send_message(utils.Message(content="❌ No agents specified in the configuration", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")

        for i, spec in enumerate(agents): 
            errors = Creator.validate_agent_spec(spec)
            if errors:
                all_errors.append(f"Agent {i} ({spec.get('agent_name', 'unknown')}):\n" + "\n".join(errors))
                continue
            
            filename = spec.get("filename", "generated/new_agent.py")
            agent_name = spec.get("agent_name", os.path.splitext(os.path.basename(filename))[0])
            module_path = f"generated.{agent_name}"
            description = spec.get("description", "An AI agent.")
            system_message = spec.get("system_message", "You are an AI agent.")

            if "tools" in spec and spec["tools"]:
                template_file = "src/templates/agent_with_tools.py"
            else:
                template_file = "src/templates/agent.py"

            if os.path.exists(filename) and not self.should_regenerate(filename, template_file):
                logger.debug(f"Agent file {filename} already exists, skipping generation")
            else:
                text_message = TextMessage(
                    content=self.get_generation_prompt(description, system_message, template_file),
                    source="user"
                )

                response = await self._delegate.on_messages([text_message], ctx.cancellation_token)

                generated_code = response.chat_message.content

                # Remove common LLM response markers
                markers = ["TERMINATE", "END", "END OF CODE", "```python", "```"]
                for marker in markers:
                    generated_code = generated_code.replace(marker, "")

                generated_code = generated_code.strip()
                
                security_issues = Creator.validate_generated_code(generated_code)
                if security_issues:
                    logger.error(f"Generated code failed security validation: {security_issues}")
                    await self.send_message(utils.Message(content=f"Security validation failed: {security_issues}", sender="Creator"), AgentId("End", "default"))
                    return utils.Message(content="", sender="Creator")
                
                try:
                    compile(generated_code, filename, 'exec')
                except SyntaxError as e:
                    logger.error(f"Generated code has syntax errors: {e}")
                    await self.send_message(utils.Message(content=f"Syntax error in generated code: {e}", sender="Creator"), AgentId("End", "default"))
                    return utils.Message(content="", sender="Creator")

                os.makedirs(os.path.dirname(filename), exist_ok=True)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                logger.debug(f"Saved generated agent code to {filename}")

            try:
                if module_path in sys.modules:
                    module_file = sys.modules[module_path].__file__
                    if module_file and os.path.exists(module_file):
                        module_mtime = os.path.getmtime(module_file)
                        current_mtime = os.path.getmtime(filename)
                        if current_mtime > module_mtime:
                            logger.info(f"File {filename} modified, reloading module {module_path}")
                            importlib.reload(sys.modules[module_path])
                        else:
                            logger.debug(f"Module {module_path} is up to date, skipping reload")
                    else:
                        logger.info(f"Reloading module {module_path} (no file info)")
                        importlib.reload(sys.modules[module_path])
                module = importlib.import_module(module_path)
            except Exception as e:
                logger.error(f"Failed to import/reload module {module_path}: {e}")
                await self.send_message(utils.Message(content=f"Error importing {agent_name}: {e}", sender="Creator"), AgentId("End", "default"))
                return utils.Message(content="", sender="Creator")

            try:
                logger.debug(f"Registering agent {agent_name}")
                await module.Agent.register(self.runtime, agent_name, Creator.create_agent(module, agent_name, system_message, spec))
                logger.debug(f"Agent {agent_name} registered and live")  
            except Exception as e:
                logger.error(f"Failed to register agent {agent_name}: {e}")
                all_errors.append(f"{agent_name}: Failed to register -> {e}")
                continue
            
            registered_agents[agent_name] = spec
        
        if not registered_agents:
            await self.send_message(utils.Message(content="❌ No agents were successfully registered", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")

        head_agent = agents[0]
        test_message = head_agent.get('test_message')
        if not test_message:
            await self.send_message(utils.Message(content="❌ Head agent has no test_message specified", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")
            
        workflow_progress = self._generate_workflow_progress(agents, registered_agents)
        logger.info(f"🚀 Starting workflow:\n{workflow_progress}")
        
        # Create workflow specification for Start agent
        workflow_spec = {
            "agents": registered_agents,
            "head_agent": head_agent,
            "workflow_config": {
                "input_mode": workflow_config.get("input_mode", "test_message"),
                "input_prompt": workflow_config.get("input_prompt", "What would you like me to help you with?")
            }
        }
        
        logger.debug(f"Workflow will start with agent {head_agent.get('agent_name')}")
        try:
            await self.send_message(utils.Message(content=json.dumps(workflow_spec), sender="Creator"), AgentId("Start", "default"))
        except Exception as e:
            logger.error(f"❌ Creator: Failed to send workflow spec to Start agent: {e}")
            await self.send_message(
                utils.Message(content=f"❌ Failed to start workflow: {e}", sender="Creator"), 
                AgentId("End", "default")
            )

        if all_errors:
            await self.send_message(
                utils.Message(content="❌ Errors encountered:\n" + "\n".join(all_errors), sender="Creator"),
                AgentId("End", "default")
            )
        

        return utils.Message(content="", sender="Creator") 
    
    @staticmethod
    def validate_agent_spec(spec: dict) -> list[str]:
        """Validate a single agent spec. Return a list of error messages."""
    
        errors = []
        required_fields = ["agent_name", "description", "system_message"]

        for field in required_fields:
            if field not in spec or not spec[field]:
                errors.append(f"Missing required field: {field}")

        return errors
    
    @staticmethod
    def validate_workflow(agents) -> list[str]:
        errors = []

        agent_names = [spec.get("agent_name") for spec in agents]

        for spec in agents:
            output_to = spec.get("output_to")

            if output_to and output_to not in agent_names:
                errors.append(f"Agent {spec.get('agent_name')} references non-existent agent: {output_to}")
        
        return errors
    
    @staticmethod
    def create_agent(module, agent_name, system_message, spec):
        return lambda: module.Agent(agent_name, system_message, spec)
    
        
    def should_regenerate(self, filename, template_file) -> bool:
        if not os.path.exists(filename):
            return True
        
        with open(filename, "r") as f:
            existing_content = f.read()
        with open(template_file, "r") as f:
            template_content = f.read()
        
        existing_version = re.search(r'TEMPLATE_VERSION = "([^"]+)"', existing_content)
        current_version = re.search(r'TEMPLATE_VERSION = "([^"]+)"', template_content)
        
        if not current_version:
            logger.warning(f"Template {template_file} missing TEMPLATE_VERSION, forcing regeneration")
            return True
        
        if not existing_version:
            logger.info(f"Existing file {filename} missing TEMPLATE_VERSION, regenerating")
            return True
        
        existing_version = existing_version.group(1)
        current_version = current_version.group(1)
        
        should_regenerate = existing_version != current_version
        if should_regenerate:
            logger.info(f"Template version mismatch: {existing_version} -> {current_version}, regenerating")
        
        return should_regenerate
    
    @staticmethod
    def validate_generated_code(code: str) -> list[str]:
        """Basic security validation for generated code. Returns list of security issues."""
        issues = []
        
        dangerous_imports = [
            'os.system', 'subprocess', 'eval', 'exec', 'compile',
            '__import__', 'open', 'file', 'input', 'raw_input',
            'socket', 'urllib', 'requests', 'http', 'ftplib'
        ]
        
        dangerous_patterns = [
            r'os\.system\s*\(', r'subprocess\s*\.', r'eval\s*\(', r'exec\s*\(',
            r'__import__\s*\(', r'compile\s*\(', r'open\s*\(', r'file\s*\(',
            r'input\s*\(', r'raw_input\s*\(', r'socket\s*\.', r'urllib\s*\.',
            r'requests\s*\.', r'http\s*\.', r'ftplib\s*\.'
        ]
        
        for dangerous_import in dangerous_imports:
            if dangerous_import in code:
                issues.append(f"Dangerous import detected: {dangerous_import}")
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"Dangerous operation detected: {pattern}")
        
        if re.search(r'open\s*\([^)]*["\']\.\./', code):
            issues.append("Attempt to access files outside generated directory")
        
        if re.search(r'(socket|urllib|requests|http|ftplib)', code, re.IGNORECASE):
            issues.append("Network operations detected - not allowed in generated agents")
        
        return issues
    
    def _generate_workflow_progress(self, agents: list, registered_agents: dict) -> str:
        """Generate a visual representation of the workflow progress."""
        if not agents:
            return "No agents configured"
        
        workflow_chain = []
        current_agent = agents[0]
        
        while current_agent:
            agent_name = current_agent.get('agent_name', 'unknown')
            status = "✓" if agent_name in registered_agents else "❌"
            timeout = current_agent.get('timeout', 30)
            has_tools = bool(current_agent.get('tools'))
            
            agent_info = f"[{status}] {agent_name}"
            if has_tools:
                tool_count = len(current_agent.get('tools', []))
                agent_info += f" (🔧{tool_count} tools)"
            agent_info += f" (⏱️{timeout}s)"
            
            workflow_chain.append(agent_info)
            
            output_to = current_agent.get('output_to')
            if output_to:
                next_agent = next((a for a in agents if a.get('agent_name') == output_to), None)
                current_agent = next_agent
            else:
                current_agent = None
        
        workflow_chain.append("[⏳] End")
        
        return " → ".join(workflow_chain)



