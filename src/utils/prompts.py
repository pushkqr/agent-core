class Prompts:

    @staticmethod
    def get_creator_system_message():
        CREATOR_SYSTEM_MESSAGE = """
    You are an Agent that creates new AI Agents based on provided templates.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You must use the EXACT template provided and ONLY modify the specific parts that need to be customized.
    
    CRITICAL REQUIREMENTS:
    1. The class must be named Agent
    2. It must inherit from RoutedAgent
    3. The __init__ method must have EXACTLY this signature: def __init__(self, name, system_message, spec) -> None:
    4. You MUST use the system_message parameter passed to __init__ as the agent's prompt - DO NOT generate your own
    5. You MUST store the spec parameter as self.spec = spec or {}
    6. Follow the template structure EXACTLY - only replace placeholders with the provided values
    
    Respond ONLY with valid Python code. 
    Do NOT include any extra markers, TERMINATE statements, explanations, or Markdown fences. 
    The code must be directly executable and importable.
    """
        return CREATOR_SYSTEM_MESSAGE

    @staticmethod
    def get_creator_prompt(description, system_message):
        CREATOR_PROMPT = (
            f"Please generate a new Agent based on this template. "
            f"The class must still be named Agent, inherit from RoutedAgent, and follow the "
            f"EXACT __init__ method signature: def __init__(self, name, system_message, spec) -> None:\n\n"
            f"IMPORTANT: Use the system_message parameter as the agent's prompt - DO NOT generate your own system message.\n"
            f"IMPORTANT: Store the spec parameter as self.spec = spec or {{}}.\n\n"
            f"The agent should reflect the following description:\n"
            f"{description}\n\n"
            f"Here is the REQUIRED system message to use:\n{system_message}\n\n"
            f"Use this EXACT system message in the agent - do not modify or generate a different one.\n\n"
            f"Respond only with valid Python code, no explanations or markdown fences.\n\n"
            "Here is the template:\n\n"
        )
        return CREATOR_PROMPT
    
    @staticmethod
    def get_end_system_message():
        PROMPT = (
            "You are the agent at the endpoint of the system's workflow.\n"
            "You will receive either a normal result(success or error) or an error message with explicit reason from the workflow execution.\n"
            "Your job is to interpret the input and output a concise natural language message to the user.\n"
            "reply in the format: success: {result}, where {result} is your clear, plain-language summary of the outcome.\n"
            "Do not include any markdown, code fences, or extra formatting—just plain text as described."
        )
        return PROMPT