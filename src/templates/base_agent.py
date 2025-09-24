from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.utils import utils
import os
import logging
from src.utils.utils import setup_logging
from typing import Optional, List, Any

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")

TEMPLATE_VERSION = "1.0.0"

class BaseAgent(RoutedAgent):
    def __init__(self, name: str, system_message: str, spec: Optional[dict] = None) -> None:
        super().__init__(name)
        self.spec: dict = spec or {}
        self._system_message: str = system_message
        self._name: str = name
        self._delegate: Optional[AssistantAgent] = None

    async def _setup_delegate(self, tools: Optional[List[Any]] = None) -> None:
        model_client = OpenAIChatCompletionClient(
            model=utils.MODEL_NAME,
            model_info=utils.GEMINI_INFO,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        self._delegate = AssistantAgent(
            self._name,
            model_client=model_client,
            system_message=self._system_message,
            tools=tools or [],
            reflect_on_tool_use=bool(tools)
        )

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        if self._delegate is None:
            await self._setup_delegate()

        logger.info(f"{self.id.type}: Received message\nFrom: {message.sender}")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        result = utils.Message(content=response.chat_message.content, sender=self.spec.get("agent_name", "agent"))

        output_to = self.spec.get("output_to")
        if output_to:
            logger.debug(f"Agent: {self.spec.get('agent_name', 'agent')} --> to: {output_to}")
            await self.send_message(result, AgentId(output_to, "default"))
        else:
            logger.debug(f"Agent: {self.spec.get('agent_name', 'agent')} --> to: End")
            await self.send_message(result, AgentId("End", "default"))
        
        return utils.Message(content="", sender=self.spec.get("agent_name", "agent"))
