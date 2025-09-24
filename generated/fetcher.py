from autogen_core import MessageContext, message_handler, AgentId
from autogen_agentchat.messages import TextMessage
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from src.templates.base_agent import BaseAgent
from src.utils import utils
import asyncio
import logging
import os
import time

logger = logging.getLogger("main")

TEMPLATE_VERSION = "1.0.0"

class Agent(BaseAgent):
    def __init__(self, name, system_message, spec) -> None:
        super().__init__(name, system_message, spec)
        self.spec = spec or {}
        self._tools_specs = spec.get("tools", []) or []
        self._delegate = None 

    async def setup_tools(self):
        try:
            all_tools = []
            for spec in self._tools_specs:
                try:
                    params = spec.get("params", {})
                    
                    if "env" in params:
                        resolved_env = {}
                        for key, value in params["env"].items():
                            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                                env_var = value[2:-1]
                                resolved_env[key] = os.getenv(env_var)
                                if resolved_env[key] is None:
                                    logger.warning(f"Environment variable {env_var} not found for tool {spec.get('name', 'unknown')}")
                            else:
                                resolved_env[key] = value
                        params["env"] = resolved_env
                    
                    server = StdioServerParams(**params)
                    tools = await mcp_server_tools(server)
                    all_tools.extend(tools)
                    logger.info(f"Successfully loaded {len(tools)} tools from {spec.get('name', 'unknown')}")
                    
                except Exception as e:
                    logger.error(f"Failed to load tools from {spec.get('name', 'unknown')}: {e}")
                    continue

            await self._setup_delegate(all_tools)
            logger.info(f"Successfully initialized {self._name} with {len(all_tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to setup tools for {self._name}: {e}")
            await self._setup_delegate([])
            logger.warning(f"Initialized {self._name} without tools due to setup failure")

    def _get_error_context(self) -> str:
        context = []
        if self._tools_specs:
            context.append(f"Tools configured: {len(self._tools_specs)}")
            tool_names = [spec.get('name', 'unknown') for spec in self._tools_specs]
            context.append(f"Tool names: {', '.join(tool_names)}")
        if self._delegate:
            context.append("Delegate initialized")
        else:
            context.append("Delegate not initialized")
        if self._last_activity:
            context.append(f"Last activity: {time.time() - self._last_activity:.1f}s ago")
        return "; ".join(context)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        if self._delegate is None:
            await self.setup_tools()

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