from dataclasses import dataclass
from autogen_ext.models.openai._model_info import ModelInfo
import logging

@dataclass
class Message:
    content: str
    sender: str

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[90m", 
        "INFO": "\033[94m",  
        "WARNING": "\033[93m",
        "ERROR": "\033[91m", 
        "CRITICAL": "\033[95m",
    }
    RESET = "\033[0m"
    

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        prefix = f"[{record.levelname}]"
        msg = super().format(record)
        
        return f"{color}{prefix}{self.RESET} {msg}"
    
def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(asctime)s - %(name)s - %(message)s"))
    logging.basicConfig(level=level, handlers=[handler])

GEMINI_INFO = ModelInfo(
    family="gemini",
    vision=True, 
    function_calling=True,
    json_output=True,
    structured_output=True
)

MODEL_NAME = "gemini-2.5-flash"