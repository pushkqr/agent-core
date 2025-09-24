from src.templates.base_agent import BaseAgent

TEMPLATE_VERSION = "1.0.0"

class Agent(BaseAgent):
    def __init__(self, name, system_message, spec) -> None:
        super().__init__(name, system_message, spec)