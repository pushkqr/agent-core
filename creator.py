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

    def get_user_prompt(self): 
        logger.debug("Building user prompt for Calculator Agent generation")
        prompt = (
            "Please generate a new Calculator Agent based strictly on this template. "
            "The class must still be named Agent, inherit from RoutedAgent, and have an __init__ "
            "method that takes a name parameter. The agent should be able to evaluate basic math "
            "expressions like 'Add 3 + 5'. Respond only with the python code, no extra text, "
            "and no markdown code blocks.\n\nHere is the template:\n\n"
        )
        with open("agent.py", "r", encoding="utf-8") as f: 
            template = f.read() 
        return prompt + template

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.info(f"Creator received message: {message.content}")
        filename = message.content
        agent_name = filename.split(".")[0]

        text_message = TextMessage(content=self.get_user_prompt(), source="user")
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

        with open(filename, "w", encoding="utf-8") as f:
            f.write(generated_code)
        logger.info(f"Saved generated agent code to {filename}")


        if agent_name in sys.modules:
            logger.debug(f"Reloading existing module {agent_name}")
            importlib.reload(sys.modules[agent_name])
        module = importlib.import_module(agent_name)

        await module.Agent.register(self.runtime, agent_name, lambda: module.Agent(agent_name))
        logger.info(f"Agent {agent_name} registered and live")

        test_message = utils.Message(content="Add 3 + 5")
        logger.info(f"Sending test message to {agent_name}: {test_message.content}")
        result = await self.send_message(test_message, AgentId(agent_name, "default"))
        logger.info(f"Test result from {agent_name}: {result.content}")

        return utils.Message(content=result.content)
