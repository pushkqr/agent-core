from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.utils import utils
import os
import logging
import asyncio
import time
from typing import Optional, List, Any

logger = logging.getLogger("main")

TEMPLATE_VERSION = "1.0.0"

class BaseAgent(RoutedAgent):
    def __init__(self, name: str, system_message: str, spec: Optional[dict] = None) -> None:
        super().__init__(name)
        self.spec: dict = spec or {}
        self._system_message: str = system_message
        self._name: str = name
        self._delegate: Optional[AssistantAgent] = None
        self._timeout: int = spec.get('timeout', 30) if spec else 30
        self._last_activity: Optional[float] = None

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

    def _get_error_context(self) -> str:
        context = []
        if hasattr(self, '_tools_specs') and self._tools_specs:
            context.append(f"Tools configured: {len(self._tools_specs)}")
        if self._delegate:
            context.append("Delegate initialized")
        else:
            context.append("Delegate not initialized")
        if self._last_activity:
            context.append(f"Last activity: {time.time() - self._last_activity:.1f}s ago")
        return "; ".join(context)

    def _get_last_activity(self) -> str:
        if self._last_activity:
            return f"{time.time() - self._last_activity:.1f}s ago"
        return "unknown"

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        self._last_activity = time.time()
        
        if self._delegate is None:
            await self._setup_delegate()

        logger.debug(f"📨 {self._name}: Received message from {message.sender}")
        text_message = TextMessage(content=message.content, source="user")
        
        try:
            response = await asyncio.wait_for(
                self._delegate.on_messages([text_message], ctx.cancellation_token),
                timeout=self._timeout
            )
            result_content = response.chat_message.content
            logger.info(f"✅ {self._name}: Completed")
            
        except asyncio.TimeoutError:
            result_content = f"Agent {self._name} timed out after {self._timeout}s. Last activity: {self._get_last_activity()}. Context: {self._get_error_context()}"
            logger.error(f"⏰ {self._name}: TIMEOUT after {self._timeout}s")
            
        except Exception as e:
            result_content = f"Agent {self._name} failed: {str(e)}. Context: {self._get_error_context()}"
            logger.error(f"❌ {self._name}: ERROR - {str(e)}")

        result = utils.Message(content=result_content, sender=self.spec.get("agent_name", "agent"))

        output_to = self.spec.get("output_to")
        if output_to:
            logger.debug(f"📤 {self._name}: Sending message to {output_to}")
            await self.send_message(result, AgentId(output_to, "default"))
        else:
            logger.debug(f"📤 {self._name}: Sending message to End")
            await self.send_message(result, AgentId("End", "default"))
        
        return utils.Message(content="", sender=self.spec.get("agent_name", "agent"))
