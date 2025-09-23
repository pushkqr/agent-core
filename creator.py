import os
import sys
import importlib
import logging
from dotenv import load_dotenv
from autogen_core import MessageContext, RoutedAgent, message_handler, TRACE_LOGGER_NAME, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import utils
from utils import setup_logging
import yaml
import re
from prompts import Prompts

load_dotenv(override=True)

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")



class Creator(RoutedAgent):

    def __init__(self, name) -> None:
        super().__init__(name)
        system_message = Prompts.get_creator_system_message()
        logger.debug(f"Initializing Creator agent: {name}")
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=system_message)
        logger.debug("Delegate AssistantAgent initialized")

    def get_generation_prompt(self, description: str, system_message: str, template_file: str) -> str:
        logger.debug("Building user prompt for Agent generation")
        prompt = Prompts.get_creator_prompt(description, system_message)

        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template


    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.info(f"Creator received message: {message.content}")
        
        try:
            config = yaml.safe_load(message.content)
        except yaml.YAMLError as e:
            await self.send_message(utils.Message(content=f"YAML parse error: {e}", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")
        
        if "agents" not in config or not isinstance(config["agents"], list):
            await self.send_message(utils.Message(content="Error: YAML must have a top-level 'agents' list.", sender="Creator"), AgentId("End", "default"))
            return utils.Message(content="", sender="Creator")

        agents = config.get("agents", [])
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
            
            filename = spec.get("filename", "agents/new_agent.py")
            agent_name = spec.get("agent_name", os.path.splitext(os.path.basename(filename))[0])
            module_path = f"agents.{agent_name}"
            description = spec.get("description", "An AI agent.")
            system_message = spec.get("system_message", "You are an AI agent.")

            if "tools" in spec and spec["tools"]:
                template_file = "templates/agent_with_tools.py"
            else:
                template_file = "templates/agent.py"

            if os.path.exists(filename) and not self.should_regenerate(filename, template_file):
                logger.info(f"Agent file {filename} already exists, skipping generation")
            else:
                text_message = TextMessage(
                    content=self.get_generation_prompt(description, system_message, template_file),
                    source="user"
                )

                logger.debug(f"Sending prompt to delegate:\n{text_message.content[:300]}...")

                response = await self._delegate.on_messages([text_message], ctx.cancellation_token)

                logger.debug(f"Received response from delegate:\n{response.chat_message.content[:300]}...")

                generated_code = response.chat_message.content

                for marker in ["TERMINATE", "END", "END OF CODE", "```python", "```"]:
                    generated_code = generated_code.replace(marker, "")

                generated_code = generated_code.strip()
                
                try:
                    compile(generated_code, filename, 'exec')
                except SyntaxError as e:
                    logger.error(f"Generated code has syntax errors: {e}")
                    await self.send_message(utils.Message(content=f"Syntax error in generated code: {e}", sender="Creator"), AgentId("End", "default"))
                    return utils.Message(content="", sender="Creator")

                os.makedirs(os.path.dirname(filename), exist_ok=True)

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                logger.info(f"Saved generated agent code to {filename}")

            try:
                if module_path in sys.modules:
                    importlib.reload(sys.modules[module_path])
                module = importlib.import_module(module_path)
            except Exception as e:
                logger.error(f"Failed to import/reload module {module_path}: {e}")
                await self.send_message(utils.Message(content=f"Error importing {agent_name}: {e}", sender="Creator"), AgentId("End", "default"))
                return utils.Message(content="", sender="Creator")

            try:
                logger.info(f"Registering agent {agent_name}")
                await module.Agent.register(self.runtime, agent_name, Creator.create_agent(module, agent_name, system_message, spec))
                logger.info(f"Agent {agent_name} registered and live")  
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
            
        logger.info(f"Workflow will start with agent {head_agent.get('agent_name')}")
        await self.send_message(utils.Message(content=test_message, sender="Creator"), AgentId(head_agent.get('agent_name'), "default"))

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
        
        existing_version = existing_version.group(1) if existing_version else "unknown"
        current_version = current_version.group(1) if current_version else "unknown"
        
        return existing_version != current_version
    



