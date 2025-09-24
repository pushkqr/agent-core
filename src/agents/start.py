from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from src.utils import utils
from workflow_state import workflow_state
import logging
import json
import asyncio

logger = logging.getLogger("main")


class Start(RoutedAgent):
    def __init__(self, name) -> None:
        super().__init__(name)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.debug(f"🚀 Start: Received workflow spec from {message.sender}")
        
        try:
            workflow_spec = json.loads(message.content)
        except json.JSONDecodeError as e:
            logger.error(f"Start: Failed to parse workflow spec: {e}")
            workflow_state.set_error(f"Failed to parse workflow spec: {e}")
            return utils.Message(content="", sender="Start")
        
        agents = workflow_spec.get("agents", [])
        head_agent = workflow_spec.get("head_agent", {})
        workflow_config = workflow_spec.get("workflow_config", {})
        
        if not agents or not head_agent:
            error_msg = "Invalid workflow spec - missing agents or head_agent"
            logger.error(f"Start: {error_msg}")
            workflow_state.set_error(error_msg)
            await self.send_message(
                utils.Message(content=f"❌ {error_msg}", sender="Start"), 
                AgentId("End", "default")
            )
            return utils.Message(content="", sender="Start")
        
        # Validate that head agent is actually registered
        head_agent_name = head_agent.get('agent_name')
        if head_agent_name not in agents:
            error_msg = f"Head agent '{head_agent_name}' not found in registered agents"
            logger.error(f"Start: {error_msg}")
            workflow_state.set_error(error_msg)
            await self.send_message(
                utils.Message(content=f"❌ {error_msg}", sender="Start"), 
                AgentId("End", "default")
            )
            return utils.Message(content="", sender="Start")
        
        # Determine input mode and get start message
        input_mode = workflow_config.get("input_mode", "test_message")
        
        if input_mode == "interactive":
            start_message = await self._get_interactive_input(workflow_config)
        else:
            start_message = head_agent.get('test_message', '')
        
        if not start_message:
            error_msg = "No start message available"
            logger.error(f"Start: {error_msg}")
            workflow_state.set_error(error_msg)
            await self.send_message(
                utils.Message(content=f"❌ {error_msg}", sender="Start"), 
                AgentId("End", "default")
            )
            return utils.Message(content="", sender="Start")
        
        # Start the workflow
        head_agent_name = head_agent.get('agent_name')
        logger.info(f"🚀 Starting workflow with agent: {head_agent_name}")
        logger.debug(f"🚀 Start message: {start_message}")
        
        try:
            await self.send_message(
                utils.Message(content=start_message, sender="Start"), 
                AgentId(head_agent_name, "default")
            )
        except Exception as e:
            error_msg = f"Failed to send message to {head_agent_name}: {e}"
            logger.error(f"❌ Start: {error_msg}")
            workflow_state.set_error(error_msg)
            # Send error to End agent
            await self.send_message(
                utils.Message(content=f"❌ Failed to start workflow: {e}", sender="Start"), 
                AgentId("End", "default")
            )
            return utils.Message(content="", sender="Start")
        
        return utils.Message(content="", sender="Start")
    
    async def _get_interactive_input(self, workflow_config: dict) -> str:
        """Get interactive input from user"""
        input_prompt = workflow_config.get("input_prompt", "What would you like me to help you with?")
        input_timeout = workflow_config.get("input_timeout", 30.0)
        
        logger.info(f"🔄 Interactive mode: {input_prompt}")
        
        try:
            input_task = asyncio.create_task(self._collect_user_input(input_prompt))
            user_input = await asyncio.wait_for(input_task, timeout=input_timeout)
            
            if user_input and user_input.strip():
                logger.info(f"✅ User input received: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
                return user_input.strip()
            else:
                logger.warning("⚠️ No user input received, using fallback message")
                return "No input provided - proceeding with default workflow"
                
        except asyncio.TimeoutError:
            logger.warning("⏰ Input timeout - using fallback message")
            return "Input timeout - proceeding with default workflow"
        except Exception as e:
            logger.error(f"❌ Error collecting input: {e}")
            return "Error collecting input - proceeding with default workflow"
    
    async def _collect_user_input(self, prompt: str) -> str:
        """Collect user input asynchronously"""
        import sys
        
        print(f"\n🤖 {prompt}")
        print("💬 Your input: ", end="", flush=True)
        
        loop = asyncio.get_event_loop()
        def read_input():
            try:
                return input()
            except (EOFError, KeyboardInterrupt):
                return ""
        
        user_input = await loop.run_in_executor(None, read_input)
        return user_input
