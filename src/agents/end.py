from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.utils.prompts import Prompts
from src.utils import utils
import os
import logging
from workflow_state import workflow_state
import asyncio

logger = logging.getLogger("main")


class End(RoutedAgent):
    def __init__(self, name) -> None:
        super().__init__(name)
        prompt = Prompts.get_end_system_message()
        model_client = OpenAIChatCompletionClient(model=utils.MODEL_NAME, model_info=utils.GEMINI_INFO, api_key=os.getenv("GOOGLE_API_KEY"))
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=prompt)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.debug(f"🏁 End: Received final message from {message.sender}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        logger.debug(f"🎉 Workflow completed successfully!")
        logger.debug(f"📋 Final result: {response.chat_message.content}")
        workflow_state.set_completion(response.chat_message.content)
        
        return utils.Message(content="", sender="End")