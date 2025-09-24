from autogen_core import MessageContext, RoutedAgent, message_handler, AgentId
from src.utils import utils
import logging
from workflow_state import workflow_state

logger = logging.getLogger("main")


class End(RoutedAgent):
    def __init__(self, name) -> None:
        super().__init__(name)

    @message_handler
    async def handle_message(self, message: utils.Message, ctx: MessageContext) -> utils.Message:
        logger.debug(f"🏁 End: Received final message from {message.sender}")
        logger.debug(f"🎉 Workflow completed successfully!")
        logger.debug(f"📋 Final result: {message.content}")
        workflow_state.set_completion(message.content)
        
        return utils.Message(content="", sender="End")