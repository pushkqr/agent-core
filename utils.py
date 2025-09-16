from dataclasses import dataclass
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import ModelInfo

@dataclass
class Message:
    content: str

GEMINI_INFO = ModelInfo(
    family="gemini",
    vision=True, 
    function_calling=True,
    json_output=True,
    structured_output=True
)

MODEL_NAME = "gemini-2.5-flash-lite"