from dataclasses import dataclass
from autogen_ext.models.openai._model_info import ModelInfo
import logging
from typing import Any

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
    

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        prefix = f"[{record.levelname}]"
        msg = super().format(record)
        
        return f"{color}{prefix}{self.RESET} {msg}"
    
def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(asctime)s - %(name)s - %(message)s"))
    logging.basicConfig(level=level, handlers=[handler])
    
    autogen_loggers = [
        "autogen_core",
        "autogen_agentchat", 
        "autogen_ext",
        "autogen_ext.runtimes.grpc",
        "autogen_ext.models.openai",
        "autogen_ext.tools.mcp"
    ]
    
    if level == logging.DEBUG:
        for logger_name in autogen_loggers:
            logging.getLogger(logger_name).setLevel(logging.DEBUG)
    else:
        for logger_name in autogen_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

GEMINI_INFO = ModelInfo(
    family="gemini",
    vision=True, 
    function_calling=True,
    json_output=True,
    structured_output=True
)

MODEL_NAME = "gemini-2.5-flash"