class Prompts:

    @staticmethod
    def get_creator_system_message():
        CREATOR_SYSTEM_MESSAGE = """
    You are an Agent that is able to create new AI Agents.
    You receive a template in the form of Python code that creates an Agent using Autogen Core and Autogen Agentchat.
    You should use this template to create a new Agent with a unique system message that is different from the template, and reflects their unique characteristics, interests and goals. 
    The requirement is that the class must be named Agent, and it must inherit from RoutedAgent and have an __init__ method that takes a name parameter. 
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
            f"exact __init__ method signature from the template. The agent should reflect the following description:\n"
            f"{description}\n\n"
            f"Here is the required system message:\n{system_message}\n\n"
            f"Respond only with valid Python code, no explanations or markdown fences.\n\n"
            "Here is the template:\n\n"
        )
        return CREATOR_PROMPT
    
    @staticmethod
    def get_end_system_message():
        PROMPT = (
            f"You are the agent at the endpoint of the system's workflow."
            f"You may recieve error messages."
            f"You may recieve successfull output from the execution of the entire generated workflow"
            f"You interpret the input and concisely frame the end output (whether error or success)"
            f"You reply in plain text and plain text only. No markdown or anything else."
        )
        return PROMPT