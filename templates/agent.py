from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import utils
import os
from dotenv import load_dotenv
import logging
from utils import setup_logging

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(override=True, dotenv_path=os.path.join(project_root, ".env"))

TEMPLATE_VERSION = "1.0.3"

class Agent(RoutedAgent):
    def __init__(self, name, system_message, spec):
        super().__init__(name)
        self.spec = spec or {}
        prompt = system_message
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=prompt)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext):
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        result = utils.Message(content=response.chat_message.content, sender=self.spec["agent_name"])

        if("ping" in message.content):
            pass
        elif(self.spec["output_to"]):
            logger.debug(f"Agent: {self.spec["agent_name"]} --> o: {self.spec["output_to"]}")
            await self.send_message(result, AgentId(self.spec["output_to"], "default"))
        else:
            await self.send_message(result, AgentId("End", "default"))
  