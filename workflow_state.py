import asyncio
from typing import Optional, Tuple

class WorkflowState:
    def __init__(self) -> None:
        self._completion_event: asyncio.Event = asyncio.Event()
        self._result: Optional[str] = None
        self._error: Optional[str] = None
    
    def set_completion(self, result: str) -> None:
        self._result = result
        self._completion_event.set()
    
    def set_error(self, error: str) -> None:
        self._error = error
        self._completion_event.set()
    
    async def wait_for_completion(self) -> Tuple[bool, str]:
        await self._completion_event.wait()
        if self._error:
            return False, self._error
        return True, self._result or "No result"
    
    def reset(self) -> None:
        self._completion_event.clear()
        self._result = None
        self._error = None


workflow_state = WorkflowState()