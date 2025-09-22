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

    def __init__(self, name):
        super().__init__(name)
        system_message = Prompts.get_creator_system_message()
        logger.debug(f"Initializing Creator agent: {name}")
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=system_message)
        logger.debug("Delegate AssistantAgent initialized")

    def get_generation_prompt(self, description: str, system_message: str, template_file: str):
        logger.debug("Building user prompt for Agent generation")
        prompt = Prompts.get_creator_prompt(description, system_message)

        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template


    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext):
        logger.info(f"Creator received message: {message.content}")
        
        try:
            config = yaml.safe_load(message.content)
        except yaml.YAMLError as e:
            await self.send_message(utils.Message(content=f"YAML parse error: {e}", sender="Creator"), AgentId("End", "default"))
        
        if "agents" not in config or not isinstance(config["agents"], list):
            self.send_message(utils.Message(content="YAML must have a top-level 'agents' list.", sender="Creator"), AgentId("End", "default"))

        agents = config.get("agents", [])
        all_errors = []
        results = []
        response_parts = []
        registered_agents = {}

        workflow_error = Creator.validate_workflow(agents)

        if not workflow_error:
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

                try:
                    creator_func = lambda: module.Agent(agent_name, system_message, spec)
                    logger.info(f"Registering agent {agent_name}")
                    await module.Agent.register(self.runtime, agent_name, creator_func)
                    await self.init_agent(agent_name)
                    logger.info(f"Agent {agent_name} registered and live")  
                    
                except Exception as e:
                    logger.error(f"Failed to register agent {agent_name}: {e}")
                    all_errors.append(f"{agent_name}: Failed to register -> {e}")
                    continue
                
                registered_agents[agent_name] = spec
            
        else:
            all_errors.append(workflow_error)           

        
        if results:
            response_parts.append("✅ Registered agents:\n" + "\n".join(results))
        if all_errors:
            response_parts.append("❌ Spec validation errors:\n" + "\n\n".join(all_errors))
        
        await self.send_message(utils.Message(content="\n\n".join(response_parts), sender="Creator"), AgentId("End", "default"))
    
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
    def validate_workflow(agents):
        errors = []

        agent_names = [spec.get("agent_name") for spec in agents]

        for spec in agents:
            output_to = spec.get("output_to")

            if output_to and output_to not in agent_names:
                errors.append(f"Agent {spec.get('agent_name')} references non-existent agent: {output_to}")
        
        return errors
    

    
    def get_template_version(self, template_file):
        with open(template_file, "r") as f:
            content = f.read()
           
            match = re.search(r'TEMPLATE_VERSION = "([^"]+)"', content)
            return match.group(1) if match else "unknown"
        
    def should_regenerate(self, filename, template_file):
        if not os.path.exists(filename):
            return True
        
        with open(filename, "r") as f:
            existing_content = f.read()
            existing_version = re.search(r'TEMPLATE_VERSION = "([^"]+)"', existing_content)
            existing_version = existing_version.group(1) if existing_version else "unknown"

        current_version = self.get_template_version(template_file)
        return existing_version != current_version
    
    async def init_agent(self, agent_name):
        test_msg = utils.Message(content="ping", sender="Creator")
        await self.send_message(test_msg, AgentId(agent_name, "default"))



