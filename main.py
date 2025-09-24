import asyncio
import os
from src.utils import utils
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost, GrpcWorkerAgentRuntime
from autogen_core import AgentId
from src.agents.creator import Creator
import logging
from src.utils.utils import setup_logging
import yaml
from src.agents.end import End
from workflow_state import workflow_state
from dotenv import load_dotenv

setup_logging(logging.DEBUG)
logger = logging.getLogger("main")


async def main() -> None:
    load_dotenv(override=True)
    workflow_state.reset()
    
    logger.info("Starting host and worker")
    host = GrpcWorkerAgentRuntimeHost(address="localhost:50051")
    worker = GrpcWorkerAgentRuntime(host_address="localhost:50051")

    try:
        host.start()
        await worker.start()

        logger.info("Registering Creator agent")
        await Creator.register(worker, "Creator", lambda: Creator("Creator"))
        creator_id = AgentId("Creator", "default")

        logger.info("Registering End agent")
        await End.register(worker, "End", lambda: End("End"))
        end_id = AgentId("End", "default")

        with open("config/agents.yaml", "r") as f:
            spec = yaml.safe_load(f)

        content = yaml.safe_dump(spec)

        await asyncio.sleep(1)

        logger.info("Sending message to Creator")
        await worker.send_message(utils.Message(content=content, sender="Host"), creator_id)
        
        timeout_seconds = int(os.getenv("WORKFLOW_TIMEOUT", "300"))
        
        try:
            success, result = await asyncio.wait_for(
                workflow_state.wait_for_completion(), 
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            timeout_minutes = timeout_seconds // 60
            logger.error(f"❌ Workflow timed out after {timeout_minutes} minutes")
            success, result = False, f"Workflow timed out after {timeout_minutes} minutes"
        
        if success:
            logger.info(f"✅ Workflow completed successfully!")
            logger.info(f"Result: {result}")
        else:
            logger.error(f"❌ Workflow failed: {result}")
            
    except Exception as e:
        logger.error(f"Main process error: {e}")

    finally:
        logger.info("Stopping worker and host cleanly")
        try:
            await worker.stop()
        except Exception as e:
            logger.error(f"Error stopping worker: {e}")
        
        try:
            await host.stop()
        except Exception as e:
            logger.error(f"Error stopping host: {e}")


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("Main process completed")
