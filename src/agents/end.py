from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.utils.prompts import Prompts
from src.utils import utils
import os
from dotenv import load_dotenv
import logging
from src.utils.utils import setup_logging
from workflow_state import workflow_state
import asyncio

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(override=True, dotenv_path=os.path.join(project_root, ".env"))


class End(RoutedAgent):
    def __init__(self, name) -> None:
        super().__init__(name)
        prompt = Prompts.get_end_system_message()
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=prompt)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.info(f"{self.id.type}: Received message\nFrom: {message.sender}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        logger.info(f"Workflow completed with result: {response.chat_message.content}")
        workflow_state.set_completion(response.chat_message.content)
        
        return utils.Message(content="", sender="End")