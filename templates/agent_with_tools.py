from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
import utils
import asyncio
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
    def __init__(self, name, system_message, spec) -> None:
        super().__init__(name)
        self._system_message = system_message
        self._name = name
        self.spec = spec or {}
        self._tools_specs = spec["tools"] or []
        self._delegate = None 
        asyncio.get_event_loop().create_task(self.setup_tools())


    async def setup_tools(self):
        """Initialize AssistantAgent with all tools resolved from MCP servers."""
        model_client = OpenAIChatCompletionClient(
            model=utils.MODEL_NAME,
            model_info=utils.GEMINI_INFO,
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        all_tools = []
        for spec in self._tools_specs:
            params = spec.get("params", {})
            
            if "env" in params:
                resolved_env = {}
                for key, value in params["env"].items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        resolved_env[key] = os.getenv(env_var)
                    else:
                        resolved_env[key] = value
                params["env"] = resolved_env
            
            server = StdioServerParams(**params)
            tools = await mcp_server_tools(server)
            all_tools.extend(tools)

        self._delegate = AssistantAgent(
            self._name,
            model_client=model_client,
            system_message=self._system_message,
            tools=all_tools,
            reflect_on_tool_use=True
        )

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext):
        if self._delegate is None:
            await self._setup_tools()

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
