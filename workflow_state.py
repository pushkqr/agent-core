import asyncio
from typing import Optional

class WorkflowState:
    def __init__(self):
        self._completion_event = asyncio.Event()
        self._result: Optional[str] = None
        self._error: Optional[str] = None
    
    def set_completion(self, result: str):
        """Set the workflow result and signal completion"""
        self._result = result
        self._completion_event.set()
    
    def set_error(self, error: str):
        """Set an error and signal completion"""
        self._error = error
        self._completion_event.set()
    
    async def wait_for_completion(self) -> tuple[bool, str]:
        """Wait for workflow completion. Returns (success, result_or_error)"""
        await self._completion_event.wait()
        if self._error:
            return False, self._error
        return True, self._result or "No result"
    
    def reset(self):
        """Reset the state for a new workflow"""
        self._completion_event.clear()
        self._result = None
        self._error = None


workflow_state = WorkflowState()