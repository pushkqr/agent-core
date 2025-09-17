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
import json

load_dotenv(override=True)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(TRACE_LOGGER_NAME)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Creator(RoutedAgent):
    system_message = """ 
    You are an Agent that is able to create new AI Agents.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template, and reflects their unique characteristics, interests and goals. 
    The requirement is that the class must be named Agent, and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter. 
    Respond ONLY with valid Python code. 
    Do NOT include any extra markers, TERMINATE statements, explanations, or Markdown fences. 
    The code must be directly executable and importable.
    """

    def __init__(self, name) -> None:
        super().__init__(name)
        logger.debug(f"Initializing Creator agent: {name}")
        model_client = OpenAIChatCompletionClient(
            model=utils.MODEL_NAME,
            model_info=utils.GEMINI_INFO,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        self._delegate = AssistantAgent(name, model_client=model_client)
        logger.debug("Delegate AssistantAgent initialized")

    def get_user_prompt(self, description: str, system_message: str):
        logger.debug("Building user prompt for Agent generation")
        prompt = (
            f"Please generate a new Agent based on this template. "
            f"The class must still be named Agent, inherit from RoutedAgent, and have an __init__ "
            f"method that takes a name parameter. The agent should reflect the following description:\n"
            f"{description}\n\n"
            f"Here is the required system message:\n{system_message}\n\n"
            f"Respond only with valid Python code, no explanations or markdown fences.\n\n"
            "Here is the template:\n\n"
        )
        with open("agent.py", "r", encoding="utf-8") as f:
            template = f.read()
        return prompt + template


    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.info(f"Creator received message: {message.content}")
        try:
            spec = json.loads(message.content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid spec JSON: {e}")
            return utils.Message(content=f"Error: invalid spec JSON - {e}")

        filename = spec.get("filename", "agents/new_agent.py")
        agent_name = spec.get("agent_name", os.path.splitext(os.path.basename(filename))[0])
        module_path = f"agents.{agent_name}"
        description = spec.get("description", "An AI agent.")
        system_message = spec.get("system_message", "You are an AI agent.")

        text_message = TextMessage(
            content=self.get_user_prompt(description, system_message),
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
            return utils.Message(content=f"Syntax error in generated code: {e}")

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(generated_code)
        logger.info(f"Saved generated agent code to {filename}")


        if module_path in sys.modules:
            logger.debug(f"Reloading existing module {agent_name}")
            importlib.reload(sys.modules[module_path])
        module = importlib.import_module(module_path)

        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        logger.info(f"Agent {agent_name} registered and live")

        test_message = utils.Message(content="Add 3 + 5")
        logger.info(f"Sending test message to {agent_name}: {test_message.content}")
        result = await self.send_message(test_message, AgentId(agent_name, "default"))
        logger.info(f"Test result from {agent_name}: {result.content}")

        return utils.Message(content=result.content)
